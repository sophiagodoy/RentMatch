"""Classificação da oferta (RF07 e RF08): compara o anunciado com o estimado.

Dois modos:
  "margem"    (padrão): Preço Justo se o anunciado estiver até +-MARGEM do estimado.
  "intervalo": Preço Justo se o anunciado cair dentro do intervalo de incerteza
               do modelo (ex.: faixa entre os quantis 10% e 90% do erro).
               É mais honesto: só chama de "Caro" quando está acima do que o
               próprio erro do modelo explicaria.
"""
import config_modelo as cfg

CARO = "Caro"
JUSTO = "Preço Justo"
OPORTUNIDADE = "Oportunidade"


def classificar(anunciado: float, estimado: float, margem: float = cfg.MARGEM_PRECO_JUSTO,
                intervalo=None, modo: str = "margem") -> dict:
    if anunciado <= 0 or estimado <= 0:
        raise ValueError("anunciado e estimado devem ser maiores que zero")

    dif = anunciado / estimado - 1  # +0.09 = anunciado 9% acima do estimado

    if modo == "intervalo" and intervalo is not None:
        baixo, alto = intervalo
        classe = CARO if anunciado > alto else (OPORTUNIDADE if anunciado < baixo else JUSTO)
    else:
        classe = CARO if dif > margem else (OPORTUNIDADE if dif < -margem else JUSTO)

    if classe == JUSTO:
        detalhe = "Dentro do esperado para imóveis parecidos"
    elif classe == CARO:
        detalhe = ("Bem acima do mercado" if dif > cfg.LIMITE_BEM_ACIMA
                   else "Levemente acima do mercado")
    elif dif < cfg.LIMITE_BEM_ABAIXO:
        detalhe = "Bem abaixo do mercado: confira se o anúncio está correto"
    else:
        detalhe = "Abaixo do mercado"

    return {
        "classificacao": classe,
        "diferenca_percentual": round(dif * 100, 1),
        "diferenca_reais": round(anunciado - estimado),
        "detalhe": detalhe,
    }