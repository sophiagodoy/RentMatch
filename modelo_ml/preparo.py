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
    df = pd.read_csv(caminho, encoding="utf-8-sig")
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


def limpar(df: pd.DataFrame, outlier_z: float = cfg.OUTLIER_Z):
    """Retorna (df_limpo, relatorio). Cada descarte é contado para auditoria."""
    rel = {"linhas_lidas": int(len(df))}
    df = df.copy()

    if "atualizado_em" in df.columns:
        df = df.sort_values("atualizado_em")
    antes = len(df)
    df = df.drop_duplicates("id_anuncio", keep="last")
    rel["duplicados_removidos"] = int(antes - len(df))

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
    df.loc[df["taxas"] < 0, "taxas"] = np.nan

    # Outliers: R$/m² muito fora do padrão do tipo (erro de digitação no anúncio,
    # imóvel comercial, aluguel por temporada etc.).
    ppm_log = np.log(df[cfg.ALVO] / df["area_m2"])
    z = pd.Series(0.0, index=df.index)
    for _, idx in df.groupby("tipo").groups.items():
        referencia = ppm_log.loc[idx] if len(idx) >= 20 else ppm_log
        z.loc[idx] = _z_robusto(ppm_log.loc[idx], referencia)
    antes = len(df)
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
    if "endereco_completo" in df.columns:
        chave = (df["endereco_completo"].fillna("").astype(str) + "|"
                 + df["area_m2"].astype(str) + "|" + df["quartos"].astype(str))
    else:
        chave = df["id_anuncio"].astype(str)
    return pd.factorize(chave)[0]


def separar_treino_teste(y: pd.Series, grupos, n_splits: int = cfg.N_FOLDS_CV,
                         semente: int = cfg.SEMENTE):
    """Holdout de teste (1/n_splits dos dados), estratificado por faixa de preço e por grupo."""
    return next(_divisor(n_splits, semente).split(np.zeros(len(y)), _faixas(y), grupos))


def dobras_cv(y: pd.Series, grupos, n_splits: int = cfg.N_FOLDS_CV, semente: int = cfg.SEMENTE):
    """Lista de (treino, validação) para validação cruzada sem vazamento entre grupos."""
    return list(_divisor(n_splits, semente).split(np.zeros(len(y)), _faixas(y), grupos))


def _divisor(n_splits, semente):
    return StratifiedGroupKFold(n_splits=n_splits, shuffle=True, random_state=semente)


def _faixas(y: pd.Series):
    return pd.qcut(pd.Series(np.asarray(y)), q=min(10, max(2, len(y) // 30)),
                   labels=False, duplicates="drop").to_numpy()


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
                if valor < minimo or (maximo is not None and valor > maximo):
                    erros.append(f"'{chave}' fora do intervalo permitido")
                return valor
        if obrigatorio:
            erros.append(f"'{nome}' é obrigatório")
        return np.nan

    area = numero("area_m2", "metragem", minimo=cfg.AREA_MIN, maximo=cfg.AREA_MAX)
    quartos = numero("quartos", maximo=20)
    vagas = numero("vagas", maximo=20)

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