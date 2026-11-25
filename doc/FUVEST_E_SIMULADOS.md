# FUVEST no Evolua+

O catálogo reúne um caderno da 1ª fase por edição, de 2018 a 2027. O
[manifesto](../acervo/fuvest/fontes.json) registra as URLs oficiais, as versões
dos cadernos e o SHA-256 de cada PDF. As imagens mantêm as alternativas, os
gráficos, as fórmulas e os textos de apoio no formato original.

| Edições | Caderno | Questões | Disponíveis |
| --- | --- | ---: | ---: |
| 2018–2021, 2023 | V | 450 | 450 |
| 2022 | V | 90 | 89 |
| 2024 | V | 90 | 89 |
| 2025 | V1 | 90 | 90 |
| 2026 | V1 | 90 | 89 |
| 2027 | V1 | 80 | 79 |
| **Total** | **10 cadernos** | **890** | **886** |

O gabarito marca como anuladas as questões 54/2022, 3/2026 e 23/2027.
A questão 48/2024 aceita D e E no gabarito retificado. As duas alternativas
oficiais ficam registradas e o seletor semanal exclui essa questão, pois a
correção do simulado exige uma única resposta oficial por questão.

## Aplicar a carga

A versão inclui o catálogo. As imagens são geradas a partir dos PDFs oficiais
na preparação e no build Docker, com conferência dos hashes das fontes. O importador valida os dados
sem acessar o banco quando chamado sem argumentos. Para gravar, use o schema
atual da aplicação e configure `DB_HOST`, `DB_NAME`, `DB_USUARIO` e `DB_SENHA`
no ambiente. `DB_PORT` é opcional e começa em 3306. Para TLS, use a mesma
configuração do importador de concursos. `DB_SSL_CA` aceita o arquivo com a
autoridade certificadora da hospedagem quando necessário.

```sh
python -m pip install -r scripts/requirements-concursos.txt
python scripts/preparar_fuvest.py
python scripts/importar_fuvest.py
python scripts/importar_fuvest.py --simular
python scripts/importar_fuvest.py --aplicar
```

`--simular` executa as operações no MySQL e desfaz cada transação.
`--aplicar` confirma uma edição de cada vez. Ao repetir a carga, o importador
reutiliza os registros equivalentes e interrompe a edição se encontrar
divergências. O catálogo contém 890 questões e 4.450 alternativas.

Para reproduzir os dados a partir dos PDFs, instale também o utilitário
`pdftotext` do Poppler e execute `python scripts/preparar_fuvest.py`.
Use `--usar-cache` para reutilizar PDFs já baixados. Se a FUVEST substituir
um arquivo, confira a nova edição do documento antes de atualizar o hash no
manifesto.

## Usar o simulado

Após aplicar a carga e publicar esta versão do Evolua+, escolha **FUVEST** no
painel e abra o simulado semanal. O sistema sorteia 40 questões válidas de
edições diferentes, com prioridade para questões que o aluno ainda não viu.
As respostas são salvas individualmente e o gabarito aparece após a conclusão.
Uma nova seleção é liberada sete dias depois da abertura, no horário de
Brasília. Os simulados anteriores podem ser retomados pelo histórico.

A tela indica o número original na página e pode exibir questões vizinhas.
Textos de apoio identificados podem aparecer antes da questão. O caderno
oficial completo fica acessível pelo link da tela.

## Publicação automática pelo GitHub

O workflow `Publicar acervo FUVEST` testa a carga em MySQL 8 e executa os
testes Java em pull requests. Depois da integração na `main`, simula e aplica
a carga no banco compartilhado. Uma execução manual na `main` permite repetir
uma importação interrompida. As execuções são serializadas para evitar duas
publicações simultâneas.

Configure uma vez os secrets `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USUARIO`
e `DB_SENHA` no ambiente `fuvest`, em Settings → Environments do repositório.
Use `DB_SSL_CA` com o certificado PEM quando o servidor exigir uma autoridade
própria. A conexão usa TLS obrigatório, conforme a configuração Require do grupo.

O secret opcional `RENDER_DEPLOY_HOOK` permite solicitar uma publicação
após a carga bem-sucedida. Sem ele, o Render segue sua configuração atual
de publicação automática. O workflow confirma a solicitação ao Render,
e a conclusão do deploy deve ser acompanhada na hospedagem.

A configuração dos acessos requer uma conta com as permissões do repositório
e os dados do banco compartilhado. Os testes locais foram executados em banco
temporário. A carga do ambiente do grupo depende desses acessos.

O build Docker instala Python e Poppler e gera as imagens antes do Maven.
A disponibilidade dos PDFs oficiais é necessária durante o build.
