# Evolua+ — trabalho dos quatro integrantes

Escopo combinado: questoes objetivas com gabarito. Eduardo ficou responsavel
pela ETEC, com a meta atualizada para os ultimos dez anos: 2017 a 2026, incluindo
os semestres disponiveis. Foram importadas 16 edicoes, com 790 questoes,
3 anuladas e 787 utilizaveis. Para as outras categorias, a meta inicial continua
sendo dez edicoes. O ENEM tem dois dias por edicao.
Para concursos, orgao, cargo, banca e disponibilidade historica precisam ser
definidos antes de prometer dez edicoes do mesmo cargo.

## Divisao do grupo

| Responsavel | Categoria | Usuario de conteudo no banco |
| --- | --- | --- |
| Eduardo | ETEC | `editor_etec` |
| Integrante 2 | ENEM | `editor_enem` |
| Integrante 3 | FUVEST, primeira fase objetiva | `editor_fuvest` |
| Integrante 4 | Concurso publico a definir | `editor_concurso` |

Os quatro usuarios de conteudo consultam e alteram `prova`, `disciplina`,
`questao` e `alternativa`. Nao recebem administracao do servidor, alteracao de
tabelas ou acesso a senhas, cadastros, respostas e recomendacoes dos estudantes.
A divisao por categoria e uma responsabilidade do grupo: os acessos acima nao
isolam linhas por categoria e permitem editar o conteudo das quatro categorias.
As alteracoes na estrutura ficam com o administrador do banco.

## Padrao para preparar os dados

Use `database/exemplo_importacao_etec.json` como contrato de dados. Ele e um
exemplo autoral, nao uma prova oficial nem um programa que importa JSON.

Cada arquivo representa um caderno de uma edicao. Identifique:

- `tipo`: `ETEC`, `ENEM`, `FUVEST` ou `CONCURSO`;
- `codigo`: identificador unico do caderno, como `ENEM-2026-DIA1-AZUL-INGLES`;
- `edicao`, `ano`, `semestre` quando houver, `etapa` e `caderno`;
- `orgao`, `cargo` e `banca` para concursos;
- URL oficial da prova e URL do gabarito definitivo/retificado;
- numero original de cada questao, disciplina, enunciado e alternativas;
- letra do gabarito, anulacao e referencia da imagem quando houver figura.

Os IDs internos sao gerados pelo MySQL. Nao atribua faixas de IDs manualmente
para cada integrante. O campo `codigo` impede cadastrar o mesmo caderno duas
vezes, e o par prova/numero original impede repetir uma questao no mesmo caderno.

As edicoes ficam agrupadas pelo par `tipo` + `edicao`; cadernos de uma mesma
edicao podem ocupar mais de uma linha na tabela `prova`. Nas selecoes de
concursos, inclua o orgao/cargo na identificacao da edicao. O nome de exibicao
deve permitir distinguir ano, semestre/dia e etapa.

## Regras de revisao antes de publicar uma prova

1. Confirme que o PDF e o gabarito correspondem ao mesmo ano, etapa e caderno.
2. Escolha uma versao de cada caderno; cores diferentes nao sao edicoes novas.
3. No ENEM, inclua os dois dias e defina a opcao de lingua estrangeira. Nao
   importe ingles e espanhol como duas questoes distintas de mesmo numero no
   mesmo caderno. Uma segunda opcao de idioma exige outro codigo de caderno.
4. Confira enunciados, acentos, formulas, tabelas e imagens. Extrair texto de
   um PDF nao garante que a questao esteja completa.
5. Uma questao objetiva valida deve ter exatamente uma alternativa correta.
6. Registre questoes anuladas com `anulada=1`; elas precisam ser excluidas do
   calculo de acertos, conforme a regra de treino adotada pelo aplicativo.
7. Mantenha a prova como `RASCUNHO` ate concluir a revisao. Altere para
   `VALIDADA` somente apos conferir o conteudo e o gabarito.
