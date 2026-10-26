"""Preparo dos dados: leitura, limpeza, normalização e divisão treino/teste.

Usado tanto no treino quanto na previsão, para que o texto digitado pelo
usuário (ex.: "Cambuí") seja tratado exatamente como nos dados de treino.
"""
import re
import unicodedata

import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.model_selection import StratifiedGroupKFold

import config_modelo as cfg

COLUNAS_NUMERICAS = ["aluguel", "total", "taxas", "area_m2", "quartos", "vagas", "preco_por_metro"]


def normalizar_texto(valor) -> str:
    """'  Cambuí ' -> 'cambui'. Vazio ou nulo -> 'desconhecido'."""
    if valor is None or pd.isna(valor):
        return "desconhecido"
    texto = unicodedata.normalize("NFKD", str(valor)).encode("ascii", "ignore").decode()
    texto = re.sub(r"\s+", " ", texto.lower().strip())
    return texto or "desconhecido"


def carregar_csv(caminho) -> pd.DataFrame:
    df = pd.read_csv(caminho, encoding="utf-8-sig", dtype={"id_anuncio": "string"})
    for col in COLUNAS_NUMERICAS:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


def _z_robusto(serie: pd.Series, referencia: pd.Series) -> pd.Series:
    mediana = referencia.median()
    mad = (referencia - mediana).abs().median() * 1.4826
    if not mad or np.isnan(mad):
        return pd.Series(0.0, index=serie.index)
    return (serie - mediana) / mad


def limpar(df: pd.DataFrame, outlier_z: float | None = None):
    """Retorna (df_limpo, relatorio). Cada descarte é contado para auditoria."""
    rel = {"linhas_lidas": int(len(df))}
    obrigatorias = {"id_anuncio", cfg.ALVO, "area_m2"}
    faltantes = obrigatorias - set(df.columns)
    if faltantes:
        raise ValueError(f"Colunas obrigatórias ausentes: {', '.join(sorted(faltantes))}.")
    if outlier_z is not None and (not np.isfinite(outlier_z) or outlier_z <= 0):
        raise ValueError("outlier_z deve ser positivo e finito.")
    df = df.copy().reset_index(drop=True)
    for col in COLUNAS_NUMERICAS:
        if col in df:
            df[col] = pd.to_numeric(df[col], errors="coerce").replace([np.inf, -np.inf], np.nan)
    df["id_anuncio"] = df["id_anuncio"].astype("string").str.strip().replace("", pd.NA)

    if "atualizado_em" in df.columns:
        datas = pd.to_datetime(df["atualizado_em"], errors="coerce", utc=True, format="mixed")
        df = df.assign(_data_ordem=datas).sort_values(
            "_data_ordem", kind="stable", na_position="first").drop(columns="_data_ordem")
    antes = len(df)
    df = df[~(df["id_anuncio"].notna() & df.duplicated("id_anuncio", keep="last"))]
    rel["duplicados_removidos"] = int(antes - len(df))

    # O coletor inclui cidades vizinhas; o escopo do projeto é Campinas.
    antes = len(df)
    if "endereco_completo" in df:
        cidades = df["endereco_completo"].astype("string").str.extract(r"·\s*([^·]+)$", expand=False)
        fora = cidades.notna() & cidades.map(normalizar_texto).ne(cfg.CIDADE_ALVO)
        df = df[~fora]
    rel["fora_da_cidade"] = int(antes - len(df))

    antes = len(df)
    df = df.dropna(subset=[cfg.ALVO, "area_m2"])
    df = df[(df[cfg.ALVO].between(cfg.ALUGUEL_MIN, cfg.ALUGUEL_MAX))
            & (df["area_m2"].between(cfg.AREA_MIN, cfg.AREA_MAX))]
    rel["fora_das_faixas_ou_sem_dados"] = int(antes - len(df))

    for col in ("bairro", "tipo"):
        df[col] = df[col].map(normalizar_texto) if col in df.columns else "desconhecido"
    for col in ("quartos", "vagas", "taxas"):
        if col not in df.columns:
            df[col] = np.nan
    rel["valores_invalidos_por_coluna"] = {}
    for col in ("quartos", "vagas", "taxas"):
        invalidos = df[col].notna() & (df[col] < 0)
        if col != "taxas":
            invalidos |= df[col].notna() & ((df[col] > 20) | (df[col] % 1 != 0))
        rel["valores_invalidos_por_coluna"][col] = int(invalidos.sum())
        df.loc[invalidos, col] = np.nan

    # Filtro estatístico apenas para exploração explícita. O fluxo de treino
    # preserva extremos válidos para não usar o alvo do teste na limpeza.
    antes = len(df)
    if outlier_z is not None and not df.empty:
        ppm_log = np.log(df[cfg.ALVO] / df["area_m2"])
        z = pd.Series(0.0, index=df.index)
        for _, idx in df.groupby("tipo").groups.items():
            referencia = ppm_log.loc[idx] if len(idx) >= 20 else ppm_log
            z.loc[idx] = _z_robusto(ppm_log.loc[idx], referencia)
        df = df[z.abs() <= outlier_z]
    rel["outliers_removidos"] = int(antes - len(df))

    df = df.reset_index(drop=True)
    rel["linhas_finais"] = int(len(df))
    return df, rel


