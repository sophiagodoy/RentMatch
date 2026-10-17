# RentMatch – Modelo de estimativa de aluguel

Base do modelo de Machine Learning do RentMatch. Lê os dados do coletor,
treina e compara modelos, e entrega para cada imóvel: **valor estimado**,
**intervalo de incerteza**, **classificação** (Caro, Preço Justo ou
Oportunidade) e os **fatores que mais pesaram**, em R$.

> **Importante:** o código foi testado com dados **sintéticos** (inventados
> por fórmula). Os números de desempenho reais só existem depois de rodar
> `treinar.py` com o CSV de verdade do coletor.

## 1. Fluxo

```
coletor ──> imoveis_campinas.csv ──> treinar.py ──> artefatos/modelo_atual.joblib
                                                          │
formulário (bairro, tipo, m², quartos, vagas, taxas, valor anunciado)
                                                          ▼
                                                     prever.py
                                                          │
        ┌─────────────────────┬───────────────────────────┤
        ▼                     ▼                           ▼
  valor estimado      classificação (classificador)   fatores em R$ (explicador)
  + intervalo         Caro / Preço Justo / Oportunidade
```

## 2. Arquivos

| Arquivo | O que faz |
|---|---|
| `config_modelo.py` | Features, limpeza, validação, margens de classificação. Quase tudo que se ajusta fica aqui. |
| `preparo.py` | Lê e limpa o CSV (duplicados, faixas, outliers), normaliza texto, separa treino/teste sem vazamento, valida a entrada do usuário (RF15). |
| `candidatos.py` | Os modelos comparados: `baseline`, `ridge`, `rf` e `hgb`, e as grades do `--ajustar`. |
| `treinar.py` | Compara os candidatos, avalia no teste, calcula o intervalo, salva modelo e metadados. |
| `explicador.py` | Contribuição de cada característica em R$ (valores de Shapley exatos, sem depender da lib `shap`). |
| `classificador.py` | Compara anunciado com estimado e classifica a oferta (RF07 e RF08). |
| `prever.py` | Junta tudo: é o que o backend chama. Funciona como biblioteca, linha de comando ou JSON por stdin. |
| `dados_sinteticos.py` | Gera CSV falso no formato do coletor, só para testar o pipeline. |
| `test_modelo.py` | 15 testes automáticos offline. |

## 3. Como rodar

```bash
pip install -r requirements.txt

# a) testar o pipeline com dados FALSOS (não serve para conclusões)
python dados_sinteticos.py --n 3000 --saida data/sintetico.csv
python treinar.py --csv data/sintetico.csv

# b) treinar com os dados reais do coletor
python treinar.py                      # lê ../rentmatch_coletor/data/imoveis_campinas.csv
python treinar.py --ajustar            # busca de hiperparâmetros (mais demorado)
python treinar.py --candidatos baseline ridge hgb   # só alguns modelos

# avaliar um imóvel
python prever.py --bairro Cambuí --tipo apartamento --area 65 --quartos 2 \
                 --vagas 1 --condominio 450 --iptu 120 --anunciado 1800

# testes
python -m unittest test_modelo -v
```

O treino cria em `artefatos/`: `modelo_<versão>.joblib`, `metadados_<versão>.json`
e as cópias `modelo_atual.joblib` e `metadados_atual.json`, que o `prever.py` usa.

## 4. O que `treinar.py` faz

1. **Limpa**: remove anúncios duplicados, valores fora de faixa e outliers (R$/m² muito fora do padrão do tipo). Cada descarte é contado no relatório.
2. **Separa 20% para teste**, estratificado por faixa de preço e **agrupado**: anúncios do mesmo endereço, área e quartos ficam todos do mesmo lado. Sem isso, o mesmo imóvel anunciado duas vezes cairia no treino e no teste, e as métricas ficariam melhores do que a realidade.
3. **Compara os candidatos** por validação cruzada só no treino.
4. **Avalia o escolhido no teste**, no geral e por faixa de preço e por tipo, e diz quanto ele melhora em relação ao baseline.
5. **Calcula o intervalo de incerteza** (quantis 10% e 90% do erro relativo da validação cruzada) e a **importância global** de cada feature.
6. **Re-treina com todos os dados** e salva, junto com versão, hash do CSV, versões das bibliotecas e métricas.

