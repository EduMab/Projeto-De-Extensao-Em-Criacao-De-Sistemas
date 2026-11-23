# ETEC: acervo oficial e simulados diarios

## O que esta pronto

Em 23/11/2026 foram importadas no MySQL `evoluamais`, no Railway, as edicoes
regulares disponiveis de 2017 a 2026 no [acervo oficial do CPS](https://www.cps.sp.gov.br/etec/vestibulinho/).
O intervalo tem 16 edicoes, 790 questoes e 3.950 alternativas. As questoes
30 e 31 de 2017/2 e a questao 23 de 2020/1 foram anuladas: ficam armazenadas,
mas fora da selecao. Restam 787 questoes utilizaveis.

| Ano | Semestres importados | Questoes | Anuladas |
| --- | --- | ---: | ---: |
| 2017 | 1 e 2 | 100 | 2 |
| 2018 | 1 e 2 | 100 | 0 |
| 2019 | 1 e 2 | 100 | 0 |
| 2020 | 1 | 50 | 1 |
| 2021 | Nenhuma edicao no acervo consultado | 0 | 0 |
| 2022 | 2 | 50 | 0 |
| 2023 | 1 e 2 | 90 | 0 |
| 2024 | 1 e 2 | 100 | 0 |
| 2025 | 1 e 2 | 100 | 0 |
| 2026 | 1 e 2 | 100 | 0 |

Foram usados os gabaritos retificados quando indicados pelo CPS. O PDF do
gabarito de 2025/2 tambem contem outros modulos: o importador usa apenas o
Modulo 01, Vestibulinho regular. As especializacoes e vagas remanescentes
nao foram incluidas nesta carga.

## Como usar no projeto

1. Integre os arquivos desta versao ao projeto e mantenha a pasta
   `src/main/resources/static/questoes/etec` inteira: contem as imagens das
   paginas originais. Os dados do Railway ja foram importados; nao precisa
   executar SQL de criacao ou importar novamente para usar esse banco.
2. No IntelliJ, abra o `pom.xml`, selecione JDK 25 e recarregue o Maven.
3. Nas variaveis de ambiente da configuracao de execucao, configure `DB_URL`,
   `DB_USUARIO=evolua_app` e `DB_SENHA`, conforme o arquivo privado de acessos.
   O usuario `editor_etec` e para conteudo no Workbench; a aplicacao usa
   `evolua_app` para acessar o historico dos estudantes.
4. Execute `EvoluaMaisApplication`. Acesse `http://localhost:8080/login.html`,
   entre novamente na sua conta ou cadastre um estudante. O login agora cria
   uma sessao no servidor; um ID salvo no navegador nao substitui esse login.
5. Abra `http://localhost:8080/simulados.html` ou o botao de simulado no painel.
6. Para disponibilizar as mudancas para todos, envie o codigo ao GitHub e
   publique a versao atualizada da API. A existencia dos dados na nuvem nao
   atualiza automaticamente os arquivos Java/HTML de cada integrante.

Exemplo de URL JDBC, sem credenciais:

```text
jdbc:mysql://thomas.proxy.rlwy.net:23871/evoluamais?sslMode=REQUIRED&connectionTimeZone=America/Sao_Paulo
```

Nao coloque senhas ou chaves no GitHub. As configuracoes de deploy estao em
[DEPLOY_NUVEM.md](DEPLOY_NUVEM.md). A integracao disponivel nesta sessao nao
conseguiu gravar no repositorio remoto; o pacote entregue contem o codigo
local completo para aplicar e revisar no IntelliJ.

## Regras dos 40 exercicios diarios

- Uma selecao de 40 questoes por estudante e data, considerando Sao Paulo.
  Reabrir no mesmo dia retoma a mesma selecao e as respostas salvas.
- Questoes ineditas para aquele estudante tem prioridade. Dentro de cada
  faixa de prioridade, o seletor intercala edicoes e embaralha a ordem.
- O historico considera as questoes selecionadas, mesmo se o estudante nao
  terminar o simulado. Tambem considera respostas do fluxo antigo.
- Depois de esgotar as ineditas, entram primeiro as vistas ha mais tempo.
  Nunca ha duas ocorrencias do mesmo ID de questao numa selecao.
- As 787 questoes rendem 19 selecoes completas sem repetir. A 20a usa as
  27 ineditas restantes e 13 das mais antigas. O acervo e finito.
- Anuladas, provas em rascunho e questoes sem cinco alternativas e um
  gabarito unico nao entram. Se houver menos de 40 validas, a API informa
  a indisponibilidade e nao cria uma tentativa incompleta.
- A tentativa armazena uma copia do conteudo e do gabarito. Uma edicao
  posterior no banco nao muda a nota daquela tentativa.
- E preciso responder as 40 antes de concluir. O servidor confere as
  alternativas, calcula a nota e libera a correcao somente ao concluir.
- Apenas o estudante autenticado acessa e responde suas tentativas.
  Requisicoes de criacao/resposta/conclusao usam `X-Evolua-Request: simulado`.

## Formato de apresentacao e limites

O acervo preserva as paginas originais em WebP, com textos, graficos, formulas
e alternativas. A interface destaca o titulo da questao que deve ser respondida,
oferece ampliacao e um link para o PDF oficial. Textos de apoio compartilhados
foram vinculados quando a referencia numerica foi identificada; paginas anteriores
e o caderno integral continuam acessiveis para consultar outras referencias.

Podem aparecer questoes vizinhas na mesma pagina. O campo `enunciado` inclui
o texto extraido da pagina, com esse escopo identificado; os registros de
alternativa indicam A-E, cujo texto completo esta na imagem original. Esta
versao nao afirma ter separado cada alternativa ou imagem em texto estruturado.
Nao foi atribuida disciplina ou dificuldade por suposicao: o acervo usa
`Conhecimentos gerais`, e a revisao pedagogica individual fica para o grupo.

O painel calcula o desempenho dos ultimos 30 simulados diarios registrados e
concluidos. A integracao da IA com esse novo historico ainda esta pendente;
as rotas antigas de IA continuam relacionadas ao fluxo anterior do MVP.
A selecao diaria desta versao contempla ETEC. ENEM, FUVEST e concursos serao
adicionados depois da carga e da validacao de cada categoria.

## Reproduzir a coleta e a importacao

Os dados prontos estao em `acervo/etec/questoes.json`. O manifesto identifica
as fontes e os hashes SHA-256 de cada PDF; o relatorio lista as contagens.

```bash
python -m pip install -r scripts/requirements-etec.txt
python scripts/importar_etec.py --inicio 2017 --fim 2026
```

O comando consulta o CPS, baixa os PDFs, confere numeracao e gabarito e gera
os dados e imagens. Por padrao busca os arquivos na fonte novamente. Para
reutilizar os PDFs ja baixados, acrescente `--usar-cache`. Para apenas baixar,
use `--somente-download`. As imagens sao refeitas quando o hash do PDF muda.

Em outro banco vazio, um administrador executa `database/01_estrutura.sql`.
Em um banco com o schema anterior, aplica uma vez as migracoes necessarias
03 e 04. O Railway deste projeto ja esta atualizado: nao repita as migracoes.

A gravacao dos dados usa Bun e variaveis de ambiente `DB_HOST`, `DB_PORT`,
`DB_NAME=evoluamais`, `DB_USUARIO` e `DB_SENHA`. Com o schema preparado,
`editor_etec` pode executar o importador de conteudo:

```bash
bun scripts/importar_banco_etec.ts
```

Cada edicao e transacional. O importador usa o codigo do caderno e o numero
original, nao cria faixas manuais de IDs e nao sobrescreve outras categorias.
Na segunda execucao da carga completa foram criadas zero questoes novas.
Se uma fonte ou um gabarito existente divergir, o importador interrompe a
edicao e preserva os dados para revisao manual; nao substitui respostas
oficiais ou alteracoes do grupo silenciosamente.

## Validacao realizada

| Camada | Resultado |
| --- | --- |
| PDFs e gabaritos | 16 edicoes; numeracao completa; gabaritos sem conflitos; 3 anuladas |
| Importacao MySQL no Railway | 790 questoes, 3.950 alternativas; 787 ativas; segunda execucao sem duplicatas |
| Conta real da API no MySQL | Selecao de 40 entre 16 edicoes; JSON das paginas; historico; nota; restricao diaria |
| Registros temporarios da verificacao | Rollback confirmado; zero estudantes/tentativas temporarios remanescentes |
| Java/JUnit | 7 testes: prioridade, esgotamento, concorrencia, retomada, propriedade das respostas, nota e fuso horario |
| JavaScript/DOM | Navegacao, resposta salva, retomada, falha de salvamento, conclusao e correcao |
| Revisao visual da nova tela em navegador | Pendente: o navegador deste ambiente nao iniciou; conferir localmente |

A conexao TCP externa deste ambiente de execucao nao alcancou o MySQL.
Por isso o SQL foi conferido dentro do Railway com a conta `evolua_app`,
e os testes Java foram executados localmente com H2 em modo de compatibilidade
MySQL. Isso nao equivale a um teste completo da tela Java contra o MySQL remoto.
O Workbench do responsavel ja havia conectado ao mesmo endpoint com TLS.

## Conferir no Workbench

Na conexao da nuvem, abra uma aba SQL e execute:

```sql
SELECT p.edicao, COUNT(q.id_questao) AS questoes,
       SUM(q.anulada = 0) AS utilizaveis
FROM prova p
JOIN questao q ON q.id_prova = p.id_prova
WHERE p.tipo = 'ETEC'
GROUP BY p.id_prova, p.edicao
ORDER BY p.ano, p.semestre;
```

O resultado da carga inicial possui 16 linhas, 790 questoes e 787 utilizaveis.
