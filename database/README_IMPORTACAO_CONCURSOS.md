# Dez concursos completos no Evolua+

A carga inicial `06_importacao_10_concursos_ensino_medio.sql` cadastrou os metadados.
A carga complementar `scripts/importar_questoes_concursos.ts` insere os enunciados,
as alternativas e os gabaritos no mesmo conjunto de registros, sem atribuir IDs manualmente.

| Prova | Questões | Anuladas | Formato |
| --- | ---: | ---: | --- |
| INSS 2022 | 120 | 8 | Certo/errado |
| TJ-SP 2023 | 100 | 4 | A–E |
| PF 2014 | 120 | 1 | Certo/errado |
| Fortaleza 2023 | 80 | 3 | A–D |
| TJ-RN 2023 | 60 | 6 | A–E |
| Campinas 2019 | 50 | 1 | A–E |
| DPE-RS 2023 | 70 | 1 | A–E |
| UFRJ 2017 | 50 | 2 | A–E |
| BNB 2018 | 120 | 4 | Certo/errado |
| Caixa 2024 | 60 | 0 | A–E |
| **Total** | **830** | **30** | **800 válidas; 2.990 alternativas** |

## Reprodução

As fontes e seus hashes estão em `acervo/concursos/fontes.json`. Instale PyMuPDF
para a extração e execute `python scripts/baixar_concursos.py`, seguido de
`python scripts/extrair_concursos.py`. O JSON legível é regenerável; a cópia
completa versionada é `acervo/concursos/questoes.json.gz` (gzip determinístico).

Com as credenciais de `editor_concurso` exclusivamente no ambiente, execute
`bun scripts/importar_questoes_concursos.ts`. Cada prova usa uma transação e
só recebe `VALIDADA` após conferência de quantidade, conteúdo e alternativas.
Registros já existentes são comparados por hash e conteúdo; divergências
interrompem a carga, sem substituir alterações do grupo. Reexecutar não duplica.
A disciplina permanece Conhecimentos gerais; não houve classificação pedagógica
individual presumida.

A fonte da rotina já existente `PreparacaoBanco` também é preservada. A carga
complementar usa a conta restrita de conteúdo; o administrador aplica apenas
a migração de índice necessária para os simulados por categoria.

## Conferência das fontes

- O caderno da Caixa é **Prova 1, Gabarito 1**; o cadastro inicial dizia 3.
- TJ-SP: aplicado o gabarito definitivo da versão 3, com anulações 47, 53, 66 e 69.
- PF: combinadas as partes básica (1–50) e específica (51–120) do gabarito oficial.
- Campinas: aplicada a anulação da questão 47, em todas as versões, da seção 3
  da publicação de resultados após recursos de 11/10/2019, página 8.
- FGV/IDECAN/UFRJ/INSS/BNB: respeitadas as anulações indicadas nos arquivos.
- Caixa: a publicação de resposta aos recursos confirma ausência de alterações
  para Técnico Bancário Novo na aplicação de 26/05/2024.

Os PDFs locais preservam textos de apoio, fórmulas, tabelas e figuras. A cópia
oficial da PF continha justificativas; a versão exibida remove essas partes,
preservando as assertivas e os textos. O conteúdo de cada questão também é
armazenado em texto para pesquisa e acessibilidade; o caderno é a referência
visual, pois a extração linear pode perder a diagramação de fórmulas e tabelas.
O visor pode mostrar questões vizinhas e permite navegar às páginas de apoio.

## Simulados de Concurso

`CONCURSO` passa a estar disponível no painel. A seleção semanal mantém 40
questões, sete dias para nova liberação, retomada das respostas, prioridade
para inéditas e correção no servidor. ETEC mantém seu acervo e histórico.
Anuladas, rascunhos e questões com alternativas/gabaritos inválidos ficam fora.
A nota é percentual de acertos para estudo, sem penalidade específica de banca.

Em banco existente, aplicar `database/07_simulados_por_categoria.sql` uma vez;
ela troca a chave única por estudante/dia pela chave estudante/categoria/dia,
preservando os dados. Em instalação nova, `01_estrutura.sql` já contém o índice.

Validação local: 24 testes Java e quatro verificações do acervo aprovados;
sintaxe JavaScript conferida. O workflow verifica também Java 25 e MySQL 8.0.
