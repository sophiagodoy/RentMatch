# Ajustes e testes do modelo

A revisão foi feita a partir da branch `02-requirements`.

Na limpeza, foram ajustados os IDs, as datas e os anúncios duplicados.
Também foi corrigido o tratamento de campos vazios e valores inválidos.
Os endereços agora seguem o mesmo formato na hora de separar os grupos
de treino e teste.

O CSV tinha 600 anúncios de outras cidades. Eles foram retirados do treino,
ficando 2.455 imóveis. A remoção automática de outliers foi desativada porque
usava os valores do teste para decidir quais anúncios descartar.

Foram adicionados 12 testes. Com os 4 que já existiam, são 16, todos passando.
Eles verificam a limpeza, os limites dos campos, CSV vazio, separação dos
grupos e se o modelo mantém as previsões depois de salvar e carregar.

Para rodar os testes, abra o terminal na pasta do projeto e use a `.venv`
com as dependências instaladas:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s modelo_ml -v
```

O treinamento também rodou com o CSV do projeto. O Random Forest teve o menor
erro na validação. Nos 492 imóveis separados para teste, o erro médio foi
de R$ 1.111,27 e o erro percentual médio ficou em 24,96%.

Ainda falta combinar com o grupo se esse erro é aceitável. O treino foi feito
sem `--ajustar`, e os anúncios sem cidade informada foram mantidos.
O arquivo `prever.py` continua vazio nesta versão.

Os relatórios antigos de `validacao/` não foram substituídos. Os resultados
desta revisão foram salvos fora do repositório.
