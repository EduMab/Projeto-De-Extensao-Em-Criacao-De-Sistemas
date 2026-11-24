# Importação de concursos de nível médio

O arquivo `06_importacao_10_concursos_ensino_medio.sql` inclui dez registros na tabela `prova` do schema Evolua+.

## Pré-requisitos

- MySQL 8.0.
- Banco criado com `database/01_estrutura.sql` atualizado; ou, em instalações antigas, migração `database/03_metadados_provas.sql` aplicada.
- Backup recente antes da execução.

## Execução

1. Selecione o banco `evoluamais` no MySQL Workbench.
2. Abra e execute `06_importacao_10_concursos_ensino_medio.sql`.
3. Confira o resultado do SELECT no fim do script: os dez códigos devem aparecer com URL da prova e do gabarito preenchidas.

## Importante: metadados não são questões

Esta carga cadastra apenas metadados e endereços dos cadernos/gabaritos. Não insere enunciados em `questao` nem alternativas em `alternativa`. Os registros ficam com `status_importacao='RASCUNHO'` para não serem disponibilizados nos simulados antes da revisão.

Para publicar cada prova no aplicativo, o responsável pelo conteúdo precisa:
- validar que a versão do caderno e o gabarito correspondem;
- inserir questões e alternativas no formato do contrato de importação do projeto;
- confirmar uma única alternativa correta por questão (ou marcar anuladas);
- alterar o status para `VALIDADA` somente após a revisão.

O script usa o campo `codigo` (chave única) com `INSERT IGNORE`; reexecutá-lo não duplica os registros existentes nem substitui correções já feitas.

Os endereços de PDF apontam para páginas de órgãos, bancas e catálogos externos. Confira as condições de uso de cada fonte antes de armazenar cópias locais ou redistribuir os documentos.
