"""Executa somente a validação cruzada, mantendo o fluxo atual de treinar.py.

Uso, a partir da raiz do projeto:
    python modelo_ml/validar.py
    python modelo_ml/validar.py --candidatos baseline ridge

Reserva o mesmo holdout de teste e compara os candidatos nas mesmas dobras.
Os ajustes dos modelos acontecem apenas dentro da validação cruzada: não há
avaliação do teste, retreino final ou gravação de um modelo de produção.
"""
import argparse
import hashlib
import json
import platform
from pathlib import Path

import numpy as np
import pandas as pd
import sklearn
from sklearn.model_selection import cross_val_predict

import config_modelo as cfg
from candidatos import construir_candidatos
from preparo import carregar_csv, dobras_cv, limpar, montar_grupos, separar_treino_teste
from treinar import metricas, metricas_por_segmento

METRICAS = ["mae", "rmse", "r2", "mape", "mediana_ape"]
SAIDA_PADRAO = cfg.BASE_DIR / "validacao"
LIMITACOES = [
    "Extremos dentro das faixas fixas são preservados. Não há remoção estatística "
    "de outliers antes da divisão. Endereços sem cidade identificável são mantidos "
    "e precisam de revisão na coleta.",
    "As métricas são usadas para escolher o modelo; a avaliação final depende do teste reservado.",
    "Não foi definido pelo grupo um limite de erro aceitável para aprovar o modelo.",
    "A validação usa os parâmetros padrão dos candidatos, sem busca de hiperparâmetros.",
]


def _numero(valor):
    return f"{valor:,.2f}".translate(str.maketrans({",": ".", ".": ","}))


def _tabela(cabecalho, linhas):
    return "\n".join([
        "| " + " | ".join(cabecalho) + " |",
        "| " + " | ".join(["---"] * len(cabecalho)) + " |",
        *("| " + " | ".join(map(str, linha)) + " |" for linha in linhas),
    ])


def _faixa_preco(valor):
    for minimo, maximo in cfg.FAIXAS_PRECO:
        if maximo is None or valor <= maximo:
            return f"{minimo}-{maximo}" if maximo is not None else f"{minimo}+"


