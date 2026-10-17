"""Treina, compara e salva o modelo de estimativa de aluguel.

Etapas:
  1. lê o CSV do coletor e limpa (duplicados, faixas, outliers)
  2. separa 20% para teste final, sem misturar anúncios quase idênticos (RIA05)
  3. compara os candidatos por validação cruzada só no treino (RIA03/RIA04)
  4. avalia o vencedor no teste, geral e por faixa de preço
  5. calcula o intervalo de incerteza e a importância global das features
  6. re-treina o vencedor com todos os dados e salva modelo + metadados (RIA08)

Uso:
    python treinar.py                       # lê ../rentmatch_coletor/data/imoveis_campinas.csv
    python treinar.py --csv data/sintetico.csv
    python treinar.py --ajustar             # busca de hiperparâmetros (mais demorado)
"""
import argparse
import hashlib
import json
import platform
import shutil
import sys
from datetime import datetime
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import sklearn
from sklearn.base import clone
from sklearn.inspection import permutation_importance
from sklearn.metrics import r2_score
from sklearn.model_selection import RandomizedSearchCV, cross_val_predict

import config_modelo as cfg
from candidatos import GRADES_AJUSTE, construir_candidatos
from preparo import carregar_csv, dobras_cv, limpar, montar_grupos, separar_treino_teste


def metricas(y, previsto) -> dict:
    y, p = np.asarray(y, float), np.asarray(previsto, float)
    erro = p - y
    ape = np.abs(erro) / y
    return {
        "mae": float(np.mean(np.abs(erro))),            # erro médio em R$
        "rmse": float(np.sqrt(np.mean(erro ** 2))),     # penaliza erros grandes
        "r2": float(r2_score(y, p)),                    # 1.0 = perfeito, 0 = igual à média
        "mape": float(np.mean(ape) * 100),              # erro médio em %
        "mediana_ape": float(np.median(ape) * 100),     # erro típico em %
        "n": int(len(y)),
    }


def _rotulo_faixa(valor):
    for minimo, maximo in cfg.FAIXAS_PRECO:
        if maximo is None or valor <= maximo:
            return f"{minimo}-{maximo}" if maximo is not None else f"{minimo}+"


def metricas_por_segmento(y, previsto, rotulos) -> dict:
    y, previsto = np.asarray(y, float), np.asarray(previsto, float)
    rotulos = np.asarray(rotulos)
    return {str(r): metricas(y[rotulos == r], previsto[rotulos == r])
            for r in sorted(set(rotulos)) if (rotulos == r).sum() >= 5}


def _hash_arquivo(caminho) -> str:
    with open(caminho, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()[:12]


def _json(o):
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.floating,)):
        return float(o)
    raise TypeError(type(o))


