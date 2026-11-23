# Publicar o Evolua+ na nuvem

Esta configuracao prepara o MVP para uma API no Render e um banco MySQL no
Railway. O codigo continua no GitHub, compartilhado entre os integrantes.

## 1. Preparar o codigo no GitHub

Envie as alteracoes em uma branch e abra um pull request para o grupo revisar.
Apos integrar a branch, o repositorio deve conter `Dockerfile`, `render.yaml`,
`database/` e `src/main/resources/application.properties`.

O Dockerfile compila e executa a aplicacao usando Java 25. A porta vem da
variavel `PORT` da hospedagem; no IntelliJ, o padrao continua sendo 8080.
As telas HTML fazem chamadas relativas a API, portanto funcionam no mesmo
endereco publicado pelo Spring Boot sem trocar cada `fetch`.

## 2. Criar o MySQL gratuito

1. Acesse https://railway.com e crie um projeto com um servico MySQL.
2. Confira que a conta esta no Trial gratuito ou no plano Free. Nao contrate
   o plano Hobby nem adicione uma forma de pagamento para esta atividade.
3. No servico MySQL, consulte as variaveis/conexao: host publico, porta publica,
   nome do banco, usuario e senha. Para acesso pelo Render ou Workbench,
   use a conexao publica por TCP; enderecos `*.railway.internal` sao internos
   ao Railway e nao funcionam a partir do Render.
4. Guarde os valores no painel da hospedagem e nas configuracoes locais de
   cada integrante. Nao os envie ao GitHub.

O nome do banco pode ser `railway` ou outro fornecido pela plataforma; ele nao
precisa se chamar `evoluamais`. Use o mesmo nome no Workbench e em `DB_URL`.

O plano Free tem US$ 1 de credito por mes, compartilhado entre os recursos.
O Trial inicial tem uma cota unica separada. Quando a cota Free acaba, o servico
para ate o proximo ciclo. Acompanhe a cota antes da avaliacao; ter um plano Free
nao garante que um MySQL ligado o mes inteiro caiba nela. Ao terminar o Trial,
selecione explicitamente Free e reimplante, conforme as instrucoes do Railway.

## 3. Preparar as tabelas e os dados

No Workbench, crie uma conexao usando o host e a porta publicos, usuario e senha
do servico. Ative SSL conforme as instrucoes do banco. Selecione o schema
fornecido pela hospedagem como padrao antes de executar qualquer SQL.

Escolha **um** caminho:

- **Levar o banco atual do grupo:** no Workbench local, use **Server > Data
  Export**, selecione `evoluamais` e exporte estrutura e dados. Para importar em
  um schema com outro nome, exporte sem **Include Create Schema**, para nao
  fixar `CREATE DATABASE`/`USE evoluamais` no arquivo. Na conexao remota, use
  **Server > Data Import** e selecione o schema de destino. Preserve os IDs,
  pois o MVP usa prova 1 e disciplina 1 (Matematica). O arquivo `.mwb` no
  repositorio e um modelo; ele nao contem uma copia dos dados atuais.
- **Comecar com dados demonstrativos:** em um schema novo e vazio, execute
  `database/01_estrutura.sql` e depois `database/02_dados_demonstracao.sql`.
  Sao nove tabelas, uma prova, uma disciplina e tres questoes autorais.
  Os scripts nao sao executados automaticamente ao iniciar a API.

Os arquivos de demonstracao nao substituem os dados que ja existem no
computador de um integrante. Se exportar usuarios reais, mantenha o dump fora
do repositorio e compartilhe-o somente com os integrantes autorizados.

## 4. Publicar a API no Render

1. Acesse https://render.com e conecte o repositorio do grupo.
2. Crie um **Web Service**, selecione o repositorio e a branch com os ajustes.
3. Selecione o ambiente **Docker**, com o `Dockerfile` na raiz, e o plano **Free**.
4. Configure as variaveis abaixo em **Environment**. Nao cole segredos no codigo.
5. Configure o health check para `/usuarios/teste` e inicie o deploy.