### Como ler as métricas

| Métrica | O que significa |
|---|---|
| `mae` | Erro médio em R$. "Em média, a estimativa erra R$ X." É a métrica usada para escolher o modelo. |
| `rmse` | Parecida com o MAE, mas pune mais os erros grandes. |
| `r2` | Quanto da variação dos preços o modelo explica. 1 é perfeito, 0 é igual a chutar a média. |
| `mape` e `mediana_ape` | Erro médio e erro típico em %. Mais fáceis de explicar para o usuário. |

Olhe sempre o **por faixa de preço**: um R² bom no geral pode esconder um
modelo fraco nos aluguéis baratos.

## 5. Requisitos de IA do documento

| Requisito | Onde está atendido |
|---|---|
| RIA01 entrada de dados | `FEATURES` em `config_modelo.py` (bairro, tipo, metragem, quartos, vagas, taxas) |
| RIA02 estimativa | `prever.avaliar_imovel` |
| RIA03 métricas MAE, RMSE, R² | `treinar.metricas` (e MAPE) |
| RIA04 qualidade satisfatória | Relatório do teste final. **O limite de "satisfatório" é decisão do grupo.** |
| RIA05 generalização | Teste agrupado, com dados que o modelo nunca viu |
| RIA06 explicabilidade | `explicador.py` |
| RIA07 tempo de resposta | Medido com dados sintéticos: cerca de 25 ms por avaliação com o ridge e 100 ms com o hgb, já com o modelo carregado (a explicação avalia 64 combinações em lote). Chamar via `--json` paga também o tempo de iniciar o Python e carregar o modelo a cada chamada. |
| RIA08 consistência | Sementes fixas, Shapley exato e versão do modelo na resposta (testado) |

## 6. Decisões e armadilhas (leia antes de mexer)

**1. Vazamento de dados.** No CSV do coletor, `total` (= aluguel + taxas) e
`preco_por_metro` (= aluguel ÷ área) são calculados a partir do aluguel, que é
o que o modelo tenta prever. Se entrarem como feature, o modelo "cola" e as
métricas ficam lindas e falsas. Por isso só entram `bairro`, `tipo`,
`area_m2`, `quartos`, `vagas` e `taxas`. Há uma trava em `treinar.py` e um teste.

**2. Taxas.** O coletor só tem `taxas` = condomínio + IPTU somados (o portal mostra o total). O formulário tem os dois campos separados, então `montar_entrada` soma os dois antes de chamar o modelo.

**3. O "valor justo" é o preço anunciado típico, não o preço fechado.** Os dados são anúncios do QuintoAndar. O modelo aprende o que imóveis parecidos *são anunciados por*, o que é uma boa referência, mas não é o valor de contrato. Vale dizer isso na apresentação.

**4. Viés de seleção.** O modelo só conhece o que o QuintoAndar mostra. Imóveis de imobiliárias tradicionais, anúncios de particulares e bairros com poucos anúncios ficam sub-representados. Bairros raros viram "outros", e o resultado traz um aviso quando isso acontece.

**5. Margem de "Preço Justo" menor que o erro do modelo.** Se o modelo erra 10% em média e a margem é 5%, parte das classificações "Caro" e "Oportunidade" será só ruído. Por isso existem dois modos em `classificador.py`: `margem` (±5%, como no protótipo) e `intervalo` (só marca Caro ou Oportunidade fora do intervalo de incerteza do modelo). Vale testar os dois e escolher com o grupo.

**6. Aluguel muito abaixo do estimado.** Pode ser oportunidade, mas também anúncio errado ou golpe. Abaixo de -25% o texto pede para conferir o anúncio.

## 7. Integração com o backend

O `prever.py --json` recebe e devolve JSON, então o backend em Node pode chamá-lo sem Python rodando como serviço:

