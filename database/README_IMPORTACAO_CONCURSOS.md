# Importação de concursos de nível médio

O arquivo `06_importacao_10_concursos_ensino_medio.sql` inclui dez registros na tabela `prova` do schema Evolua+.

## Pré-requisitos

- MySQL 8.0.
- Banco criado com `database/01_estrutura.sql` atualizado; ou, em instalações antigas, migração `database/03_metadados_provas.sql` aplicada.
- Backup recente antes da execução.

## Execução automatizada

O programa `scripts/importar_concursos.py` usa a mesma carga SQL, mas controla
a transação: confere schema e chave única, preserva cadastros existentes,
inclui os ausentes e verifica os dez códigos antes de confirmar. Qualquer
falha reverte todos os novos cadastros. Não cria tabelas nem altera questões,
alternativas, estudantes ou provas de outras categorias.

No GitHub, configure os Secrets do ambiente `concursos` (ou do repositório):

| Secret | Conteúdo |
| --- | --- |
| `DB_HOST` | Host público do MySQL compartilhado |
| `DB_PORT` | Porta pública; padrão 3306 |
| `DB_NAME` | Nome exato do banco existente |
| `DB_USUARIO` | Conta com SELECT e INSERT em `prova` |
| `DB_SENHA` | Senha da conta, cadastrada somente em Secrets |
| `DB_SSL_CA` | Opcional: conteúdo PEM do certificado CA da hospedagem |

O MySQL deve ser o mesmo utilizado pelo grupo. Acesso ao GitHub/Railway da API
não fornece automaticamente acesso a um banco em outra conta/workspace.
Não recrie o banco que já contém as edições ETEC.

O workflow `.github/workflows/importar-concursos.yml` precisa estar na branch
padrão para aparecer em **Actions > Importar dez concursos > Run workflow**.
Primeiro ele testa a carga em um MySQL 8.0 isolado. Depois usa os Secrets para
simular no banco compartilhado. Marque `aplicar` para confirmar os cadastros.
Pull requests executam apenas testes isolados, sem acesso ao banco do grupo.
O resultado informa `novas`, `existentes` e `questoes_importadas=0`.

Para executar localmente com as mesmas variáveis no ambiente:

```bash
python -m pip install -r scripts/requirements-concursos.txt
python scripts/importar_concursos.py --validar-arquivo
python scripts/importar_concursos.py
python scripts/importar_concursos.py --aplicar
```

Sem `--aplicar`, o programa testa a inserção e faz rollback; pode consumir
números de AUTO_INCREMENT mesmo revertendo os cadastros. O padrão é TLS com
validação do certificado e hostname (`DB_SSL_MODE=VERIFY_IDENTITY`). Se a
hospedagem exige TLS com certificado autoassinado sem CA disponível, configure
a variável `DB_SSL_MODE=REQUIRED`: mantém criptografia, mas não autentica o
certificado do servidor. O modo `DISABLED` só funciona em testes em localhost.
Não registre credenciais no código, no SQL, em logs ou na conversa.

## Execução manual no Workbench

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


## Carga executada no Railway em 24/11/2026

A rotina `PreparacaoBanco` do projeto `EvoluaMais` executou a carga no banco
`evoluamais`, usando `editor_concurso` e as credenciais existentes no ambiente.
A primeira execução incluiu dez cadastros (IDs 17–26), todos em RASCUNHO com
links preenchidos. A reexecução confirmou os mesmos dez e incluiu zero novos.
Foram preservadas 16 provas ETEC, 790 questões e 3.950 alternativas.
Os comprovantes estão em `acervo/concursos/comprovante-nuvem.json`, e a fonte
completa da rotina está em `scripts/railway_preparacao_concursos.ts`.
As questões e alternativas destes concursos ainda precisam ser importadas.