Alternativamente, use **New > Blueprint** com o `render.yaml` deste repositorio.
Ele ja define o plano Free e solicita as variaveis que nao devem ser salvas no Git.

| Variavel | Valor |
| --- | --- |
| `DB_URL` | `jdbc:mysql://HOST_PUBLICO:PORTA_PUBLICA/NOME_DO_BANCO?sslMode=REQUIRED&connectTimeout=10000&socketTimeout=30000` |
| `DB_USUARIO` | Usuario fornecido pelo banco |
| `DB_SENHA` | Senha fornecida pelo banco |
| `OPENROUTER_API_KEY` | Chave da integracao do grupo, configurada somente no painel |

Substitua os campos em maiusculas da URL. A URL JDBC comeca com `jdbc:mysql://`;
nao cole diretamente uma URL `mysql://`. Cole o valor sem aspas. Se a hospedagem
fornecer um certificado CA, configure a validacao TLS conforme sua documentacao.

Sem `OPENROUTER_API_KEY`, cadastro, login e simulado podem ser testados, mas a
recomendacao da IA nao sera gerada. A porta `PORT` e fornecida pelo Render.

O Render Free suspende a API apos 15 minutos sem acesso. A primeira chamada
seguinte pode levar cerca de um minuto para responder. Ele tambem tem limites
mensais de uso. Use o plano Free sem forma de pagamento para esta atividade.

## 5. Conferir a publicacao

1. Abra `https://SEU_SERVICO.onrender.com/usuarios/teste`. A resposta esperada e
   `UsuarioController funcionando!`. Esse endpoint testa a API, nao o banco.
2. Abra `/cadastro.html` no mesmo dominio e cadastre um estudante de teste.
3. Consulte o banco remoto no Workbench para comprovar a gravacao:

   ```sql
   SELECT id_usuario, nome, email FROM usuario ORDER BY id_usuario DESC LIMIT 5;
   SELECT id_estudante, id_usuario, id_prova FROM estudante ORDER BY id_estudante DESC LIMIT 5;
   ```

4. Faca login em `/login.html`, responda ao simulado e confira o resultado.
5. Confira as gravacoes com consultas que nao exibem senhas:

   ```sql
   SELECT id_resposta, id_estudante, id_questao, acertou FROM resposta ORDER BY id_resposta DESC LIMIT 5;
   SELECT id_estudante, percentual_acerto FROM desempenho;
   SELECT id_recomendacao, id_estudante, data_recomendacao FROM recomendacao_ia ORDER BY id_recomendacao DESC LIMIT 5;
   ```

Os testes com o endereco `onrender.com` e a consulta no banco remoto sao
necessarios para confirmar o deploy; compilar o projeto localmente nao basta.

## 6. Acesso do grupo

- O dono do repositorio convida os integrantes em **Settings > Collaborators**.
  Os integrantes trabalham em branches e enviam pull requests para revisao.
- Cada integrante pode executar a API no IntelliJ, configurando `DB_URL`,
  `DB_USUARIO` e `DB_SENHA`. Sem `DB_URL`, o banco padrao e o MySQL local.
- Para acessar o banco pelo Workbench, cada integrante precisa de uma conexao
  autorizada ao servidor. O acesso ao GitHub nao concede acesso ao MySQL.
- Em uma interface separada, use o endereco HTTPS da API em vez de localhost
  e configure CORS apenas para as origens necessarias. As telas incluidas neste
  repositorio ja sao servidas junto da API e utilizam o mesmo dominio.

## Referencias oficiais

- https://render.com/docs/docker
- https://render.com/docs/free
- https://docs.railway.com/pricing/free-plan
- https://docs.railway.com/databases/mysql
- https://dev.mysql.com/doc/workbench/en/wb-admin-export-import-management.html

Planos conferidos em 23/11/2026. Confira as condicoes mostradas na sua conta
antes de criar os servicos.
