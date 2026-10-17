"""Modelos candidatos. Todos recebem as mesmas colunas (cfg.FEATURES) e devolvem R$.

O documento do projeto deixa o algoritmo em aberto: a escolha é feita por
experimento (treinar.py compara todos com validação cruzada).

  baseline : área x mediana do R$/m² do bairro (o "olhômetro" do corretor).
             Qualquer modelo de ML precisa ganhar dele para valer a pena.
  ridge    : regressão linear regularizada (simples, rápida, interpretável).
  rf       : Random Forest.
  hgb      : Gradient Boosting por histograma (costuma ser o melhor em dados
             tabulares; aceita categorias e valores faltantes direto).

Os modelos de ML aprendem o log(aluguel): preços são assimétricos e o erro
relativo importa mais do que o absoluto. A previsão volta sempre em R$.
"""
import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, RegressorMixin
from sklearn.compose import ColumnTransformer, TransformedTargetRegressor
from sklearn.ensemble import HistGradientBoostingRegressor, RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import FunctionTransformer, OneHotEncoder, OrdinalEncoder, StandardScaler

import config_modelo as cfg
from preparo import AgrupadorRaros


class BaselineMedianaBairro(RegressorMixin, BaseEstimator):
    """aluguel = área x mediana do R$/m² do bairro (cai na mediana geral se faltar)."""

    def fit(self, X, y):
        X = pd.DataFrame(X)
        ppm = np.asarray(y, float) / X["area_m2"].to_numpy(float)
        self.geral_ = float(np.median(ppm))
        self.por_bairro_ = pd.Series(ppm, index=X["bairro"].to_numpy()).groupby(level=0).median().to_dict()
        return self

    def predict(self, X):
        X = pd.DataFrame(X)
        ppm = X["bairro"].map(self.por_bairro_).fillna(self.geral_).to_numpy(float)
        return ppm * X["area_m2"].to_numpy(float)


def _log_alvo(regressor):
    return TransformedTargetRegressor(regressor=regressor, func=np.log1p, inverse_func=np.expm1)


def _pipeline(pre, estimador):
    return Pipeline([("agrupar", AgrupadorRaros(cfg.FEATURES_CAT, cfg.MIN_FREQ)),
                     ("pre", pre), ("modelo", estimador)])


def _pre_linear():
    num = Pipeline([("imp", SimpleImputer(strategy="median", add_indicator=True)),
                    ("log", FunctionTransformer(np.log1p)), ("esc", StandardScaler())])
    return ColumnTransformer([
        ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), cfg.FEATURES_CAT),
        ("num", num, cfg.FEATURES_NUM)])


def _pre_floresta():
    return ColumnTransformer([
        ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), cfg.FEATURES_CAT),
        ("num", SimpleImputer(strategy="median"), cfg.FEATURES_NUM)])


def _pre_hgb():
    # Categorias viram códigos 0..k; desconhecidas (-1) o HGB trata como faltante.
    return ColumnTransformer([
        ("cat", OrdinalEncoder(handle_unknown="use_encoded_value", unknown_value=-1,
                               encoded_missing_value=-1), cfg.FEATURES_CAT),
        ("num", "passthrough", cfg.FEATURES_NUM)])


def construir_candidatos(semente: int = cfg.SEMENTE) -> dict:
    """nome -> modelo ainda não treinado."""
    mascara_cat = [True] * len(cfg.FEATURES_CAT) + [False] * len(cfg.FEATURES_NUM)
    return {
        "baseline": Pipeline([("agrupar", AgrupadorRaros(cfg.FEATURES_CAT, cfg.MIN_FREQ)),
                              ("modelo", BaselineMedianaBairro())]),
        "ridge": _log_alvo(_pipeline(_pre_linear(), Ridge(alpha=3.0))),
        "rf": _log_alvo(_pipeline(_pre_floresta(), RandomForestRegressor(
            n_estimators=300, min_samples_leaf=2, max_features=0.8, n_jobs=-1, random_state=semente))),
        "hgb": _log_alvo(_pipeline(_pre_hgb(), HistGradientBoostingRegressor(
            categorical_features=mascara_cat, learning_rate=0.05, max_iter=400,
            max_leaf_nodes=15, min_samples_leaf=20, l2_regularization=0.1,
            early_stopping=False, random_state=semente))),
    }


# Grades para o --ajustar (RandomizedSearchCV). O prefixo "regressor__modelo__"
# atravessa o TransformedTargetRegressor e o Pipeline.
GRADES_AJUSTE = {
    "ridge": {"regressor__modelo__alpha": [0.1, 0.3, 1, 3, 10, 30]},
    "rf": {"regressor__modelo__n_estimators": [200, 400],
           "regressor__modelo__min_samples_leaf": [1, 2, 5],
           "regressor__modelo__max_features": [0.5, 0.8, 1.0],
           "regressor__modelo__max_depth": [None, 12, 20]},
    "hgb": {"regressor__modelo__learning_rate": [0.03, 0.05, 0.1],
            "regressor__modelo__max_iter": [200, 400, 600],
            "regressor__modelo__max_leaf_nodes": [7, 15, 31],
            "regressor__modelo__min_samples_leaf": [10, 20, 40],
            "regressor__modelo__l2_regularization": [0.0, 0.1, 1.0]},
}