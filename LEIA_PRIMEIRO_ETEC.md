# Abrir a versao ETEC do Evolua+

O banco compartilhado no Railway ja recebeu 16 edicoes oficiais de 2017 a
2026: 790 questoes, com 787 utilizaveis. A estrutura dos simulados diarios
tambem ja esta aplicada nesse banco.

1. Extraia o ZIP em uma **pasta nova**, preservando seu projeto atual.
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
5. No painel, clique em **Abrir simulado diario**, ou abra
   [a pagina de simulados](http://localhost:8080/simulados.html).

Mantenha a pasta `src/main/resources/static/questoes/etec` completa: ela
contem as paginas das provas, incluindo imagens e formulas. A tela informa
qual questao responder e permite ampliar a pagina.

Use o banco da nuvem ja configurado. Os scripts de criacao, migracao e
importacao acompanham o projeto para reproducao; essa carga no Railway
ja foi concluida, sem necessidade de repeti-los.

Cada estudante recebe 40 questoes por dia, mescladas entre edicoes. Reabrir
o simulado retoma as respostas. Ha 19 dias completos de questoes ineditas;
na 20a selecao entram 27 ineditas e 13 vistas ha mais tempo.

O codigo foi compilado com sete testes aprovados. O SQL foi conferido no
MySQL real, e os fluxos da interface passaram por testes de DOM/JavaScript.
A revisao visual em navegador fica para a execucao local.

O acesso disponivel nesta sessao nao permitiu enviar as alteracoes ao
GitHub. Este pacote contem a versao local completa, que ainda precisa ser
integrada ao repositorio e publicada na API para disponibilizar a nova
interface ao grupo. O banco ja esta atualizado.

Detalhes e fontes: [ETEC e simulados](doc/ETEC_E_SIMULADOS.md).
