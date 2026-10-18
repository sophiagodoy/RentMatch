# Análise da validação do RentMatch

## Como reproduzir

Na raiz do projeto, com as dependências de `modelo_ml/requirements.txt` instaladas:

```powershell
python modelo_ml/validar.py
```

Use `--csv caminho.csv`, `--saida pasta` ou `--candidatos baseline ridge` para escolher a entrada, a pasta dos relatórios ou os candidatos. Essas opções podem produzir resultados diferentes dos apresentados aqui.

## Dados e método

- CSV avaliado: `C:\Users\sophi\RentMatch\modelo_ml\data\imoveis_campinas.csv`.
- SHA-256 do CSV: `331f9e84ebd28a3ad67e744f4c2ef7116739c3381faab16e32f05d4258fe5a9f`.
- Semente: 42; dobras: 5.
- Linhas lidas: 3055; após limpeza: 3040.
- Descartes: 0 duplicados, 0 fora das faixas/sem dados e 15 outliers.
- Treino usado na validação cruzada: 2432 anúncios (80,00%).
- Teste reservado: 608 anúncios (20,00%), sem ajuste ou previsão dos candidatos nessa parte.

Foram reutilizadas a limpeza, a divisão agrupada e as funções de métricas do projeto. Anúncios do mesmo grupo ficam do mesmo lado da divisão e da dobra. Imputação, agrupamento de categorias raras e codificação são ajustados pelos pipelines apenas no treino de cada dobra. A limitação da limpeza global de outliers está detalhada abaixo.

Cada anúncio da parte de treino recebe uma previsão fora da amostra: o modelo que faz essa previsão foi ajustado nas outras dobras. As métricas agregadas são calculadas juntando essas previsões; a média por dobra é apresentada separadamente.

## Comparação dos modelos

| Modelo | MAE (R$) | RMSE (R$) | R² | MAPE (%) | Mediana APE (%) |
| --- | --- | --- | --- | --- | --- |
| hgb | 1.038,54 | 1.840,47 | 0,75 | 24,65 | 19,33 |
| rf | 1.040,63 | 1.830,57 | 0,76 | 25,39 | 19,84 |
| ridge | 1.206,27 | 2.133,66 | 0,67 | 28,80 | 23,83 |
| baseline | 1.741,49 | 3.366,80 | 0,17 | 39,97 | 28,40 |

MAE é o erro absoluto médio em reais e orienta a escolha. RMSE dá mais peso a erros grandes. R² compara as previsões com a média dos aluguéis. MAPE e mediana APE expressam o erro percentual médio e mediano.

## Escolha e estabilidade

O candidato indicado para a etapa de teste é **hgb**, escolhido pelo menor MAE. Seu MAE agregado é **R$ 1.038,54**, com MAPE de **24,65%**.

O MAE foi **40,37% menor** que o do baseline (área × mediana do preço por m² do bairro).

O segundo colocado foi **rf**, com MAE de R$ 1.040,63. A diferença para hgb foi de **R$ 2,10**. O escolhido teve MAE menor que o segundo colocado em 2 das 5 dobras. A ordenação pelo MAE agregado não demonstra, sozinha, superioridade estatística entre os candidatos.

Entre as dobras, o MAE do escolhido variou de R$ 955,88 a R$ 1.152,18; média de R$ 1.038,50 e desvio padrão amostral de R$ 84,64. Esses valores mostram a variação entre as partições; o desvio padrão não é um intervalo de confiança.

## Desempenho do escolhido por segmento

### Tipo de imóvel

| Segmento | Anúncios | MAE (R$) | MAPE (%) |
| --- | --- | --- | --- |
| apartamento | 1024 | 824,23 | 26,02 |
| casa | 553 | 1.903,45 | 26,49 |
| desconhecido | 717 | 804,72 | 22,28 |
| kitnet | 138 | 377,68 | 19,32 |

### Faixa de aluguel (R$)

| Segmento | Anúncios | MAE (R$) | MAPE (%) |
| --- | --- | --- | --- |
| 0-1500 | 299 | 461,38 | 37,58 |
| 1501-3000 | 1115 | 466,84 | 20,50 |
| 3001+ | 1018 | 1.834,22 | 25,39 |

Segmentos com menos de cinco anúncios não são apresentados. Essas métricas também usam somente as previsões da validação cruzada.

A faixa **0-1500** apresentou o maior erro percentual médio: **37,58%**. Essa diferença entre faixas deve entrar na avaliação de qualidade, além das métricas gerais.

O tipo do imóvel está ausente em **717 anúncios** da parte usada para validação (29,48%). A revisão desses campos na coleta pode melhorar a informação disponível ao modelo.

## Cinco maiores erros absolutos do escolhido

| Anúncio | Bairro | Real (R$) | Previsto (R$) | Erro absoluto (R$) |
| --- | --- | --- | --- | --- |
| h6aa53aeb9acb6b8c | vila sonia (sousas) | 25.000,00 | 7.316,80 | 17.683,20 |
| 893959077 | jardim chapadao | 22.000,00 | 7.671,87 | 14.328,13 |
| 895576624 | chacara da barra | 25.500,00 | 12.516,25 | 12.983,75 |
| h47c90f620d648d2e | vila progresso | 25.000,00 | 12.409,05 | 12.590,95 |
| 895104865 | loteamento alphaville campinas | 29.540,00 | 17.188,94 | 12.351,06 |

Esses anúncios são pontos para revisão dos dados e das características disponíveis. Um erro alto, por si só, não demonstra que o anúncio está incorreto.

## Limitações e conclusão

- A limpeza de outliers usa estatísticas da base inteira antes da divisão, como em treinar.py. Isso pode tornar a avaliação otimista. Para uma avaliação mais rigorosa, essas estatísticas devem ser aprendidas apenas no treino de cada dobra.
- As métricas são usadas para escolher o modelo; a avaliação final depende do teste reservado.
- Não foi definido pelo grupo um limite de erro aceitável para aprovar o modelo.
- A validação usa os parâmetros padrão dos candidatos, sem busca de hiperparâmetros.

A execução fornece evidência preliminar para selecionar um candidato. A aprovação para uso depende da revisão da limpeza, do limite de erro combinado pelo grupo e da avaliação final no teste reservado. Não foi gerado um modelo final nesta etapa.

## Arquivos gerados

- `resultados_validacao.csv`: métricas agregadas e variação do MAE entre dobras.
- `metricas_por_dobra.csv`: métricas de cada modelo em cada dobra.
- `previsoes_validacao.csv`: previsões fora da amostra do candidato escolhido.
- `relatorio_validacao.json`: resultados, versões das bibliotecas e índices da divisão referentes ao CSV após a limpeza, para auditoria e reprodução.

O erro em reais na tabela de previsões é `previsto - real`; valores positivos indicam superestimação. Para verificar os testes automatizados desta etapa:

```powershell
python -m unittest discover -s modelo_ml -p "test_validar.py" -v
```
