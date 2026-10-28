# RentMatch — Backend

Este é o **backend** do **RentMatch**, um sistema web que ajuda a descobrir se o aluguel de um imóvel em Campinas está caro, justo ou é uma oportunidade. O sistema estima um valor justo com Machine Learning, compara com o valor anunciado e explica quais características do imóvel mais pesaram na estimativa.

Projeto da disciplina **Projeto Integrador VI — Engenharia de Software (PUC Campinas)**.

O backend é a parte "invisível" do sistema: ele recebe os pedidos das telas, aplica as regras, guarda e busca informações no banco de dados e devolve as respostas.

> Este README foi escrito para quem **nunca viu o projeto** e não precisa saber de antemão o que é Zod, DTO, Prisma ou Docker: cada conceito é explicado antes de ser usado. O serviço de Machine Learning e as rotas do próprio modelo estão fora do escopo deste documento.

---

## Como usar este README

| Eu quero... | Vá para |
|---|---|
| Entender os termos (API, rota, Zod, DTO, Prisma, Docker, JWT...) | [1. Conceitos básicos](#1-conceitos-básicos) |
| Só colocar o projeto para rodar | [3. O que instalar antes](#3-o-que-instalar-antes) e [4. Primeiros passos](#4-primeiros-passos) |
| Entender as pastas e os arquivos | [10. Estrutura de pastas](#10-estrutura-de-pastas) |
| Entender como o código funciona por dentro | [11. Seguindo o código passo a passo](#11-seguindo-o-código-passo-a-passo) |
| Testar as rotas | [15. Testando a API](#15-testando-a-api) |
| Saber o que ainda falta fazer | [16. O que falta implementar](#16-o-que-falta-implementar) |
| Programar uma funcionalidade nova | [17. Como criar um novo módulo](#17-como-criar-um-novo-módulo) |
| Resolver um erro | [19. Solução de problemas](#19-solução-de-problemas) |

**Sugestão para quem está começando:** leia a seção 1, depois a 2, e só então rode o projeto (seções 3 e 4).

---

## Sumário

1. [Conceitos básicos](#1-conceitos-básicos)
2. [Visão geral do projeto](#2-visão-geral-do-projeto)
3. [O que instalar antes](#3-o-que-instalar-antes)
4. [Primeiros passos](#4-primeiros-passos)
5. [Variáveis de ambiente](#5-variáveis-de-ambiente)
6. [Docker e o banco de dados](#6-docker-e-o-banco-de-dados)
7. [Prisma](#7-prisma)
8. [Scripts npm](#8-scripts-npm)
9. [Dependências](#9-dependências)
10. [Estrutura de pastas](#10-estrutura-de-pastas)
11. [Seguindo o código passo a passo](#11-seguindo-o-código-passo-a-passo)
12. [Autenticação](#12-autenticação)
13. [Tratamento de erros](#13-tratamento-de-erros)
14. [Rotas implementadas](#14-rotas-implementadas)
15. [Testando a API](#15-testando-a-api)
16. [O que falta implementar](#16-o-que-falta-implementar)
17. [Como criar um novo módulo](#17-como-criar-um-novo-módulo)
18. [Rotina do dia a dia](#18-rotina-do-dia-a-dia)
19. [Solução de problemas](#19-solução-de-problemas)

---

## 1. Conceitos básicos

Esta seção explica, em linguagem simples, os termos que aparecem no resto do documento. Não precisa decorar: volte aqui sempre que travar em alguma palavra.

### 1.1 Como o site e o servidor conversam

**Frontend** é a parte que o usuário vê e usa: as telas de login, cadastro, home e perfil (arquivos HTML, CSS e JavaScript).

**Backend** é o programa que roda "por trás": guarda os dados, confere senhas, aplica as regras do sistema e responde ao frontend. **É este projeto.**

**API** é o conjunto de "portas" que o backend oferece para o frontend pedir coisas. Uma **API REST** é uma API que conversa usando o protocolo da web (HTTP) e troca dados em formato JSON.

**Requisição e resposta.** Toda conversa tem dois lados: o frontend envia uma **requisição** ("quero fazer login com este e-mail e esta senha") e o backend devolve uma **resposta** ("login feito, aqui está seu token").

**Rota (ou endpoint)** é o "endereço" de uma dessas portas: um **método** + um **caminho**. Exemplo: `POST /login`.

| Método HTTP | Significado | Exemplo no projeto |
|---|---|---|
| `GET` | Buscar informações | Ver o perfil (`GET /me`) |
| `POST` | Enviar dados para criar algo | Cadastrar usuário (`POST /register`) |
| `PUT` | Atualizar um recurso | Atualizar o perfil (`PUT /me`) |
| `PATCH` | Atualizar só uma parte | Marcar uma avaliação como salva |
| `DELETE` | Remover | Apagar uma avaliação |

**JSON** é um formato de texto para trocar dados, parecido com uma ficha de cadastro:

```json
{ "email": "lucas@email.com", "password": "123456" }
```

**Corpo (body) e cabeçalhos (headers).** O *corpo* é o conteúdo principal da requisição (o JSON acima). Os *cabeçalhos* são informações extras sobre ela, como o `Authorization`, que leva o token de login.

**Status HTTP** é um número que a resposta traz para dizer, rapidamente, como foi o pedido:

| Status | Nome | Significado em palavras simples |
|---|---|---|
| `200` | OK | Deu certo. |
| `201` | Created | Deu certo e algo novo foi criado (ex.: uma conta). |
| `204` | No Content | Deu certo, e não há nada para devolver. |
| `400` | Bad Request | Os dados enviados estão errados ou incompletos. |
| `401` | Unauthorized | Você não está logado ou o token é inválido. |
| `404` | Not Found | O que você procurou não existe. |
| `409` | Conflict | Conflito, por exemplo: esse e-mail já está cadastrado. |
| `500` | Internal Server Error | Erro inesperado no servidor. |

### 1.2 Ferramentas de programação

**Node.js** permite executar JavaScript fora do navegador, como um programa comum. É o que roda o backend.

**TypeScript** é o JavaScript com "etiquetas de tipo" (por exemplo, dizer que uma variável é um texto ou um número). O editor avisa de erros **antes** de o código rodar. Os arquivos terminam em `.ts`. O Node não entende TypeScript diretamente, então ele é *traduzido* para JavaScript (isso se chama **compilar**) ou executado por uma ferramenta que faz essa tradução na hora (o `tsx`).

**npm** é o "loja de aplicativos" do Node: instala bibliotecas feitas por outras pessoas (chamadas **pacotes** ou **dependências**).

- `package.json` é a lista de compras: nome do projeto, scripts e quais pacotes ele usa.
- `node_modules/` é a pasta onde os pacotes baixados ficam. É grande e **nunca vai para o Git**; qualquer pessoa recria com `npm install`.
- `package-lock.json` trava as versões exatas instaladas, para todos da equipe usarem as mesmas.

**Express** é uma biblioteca que facilita criar o servidor web e definir as rotas.

**Módulos ES e o `.js` nos imports.** O projeto usa o sistema moderno de módulos do JavaScript (`"type": "module"` no `package.json`). Nele, ao importar um arquivo local, é preciso escrever a extensão do arquivo **compilado**, mesmo que o original seja `.ts`:

```ts
import { UserService } from "../service/UserService.js"   // o arquivo real é UserService.ts
```

Isso parece estranho, mas é uma regra do TypeScript com módulos ES. Se esquecer o `.js`, aparece o erro `ERR_MODULE_NOT_FOUND`.

### 1.3 Banco de dados e Docker

**Banco de dados** é onde as informações ficam guardadas de forma permanente, organizadas em **tabelas** (como planilhas): uma tabela de usuários, uma de avaliações, etc. Sem ele, tudo se perderia quando o servidor fosse desligado.

**PostgreSQL** é o programa de banco de dados que o projeto usa. Ele entende a linguagem **SQL**.

**Docker** é uma ferramenta que executa programas dentro de "caixas" isoladas, já configuradas. Em vez de instalar e configurar o PostgreSQL no seu computador (o que varia de máquina para máquina), você roda uma caixa pronta com o PostgreSQL dentro. Vocabulário:

| Termo | Em palavras simples |
|---|---|
| **Imagem** | O "molde" ou receita de um programa (ex.: a imagem do PostgreSQL). |
| **Container** | A "caixa" em funcionamento criada a partir de uma imagem. |
| **docker-compose.yml** | Arquivo que descreve quais containers subir e com quais configurações (usuário, senha, porta do banco). |
| **Volume** | Um espaço de armazenamento que fica fora do container. Garante que os dados do banco **não sumam** quando o container é desligado. |
| **Docker Desktop** | O aplicativo que gerencia tudo isso no Windows e no Mac. |

Neste projeto o Docker é usado para o **banco de dados**. A API em si roda direto no seu computador com `npm run dev`.

### 1.4 Prisma

**ORM** é uma ferramenta que faz a "tradução" entre o código e o banco de dados. Em vez de escrever SQL à mão (`INSERT INTO users ...`), escrevemos código TypeScript (`prisma.user.create(...)`). O ORM usado aqui é o **Prisma**.

Os quatro conceitos do Prisma que você vai encontrar:

| Termo | Em palavras simples |
|---|---|
| **`schema.prisma`** | A "planta da casa": descreve as tabelas e os campos do banco (ex.: usuário tem `id`, `name`, `email`, `password`...). |
| **Migration** | Cada mudança no banco vira um arquivo numerado na pasta `prisma/migrations`. É como o **Git do banco de dados**: um histórico que qualquer pessoa da equipe pode aplicar para ter o banco idêntico. |
| **Prisma Client** | Código TypeScript **gerado automaticamente** a partir do `schema.prisma`, com as funções para criar, buscar, atualizar e apagar registros. Fica em `src/generated/prisma`. |
| **Adapter (`adapter-pg`)** | A peça que liga o Prisma ao PostgreSQL (usando o driver `pg`). O Prisma 7 exige esse adapter. |

Existe ainda o **Prisma Studio**, uma interface visual (parecida com uma planilha) para ver e editar os dados do banco.

### 1.5 Zod, schema e DTO

**O problema:** o backend não pode confiar no que chega. Qualquer pessoa pode enviar um e-mail vazio, uma senha de uma letra, ou um texto onde deveria haver um número. Os dados precisam ser conferidos na entrada.

**Zod** é uma biblioteca que resolve isso. Com ela você descreve **como os dados devem ser** e ela confere. Se algo estiver errado, ela interrompe o processo e informa **exatamente o que falhou**. Pense nela como um porteiro que confere os documentos antes de deixar alguém entrar.

```ts
z.string().min(2, "Nome invalido")      // precisa ser um texto com pelo menos 2 caracteres
z.email("email invalido")               // precisa ter formato de e-mail
```

**Schema** é essa descrição de regras. Exemplo: `UserRegisterSchemaDto` define o que é aceito no cadastro.

**DTO** (*Data Transfer Object*, "objeto de transferência de dados") é o nome dado ao **molde dos dados que viajam** entre o frontend e o backend. Cada rota tem o seu DTO de entrada (o que ela aceita) e, às vezes, de saída (o que ela devolve). No projeto, os schemas terminam em `SchemaDto` e os tipos em `DTO`:

| Nome no código | Papel |
|---|---|
| `UserRegisterSchemaDto` | Molde do que chega no **cadastro**. |
| `UserLoginSchemaDto` | Molde do que chega no **login**. |
| `UserResponseSchemaDto` | Molde do que **sai**: o usuário **sem a senha**. |

**Entidade** é o registro completo, do jeito que está no banco, incluindo campos internos como a senha com hash (`UserEntitySchema`).

**Tipos inferidos.** Com `z.infer`, o Zod cria automaticamente o **tipo TypeScript** a partir do schema (por exemplo, `UserRegisterDTO`). Assim o editor sabe quais campos existem e sugere o autocompletar, sem escrever as regras duas vezes.

**Dica:** o Zod também **descarta campos que não estão no molde**. É assim que o `UserResponseSchemaDto` remove a senha antes de a resposta sair.

### 1.6 Segurança: senha, hash, JWT e middleware

**Hash de senha.** Nunca guardamos a senha em texto puro: se o banco vazasse, todas as senhas estariam expostas. Guardamos um **hash**, um "embaralhamento" que não tem volta (como passar uma fruta no liquidificador: não dá para desfazer). Para conferir um login, o sistema aplica o mesmo hash na senha digitada e compara os resultados. O projeto usa a biblioteca `bcryptjs` com **custo 12** (quanto maior o número, mais lento e mais difícil de quebrar).

**JWT (token).** Depois que o usuário faz login, o backend entrega um **token**, uma espécie de **crachá digital** assinado. O frontend mostra esse crachá em toda requisição seguinte, e o backend confere a assinatura. Assim o usuário não precisa enviar e-mail e senha toda vez. O token vai no cabeçalho:

```
Authorization: Bearer <token>
```

**Middleware** é uma função que fica "no meio do caminho", entre a requisição e o código final da rota, para fazer uma verificação ou um tratamento. O projeto tem dois:

- `authMiddleware`: o "segurança da portaria". Confere o token antes de liberar a rota.
- `errorHandler`: a "central de reclamações". Recebe qualquer erro e o transforma em uma resposta organizada.

### 1.7 Variáveis de ambiente e o arquivo `.env`

Algumas informações **mudam de máquina para máquina** (endereço do banco) ou **são secretas** (a senha do banco, o segredo do token). Elas não devem ficar escritas dentro do código, porque o código vai para o Git e é visto por todos. A solução são as **variáveis de ambiente**, guardadas no arquivo `.env`, que **nunca é versionado**. O `.env.example` é um modelo sem os valores secretos, para cada pessoa criar o seu `.env`.

---

## 2. Visão geral do projeto

### Tecnologias usadas

| Camada | Tecnologia |
|---|---|
| Linguagem | TypeScript (módulos ES, `"type": "module"`) |
| Execução | Node.js |
| Servidor HTTP | Express 5 |
| Banco de dados | PostgreSQL, executado via Docker |
| ORM | Prisma 7 com adapter `@prisma/adapter-pg` |
| Validação | Zod 4 |
| Autenticação | JWT (`jsonwebtoken`) |
| Hash de senha | `bcryptjs` (custo 12) |
| Modo desenvolvimento | `tsx` (roda TypeScript direto e reinicia ao salvar) |
| Infraestrutura local | Docker Compose |

### Organização em camadas

O código é dividido em camadas, e **cada camada tem uma única responsabilidade**. Uma analogia ajuda: imagine um restaurante.

| No restaurante | No projeto | Faz o quê |
|---|---|---|
| Porta de entrada e cardápio | **Routes** (rotas) | Define quais pedidos existem (`POST /login`, `GET /me`...) e para quem encaminhar cada um. |
| Recepcionista que confere a reserva | **Middleware** | Confere se o cliente pode entrar (token válido). |
| Garçom | **Controller** | Recebe o pedido, confere se faz sentido (Zod), leva para a cozinha e entrega a resposta. |
| Cozinha | **Service** | Aplica as regras do negócio (aplicar hash na senha, comparar senhas, gerar o token...). |
| Estoquista | **Repository** | O único que vai à despensa: lê e grava no banco, usando o Prisma. |
| Despensa | **Banco de dados** | Onde tudo fica guardado. |

O caminho de uma requisição:

```
Frontend
   │  (requisição HTTP)
   ▼
Routes ──► Middleware (auth) ──► Controller ──► Service ──► Repository ──► Prisma ──► PostgreSQL
                                (valida com Zod) (regras)   (acesso a dados)
   ▲                                                                                      │
   └───────────────────────────────  resposta (JSON + status)  ◄──────────────────────────┘
```

**Por que separar assim?** Porque cada arquivo fica pequeno e com um papel claro, o que facilita achar erros, reaproveitar código e **dividir o trabalho entre pessoas da equipe**: uma pessoa pode mexer no repository sem quebrar o controller de outra.

---

## 3. O que instalar antes

| Ferramenta | Para que serve | Onde obter |
|---|---|---|
| **Node.js** (versão LTS atual ou mais recente) | Executar o backend. Já inclui o `npm`. | nodejs.org |
| **Docker Desktop** | Rodar o banco de dados. | docker.com |
| **Git** | Baixar e versionar o código. | git-scm.com |

Para confirmar que tudo foi instalado, abra um terminal e rode:

```bash
node -v
npm -v
docker -v
docker compose version
git --version
```

Cada comando deve mostrar um número de versão. Se algum disser "comando não encontrado", a ferramenta correspondente não foi instalada (ou o terminal precisa ser reaberto).

> **No Windows:** abra o **Docker Desktop** e espere ele terminar de iniciar antes de subir o banco. Durante a instalação, ele pode pedir para ativar o **WSL 2**; siga o assistente.

---

## 4. Primeiros passos

Faça tudo dentro da pasta `backend/`, em um terminal aberto nessa pasta (por exemplo, o terminal integrado do seu editor de código).

### Passo 1 — Instalar as dependências

```bash
npm install
```

**O que faz:** lê o `package.json` e baixa todos os pacotes para a pasta `node_modules`.
**O que esperar:** pode levar alguns minutos; ao final aparece um resumo dos pacotes adicionados.

### Passo 2 — Criar o arquivo `.env`

```bash
# Linux / macOS / Git Bash
cp .env.example .env

# Windows (cmd ou PowerShell)
copy .env.example .env
```

**O que faz:** cria o seu `.env` a partir do modelo. Depois, abra o arquivo e preencha os valores (veja a [seção 5](#5-variáveis-de-ambiente)).

### Passo 3 — Subir o banco de dados

```bash
npm run docker
```

**O que faz:** executa `docker compose up -d`, que baixa (na primeira vez) e liga o container do PostgreSQL em segundo plano.
**Como conferir:**

```bash
docker compose ps
```

O banco deve aparecer com o estado `running` (ou `Up`). No Docker Desktop, o container aparece com um indicador verde.

### Passo 4 — Gerar o Prisma Client

```bash
npx prisma generate --config prisma7.config.ts
```

**O que faz:** lê o `schema.prisma` e **gera o código** que o projeto usa para falar com o banco (a pasta `src/generated/prisma`).
**O que esperar:** uma mensagem de que o Prisma Client foi gerado.
**Por que é necessário:** essa pasta é gerada, não é escrita à mão, e pode nem estar no Git. Sem ela, o projeto não compila.

### Passo 5 — Criar as tabelas no banco

```bash
npx prisma migrate dev --config prisma7.config.ts
```

**O que faz:** aplica ao banco todas as migrations (o histórico de mudanças) que ainda não foram aplicadas, criando as tabelas.
**O que esperar:** uma mensagem informando as migrations aplicadas. Se o Prisma perguntar um nome de migration, é porque o `schema.prisma` mudou sem uma migration correspondente (veja a [seção 7](#7-prisma)).

### Passo 6 — Iniciar a API

```bash
npm run dev
```

**O que faz:** inicia o servidor e o mantém em modo *watch*: **cada vez que você salva um arquivo, ele reinicia sozinho**.
**O que esperar:** o terminal mostra uma mensagem do servidor indicando a porta (o texto exato depende do arquivo `server.ts`). A API está no ar em `http://localhost:<PORT>`.

Para parar o servidor, pressione `Ctrl + C` no terminal.

### Resumo para copiar e colar

```bash
npm install
cp .env.example .env        # depois, preencha os valores no .env
npm run docker
npx prisma generate --config prisma7.config.ts
npx prisma migrate dev --config prisma7.config.ts
npm run dev
```

Na próxima vez, basta `npm run docker` (se o banco estiver parado) e `npm run dev`.

---

## 5. Variáveis de ambiente

As variáveis ficam no arquivo `.env` (veja o conceito na [seção 1.7](#17-variáveis-de-ambiente-e-o-arquivo-env)).

<!-- CONFERIR: os nomes abaixo devem bater com o .env.example real do projeto -->

| Variável | Para que serve | Exemplo |
|---|---|---|
| `PORT` | Porta em que a API fica escutando. | `3000` |
| `DATABASE_URL` | "Endereço" do banco de dados: quem é o usuário, a senha, onde fica e qual o nome do banco. | `postgresql://postgres:postgres@localhost:5432/rentmatch?schema=public` |
| `JWT_SECRET` | Segredo usado para assinar e conferir os tokens de login. Quem souber esse segredo consegue forjar tokens. | uma sequência longa e aleatória |

Exemplo de `.env`:

```env
PORT=3000
DATABASE_URL="postgresql://postgres:postgres@localhost:5432/rentmatch?schema=public"
JWT_SECRET="troque-por-um-segredo-longo-e-aleatorio"
```

**Como ler a `DATABASE_URL`:**

```
postgresql://  postgres  :  postgres  @  localhost  :  5432  /  rentmatch  ?schema=public
              └usuário┘   └senha─┘      └─onde─┘      └porta┘   └nome do banco┘
```

**Pontos de atenção:**

- Usuário, senha, porta e nome do banco da `DATABASE_URL` precisam **ser iguais aos definidos no `docker-compose.yml`**. Se forem diferentes, a API não consegue se conectar.
- Para gerar um `JWT_SECRET` forte, rode:

  ```bash
  node -e "console.log(require('crypto').randomBytes(48).toString('hex'))"
  ```

- **Nunca** faça commit do `.env` nem compartilhe seus segredos em mensagens.
- Se criar uma variável nova, adicione-a também ao `.env.example` (sem o valor real), para o resto da equipe saber que ela existe.

---

## 6. Docker e o banco de dados

O `docker-compose.yml` é o arquivo que descreve o container do **PostgreSQL**. Você não precisa editá-lo no dia a dia; basta usar os comandos abaixo.

| Comando | O que faz | Quando usar |
|---|---|---|
| `npm run docker` | Atalho para `docker compose up -d`. Liga o banco em **segundo plano** (`-d` = *detached*, o terminal fica livre). | Ao começar a trabalhar. |
| `docker compose ps` | Lista os containers e mostra se estão rodando. | Para conferir se o banco está no ar. |
| `docker compose logs -f` | Mostra os registros (logs) do banco em tempo real. `Ctrl + C` sai. | Para investigar erros de conexão. |
| `docker compose stop` | **Pausa** os containers, mantendo tudo. | Ao terminar o trabalho. |
| `docker compose start` | Liga novamente containers pausados. | Depois de um `stop`. |
| `docker compose down` | **Remove** os containers, mas **mantém os dados** (o volume continua). | Para "desligar tudo" sem perder dados. |
| `docker compose down -v` | Remove os containers **e apaga o volume**. **Todos os dados do banco são perdidos.** | Só para zerar o banco do zero. |
| `docker compose restart` | Reinicia os serviços. | Se o banco travar. |

**Se o banco não subir:**

1. Confirme que o Docker Desktop está aberto e iniciado.
2. Rode `docker compose ps` e `docker compose logs -f` para ver a mensagem de erro.
3. Veja a [seção 19](#19-solução-de-problemas), principalmente o caso de "porta já em uso".

**Para zerar o banco local** (útil se os dados de teste ficaram bagunçados):

```bash
docker compose down -v
npm run docker
npx prisma migrate dev --config prisma7.config.ts
```

---

## 7. Prisma

O Prisma é quem conversa com o banco. Os conceitos (schema, migration, client, adapter) estão na [seção 1.4](#14-prisma). Esta seção mostra como usá-lo.

### Particularidades do Prisma 7 neste projeto

- O **Prisma Client é gerado dentro do projeto**, em `src/generated/prisma` (e não em `node_modules`). O código importa o client dessa pasta.
- A conexão com o banco usa o **adapter** `@prisma/adapter-pg` com o driver `pg`, configurados em `src/lib/prisma.ts`.
- A configuração do **CLI** (onde está o schema, onde ficam as migrations, qual a URL do banco) fica no arquivo **`prisma7.config.ts`**, e não mais no `schema.prisma`.
- O Prisma 7 **não lê o `.env` sozinho**: isso é feito no arquivo de configuração (por isso o pacote `dotenv`).
- Os comandos `migrate dev` e `db push` **não rodam o `generate` automaticamente**. Depois de mudar o schema, rode o `generate` à mão.

> **Por que todo comando tem `--config prisma7.config.ts`?** O CLI do Prisma procura, por padrão, um arquivo chamado `prisma.config.ts`. Como o arquivo deste projeto se chama `prisma7.config.ts`, é preciso apontar o caminho com a flag `--config`.

### Comandos

| Comando | O que faz | Quando usar |
|---|---|---|
| `npx prisma generate --config prisma7.config.ts` | Gera o Prisma Client em `src/generated/prisma`. | Depois de clonar o projeto e **sempre que o `schema.prisma` mudar**. |
| `npx prisma migrate dev --name <nome> --config prisma7.config.ts` | Cria uma nova migration com a mudança do schema e a aplica ao banco. | Quando **você** alterar o `schema.prisma`, ou para aplicar as migrations de outras pessoas. Depois, rode o `generate`. |
| `npx prisma migrate deploy --config prisma7.config.ts` | Aplica as migrations pendentes **sem criar novas**. | Em produção ou CI. |
| `npx prisma migrate status --config prisma7.config.ts` | Mostra quais migrations já foram aplicadas e quais faltam. | Para conferir o estado do banco. |
| `npx prisma migrate reset --config prisma7.config.ts` | **Apaga e recria o banco**, reaplicando todas as migrations. | Só em desenvolvimento, quando quiser recomeçar. |
| `npx prisma db push --config prisma7.config.ts` | Faz o banco ficar igual ao schema **sem criar migration**. | Testes rápidos. Evite no fluxo da equipe, pois não deixa histórico. |
| `npx prisma studio --config prisma7.config.ts` | Abre no navegador uma interface para ver e editar os dados. | Para inspecionar ou inserir dados de teste. |
| `npx prisma format --config prisma7.config.ts` | Organiza e formata o `schema.prisma`. | Depois de editar o schema. |
| `npx prisma validate --config prisma7.config.ts` | Confere se o `schema.prisma` está correto. | Se o Prisma reclamar do schema. |

### Fluxo para alterar o banco (por exemplo, criar a tabela de avaliações)

1. **Edite** o arquivo `prisma/schema.prisma` (novo model, novo campo...).
2. **Crie e aplique a migration**, dando um nome que descreva a mudança:

   ```bash
   npx prisma migrate dev --name cria_tabela_evaluation --config prisma7.config.ts
   ```

3. **Gere o client de novo** para o código enxergar a mudança:

   ```bash
   npx prisma generate --config prisma7.config.ts
   ```

4. **Faça o commit** do `schema.prisma` **e** da pasta `prisma/migrations`. Sem as migrations no Git, as outras pessoas não conseguem reproduzir o seu banco.

**Quando outra pessoa da equipe mudar o schema:** depois do `git pull`, rode `migrate dev` (ou `migrate deploy`) e `generate`.

### Usando o Prisma no código

Todos os repositories importam a instância única do Prisma de `src/lib/prisma.ts`:

```ts
import { prisma } from "../lib/prisma.js";

// buscar um usuário pelo e-mail
const user = await prisma.user.findUnique({ where: { email } });

// criar um usuário
const novo = await prisma.user.create({ data: { name, email, password } });
```

Repare que `prisma.user` corresponde ao model `User` do schema. Se você criar o model `Evaluation`, passa a existir `prisma.evaluation`.

> A pasta `src/generated/prisma` é **gerada automaticamente**: nunca edite esses arquivos à mão (a próxima geração apagaria a edição). Se ela não estiver no Git, lembre de rodar o `generate` depois de clonar.

---

## 8. Scripts npm

Scripts são atalhos para comandos longos, definidos no `package.json`. Rodam com `npm run <nome>` (o `start` pode ser abreviado para `npm start`).

| Script | Comando por trás | O que faz |
|---|---|---|
| `npm run dev` | `tsx --watch src/server.ts` | Inicia a API em desenvolvimento. O `tsx` executa o TypeScript direto e o `--watch` **reinicia o servidor sempre que você salva um arquivo**. |
| `npm run docker` | `docker compose up -d` | Sobe o banco de dados em segundo plano. |
| `npm run build` | `tsc` | **Compila** o TypeScript para JavaScript na pasta `dist/`. Também serve para encontrar erros de tipo. |
| `npm start` | `node dist/server.js` | Executa a versão compilada (modo "produção"). **Rode `npm run build` antes**, senão a pasta `dist/` não existe. |

---

## 9. Dependências

### Pacotes de produção (`dependencies`)

São os pacotes que o projeto precisa para **funcionar**.

| Pacote | Em palavras simples | Onde é usado |
|---|---|---|
| `express` (v5) | Cria o servidor web e as rotas. A versão 5 já repassa ao `errorHandler` os erros que acontecem em funções `async`. | Rotas, controllers e middlewares |
| `@prisma/client` | O Prisma Client em tempo de execução: as funções que consultam o banco. | Repositories |
| `@prisma/adapter-pg` | O "plugue" que liga o Prisma ao PostgreSQL (exigido pelo Prisma 7). | `lib/prisma.ts` |
| `pg` | O driver que realmente conversa com o PostgreSQL. | Usado pelo adapter |
| `zod` (v4) | Valida os dados de entrada e saída (veja a [seção 1.5](#15-zod-schema-e-dto)). | `models/` e controllers |
| `bcryptjs` | Aplica hash nas senhas e compara senhas com hashes. | `UserService` |
| `jsonwebtoken` | Cria e verifica os tokens JWT. | `TokenService` |
| `dotenv` | Lê o arquivo `.env` e disponibiliza os valores ao programa. | Configuração do projeto e do Prisma |

### Pacotes de desenvolvimento (`devDependencies`)

Só são necessários **enquanto se programa** (não vão para a execução em produção).

| Pacote | Em palavras simples |
|---|---|
| `typescript` | O compilador do TypeScript (comando `tsc`). |
| `tsx` | Executa arquivos `.ts` diretamente e reinicia ao salvar. Usado no `npm run dev`. |
| `prisma` | A ferramenta de linha de comando do Prisma (`generate`, `migrate`, `studio`...). |
| `@types/node` | "Dicionário" de tipos do Node.js para o editor entender. |
| `@types/express` | Tipos do Express. |
| `@types/jsonwebtoken` | Tipos do `jsonwebtoken`. |
| `@types/pg` | Tipos do `pg`. |
| `@types/bcrypt` | Tipos do pacote `bcrypt`. O projeto usa o `bcryptjs`, que já inclui seus próprios tipos. |

> Os pacotes que começam com `@types/` não adicionam funcionalidade: só ensinam o TypeScript como cada biblioteca funciona.

### Gerenciando dependências

```bash
npm install <pacote>        # instala e adiciona em dependencies
npm install -D <pacote>     # instala e adiciona em devDependencies
npm uninstall <pacote>      # remove
npm outdated                # mostra pacotes com versão mais nova
```

Sempre faça o commit do `package.json` **e** do `package-lock.json` juntos.

---

## 10. Estrutura de pastas

```
backend/
├── node_modules/                 # pacotes baixados (não vai para o Git)
├── prisma/                       # schema.prisma e migrations
├── src/
│   ├── controller/
│   │   └── UserController.ts
│   ├── generated/
│   │   └── prisma/               # Prisma Client gerado (não editar)
│   │       ├── internal/
│   │       ├── models/
│   │       ├── browser.ts
│   │       ├── client.ts
│   │       ├── commonInputTypes.ts
│   │       ├── enums.ts
│   │       └── models.ts
│   ├── lib/
│   │   └── prisma.ts
│   ├── middleware/
│   │   ├── AuthMiddleware.ts
│   │   └── ErrorHandler.ts
│   ├── models/
│   │   └── User.ts
│   ├── repository/
│   │   └── UserRepository.ts
│   ├── routes/
│   │   └── UserRoutes.ts
│   ├── service/
│   │   └── UserService.ts
│   ├── utils/
│   │   ├── AppError.ts
│   │   └── TokenService.ts
│   ├── index.ts
│   └── server.ts
├── .env                          # seus valores reais (não vai para o Git)
├── .env.example                  # modelo das variáveis
├── .gitignore
├── docker-compose.yml
├── package-lock.json
├── package.json
├── prisma7.config.ts
└── tsconfig.json
```

### Arquivos da raiz do backend

| Arquivo / pasta | O que é |
|---|---|
| `package.json` | Nome do projeto, scripts e lista de dependências. |
| `package-lock.json` | Trava as versões exatas dos pacotes instalados. |
| `node_modules/` | Pacotes baixados pelo `npm install`. |
| `.env` | Seus valores reais de configuração e segredos. **Nunca** vai para o Git. |
| `.env.example` | Modelo das variáveis, sem segredos. Vai para o Git. |
| `.gitignore` | Lista do que o Git deve ignorar (`.env`, `node_modules`, `dist`...). |
| `docker-compose.yml` | Receita do container do banco de dados. |
| `prisma/` | Contém o `schema.prisma` (a "planta" do banco) e a pasta `migrations/` (o histórico de mudanças). |
| `prisma7.config.ts` | Configuração do CLI do Prisma: onde estão o schema e as migrations e qual a URL do banco. |
| `tsconfig.json` | Configuração do compilador TypeScript (como traduzir `.ts` para `.js`). |
| `dist/` | Aparece depois do `npm run build`. É o código compilado. Não vai para o Git. |

### A pasta `src/`, arquivo por arquivo

<!-- CONFERIR: descrição de index.ts, server.ts e lib/prisma.ts inferida do uso nos outros arquivos -->

#### `index.ts` e `server.ts` — onde tudo começa

- **`index.ts`** monta a aplicação: cria o app Express, instancia as peças na ordem `UserRepository` → `UserService` → `UserController` (cada uma recebe a anterior), **exporta o `userController`** (as rotas importam ele daqui) e liga as rotas e o `errorHandler`.
- **`server.ts`** é o **ponto de entrada**: coloca o servidor para escutar na porta definida em `PORT`. É o arquivo que o `npm run dev` executa.

#### `routes/` — o "cardápio"

**`UserRoutes.ts`** diz quais rotas de usuário existem e qual método do controller atende cada uma. Também é aqui que se aplica o `authMiddleware` nas rotas que exigem login:

```ts
userRoutes.post("/login", (req, res) => userController.login(req, res))                    // pública
userRoutes.get("/me", authMiddleware, (req, res) => userController.me(req, res))           // exige login
```

**Mexa aqui quando:** criar uma rota nova ou mudar o caminho/método de uma existente.

#### `controller/` — o "garçom"

**`UserController.ts`** é a camada HTTP. Cada método: (1) lê o que veio na requisição, (2) **valida com o Zod**, (3) chama o service, (4) devolve a resposta com o status correto. **Não contém regra de negócio.**

| Método | O que faz | Resposta |
|---|---|---|
| `register` | Valida o corpo com `UserRegisterSchemaDto` e cadastra o usuário. | `201` + usuário criado |
| `login` | Valida com `UserLoginSchemaDto` e autentica. | `200` + `{ token }` |
| `me` | Busca o perfil do usuário logado. | `200` + usuário |
| `updateMe` | Valida com `UserUpdateProfileSchemaDto` e atualiza nome/e-mail. | `200` + usuário |
| `changePassword` | Valida com `UserChangePasswordSchemaDto` e troca a senha. | `204` (sem corpo) |

**Mexa aqui quando:** mudar o formato da resposta ou o status devolvido.

#### `service/` — a "cozinha"

**`UserService.ts`** contém as **regras de negócio**, sem saber nada de `req`/`res`:

- `register`: aplica o hash na senha (custo 12) e manda o repository gravar.
- `login`: busca o usuário pelo e-mail, compara a senha digitada com o hash e gera o token.
- `getProfile` / `updateProfile`: lê e atualiza nome e e-mail.
- `changePassword`: confere a senha atual (se estiver errada, lança `AppError` com status 400), aplica hash na nova e atualiza.

**Mexa aqui quando:** mudar uma regra do sistema (ex.: como a classificação de uma avaliação é calculada).

#### `repository/` — o "estoquista"

**`UserRepository.ts`** é a **única camada que fala com o banco** (via Prisma). Métodos: `create`, `update`, `findById`, `findEntityById`, `findByEmail` e `delete`.

Atenção a um detalhe importante:

- `create`, `update` e `findById` devolvem o usuário **sem a senha** (passam pelo `UserResponseSchemaDto`).
- `findByEmail` e `findEntityById` devolvem a **entidade completa, com o hash da senha**, para uso **interno** (login e troca de senha). Esse retorno nunca deve ser enviado direto ao cliente.

**Mexa aqui quando:** precisar de uma consulta nova ao banco.

#### `models/` — os "moldes" dos dados

**`User.ts`** reúne os schemas do Zod e os tipos do usuário (veja a [seção 1.5](#15-zod-schema-e-dto)):

| Schema | Para que serve |
|---|---|
| `UserEntitySchema` | O usuário completo: `id`, `name`, `email`, `password`, `createdAt`. É a base dos outros. |
| `UserRegisterSchemaDto` | O que o **cadastro** aceita: `name` (mín. 2 caracteres), `email` válido e `password` (mín. 6 caracteres). |
| `UserUpdateSchemaDto` | Versão parcial (todos os campos opcionais), usada pelo repository ao atualizar. |
| `UserLoginSchemaDto` | O que o **login** aceita: `email` e `password`. |
| `UserResponseSchemaDto` | O que **sai** para o cliente: o usuário **sem** a senha. |
| `UserUpdateProfileSchemaDto` | O que a **edição de perfil** aceita: `name` e `email`, ambos opcionais. |
| `UserChangePasswordSchemaDto` | O que a **troca de senha** aceita: `currentPassword`, `newPassword` (mín. 6) e `confirmNewPassword` (precisa ser igual à nova senha). |

No fim do arquivo, os tipos (`UserRegisterDTO`, `UserLoginDTO`...) são criados automaticamente a partir dos schemas com `z.infer`.

**Mexa aqui quando:** mudar as regras de validação (ex.: exigir senha de 8 caracteres) ou adicionar um campo.

#### `middleware/` — o que fica "no meio do caminho"

- **`AuthMiddleware.ts`** é o "segurança da portaria". Lê o header `Authorization: Bearer <token>`, confere o token e, se estiver tudo certo, guarda o id do usuário em `res.locals.userId` para os próximos passos usarem. Se algo estiver errado, responde `401`.
- **`ErrorHandler.ts`** é a "central de reclamações": captura qualquer erro lançado no sistema e o transforma numa resposta organizada (veja a [seção 13](#13-tratamento-de-erros)).

#### `utils/` — ferramentas de apoio

- **`AppError.ts`**: uma classe de erro que carrega uma **mensagem** e um **status HTTP**. Para devolver um erro de negócio, basta `throw new AppError("Senha atual incorreta", 400)`.
- **`TokenService.ts`**: `generateToken(userId)` cria o token JWT e `verifyToken(token)` o confere, usando o `JWT_SECRET`.

#### `lib/` — configurações compartilhadas

- **`prisma.ts`** exporta a **instância única do Prisma** (configurada com o adapter do `pg` e a `DATABASE_URL`). Todos os repositories importam daqui, em vez de criar uma conexão cada um.

#### `generated/prisma/` — código gerado

É o **Prisma Client**, gerado pelo `prisma generate`. Contém o client (`client.ts`), os tipos das tabelas (`models.ts` e `models/`), os enums (`enums.ts`), tipos de filtros (`commonInputTypes.ts`), a versão para navegador (`browser.ts`) e arquivos internos (`internal/`). **Não edite nada aqui.**

### Por onde começar a ler o código

Siga o caminho que a requisição percorre:

1. `index.ts` — como tudo é montado.
2. `routes/UserRoutes.ts` — quais rotas existem.
3. `controller/UserController.ts` — o que cada rota faz.
4. `models/User.ts` — quais dados são aceitos.
5. `service/UserService.ts` — as regras de negócio.
6. `repository/UserRepository.ts` — como o banco é acessado.
7. `middleware/` e `utils/` — segurança e tratamento de erros.

---

## 11. Seguindo o código passo a passo

Nada explica melhor do que acompanhar um caso real. Vamos seguir o **cadastro** de um usuário do começo ao fim.

O frontend envia:

```
POST /register
Content-Type: application/json

{ "name": "Lucas Almeida", "email": "lucas@email.com", "password": "123456" }
```

### Passo 1 — A rota

Em `routes/UserRoutes.ts`:

```ts
userRoutes.post("/register", (req, res) => userController.register(req, res))
```

A rota apenas encaminha o pedido para o método `register` do controller. Não há middleware de login, já que ninguém pode estar logado antes de ter uma conta.

### Passo 2 — O controller valida os dados

Em `controller/UserController.ts`:

```ts
async register(req: Request, res: Response) {
    const data = UserRegisterSchemaDto.parse(req.body)
    const userCreated = await this.userService.register(data)
    return res.status(201).json(userCreated)
}
```

Linha por linha:

- `req.body` é o JSON que o frontend enviou.
- `UserRegisterSchemaDto.parse(...)` é o **porteiro Zod**: confere se o corpo respeita as regras. Se algo estiver errado (nome com 1 letra, e-mail inválido, senha curta), o `parse` **lança um erro** e o código para aqui. O `errorHandler` transforma esse erro em um `400` com a lista de problemas. Se estiver tudo certo, `data` contém os dados já validados e com o tipo correto.
- `await this.userService.register(data)` chama o service e espera ele terminar.
- `res.status(201).json(userCreated)` responde com status `201` (criado) e o usuário em JSON.

### Passo 3 — O schema define as regras

Em `models/User.ts`:

```ts
export const UserRegisterSchemaDto = UserEntitySchema.omit({
    id: true,
    createdAt: true
}).extend({
    password: z.string().min(6, "A senha deve ter no minimo 6 caracteres.")
})
```

- `UserEntitySchema` é o molde do usuário completo.
- `.omit({ id, createdAt })` **tira** o `id` e o `createdAt`: quem se cadastra não informa isso, o banco gera.
- `.extend({ password: ... })` **reforça** a regra da senha (mínimo de 6 caracteres) e define a mensagem de erro.

Resultado: o cadastro aceita exatamente `name`, `email` e `password`.

### Passo 4 — O service aplica as regras de negócio

Em `service/UserService.ts`:

```ts
async register(data: UserRegisterDTO) {
    const { password } = data
    data.password = await hash(password, 12)
    const userCreated = await this.userRepository.create(data)
    return userCreated;
}
```

Aqui acontece o que **nunca pode faltar**: a senha é trocada pelo **hash** antes de ir ao banco (`hash(password, 12)`). O banco jamais recebe a senha real.

### Passo 5 — O repository grava no banco

Em `repository/UserRepository.ts`:

```ts
async create(data: UserRegisterDTO) {
    const { name, email, password } = data
    const user = await prisma.user.create({
        data: { name, email, password }
    })
    return UserResponseSchemaDto.parse(user)
}
```

- `prisma.user.create(...)` insere uma linha na tabela de usuários (o `id` e o `createdAt` são gerados pelo banco).
- `UserResponseSchemaDto.parse(user)` passa o resultado pelo molde de **saída**, que não tem o campo `password`. Como o Zod descarta o que não está no molde, **o hash da senha não sai do repository**.

### Passo 6 — A resposta

O usuário volta pelo caminho inverso (repository → service → controller) e o frontend recebe:

```
201 Created

{ "id": "9c0f...", "name": "Lucas Almeida", "email": "lucas@email.com", "createdAt": "2026-10-28T12:00:00.000Z" }
```

### E se algo der errado?

| Situação | O que acontece | Resposta |
|---|---|---|
| Nome com 1 letra | O `parse` do Zod lança `ZodError` | `400` com a lista de campos inválidos |
| E-mail já cadastrado | O banco rejeita (e-mail é único) e o Prisma lança o erro `P2002` | `409` "Registro ja existe" |
| Falha inesperada | Qualquer outro erro | `500` "Erro interno do servidor" |

Todos esses erros caem no `errorHandler`, que decide o status e a mensagem (veja a [seção 13](#13-tratamento-de-erros)).

### O login e as rotas protegidas

**Login** (`POST /login`): o controller valida e-mail e senha; o service busca o usuário pelo e-mail, usa o `compare` do `bcryptjs` para checar a senha contra o hash e, se bater, chama `generateToken(user.id)`. O controller devolve `200` com `{ "token": "..." }`.

**Usando o token** (`GET /me`):

1. O frontend envia `Authorization: Bearer <token>`.
2. O `authMiddleware` confere o token e coloca o id em `res.locals.userId`.
3. O controller chama `this.userService.getProfile(res.locals.userId)`.
4. O perfil do **próprio** usuário volta na resposta.

Como o id vem do **token** e não do corpo da requisição, um usuário não consegue pedir os dados de outro: é assim que se garante a privacidade (requisito RNF05).

---

## 12. Autenticação

- O login devolve um **JWT** em `{ "token": "..." }`.
- O frontend guarda esse token e o envia em toda rota protegida, no cabeçalho:

  ```
  Authorization: Bearer <token>
  ```

- O `authMiddleware` valida o token e disponibiliza o id do usuário em `res.locals.userId`. **Toda consulta a dados de um usuário deve filtrar por esse id.**
- As senhas são armazenadas com **hash `bcryptjs` (custo 12)**, nunca em texto puro (requisito RNF04).
- **Logout** é feito no frontend, apagando o token guardado. Não existe rota de logout: o JWT não fica registrado no servidor, então não há nada para encerrar lá.

**Mensagens do `authMiddleware`** (todas com status `401` e no formato `{ "error": "<mensagem>" }`):

| Situação | Mensagem |
|---|---|
| Não enviou o header `Authorization` | `Token não fornecido` |
| Header fora do formato `Bearer <token>` | `Erro no formato do token` |
| Token vazio | `Erro ao extrair conteudo do token` |
| Token inválido ou expirado | `Token inválido ou expirado` |

---

## 13. Tratamento de erros

Em vez de cada rota tratar os próprios erros, o projeto tem **um único lugar** que decide como responder: o `errorHandler` (`middleware/ErrorHandler.ts`). O código lança o erro e o `errorHandler` cuida do resto.

| Origem do erro | Status | Corpo da resposta |
|---|---|---|
| `ZodError` (dados fora das regras) | `400` | `{ "message": "Dados invalidos", "errors": [{ "field": "email", "message": "email invalido" }] }` |
| `AppError` (erro de negócio lançado de propósito) | o status informado | `{ "message": "<mensagem>" }` |
| Erro `P2002` do Prisma (registro duplicado, como e-mail já usado) | `409` | `{ "message": "Registro ja existe" }` |
| Qualquer outro erro | `500` | `{ "message": "Erro interno do servidor" }` (o erro real é impresso no console do servidor) |

**Como lançar um erro de negócio:**

```ts
import { AppError } from "../utils/AppError.js"

throw new AppError("Avaliação não encontrada", 404)
```

---

## 14. Rotas implementadas

Os caminhos abaixo são **relativos ao prefixo** em que o router de usuário é montado no `index.ts` (por exemplo, `/users`).

| Método | Rota | Precisa de login? | Para que serve | Sucesso |
|---|---|---|---|---|
| `POST` | `/register` | não | Criar uma conta | `201` + usuário |
| `POST` | `/login` | não | Entrar e receber o token | `200` + `{ token }` |
| `GET` | `/me` | sim | Ver os dados do usuário logado | `200` + usuário |
| `PUT` | `/me` | sim | Alterar nome e/ou e-mail | `200` + usuário |
| `PUT` | `/me/password` | sim | Alterar a senha | `204` |

### `POST /register`

Corpo enviado:

```json
{ "name": "Lucas Almeida", "email": "lucas@email.com", "password": "123456" }
```

Resposta `201`:

```json
{ "id": "uuid", "name": "Lucas Almeida", "email": "lucas@email.com", "createdAt": "2026-10-28T12:00:00.000Z" }
```

Erros possíveis: `400` (dados inválidos) e `409` (e-mail já cadastrado).

### `POST /login`

Corpo enviado:

```json
{ "email": "lucas@email.com", "password": "123456" }
```

Resposta `200`:

```json
{ "token": "eyJhbGciOi..." }
```

Guarde esse token: ele será necessário nas rotas protegidas.

### `GET /me`

Não leva corpo; precisa do header `Authorization`. Resposta `200`: `{ "id", "name", "email", "createdAt" }`. O `createdAt` alimenta o "Membro desde" da tela de perfil.

### `PUT /me`

Corpo enviado (os dois campos são opcionais; envie só o que quer mudar):

```json
{ "name": "Lucas A. Almeida", "email": "novo@email.com" }
```

Erros possíveis: `400` (dados inválidos) e `409` (o novo e-mail já está em uso).

### `PUT /me/password`

Corpo enviado:

```json
{ "currentPassword": "123456", "newPassword": "654321", "confirmNewPassword": "654321" }
```

Resposta `204` (sem corpo). Erros possíveis: `400` com "Senha atual incorreta" ou "As senhas nao conferem".

> O `UserRepository` tem um método `delete`, mas **ainda não existe rota** que o use.

---

## 15. Testando a API

Para testar rotas sem precisar das telas, use um cliente de API, como o **Thunder Client** (extensão do VS Code) ou o **Postman**. O passo a passo abaixo usa o Thunder Client; no Postman é equivalente.

### Exemplo no Thunder Client

**1. Cadastrar**

1. Clique em *New Request*.
2. Escolha o método `POST` e a URL `http://localhost:3000/users/register` (ajuste a porta e o prefixo conforme o seu projeto).
3. Abra a aba **Body**, escolha **JSON** e cole:

   ```json
   { "name": "Lucas Almeida", "email": "lucas@email.com", "password": "123456" }
   ```

4. Clique em **Send**. Você deve ver o status `201` e o usuário na resposta.

**2. Fazer login**

1. Nova requisição `POST` para `/users/login` com o corpo `{ "email": "lucas@email.com", "password": "123456" }`.
2. A resposta traz o `token`. **Copie o valor.**

**3. Chamar uma rota protegida**

1. Nova requisição `GET` para `/users/me`.
2. Na aba **Auth** (ou **Headers**), configure `Authorization: Bearer <cole_o_token_aqui>`.
3. Clique em **Send**: deve voltar `200` com os seus dados. Sem o token, a resposta é `401`.

### Exemplo com `curl` (terminal)

```bash
# cadastro
curl -X POST http://localhost:3000/users/register \
  -H "Content-Type: application/json" \
  -d '{"name":"Lucas Almeida","email":"lucas@email.com","password":"123456"}'

# login (devolve { "token": "..." })
curl -X POST http://localhost:3000/users/login \
  -H "Content-Type: application/json" \
  -d '{"email":"lucas@email.com","password":"123456"}'

# perfil (rota protegida)
curl http://localhost:3000/users/me -H "Authorization: Bearer SEU_TOKEN_AQUI"
```

> No **PowerShell**, `curl` é um apelido de outro comando. Use `curl.exe` ou um cliente gráfico.

### Conferindo os dados no banco

```bash
npx prisma studio --config prisma7.config.ts
```

Abre no navegador uma interface em que você vê as tabelas, as linhas criadas e pode editar ou apagar registros de teste.

---

## 16. O que falta implementar

Levantamento feito a partir da documentação (requisitos funcionais RF01 a RF15) e das telas do frontend (`signup`, `login`, `recover_password`, `home` e `profile`).

### 16.1 Rotas pendentes

| Status | Método | Rota | Tela | Requisito | Descrição |
|---|---|---|---|---|---|
| pendente | `POST` | `/forgot-password` | `recover_password` | RF03 | Recebe o e-mail, gera um token com validade curta e envia o e-mail de recuperação. **Sempre responde `200`**, para não revelar se o e-mail existe. |
| pendente | `POST` | `/reset-password` | `reset_password` (nova) | RF03 | Recebe `token`, `newPassword` e `confirmNewPassword`; valida o token e atualiza a senha. |
| pendente | `GET` | `/evaluations/options` | `home` (selects) | RF04 | Lista de bairros e tipos de imóvel aceitos. Deve usar a mesma lista do treino do modelo. |
| **provisória** | `POST` | `/evaluations` | `home` ("Avaliar imóvel") | RF04 a RF10, RF15 | **Depende do modelo.** Veja a [seção 16.3](#163-rota-que-depende-do-modelo). |
| pendente | `GET` | `/evaluations/summary` | `home` (4 cartões) e `profile` (3 números) | RF13 | Totais por classificação, considerando só as avaliações **salvas**. |
| pendente | `GET` | `/evaluations` | `home` ("Avaliações recentes", `?limit=4`) e histórico completo (nova) | RF12 | Histórico paginado, só salvas, mais recentes primeiro. |
| pendente | `GET` | `/evaluations/:id` | resultado e explicabilidade (novas) | RF09, RF10 | Resultado completo da avaliação, com os fatores. |
| pendente | `PATCH` | `/evaluations/:id/save` | resultado ("Salvar") | RF11 | Marca a avaliação como salva. |
| opcional | `DELETE` | `/evaluations/:id` | nenhuma ainda | n/a | Remove uma avaliação do histórico. |

Observações:

- **Todas as rotas de `/evaluations` exigem login** (`authMiddleware`) e **filtram por `res.locals.userId`** (RNF05: cada usuário só acessa os próprios dados). Se alguém pedir uma avaliação de outra pessoa, responda `404`.
- **Ordem das rotas no Express:** declare `/evaluations/summary` e `/evaluations/options` **antes** de `/evaluations/:id`. Caso contrário, o Express interpreta "summary" e "options" como se fossem um `:id`.
- **Rascunho e salvar:** `POST /evaluations` grava a avaliação como **rascunho** (`saved: false`). Só depois que o usuário clica em "Salvar" (`PATCH .../save`) ela entra no histórico e nas contagens. Por isso os cartões da home contam só as salvas, senão o total não bateria com o histórico.
- Não há rota para "Nova avaliação" (RF14 é só navegação no frontend), e a validação dos dados (RF15) é feita com Zod dentro do `POST /evaluations`.
- "Sair da conta", "Sobre" e "Contato" também não precisam de rota.

### 16.2 Contrato previsto (quando o modelo estiver pronto)

"Contrato" é o combinado entre frontend e backend sobre o formato dos dados. Ele permite que as duas partes sejam desenvolvidas ao mesmo tempo. Os nomes dos campos seguem o padrão em inglês dos DTOs atuais; o frontend faz a tradução dos seus ids (por exemplo, `valor-anunciado` vira `advertisedPrice`).

**`POST /evaluations` — corpo enviado**

```json
{
  "neighborhood": "Cambuí",
  "propertyType": "Apartamento",
  "area": 65,
  "bedrooms": 2,
  "parking": 1,
  "advertisedPrice": 1800,
  "condoFee": 450,
  "iptu": 120
}
```

Regras de validação (RF15): `neighborhood` e `propertyType` precisam estar nas listas aceitas; `area` e `advertisedPrice` maiores que 0; `bedrooms` e `parking` inteiros maiores ou iguais a 0; `condoFee` e `iptu` opcionais (padrão 0).

**`POST /evaluations` — resposta `201` (versão final)**

```json
{
  "id": "uuid",
  "neighborhood": "Cambuí",
  "propertyType": "Apartamento",
  "area": 65,
  "bedrooms": 2,
  "parking": 1,
  "advertisedPrice": 1800,
  "condoFee": 450,
  "iptu": 120,
  "estimatedPrice": 1650,
  "difference": 150,
  "differencePercent": 9.1,
  "classification": "CARO",
  "factors": [{ "feature": "condoFee", "contribution": 90 }],
  "saved": false,
  "createdAt": "2026-10-28T12:00:00.000Z"
}
```

- `classification` pode ser `CARO`, `PRECO_JUSTO` ou `OPORTUNIDADE`.
- O **limiar** entre as classes ainda precisa ser definido pelo grupo. Os exemplos da tela `home` combinam com **±5%** em relação ao valor estimado: Cambuí +9,1% = Caro; Centro +2,4% e Taquaral −4,6% = Preço justo; Barão Geraldo −14,7% = Oportunidade.
- Os `factors` dizem o quanto cada característica pesou, em reais. O texto exibido ("Condomínio acima da média") pode ser montado no frontend a partir de `feature` e do sinal de `contribution`.

**`GET /evaluations/summary`**

```json
{ "total": 14, "opportunities": 5, "fair": 6, "expensive": 3 }
```

**`GET /evaluations?page=1&limit=10&classification=CARO`**

```json
{
  "data": [
    {
      "id": "uuid",
      "neighborhood": "Cambuí",
      "bedrooms": 2,
      "area": 65,
      "advertisedPrice": 1800,
      "estimatedPrice": 1650,
      "classification": "CARO",
      "createdAt": "2026-10-04T12:00:00.000Z"
    }
  ],
  "meta": { "page": 1, "limit": 10, "totalItems": 14 }
}
```

A tabela da home mostra "2 quartos, 65 m²" e a data, por isso a listagem inclui esses campos.

**`GET /evaluations/options`**

```json
{ "neighborhoods": ["Barão Geraldo", "Bosque", "Cambuí"], "propertyTypes": ["Apartamento", "Casa", "Kitnet"] }
```

**`GET /evaluations/:id`** devolve o mesmo objeto do `POST /evaluations`. **`PATCH /evaluations/:id/save`** devolve a avaliação com `saved: true`. **`DELETE /evaluations/:id`** responde `204`.

### 16.3 Rota que depende do modelo

A única rota que **depende do modelo de Machine Learning** é a de criar a avaliação. Enquanto o modelo não estiver pronto, **`POST /evaluations` só responde `200 OK`**. A rota deve existir e estar protegida pelo `authMiddleware`, para o frontend já poder integrar:

```ts
// routes/EvaluationRoutes.ts (provisório)
evaluationRoutes.post("/", authMiddleware, (_req, res) => {
  return res.status(200).json({ message: "ok" })
})
```

Quando o modelo estiver pronto, a rota passa a seguir o contrato da [seção 16.2](#162-contrato-previsto-quando-o-modelo-estiver-pronto): validar o corpo, obter a estimativa e os fatores, classificar, gravar como rascunho (`saved: false`) e devolver `201`.

As demais rotas de avaliação (`GET`, `PATCH`, `DELETE`, `summary` e `options`) **não dependem do modelo** e podem ser desenvolvidas desde já. Para testá-las sem o `POST` real, crie registros de exemplo pelo **Prisma Studio** (`npx prisma studio --config prisma7.config.ts`).

### 16.4 Modelos de dados a criar (Prisma)

Models previstos para as rotas pendentes, no formato do `schema.prisma`. O model `User` já existe.

```prisma
enum Classification {
  CARO
  PRECO_JUSTO
  OPORTUNIDADE
}

model Evaluation {
  id              String          @id @default(uuid())
  userId          String
  user            User            @relation(fields: [userId], references: [id], onDelete: Cascade)

  neighborhood    String
  propertyType    String
  area            Float
  bedrooms        Int
  parking         Int
  advertisedPrice Float
  condoFee        Float           @default(0)
  iptu            Float           @default(0)

  estimatedPrice  Float?
  classification  Classification?
  factors         Json?
  modelVersion    String?

  saved           Boolean         @default(false)
  createdAt       DateTime        @default(now())

  @@index([userId, saved, createdAt])
}

model PasswordResetToken {
  id         String    @id @default(uuid())
  userId     String
  user       User      @relation(fields: [userId], references: [id], onDelete: Cascade)
  tokenHash  String    @unique
  expiresAt  DateTime
  usedAt     DateTime?
  createdAt  DateTime  @default(now())
}
```

No model `User` já existente entram as relações:

```prisma
evaluations         Evaluation[]
passwordResetTokens PasswordResetToken[]
```

Explicando as escolhas:

- Os campos de resultado (`estimatedPrice`, `classification`, `factors`, `modelVersion`) são **opcionais** (`?`) porque, enquanto o modelo não está pronto, não há estimativa para gravar.
- `factors` é do tipo `Json`: guarda a lista de fatores como está, sem precisar de uma tabela própria.
- `onDelete: Cascade` apaga as avaliações e tokens de um usuário se ele for removido.
- Na recuperação de senha, o token é guardado **apenas como hash** (`tokenHash`), nunca em texto puro, pela mesma razão das senhas.

Depois de editar o schema, o fluxo é o da [seção 7](#7-prisma): `migrate dev` e `generate`.

---

## 17. Como criar um novo módulo

Um **módulo** é o conjunto de arquivos de uma funcionalidade (por exemplo, "avaliações"). Seguimos sempre o mesmo padrão dos arquivos de usuário. Na ordem:

1. **Prisma:** adicione o model no `schema.prisma`, rode `migrate dev` e `generate` (seção 7).
2. **Models** (`src/models/Evaluation.ts`): os schemas Zod e os tipos.
3. **Repository** (`src/repository/EvaluationRepository.ts`): as consultas ao banco, **sempre filtrando por `userId`**.
4. **Service** (`src/service/EvaluationService.ts`): as regras de negócio.
5. **Controller** (`src/controller/EvaluationController.ts`): valida a entrada, chama o service e escolhe o status.
6. **Routes** (`src/routes/EvaluationRoutes.ts`): declara as rotas com o `authMiddleware`.
7. **`index.ts`:** instancie `Repository` → `Service` → `Controller`, exporte o controller e monte o router (`app.use("/evaluations", evaluationRoutes)`).

### Exemplo ilustrativo: `GET /evaluations/:id`

Mostra o padrão aplicado a uma rota que busca uma avaliação do usuário logado. Os nomes seguem o schema previsto na seção 16.4.

**Repository** — busca **pelo id e pelo dono** ao mesmo tempo:

```ts
async findByIdAndUser(id: string, userId: string) {
    return prisma.evaluation.findFirst({ where: { id, userId } })
}
```

**Service** — decide o que fazer se não existir:

```ts
async getById(id: string, userId: string) {
    const evaluation = await this.evaluationRepository.findByIdAndUser(id, userId)
    if (!evaluation) throw new AppError("Avaliação não encontrada", 404)
    return evaluation
}
```

**Controller** — confere o id da URL com o Zod e pega o dono pelo token:

```ts
async getById(req: Request, res: Response) {
    const { id } = z.object({ id: z.uuid() }).parse(req.params)   // z vem de: import z from "zod"
    const evaluation = await this.evaluationService.getById(id, res.locals.userId)
    return res.status(200).json(evaluation)
}
```

**Routes** — liga tudo, exigindo login:

```ts
evaluationRoutes.get("/:id", authMiddleware, (req, res) => evaluationController.getById(req, res))
```

Se a avaliação for de outra pessoa, a busca por `id` **e** `userId` não encontra nada e a resposta é `404`: o usuário nem fica sabendo que aquele id existe.

### Regras gerais

- **Erros de negócio:** `throw new AppError("mensagem", statusCode)`.
- **Dados de entrada:** sempre validados com Zod no controller.
- **Dados sensíveis:** nunca devolva ao cliente um retorno que inclua campos como `password`.
- **Isolamento por usuário:** toda consulta de avaliação filtra por `userId`.

---

## 18. Rotina do dia a dia

**Ao começar a trabalhar:**

```bash
git pull                     # baixa o trabalho da equipe
npm install                  # só é necessário se o package.json mudou
npm run docker               # liga o banco (se estiver desligado)
npx prisma migrate dev --config prisma7.config.ts   # só se o schema/migrations mudaram
npx prisma generate --config prisma7.config.ts      # só se o schema mudou
npm run dev                  # inicia a API
```

**Enquanto trabalha:** salve os arquivos; o `npm run dev` reinicia sozinho. O comando `npm run build` confere se há erros de tipo.

**Ao terminar:** `Ctrl + C` no terminal da API e, se quiser, `docker compose stop`.

---

## 19. Solução de problemas

| Sintoma | O que significa | Solução |
|---|---|---|
| `Cannot find module '.../generated/prisma/client.js'` | O Prisma Client ainda não foi gerado. | `npx prisma generate --config prisma7.config.ts` |
| `Environment variable not found: DATABASE_URL` | O `.env` não existe ou não foi carregado. | Criar o `.env` a partir do `.env.example` e conferir o carregamento no `prisma7.config.ts`. |
| `P1001: Can't reach database server` | A API não consegue se conectar ao banco: ele está desligado, ou a `DATABASE_URL` aponta para o lugar errado. | Rodar `docker compose ps`; subir com `npm run docker`; conferir usuário, senha, porta e nome do banco na `DATABASE_URL`. |
| `port is already allocated` ao subir o Docker | Outro programa (talvez um PostgreSQL instalado no PC) já usa a porta do banco. | Parar o outro serviço, ou trocar a porta no `docker-compose.yml` e na `DATABASE_URL`. |
| `Cannot connect to the Docker daemon` | O Docker Desktop está fechado. | Abrir o Docker Desktop e esperar iniciar. |
| `ERR_MODULE_NOT_FOUND` em um import local | Faltou o `.js` no final do caminho do import. | Escrever `import ... from "./arquivo.js"`. |
| O comando `prisma` diz que não encontra a configuração | O arquivo se chama `prisma7.config.ts`, não o nome padrão. | Passar `--config prisma7.config.ts` em todos os comandos do Prisma. |
| O editor não reconhece um model ou campo novo do Prisma | O `generate` não foi executado depois da mudança (no Prisma 7 não é automático). | `npx prisma generate --config prisma7.config.ts` |
| Resposta `409 Registro ja existe` | Já há um registro com esse valor único (ex.: e-mail). | Usar outro e-mail ou apagar o registro de teste no Prisma Studio. |
| Resposta `401 Token inválido ou expirado` | O token venceu ou o `JWT_SECRET` foi alterado. | Fazer login de novo e usar o token novo. |
| Resposta `401 Token não fornecido` | A requisição foi sem o header `Authorization`. | Enviar `Authorization: Bearer <token>`. |
| Resposta `400 Dados invalidos` | Algum campo não respeitou as regras do Zod. | Ler a lista `errors` na resposta: ela diz qual campo e por quê. |
| `npm start` falha com arquivo não encontrado | Falta compilar o projeto. | `npm run build` antes de `npm start`. |
| Quero zerar o banco local | n/a | `docker compose down -v`, depois `npm run docker` e `npx prisma migrate dev --config prisma7.config.ts`. |