```js
import { spawn } from "node:child_process";

function avaliar(dados, valorAnunciado) {
  return new Promise((resolve, reject) => {
    const py = spawn("python", ["prever.py", "--json"], { cwd: "rentmatch_modelo" });
    let saida = "";
    py.stdout.on("data", (d) => (saida += d));
    py.on("close", (codigo) => {
      const resposta = JSON.parse(saida);
      codigo === 0 ? resolve(resposta) : reject(new Error(resposta.erro));
    });
    py.stdin.end(JSON.stringify({ dados, valor_anunciado: valorAnunciado }));
  });
}
```

Resposta de exemplo (resumida, com valores ilustrativos):

```json
{
  "valor_estimado": 1650,
  "valor_anunciado": 1800,
  "intervalo_estimado": [1480, 1890],
  "classificacao": "Caro",
  "diferenca_percentual": 9.1,
  "diferenca_reais": 150,
  "detalhe": "Levemente acima do mercado",
  "fatores": [
    {"fator": "bairro", "descricao": "Bairro valorizado", "contribuicao_reais": 60, "sentido": "aumenta"}
  ],
  "avisos": [],
  "versao_modelo": "20261017-103447"
}
```

Isso casa direto com as telas: o card de resultado, as barras de anunciado e estimado, e a tela "Fatores que mais pesaram". Em caso de entrada inválida, o retorno é `{"erro": "..."}` com código de saída 1 (RF15).

Quando valer a pena trocar: um **microserviço FastAPI** (carrega o modelo uma vez, evita o custo de iniciar o Python a cada chamada) é o passo natural depois do spawn.

## 8. Ideias de evolução, em ordem de retorno

1. **Mais dados e dados melhores.** É o que mais melhora o modelo. Rode a coleta completa, repita mensalmente e guarde o histórico (o `atualizado_em` já permite acompanhar variação de preço).
2. **Localização de verdade.** Hoje o bairro é só um rótulo. Geocodificar o `endereco_completo` (latitude e longitude) e calcular distância até Unicamp, PUC, centro e shoppings captura o que a introdução do projeto diz que influencia o aluguel, e ajuda justamente nos bairros raros.
3. **Melhor tratamento do bairro.** `TargetEncoder` do scikit-learn (média do R$/m² do bairro com suavização) ou um modelo hierárquico que "empresta" força de bairros vizinhos.
4. **Outros algoritmos.** LightGBM ou CatBoost (o CatBoost trata categorias muito bem com poucos dados). O `candidatos.py` é só adicionar uma entrada.
5. **Intervalos melhores.** Hoje o intervalo é o mesmo para todos. Dá para calcular por faixa de preço ou usar regressão quantílica (`HistGradientBoostingRegressor(loss="quantile")`).
6. **Mais features, se o formulário puder pedir.** Mobiliado, aceita pet, andar, idade do imóvel, piscina e área de lazer. Cada uma exige que o coletor também extraia o campo.
7. **Monitoramento.** Re-treinar junto com o agendamento da coleta (Sprint 3), comparar o MAE da versão nova com a anterior antes de trocar o `modelo_atual`, e acompanhar o erro por bairro.
8. **Validação com a comunidade externa.** Pedir a corretores ou moradores uma estimativa para 20 imóveis e comparar com o modelo. É a evidência mais forte para a apresentação.
9. **Calibrar a classificação com feedback.** Se o usuário puder marcar "essa avaliação fez sentido", dá para ajustar a margem de "Preço Justo" com dados reais.

## 9. Limitações

- Testado só com dados sintéticos. O desempenho real é desconhecido até treinar com o CSV do coletor.
- O explicador mostra o que pesou **na estimativa do modelo**, não uma causa no mundo real. "Bairro valorizado +R$ 60" significa que o bairro empurra a estimativa para cima em relação a um imóvel típico da base.
- Com poucos imóveis em um tipo ou bairro, a estimativa é pouco confiável (o resultado avisa no caso de bairro).
- O modelo não sabe de reformas, vista, estado de conservação nem fotos.