def montar_grupos(df: pd.DataFrame) -> np.ndarray:
    """Anúncios do mesmo endereço, área e quartos viram um grupo.

    Assim, quase-duplicatas (o mesmo imóvel anunciado duas vezes, ou unidades
    idênticas do mesmo prédio) não ficam metade no treino e metade no teste,
    o que inflaria as métricas (RIA05).
    """
    chaves = []
    for posicao, (_, linha) in enumerate(df.iterrows()):
        endereco = normalizar_texto(linha.get("endereco_completo"))
        if endereco != "desconhecido":
            chave = ("endereco", endereco, float(linha["area_m2"]),
                     None if pd.isna(linha["quartos"]) else float(linha["quartos"]))
        elif pd.notna(linha.get("id_anuncio")) and str(linha["id_anuncio"]).strip():
            chave = ("anuncio", str(linha["id_anuncio"]).strip())
        else:
            chave = ("linha", posicao)
        chaves.append(chave)
    return pd.factorize(pd.Series(chaves, dtype=object))[0]


def separar_treino_teste(y: pd.Series, grupos, n_splits: int = cfg.N_FOLDS_CV,
                         semente: int = cfg.SEMENTE):
    """Holdout de teste (1/n_splits dos dados), estratificado por faixa de preço e por grupo."""
    _validar_divisao(y, grupos, n_splits)
    return next(_divisor(n_splits, semente).split(np.zeros(len(y)), _faixas(y), grupos))


def dobras_cv(y: pd.Series, grupos, n_splits: int = cfg.N_FOLDS_CV, semente: int = cfg.SEMENTE):
    """Lista de (treino, validação) para validação cruzada sem vazamento entre grupos."""
    _validar_divisao(y, grupos, n_splits)
    return list(_divisor(n_splits, semente).split(np.zeros(len(y)), _faixas(y), grupos))


def _validar_divisao(y, grupos, n_splits):
    if n_splits < 2 or len(y) != len(grupos):
        raise ValueError("Divisão requer ao menos duas dobras e um grupo por linha.")
    if len(np.unique(grupos)) < n_splits:
        raise ValueError("Não há grupos suficientes para a divisão solicitada.")
    if not np.isfinite(np.asarray(y, float)).all():
        raise ValueError("O alvo deve conter apenas números finitos.")


def _divisor(n_splits, semente):
    return StratifiedGroupKFold(n_splits=n_splits, shuffle=True, random_state=semente)


def _faixas(y: pd.Series):
    return pd.qcut(pd.Series(np.asarray(y)), q=min(10, max(2, len(y) // 30)),
                   labels=False, duplicates="drop").fillna(0).astype(int).to_numpy()


class AgrupadorRaros(BaseEstimator, TransformerMixin):
    """Troca categorias raras (e categorias nunca vistas) por 'outros'.

    Aprende quais categorias são frequentes apenas nos dados de TREINO,
    então não vaza informação do teste.
    """

    def __init__(self, colunas=None, min_freq=None, rotulo="outros"):
        self.colunas = colunas
        self.min_freq = min_freq
        self.rotulo = rotulo

    def fit(self, X, y=None):
        X = pd.DataFrame(X)
        colunas = self.colunas or cfg.FEATURES_CAT
        minimos = self.min_freq or cfg.MIN_FREQ
        self.frequentes_ = {}
        for col in colunas:
            contagem = X[col].value_counts()
            self.frequentes_[col] = set(contagem[contagem >= minimos.get(col, 1)].index)
        return self

    def transform(self, X):
        X = pd.DataFrame(X).copy()
        for col, frequentes in self.frequentes_.items():
            X[col] = X[col].where(X[col].isin(frequentes), self.rotulo)
        return X


def montar_entrada(dados: dict) -> pd.DataFrame:
    """Dict vindo do formulário/backend -> DataFrame de 1 linha no formato do modelo.

    Aceita 'metragem' ou 'area_m2'; e 'condominio' + 'iptu' (somados em 'taxas')
    ou 'taxas' direto. Levanta ValueError com todos os problemas encontrados (RF15).
    """
    erros = []

    def numero(nome, *apelidos, minimo=0, maximo=None, obrigatorio=True):
        for chave in (nome, *apelidos):
            if dados.get(chave) not in (None, ""):
                try:
                    valor = float(dados[chave])
                except (TypeError, ValueError):
                    erros.append(f"'{chave}' deve ser um número")
                    return np.nan
                if not np.isfinite(valor) or valor < minimo or (maximo is not None and valor > maximo):
                    erros.append(f"'{chave}' fora do intervalo permitido")
                return valor
        if obrigatorio:
            erros.append(f"'{nome}' é obrigatório")
        return np.nan

    area = numero("area_m2", "metragem", minimo=cfg.AREA_MIN, maximo=cfg.AREA_MAX)
    quartos = numero("quartos", maximo=20)
    vagas = numero("vagas", maximo=20)
    for nome, valor in (("quartos", quartos), ("vagas", vagas)):
        if np.isfinite(valor) and not valor.is_integer():
            erros.append(f"'{nome}' deve ser um inteiro")

    if dados.get("taxas") not in (None, ""):
        taxas = numero("taxas", obrigatorio=False)
    else:
        cond = numero("condominio", obrigatorio=False)
        iptu = numero("iptu", obrigatorio=False)
        taxas = np.nan if (np.isnan(cond) and np.isnan(iptu)) else np.nansum([cond, iptu])

    bairro = normalizar_texto(dados.get("bairro"))
    if bairro == "desconhecido":
        erros.append("'bairro' é obrigatório")
    tipo = normalizar_texto(dados.get("tipo"))
    if tipo == "desconhecido":
        erros.append("'tipo' é obrigatório")

    if erros:
        raise ValueError("; ".join(erros))
    return pd.DataFrame([{"bairro": bairro, "tipo": tipo, "area_m2": area,
                          "quartos": quartos, "vagas": vagas, "taxas": taxas}])[cfg.FEATURES]
