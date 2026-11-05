# RentMatch

Sistema web inteligente de avaliação de aluguéis residenciais, desenvolvido como Projeto Integrador VI - Engenharia de Software na PUC-Campinas.

## Sobre o projeto

O mercado de locação de imóveis residenciais em Campinas apresenta desafios na definição de valores de aluguel, já que a precificação é frequentemente feita com base em comparações informais ou na experiência dos responsáveis pela negociação — o que pode resultar em valores acima ou abaixo dos praticados no mercado.

O **RentMatch** utiliza técnicas de Inteligência Artificial e Machine Learning para estimar um valor justo de aluguel a partir de características estruturais e contextuais do imóvel, como localização, metragem, número de quartos e vagas, e taxas associadas. Além da estimativa, o sistema classifica a oferta informada pelo usuário como **Caro**, **Preço Justo** ou **Oportunidade**, e oferece explicabilidade (XAI) sobre os fatores que mais influenciaram cada avaliação, promovendo maior transparência ao usuário.

## Objetivos

### Objetivo geral

Desenvolver um sistema web inteligente para estimativa e classificação de valores de aluguéis residenciais na cidade de Campinas, por meio de técnicas de Inteligência Artificial e Machine Learning, de modo a apoiar a tomada de decisão de inquilinos, proprietários e profissionais do setor imobiliário.

### Objetivos específicos

- Levantar e coletar dados de imóveis residenciais disponíveis para locação em Campinas, considerando localização, metragem, número de quartos e vagas, e taxas associadas.
- Desenvolver e treinar um modelo de Machine Learning capaz de estimar um valor de aluguel justo a partir das características do imóvel.
- Classificar a oferta informada pelo usuário nas categorias "Caro", "Preço Justo" ou "Oportunidade".
- Implementar mecanismos de explicabilidade (XAI) que apresentem os principais fatores que influenciaram a estimativa.
- Projetar e desenvolver uma interface web intuitiva para o usuário informar os dados do imóvel e visualizar os resultados.
- Validar o desempenho do modelo preditivo por meio de métricas de avaliação (ex.: erro médio, acurácia).

## Funcionalidades / Telas

- **Login e Cadastro** — autenticação de usuários
- **Avaliação do imóvel** — formulário com bairro, tipo, metragem, quartos, vagas, taxas e valor anunciado
- **Resultado** — valor estimado e classificação (Caro / Preço Justo / Oportunidade)
- **Explicabilidade (XAI)** — fatores que mais influenciaram a estimativa
- **Dashboard** — histórico de avaliações do usuário
- **Histórico completo** — acesso às avaliações salvas, busca por bairro ou tipo, filtro por classificação, ordenação e consulta dos detalhes

## Metodologia

O desenvolvimento seguiu a metodologia **SCRUM**, organizada em sprints com entregas incrementais, desde o levantamento de requisitos junto à comunidade externa até a implementação e validação do modelo preditivo.

## Tecnologias


- Frontend:
- Backend:
- Machine Learning:
- Banco de dados:

## Como executar

Com o backend configurado e rodando na porta 3000, acesse **http://localhost:3000/** para abrir o login. O backend também serve os arquivos do frontend.

Com o Docker Desktop aberto e o `backend/.env` configurado:

```powershell
python -m pip install -r modelo_ml/requirements.txt
python modelo_ml/treinar.py
cd backend
npm.cmd install --include=dev
npx.cmd prisma generate --config prisma7.config.ts
npm.cmd run docker
npx.cmd prisma migrate deploy --config prisma7.config.ts
npm.cmd run dev
```

O treinamento é necessário na primeira execução ou quando a base de imóveis mudar. Os artefatos ficam em `modelo_ml/artefatos/` e não são versionados. O backend usa o Python da `.venv` da raiz, quando existe, ou o Python instalado no sistema. Para escolher outro executável, configure `PYTHON_EXECUTABLE` no `backend/.env`.

Para testar no navegador, faça login, preencha **Avalie seu aluguel** e clique em **Avaliar imóvel**. O resultado mostra a estimativa, a classificação, a faixa estimada e os fatores. Clique em **Salvar no histórico** para incluir a avaliação no histórico e nos totais. O link **Reabrir último resultado** permite retornar ao resultado enquanto a página continua aberta.

## Consulta e salvamento de avaliações

As rotas abaixo exigem `Authorization: Bearer <token>` e acessam somente avaliações do usuário autenticado.

| Rota | Comportamento |
| --- | --- |
| `POST /evaluations` | Valida o formulário, calcula com o modelo Python e cria uma avaliação com `saved: false`. Responde `201` com o resultado persistido. |
| `GET /evaluations/:id` | Retorna os dados do imóvel, valores, classificação, fatores, data e `saved`, inclusive quando a avaliação ainda não foi salva. |
| `PATCH /evaluations/:id/save` | Define `saved: true` e retorna a avaliação atualizada. Não exige corpo e pode ser repetida sem duplicar a avaliação. |
| `GET /evaluations` | Lista somente as avaliações salvas e retorna paginação e totais dessas avaliações. |

Os detalhes e o salvamento respondem `200` com o objeto da avaliação; ID inválido retorna `400`, autenticação ausente ou inválida retorna `401` e avaliação inexistente ou de outra conta retorna `404`.

O `POST` recebe `bairro`, `tipo` (`Apartamento`, `Casa` ou `Kitnet`), `areaM2` (8 a 2000), `quartos` e `vagas` (inteiros de 0 a 20), `valorAnunciado` e, opcionalmente, `condominio` e `iptu`. Valores monetários aceitam até duas casas decimais. A identidade do dono vem do token; estimativa, classificação, fatores e estado de salvamento vêm do servidor.

O botão de detalhes na home e no histórico consulta `GET /evaluations/:id`. Os fatores e os metadados do modelo (`modelo`) são os registrados na avaliação. A migração `20261105160000_add_evaluation_model_result` preserva a versão, a faixa estimada e os avisos. Se o Python ou o artefato do modelo estiver indisponível, a criação retorna `503` sem gravar um resultado fictício.

A migração `20261105150000_add_evaluation_saved` mantém os registros anteriores como salvos. Novas avaliações começam com `saved: false` e entram no histórico após o `PATCH`.

Com o modelo treinado, o banco rodando e as migrações aplicadas, execute `npm.cmd run test:evaluations` dentro de `backend`. Os testes criam duas contas temporárias e removem seus dados ao terminar. Para verificar o modelo, execute `python -m unittest discover -s modelo_ml -p "test_*.py" -v` na raiz.

## Integrantes do grupo

Arthur Azevedo
Priscila Amorim dos Santos - 24787350
Ryan Chaves Dias
Sophia Franco de Godoy - 24000833

## Orientação

Professora orientadora: Sílvia Cristina de Mato Soares
Disciplina: Projeto Integrador VI - Engenharia de Software (218131P)
Instituição: Pontifícia Universidade Católica de Campinas
