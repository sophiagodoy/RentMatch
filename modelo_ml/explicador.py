"""Explicabilidade (RIA06 / RF10): quanto cada característica pesou, em R$.

Calcula valores de Shapley EXATOS para uma estimativa. Como o modelo tem só
6 features, dá para enumerar todas as 2^6 = 64 combinações em vez de
aproximar, e o resultado é determinístico (RIA08). Não depende da biblioteca
`shap`.

Como funciona: para cada combinação de features, as escolhidas assumem o valor
do imóvel avaliado e as demais assumem o valor de imóveis de referência
(`fundo`). A diferença média da previsão mostra o efeito de cada feature.

Propriedade garantida (testada): soma das contribuições = estimativa - valor base,
onde o valor base é a previsão média dos imóveis de referência.
"""
from itertools import combinations
from math import factorial

import numpy as np
import pandas as pd

import config_modelo as cfg


def valores_shapley(modelo, x: pd.DataFrame, fundo: pd.DataFrame, features=None) -> dict:
    """Retorna {'base': R$, 'previsao': R$, 'contribuicoes': {feature: R$}}."""
    features = list(features or cfg.FEATURES)
    n, m = len(features), len(fundo)
    fundo = fundo[features].reset_index(drop=True)
    linha = x[features].iloc[0]

    # v[mascara] = previsão média quando só as features da máscara usam o valor do imóvel
    lotes = []
    for mascara in range(2 ** n):
        copia = fundo.copy()
        for j, nome in enumerate(features):
            if mascara >> j & 1:
                copia[nome] = linha[nome]
        lotes.append(copia)
    previsoes = np.asarray(modelo.predict(pd.concat(lotes, ignore_index=True)), float)
    v = previsoes.reshape(2 ** n, m).mean(axis=1)

    contribuicoes = {}
    for i, nome in enumerate(features):
        outros = [j for j in range(n) if j != i]
        total = 0.0
        for k in range(n):
            peso = factorial(k) * factorial(n - k - 1) / factorial(n)
            for subconjunto in combinations(outros, k):
                mascara = sum(1 << j for j in subconjunto)
                total += peso * (v[mascara | (1 << i)] - v[mascara])
        contribuicoes[nome] = float(total)

    return {"base": float(v[0]), "previsao": float(v[-1]), "contribuicoes": contribuicoes}


def _sinal(valor: float, neutro: float) -> int:
    return 0 if abs(valor) < neutro else (1 if valor > 0 else -1)


def descrever_fator(feature: str, valor, contribuicao: float, neutro: float) -> str:
    """Frase curta para a tela de explicabilidade (como no protótipo)."""
    s = _sinal(contribuicao, neutro)
    if feature == "bairro":
        return ["Bairro com aluguéis abaixo da média", "Bairro dentro da média", "Bairro valorizado"][s + 1]
    if feature == "tipo":
        return ["Tipo de imóvel com aluguel abaixo da média", "Tipo de imóvel dentro da média",
                "Tipo de imóvel com aluguel acima da média"][s + 1]
    if feature == "area_m2":
        return ["Metragem abaixo da média", "Metragem dentro da média", "Metragem acima da média"][s + 1]
    if feature == "quartos":
        return ["Menos quartos que o comum", "Quartos dentro da média", "Mais quartos que o comum"][s + 1]
    if feature == "vagas":
        if pd.notna(valor) and valor == 0 and s <= 0:
            return "Sem vaga de garagem"
        return ["Menos vagas que o comum", "Vagas dentro da média", "Vagas de garagem valorizam o imóvel"][s + 1]
    if feature == "taxas":
        return ["Condomínio e IPTU abaixo da média", "Condomínio e IPTU dentro da média",
                "Condomínio e IPTU acima da média"][s + 1]
    return feature


def fatores_para_usuario(resultado: dict, x: pd.DataFrame, top: int = cfg.TOP_FATORES) -> list:
    """Ordena por impacto e devolve a lista pronta para a interface/API."""
    neutro = max(5.0, 0.01 * resultado["previsao"])  # menos de 1% (ou R$ 5) = "dentro da média"
    itens = []
    for feature, contrib in resultado["contribuicoes"].items():
        valor = x[feature].iloc[0]
        itens.append({
            "fator": feature,
            "descricao": descrever_fator(feature, valor, contrib, neutro),
            "valor_informado": None if pd.isna(valor) else (valor.item() if hasattr(valor, "item") else valor),
            "contribuicao_reais": int(round(contrib)),
            "sentido": "aumenta" if contrib >= neutro else ("reduz" if contrib <= -neutro else "neutro"),
        })
    itens.sort(key=lambda i: abs(i["contribuicao_reais"]), reverse=True)
    return itens[:top]