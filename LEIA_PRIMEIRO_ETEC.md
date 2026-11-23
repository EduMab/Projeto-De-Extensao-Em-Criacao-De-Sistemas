# Abrir a versao ETEC do Evolua+

O banco compartilhado no Railway ja recebeu 16 edicoes oficiais de 2017 a
2026: 790 questoes, com 787 utilizaveis. A estrutura dos simulados semanais
tambem ja esta aplicada nesse banco.

1. Atualize seu clone pelo GitHub/IntelliJ. Se usar o ZIP do repositorio,
   extraia em uma **pasta nova**, preservando seu projeto atual.
2. No IntelliJ, abra o `pom.xml` dessa pasta como projeto Maven e selecione
   o **JDK 25**. Aguarde o carregamento das dependencias.
3. Na configuracao de execucao de `EvoluaMaisApplication`, preencha as
   variaveis de ambiente:

   - `DB_URL`: `jdbc:mysql://thomas.proxy.rlwy.net:23871/evoluamais?sslMode=REQUIRED&connectionTimeZone=America/Sao_Paulo`
   - `DB_USUARIO`: `evolua_app`
   - `DB_SENHA`: a senha desse usuario no seu arquivo privado de acessos.

4. Execute `EvoluaMaisApplication` e abra
   [o login](http://localhost:8080/login.html). Entre novamente ou cadastre
   um estudante para criar a sessao no servidor.
5. No painel, clique em **Abrir simulado semanal**, ou abra
   [a pagina de simulados](http://localhost:8080/simulados.html).

Mantenha a pasta `src/main/resources/static/questoes/etec` completa: ela
contem as paginas das provas, incluindo imagens e formulas. A tela informa
qual questao responder e permite ampliar a pagina.

Use o banco da nuvem ja configurado. Os scripts de criacao, migracao e
importacao acompanham o projeto para reproducao; essa carga no Railway
ja foi concluida, sem necessidade de repeti-los.

Cada estudante recebe 40 questoes por semana, mescladas entre edicoes. Uma
nova selecao fica disponivel na data de abertura mais sete dias, as 00h de
Brasilia. Exemplo: abriu em 23/11, a proxima fica disponivel em 30/11.
Reabrir antes dessa data retoma a mesma selecao e as respostas, mesmo se o
simulado ja estiver concluido. O historico permite continuar ou consultar
simulados anteriores. Nao ha acumulo de selecoes durante semanas sem acesso.

Ha 19 selecoes semanais completas de questoes ineditas; na 20a entram 27
ineditas e 13 vistas ha mais tempo. Nao e necessario recriar o banco nem
importar as provas novamente: os nomes internos das tabelas foram mantidos.

A versao semanal foi compilada com 11 testes aprovados, incluindo retomada
nos seis dias seguintes, liberacao no setimo dia, concorrencia e preservacao
de tentativas antigas. Os fluxos da interface passaram por testes de
DOM/JavaScript. A revisao visual em navegador fica para a execucao local.

Os integrantes compartilham o codigo pelo repositorio GitHub. Atualize o
clone antes de executar. A API hospedada deve usar esta versao do codigo
para disponibilizar a nova interface; o banco da nuvem ja esta atualizado.

Detalhes e fontes: [ETEC e simulados](doc/ETEC_E_SIMULADOS.md).