8. Importe uma edicao por transacao e verifique as contagens antes de expandir
   para as dez edicoes. Nao sobrescreva o conteudo de outro integrante.

O escopo e percentual de acertos para estudo. Isso nao implementa a TRI do
ENEM, pesos oficiais ou as regras particulares de pontuacao de cada concurso.

## ETEC e simulados diarios implementados

Consulte [ETEC_E_SIMULADOS.md](ETEC_E_SIMULADOS.md) para a carga reproduzivel,
as fontes, o uso da nova interface e a validacao. Os dados da ETEC ja estao no
MySQL compartilhado. O codigo local precisa ser integrado ao GitHub e publicado
na API para que a nova interface fique disponivel para o grupo.

- Importacao por edicao, transacional e sem duplicatas; divergencias de fonte
  ou gabarito interrompem a edicao sem sobrescrever alteracoes do grupo.
- Paginas originais em imagens externas ao MySQL preservam formulas e figuras.
  A interface identifica a questao a responder; podem aparecer questoes vizinhas.
- Selecao de 40 questoes por estudante/dia, com prioridade para ineditas e
  mistura de edicoes. A selecao e retomada no mesmo dia, sem novo sorteio.
- Apos o acervo acabar, reutiliza as exibidas ha mais tempo. O historico inclui
  questoes selecionadas, mesmo quando nao respondidas, e respostas do fluxo antigo.
- Questoes anuladas, rascunhos e gabaritos invalidos ficam fora da selecao.
- O gabarito e o conteudo ficam congelados na tentativa; a nota e calculada no
  servidor. A API diaria exige sessao e exibe a correcao depois da conclusao.
- As tabelas novas `simulado_diario` e `simulado_diario_questao` guardam o historico.

Antes de oferecer todas as categorias, ainda e necessario importar seus acervos,
adaptar a selecao diaria alem da ETEC e validar um ciclo de cada categoria.
A classificacao pedagogica individual por disciplina/dificuldade e a integracao
das recomendacoes de IA ao novo historico tambem ficam para a etapa seguinte.
As rotas antigas de IA continuam relacionadas ao fluxo anterior do MVP.

Cada integrante trabalha em sua branch, por exemplo `provas/enem`,
`provas/fuvest` e `provas/concurso`. O banco compartilhado nao sincroniza
arquivos Java: o codigo e integrado pelo GitHub com pull requests.

## Estrutura nova e banco antigo

- Em um banco novo: execute `database/01_estrutura.sql` atualizado.
- Em um banco com a estrutura anterior: execute uma vez
  `database/03_metadados_provas.sql`, apos revisar a estrutura existente.
- Bancos existentes precisam tambem de `database/04_simulados_diarios.sql`, uma vez.
  A migracao ja foi aplicada no Railway; nao a execute novamente la.
- O arquivo de dados demonstrativos e opcional. Ele nao contem o acervo real
  do grupo e nao substitui uma exportacao do MySQL local.

O arquivo `.mwb` documenta as nove entidades do MVP original. Os novos
metadados constam no SQL; atualize o MER pelo Workbench depois de consolidar
a modelagem com o grupo.

## Fontes oficiais para o acervo

- ETEC: https://www.cps.sp.gov.br/etec/vestibulinho/ e
  https://vestibulinho.etec.sp.gov.br/provas-gabaritos/
- ENEM: https://www.gov.br/inep/pt-br/areas-de-atuacao/avaliacao-e-exames-educacionais/enem/provas-e-gabaritos
- FUVEST: https://www.fuvest.br/acervo/
- Concurso publico: pagina oficial do orgao e da banca do edital escolhido.

Registre as fontes por caderno. A quantidade de arquivos PDF nao e a
quantidade de edicoes, e a existencia de um acervo online nao comprova que
todos os cadernos ja foram importados e revisados.