def _analise(relatorio, comparacao, previsoes):
    """Produz uma análise reproduzível, calculada a partir desta execução."""
    divisao = relatorio["divisao"]
    melhor = relatorio["modelo_escolhido"]
    resultado = relatorio["cv_treino"][melhor]
    dispersao = comparacao.loc[melhor]
    limpeza = relatorio["limpeza"]
    linhas = [
        "# Análise da validação do RentMatch", "",
        "## Como reproduzir", "",
        "Na raiz do projeto, com as dependências de `modelo_ml/requirements.txt` instaladas:", "",
        "```powershell", "python modelo_ml/validar.py", "```", "",
        "Use `--csv caminho.csv`, `--saida pasta` ou `--candidatos baseline ridge` "
        "para escolher a entrada, a pasta dos relatórios ou os candidatos. "
        "Essas opções podem produzir resultados diferentes dos apresentados aqui.", "",
        "## Dados e método", "",
        f"- CSV avaliado: `{relatorio['csv']}`.",
        f"- SHA-256 do CSV: `{relatorio['csv_sha256']}`.",
        f"- Semente: {relatorio['semente']}; dobras: {relatorio['n_dobras']}.",
        f"- Linhas lidas: {limpeza['linhas_lidas']}; após limpeza: {limpeza['linhas_finais']}.",
        f"- Descartes: {limpeza['duplicados_removidos']} duplicados, "
        f"{limpeza['fora_das_faixas_ou_sem_dados']} fora das faixas/sem dados e "
        f"{limpeza['outliers_removidos']} outliers e {limpeza['fora_da_cidade']} fora da cidade.",
        f"- Treino usado na validação cruzada: {divisao['linhas_treino']} anúncios "
        f"({_numero(divisao['percentual_treino'])}%).",
        f"- Teste reservado: {divisao['linhas_teste_reservado']} anúncios "
        f"({_numero(divisao['percentual_teste'])}%), sem ajuste ou previsão dos candidatos nessa parte.", "",
        "Foram reutilizadas a limpeza, a divisão agrupada e as funções de métricas do projeto. "
        "Anúncios do mesmo grupo ficam do mesmo lado da divisão e da dobra. "
        "Imputação, agrupamento de categorias raras e codificação são ajustados pelos pipelines "
        "apenas no treino de cada dobra. A limpeza anterior usa somente regras fixas.", "",
        "Cada anúncio da parte de treino recebe uma previsão fora da amostra: o modelo "
        "que faz essa previsão foi ajustado nas outras dobras. As métricas agregadas são "
        "calculadas juntando essas previsões; a média por dobra é apresentada separadamente.", "",
        "## Comparação dos modelos", "",
        _tabela(["Modelo", "MAE (R$)", "RMSE (R$)", "R²", "MAPE (%)", "Mediana APE (%)"], [
            [nome, *[_numero(fila[m]) for m in METRICAS]]
            for nome, fila in comparacao.iterrows()
        ]), "",
        "MAE é o erro absoluto médio em reais e orienta a escolha. RMSE dá mais peso "
        "a erros grandes. R² compara as previsões com a média dos aluguéis. "
        "MAPE e mediana APE expressam o erro percentual médio e mediano.", "",
        "## Escolha e estabilidade", "",
        f"O candidato indicado para a etapa de teste é **{melhor}**, escolhido pelo menor "
        f"{relatorio['metrica_selecao'].upper()}. Seu MAE agregado é "
        f"**R$ {_numero(resultado['mae'])}**, com MAPE de **{_numero(resultado['mape'])}%**.", "",
    ]
    ganho = relatorio["ganho_mae_vs_baseline_pct"]
    if melhor == "baseline":
        linhas += ["O baseline apresentou o menor MAE entre os candidatos incluídos nesta execução.", ""]
    elif ganho is not None:
        linhas += [f"O MAE foi **{_numero(ganho)}% menor** que o do baseline "
                   "(área × mediana do preço por m² do bairro).", ""]
    else:
        linhas += ["Não há comparação percentual com o baseline nesta execução "
                   "(não incluído ou com MAE igual a zero).", ""]
    if len(comparacao) > 1 and relatorio["metrica_selecao"] == "mae":
        segundo = comparacao.index[1]
        mae_segundo = float(comparacao.loc[segundo, "mae"])
        diferenca = mae_segundo - resultado["mae"]
        erros_melhor = [m["mae"] for m in relatorio["por_dobra"] if m["modelo"] == melhor]
        erros_segundo = [m["mae"] for m in relatorio["por_dobra"] if m["modelo"] == segundo]
        vitorias = sum(a < b for a, b in zip(erros_melhor, erros_segundo))
        linhas += [
            f"O segundo colocado foi **{segundo}**, com MAE de R$ {_numero(mae_segundo)}. "
            f"A diferença para {melhor} foi de **R$ {_numero(diferenca)}**. "
            f"O escolhido teve MAE menor que o segundo colocado em {vitorias} das "
            f"{relatorio['n_dobras']} dobras. A ordenação pelo MAE agregado "
            "não demonstra, sozinha, superioridade estatística entre os candidatos.", "",
        ]
    linhas += [
        f"Entre as dobras, o MAE do escolhido variou de R$ {_numero(dispersao['mae_min_dobras'])} "
        f"a R$ {_numero(dispersao['mae_max_dobras'])}; média de "
        f"R$ {_numero(dispersao['mae_media_dobras'])} e desvio padrão amostral de "
        f"R$ {_numero(dispersao['mae_desvio_dobras'])}. Esses valores mostram a variação "
        "entre as partições; o desvio padrão não é um intervalo de confiança.", "",
        "## Desempenho do escolhido por segmento", "",
    ]
    for titulo, chave in [("Tipo de imóvel", "validacao_por_tipo"), ("Faixa de aluguel (R$)", "validacao_por_faixa")]:
        segmentos = relatorio[chave]
        linhas += [f"### {titulo}", ""]
        linhas += [_tabela(["Segmento", "Anúncios", "MAE (R$)", "MAPE (%)"], [
            [nome, m["n"], _numero(m["mae"]), _numero(m["mape"])] for nome, m in segmentos.items()
        ]) if segmentos else "Nenhum segmento com pelo menos cinco anúncios.", ""]
    linhas += [
        "Segmentos com menos de cinco anúncios não são apresentados. Essas métricas "
        "também usam somente as previsões da validação cruzada.", "",
    ]
    faixas = relatorio["validacao_por_faixa"]
    if faixas:
        pior_faixa = max(faixas, key=lambda faixa: faixas[faixa]["mape"])
        linhas += [f"A faixa **{pior_faixa}** apresentou o maior erro percentual médio: "
                   f"**{_numero(faixas[pior_faixa]['mape'])}%**. Essa diferença entre faixas "
                   "deve entrar na avaliação de qualidade, além das métricas gerais.", ""]
    desconhecido = relatorio["validacao_por_tipo"].get("desconhecido")
    if desconhecido:
        linhas += [f"O tipo do imóvel está ausente em **{desconhecido['n']} anúncios** "
                   f"da parte usada para validação "
                   f"({_numero(100 * desconhecido['n'] / divisao['linhas_treino'])}%). "
                   "A revisão desses campos na coleta pode melhorar a informação disponível ao modelo.", ""]
    linhas += [
        "## Cinco maiores erros absolutos do escolhido", "",
        _tabela(["Anúncio", "Bairro", "Real (R$)", "Previsto (R$)", "Erro absoluto (R$)"], [
            [fila.id_anuncio, fila.bairro, _numero(fila.aluguel_real),
             _numero(fila.aluguel_previsto), _numero(abs(fila.erro_reais))]
            for fila in previsoes.loc[previsoes.erro_reais.abs().nlargest(5).index].itertuples()
        ]), "",
        "Esses anúncios são pontos para revisão dos dados e das características disponíveis. "
        "Um erro alto, por si só, não demonstra que o anúncio está incorreto.", "",
        "## Limitações e conclusão", "",
        *[f"- {texto}" for texto in relatorio["limitacoes"]], "",
        "A execução fornece evidência preliminar para selecionar um candidato. "
        "A aprovação para uso depende da revisão da limpeza, do limite de erro "
        "combinado pelo grupo e da avaliação final no teste reservado. Não foi gerado "
        "um modelo final nesta etapa.", "",
        "## Arquivos gerados", "",
        "- `resultados_validacao.csv`: métricas agregadas e variação do MAE entre dobras.",
        "- `metricas_por_dobra.csv`: métricas de cada modelo em cada dobra.",
        "- `previsoes_validacao.csv`: previsões fora da amostra do candidato escolhido.",
        "- `relatorio_validacao.json`: resultados, versões das bibliotecas e índices da divisão "
        "referentes ao CSV após a limpeza, para auditoria e reprodução.", "",
        "O erro em reais na tabela de previsões é `previsto - real`; valores positivos "
        "indicam superestimação. Para verificar os testes automatizados desta etapa:", "",
        "```powershell",
        'python -m unittest discover -s modelo_ml -p "test_validar.py" -v',
        "```", "",
    ]
    return "\n".join(linhas)


