"""Configurações do modelo de estimativa de aluguel do RentMatch.

Tudo que costuma ser ajustado fica aqui: features, limpeza, validação,
margens de classificação e caminhos.
"""
from pathlib import Path

BASE_DIR = Path(__file__).parent
# CSV gerado pelo coletor (rentmatch_coletor/data/imoveis_campinas.csv)
CSV_PADRAO = BASE_DIR.parent / "modelo_ml" / "data" / "imoveis_campinas.csv"
ARTEFATOS_DIR = BASE_DIR / "artefatos"

SEMENTE = 42  # fixa a aleatoriedade: mesmos dados + mesmo código = mesmo modelo (RIA08)

# ------------------------------------------------------------------- features
ALVO = "aluguel"

# Só entram como feature informações que o USUÁRIO consegue informar no
# formulário (RF04). `taxas` = condomínio + IPTU (o backend soma os dois campos).
FEATURES_CAT = ["bairro", "tipo"]
FEATURES_NUM = ["area_m2", "quartos", "vagas", "taxas"]
FEATURES = FEATURES_CAT + FEATURES_NUM

# ATENÇÃO, vazamento de dados: estas colunas do CSV são calculadas a partir do
# aluguel (o alvo). Se virarem feature o modelo "cola" e as métricas ficam
# lindas e falsas. Nunca adicionar em FEATURES.
PROIBIDAS = ["aluguel", "total", "preco_por_metro"]

# Categorias raras são agrupadas em "outros" (também é o destino de bairros que
# o modelo nunca viu).
MIN_FREQ = {"bairro": 15, "tipo": 30}

# ---------------------------------------------------------------- limpeza
OUTLIER_Z = 4.0          # z-score robusto do log(R$/m²) por tipo; maior que isso = descarta
AREA_MIN, AREA_MAX = 8, 2000
ALUGUEL_MIN, ALUGUEL_MAX = 300, 100_000
MIN_LINHAS_TREINO = 300  # abaixo disso o treino não faz sentido

# ---------------------------------------------------------------- validação
N_FOLDS_CV = 5           # 5 folds = holdout de teste de 20% (via StratifiedGroupKFold)
METRICA_SELECAO = "mae"  # escolhe o candidato com menor MAE (erro médio em R$)
N_ITER_AJUSTE = 15       # sorteios por candidato no --ajustar
FAIXAS_PRECO = [(0, 1500), (1501, 3000), (3001, None)]  # mesmas faixas do coletor

# ------------------------------------------------------------- classificação
# Quanto acima ou abaixo do estimado ainda conta como "Preço Justo".
# No protótipo, R$ 1.800 anunciado vs R$ 1.650 estimado (+9%) aparece como Caro,
# então a margem precisa ser menor que 9%. Decisão do time, ajuste à vontade.
MARGEM_PRECO_JUSTO = 0.05
LIMITE_BEM_ACIMA = 0.15      # acima disso: "Bem acima do mercado"
LIMITE_BEM_ABAIXO = -0.25    # abaixo disso: pede para conferir o anúncio
QUANTIS_INTERVALO = (0.10, 0.90)   # intervalo de incerteza da estimativa

# --------------------------------------------------------------- explicabilidade
N_FUNDO_EXPLICADOR = 100   # imóveis de referência usados para calcular as contribuições
TOP_FATORES = 4