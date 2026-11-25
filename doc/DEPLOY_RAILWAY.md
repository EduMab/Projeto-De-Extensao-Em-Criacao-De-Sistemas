# Publicação do Evolua+ no Railway

O serviço Java serve a API e a interface no mesmo domínio. O GitHub armazena o
código; o Railway executa a aplicação. A publicação deve usar a branch `main`
com o `Dockerfile` e `railway.json` na raiz do repositório.

## Serviço e banco

No projeto Railway que já contém o MySQL compartilhado, crie um serviço a partir
de `EduMab/Projeto-De-Extensao-Em-Criacao-De-Sistemas`. Se já existir um serviço
Java para esse repositório, reutilize-o. Configure as variáveis do serviço:

| Variável | Valor |
| --- | --- |
| `DB_URL` | URL JDBC do MySQL existente: `jdbc:mysql://HOST:PORT/evoluamais?connectTimeout=10000&socketTimeout=30000` |
| `DB_USUARIO` | Usuário do MySQL existente |
| `DB_SENHA` | Senha do MySQL existente |
| `OPENROUTER_API_KEY` | Chave existente para recomendações, se habilitadas |

Use referências às variáveis do banco quando disponíveis. Não use uma URL
`mysql://` em `DB_URL`; o conector Java espera `jdbc:mysql://`. Não exponha
credenciais no repositório. Preserve o banco que contém usuários e históricos.

A aplicação utiliza a variável `PORT` definida pela hospedagem. O healthcheck
`/usuarios/teste` confirma a inicialização HTTP; ele não valida o banco nem o
acervo. Depois da publicação, gere o domínio público do serviço e abra
`https://DOMINIO/index.html`.

## Importação do ENEM sem depender do Render

No ambiente `enem` do GitHub Actions, configure a variável `EVOLUA_PUBLIC_URL`
com a origem pública Railway, por exemplo `https://DOMINIO`, sem `/index.html`.
A rotina valida o JavaScript e todas as imagens nessa origem antes de conectar
ao MySQL. A ausência dessa variável interrompe a importação; nenhuma outra
hospedagem é usada automaticamente. Os secrets de banco existentes permanecem.

Execute o workflow `Validar e publicar ENEM amarelo` na `main` depois de os
recursos estarem publicados. A importação FUVEST usa seu workflow já existente.
Não é necessário acionar nem configurar um serviço Render para publicar o
serviço Java no Railway.

## Conferência após publicar

1. `/usuarios/teste` deve responder HTTP 200.
2. `/api/simulados-semanais/acervo?tipo=FUVEST` deve responder HTTP 200 com acervo.
3. `/api/simulados-semanais/acervo?tipo=ENEM` deve responder HTTP 200 com acervo.
4. Faça login com uma conta de teste, selecione o objetivo, abra um simulado e
   confira imagens, salvamento e retomada das respostas.

Se uma categoria aceita retornar zero questões, confira a importação no mesmo
banco usado pela aplicação. Se retornar `Categoria indisponível`, confira o
commit efetivamente publicado: a `main` suporta ETEC, CONCURSO, FUVEST e ENEM.