def executar(csv=None, saida=None, candidatos=None,
             min_linhas=cfg.MIN_LINHAS_TREINO, verboso=True):
    """Valida os candidatos e grava relatórios; retorna os resultados em dict."""
    csv = Path(csv) if csv is not None else cfg.CSV_PADRAO
    saida = Path(saida) if saida is not None else SAIDA_PADRAO
    say = print if verboso else (lambda *a, **k: None)
    todos = construir_candidatos()
    nomes = list(dict.fromkeys(todos if candidatos is None else candidatos))
    if not nomes or set(nomes) - set(todos):
        raise ValueError(f"Escolha candidatos válidos: {', '.join(todos)}.")
    if set(cfg.FEATURES) & set(cfg.PROIBIDAS):
        raise ValueError("As features contêm uma coluna derivada do alvo (vazamento).")
    if min_linhas < 1:
        raise ValueError("O mínimo de linhas deve ser positivo.")

    # Mesma preparação e mesmo holdout de treinar.py, para preservar o padrão.
    df, limpeza = limpar(carregar_csv(csv))
    if len(df) < min_linhas:
        raise ValueError(f"Só {len(df)} imóveis após a limpeza (mínimo {min_linhas}).")
    y, grupos = df[cfg.ALVO], montar_grupos(df)
    if len(np.unique(grupos)) < cfg.N_FOLDS_CV:
        raise ValueError("Não há grupos suficientes para separar treino e teste.")
    i_tr, i_te = separar_treino_teste(y, grupos, cfg.N_FOLDS_CV)
    X_tr = df.iloc[i_tr][cfg.FEATURES].reset_index(drop=True)
    y_tr = y.iloc[i_tr].reset_index(drop=True)
    g_tr = grupos[i_tr]
    if len(np.unique(g_tr)) < cfg.N_FOLDS_CV:
        raise ValueError("Não há grupos suficientes no treino para a validação cruzada.")
    if np.intersect1d(g_tr, grupos[i_te]).size:
        raise ValueError("Há grupos compartilhados entre treino e teste.")
    dobras = dobras_cv(y_tr, g_tr, cfg.N_FOLDS_CV)
    numero_dobra = np.zeros(len(y_tr), dtype=int)
    for k, (treino, validacao) in enumerate(dobras, 1):
        if np.intersect1d(g_tr[treino], g_tr[validacao]).size:
            raise ValueError(f"Há grupos compartilhados na dobra {k}.")
        numero_dobra[validacao] = k

    say(f"[dados] {limpeza}", flush=True)
    say(f"[divisão] {len(i_tr)} anúncios para validação cruzada; "
        f"{len(i_te)} reservados para teste.", flush=True)
    resultados, previsoes_modelos, por_dobra, variacao = {}, {}, [], {}
    for nome in nomes:
        say(f"[validação] {nome}: {len(dobras)} dobras...", flush=True)
        previsto = cross_val_predict(todos[nome], X_tr, y_tr, cv=dobras)
        resultados[nome] = metricas(y_tr, previsto)
        previsoes_modelos[nome] = previsto
        maes = []
        for k, (treino, validacao) in enumerate(dobras, 1):
            m = metricas(y_tr.iloc[validacao], previsto[validacao])
            por_dobra.append({"modelo": nome, "dobra": k, "n_treino": len(treino), **m})
            maes.append(m["mae"])
        variacao[nome] = {
            "mae_media_dobras": float(np.mean(maes)),
            "mae_desvio_dobras": float(np.std(maes, ddof=1)),
            "mae_min_dobras": float(np.min(maes)),
            "mae_max_dobras": float(np.max(maes)),
        }

    melhor = min(resultados, key=lambda nome: resultados[nome][cfg.METRICA_SELECAO])
    comparacao = pd.DataFrame({nome: {**resultados[nome], **variacao[nome]} for nome in nomes}).T
    comparacao = comparacao.sort_values(cfg.METRICA_SELECAO, kind="stable").rename_axis("modelo")
    comparacao["n"] = comparacao["n"].astype(int)
    previsto = previsoes_modelos[melhor]
    previsoes = df.iloc[i_tr][["id_anuncio", "bairro", "tipo"]].reset_index(drop=True).copy()
    previsoes.insert(0, "indice_csv_limpo", i_tr)
    previsoes["grupo"] = g_tr
    previsoes["dobra"] = numero_dobra
    previsoes["aluguel_real"] = y_tr.to_numpy()
    previsoes["aluguel_previsto"] = previsto
    previsoes["erro_reais"] = previsto - y_tr.to_numpy()
    previsoes["erro_percentual"] = 100 * previsoes["erro_reais"] / previsoes["aluguel_real"]
    ganho = None
    if "baseline" in resultados and resultados["baseline"]["mae"] > 0:
        ganho = 100 * (1 - resultados[melhor]["mae"] / resultados["baseline"]["mae"])

    relatorio = {
        "csv": str(csv.resolve()),
        "csv_sha256": hashlib.sha256(csv.read_bytes()).hexdigest(),
        "semente": cfg.SEMENTE, "n_dobras": len(dobras), "features": cfg.FEATURES,
        "limpeza": limpeza,
        "divisao": {
            "linhas_treino": len(i_tr), "linhas_teste_reservado": len(i_te),
            "percentual_treino": 100 * len(i_tr) / len(df),
            "percentual_teste": 100 * len(i_te) / len(df),
            "indices_treino": i_tr.tolist(), "indices_teste_reservado": i_te.tolist(),
        },
        "teste_avaliado": False, "modelo_final_treinado": False,
        "metrica_selecao": cfg.METRICA_SELECAO, "modelo_escolhido": melhor,
        "cv_treino": resultados, "variacao_mae_dobras": variacao, "por_dobra": por_dobra,
        "ganho_mae_vs_baseline_pct": ganho,
        "validacao_por_tipo": metricas_por_segmento(y_tr, previsto, X_tr["tipo"]),
        "validacao_por_faixa": metricas_por_segmento(y_tr, previsto, [_faixa_preco(v) for v in y_tr]),
        "bibliotecas": {"python": platform.python_version(), "sklearn": sklearn.__version__,
                        "pandas": pd.__version__, "numpy": np.__version__},
        "limitacoes": LIMITACOES,
    }
    # Gera todo o conteúdo antes de criar a pasta de saída.
    conteudo_json = json.dumps(relatorio, ensure_ascii=False, indent=2, allow_nan=False)
    analise = _analise(relatorio, comparacao, previsoes)
    saida.mkdir(parents=True, exist_ok=True)
    comparacao.to_csv(saida / "resultados_validacao.csv", encoding="utf-8-sig", float_format="%.6f")
    pd.DataFrame(por_dobra).to_csv(saida / "metricas_por_dobra.csv", index=False,
                                 encoding="utf-8-sig", float_format="%.6f")
    previsoes.to_csv(saida / "previsoes_validacao.csv", index=False,
                    encoding="utf-8-sig", float_format="%.6f")
    (saida / "relatorio_validacao.json").write_text(conteudo_json + "\n", encoding="utf-8")
    (saida / "analise_validacao.md").write_text(analise, encoding="utf-8")
    say("\n" + comparacao[METRICAS].round(2).to_string())
    say(f"\n[escolhido na validação] {melhor}")
    say(f"[relatórios] {saida.resolve()}")
    return relatorio


def main():
    ap = argparse.ArgumentParser(description="Validação cruzada do RentMatch, sem executar o teste final.")
    ap.add_argument("--csv", type=Path, help="CSV do coletor; padrão: CSV incluído no projeto")
    ap.add_argument("--saida", type=Path, help="Pasta dos relatórios; padrão: modelo_ml/validacao")
    ap.add_argument("--candidatos", nargs="+", choices=list(construir_candidatos()),
                    help="Padrão: todos os candidatos")
    ap.add_argument("--min-linhas", type=int, default=cfg.MIN_LINHAS_TREINO)
    args = ap.parse_args()
    try:
        executar(csv=args.csv, saida=args.saida, candidatos=args.candidatos, min_linhas=args.min_linhas)
    except (ValueError, FileNotFoundError) as erro:
        ap.error(str(erro))


if __name__ == "__main__":
    main()