def executar(csv=None, saida=None, ajustar=False, min_linhas=cfg.MIN_LINHAS_TREINO,
             candidatos=None, n_folds=cfg.N_FOLDS_CV, verboso=True) -> dict:
    csv = csv or cfg.CSV_PADRAO
    saida = saida or cfg.ARTEFATOS_DIR
    saida.mkdir(parents=True, exist_ok=True)
    say = print if verboso else (lambda *a, **k: None)

    # 1. dados
    df, relatorio = limpar(carregar_csv(csv))
    say(f"\n[dados] {relatorio}")
    if len(df) < min_linhas:
        raise SystemExit(f"Só {len(df)} imóveis após a limpeza (mínimo {min_linhas}). "
                         "Rode o coletor antes ou use --min-linhas para forçar.")
    X, y, grupos = df[cfg.FEATURES], df[cfg.ALVO], montar_grupos(df)
    assert not set(cfg.FEATURES) & set(cfg.PROIBIDAS), "feature derivada do alvo (vazamento)"
    say(f"[dados] bairros distintos: {X['bairro'].nunique()} | tipos: {X['tipo'].nunique()} | "
        f"faltantes em taxas: {X['taxas'].isna().mean():.0%}")

    # 2. holdout de teste
    i_tr, i_te = separar_treino_teste(y, grupos, n_folds)
    X_tr, y_tr, g_tr = X.iloc[i_tr].reset_index(drop=True), y.iloc[i_tr].reset_index(drop=True), grupos[i_tr]
    X_te, y_te = X.iloc[i_te].reset_index(drop=True), y.iloc[i_te].reset_index(drop=True)
    say(f"[split] treino={len(X_tr)} | teste={len(X_te)}")

    # 3. comparação por validação cruzada (só no treino)
    todos = construir_candidatos()
    escolhidos = {n: todos[n] for n in (candidatos or todos)}
    dobras = dobras_cv(y_tr, g_tr, n_folds)
    resultados, oof = {}, {}
    for nome, modelo in escolhidos.items():
        if ajustar and nome in GRADES_AJUSTE:
            busca = RandomizedSearchCV(modelo, GRADES_AJUSTE[nome], n_iter=cfg.N_ITER_AJUSTE, cv=dobras,
                                       scoring="neg_mean_absolute_error", random_state=cfg.SEMENTE,
                                       n_jobs=-1).fit(X_tr, y_tr)
            modelo = escolhidos[nome] = busca.best_estimator_
            say(f"[ajuste] {nome}: {busca.best_params_}")
        oof[nome] = cross_val_predict(modelo, X_tr, y_tr, cv=dobras)
        resultados[nome] = metricas(y_tr, oof[nome])
    say("\n[validação cruzada, só treino]")
    say(pd.DataFrame(resultados).T[["mae", "rmse", "r2", "mape", "mediana_ape"]].round(2).to_string())

    melhor = min(resultados, key=lambda n: resultados[n][cfg.METRICA_SELECAO])
    say(f"\n[escolhido] {melhor} (menor {cfg.METRICA_SELECAO.upper()})")

    # 4. teste final (dados que o modelo nunca viu)
    modelo_teste = clone(escolhidos[melhor]).fit(X_tr, y_tr)
    prev_te = modelo_teste.predict(X_te)
    teste = metricas(y_te, prev_te)
    por_faixa = metricas_por_segmento(y_te, prev_te, [_rotulo_faixa(v) for v in y_te])
    por_tipo = metricas_por_segmento(y_te, prev_te, X_te["tipo"])
    ganho = None
    if "baseline" in escolhidos and melhor != "baseline":
        base_te = clone(escolhidos["baseline"]).fit(X_tr, y_tr).predict(X_te)
        ganho = 100 * (1 - teste["mae"] / metricas(y_te, base_te)["mae"])
    say(f"\n[teste final] {({k: round(v, 2) for k, v in teste.items()})}")
    if ganho is not None:
        say(f"[teste final] erro médio {ganho:.0f}% menor que o baseline (mediana R$/m² do bairro)")
    say("[teste por faixa de preço]")
    say(pd.DataFrame(por_faixa).T[["n", "mae", "mape", "r2"]].round(2).to_string())

    # 5. incerteza e importância global
    erro_rel = (np.asarray(y_tr, float) - oof[melhor]) / oof[melhor]
    q_baixo, q_alto = np.quantile(erro_rel, cfg.QUANTIS_INTERVALO)
    imp = permutation_importance(modelo_teste, X_te, y_te, n_repeats=10, random_state=cfg.SEMENTE,
                                 scoring="neg_mean_absolute_error")
    importancia = {f: round(float(v), 2) for f, v in
                   sorted(zip(cfg.FEATURES, imp.importances_mean), key=lambda t: -t[1])}
    say(f"[importância global, aumento do MAE em R$ ao embaralhar] {importancia}")

    # 6. versão final com todos os dados
    final = clone(escolhidos[melhor]).fit(X, y)
    fundo = X.sample(min(cfg.N_FUNDO_EXPLICADOR, len(X)), random_state=cfg.SEMENTE).reset_index(drop=True)
    versao = datetime.now().strftime("%Y%m%d-%H%M%S")
    meta = {
        "versao": versao, "algoritmo": melhor, "features": cfg.FEATURES,
        "linhas_treino_final": int(len(X)), "limpeza": relatorio,
        "csv": str(csv), "csv_hash": _hash_arquivo(csv),
        "cv_treino": resultados, "teste": teste, "teste_por_faixa": por_faixa, "teste_por_tipo": por_tipo,
        "ganho_vs_baseline_pct": ganho, "importancia_global": importancia,
        "intervalo_erro_relativo": [float(q_baixo), float(q_alto)], "quantis": list(cfg.QUANTIS_INTERVALO),
        "bibliotecas": {"python": platform.python_version(), "sklearn": sklearn.__version__,
                        "pandas": pd.__version__, "numpy": np.__version__},
    }
    caminho = saida / f"modelo_{versao}.joblib"
    joblib.dump({"modelo": final, "fundo": fundo, "intervalo_erro": (float(q_baixo), float(q_alto)),
                 "meta": meta}, caminho)
    (saida / f"metadados_{versao}.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2, default=_json), encoding="utf-8")
    shutil.copyfile(caminho, saida / "modelo_atual.joblib")
    shutil.copyfile(saida / f"metadados_{versao}.json", saida / "metadados_atual.json")
    say(f"\n[salvo] {caminho} (e modelo_atual.joblib)")
    return meta


def main():
    ap = argparse.ArgumentParser(description="Treino do modelo RentMatch")
    ap.add_argument("--csv", type=Path)
    ap.add_argument("--ajustar", action="store_true", help="busca de hiperparâmetros")
    ap.add_argument("--min-linhas", type=int, default=cfg.MIN_LINHAS_TREINO)
    ap.add_argument("--candidatos", nargs="+", help="ex.: --candidatos baseline ridge hgb")
    args = ap.parse_args()
    executar(csv=args.csv, ajustar=args.ajustar, min_linhas=args.min_linhas, candidatos=args.candidatos)


if __name__ == "__main__":
    sys.exit(main())