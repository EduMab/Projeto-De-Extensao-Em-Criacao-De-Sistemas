# Texto para colar no ChatGPT Pro do responsável pelo Render

Conclua a publicação do Evolua+ usando o Render conectado à conta que administra o serviço abaixo. O código, os PDFs, os recortes, as questões e os gabaritos já estão preparados. Execute as etapas autorizadas e confira os resultados. Se faltar conexão, credencial ou aprovação exigida pela plataforma, indique exatamente esse bloqueio; não invente acesso nem peça senhas no chat.

## Alvo exato

- Serviço Render: `srv-dc2dkljrjlhs73cd7ndg`.
- Painel: https://dashboard.render.com/web/srv-dc2dkljrjlhs73cd7ndg
- Aplicação: https://evoluamais-api.onrender.com
- Repositório: https://github.com/EduMab/Projeto-De-Extensao-Em-Criacao-De-Sistemas
- Branch: `main`.
- A versão publicada precisa conter o commit `2a138b5eb6bd0a9f6e85f62575ff4a0e2209a2c2` (ou um descendente que preserve essas mudanças).
- PRs implementados: #25 e #26. Construção Docker e testes Java/MySQL aprovados.

## Sua parte no Render

1. Descubra o workspace que realmente contém esse serviço. Não assuma que “My Workspace” de outra conta tem acesso. Use as ferramentas do Render; se indisponíveis para a operação, use o painel autorizado.
2. Confira a origem do serviço e a branch. O alvo é o repositório acima em `main`. Se estiver configurado para outro repositório ou outra branch, informe a divergência antes de alterar essa origem.
3. Se já houver um deploy da versão correta em andamento, acompanhe esse deploy. Caso contrário, publique `main` uma única vez, pelo equivalente a **Manual Deploy → Deploy latest commit**. Não crie outro serviço.
4. Mantenha o Dockerfile do repositório e as variáveis já configuradas. O serviço web continua sendo Java. Não substitua o comando de inicialização pelo script TypeScript de importação.
5. Aguarde o deploy terminar e confirme a versão/commit efetivamente publicado. Se falhar, examine os logs e relate a causa concreta; não diga que publicou apenas porque disparou o deploy.
6. Confirme, quando suas ferramentas permitirem, que `/simulados.js` contém `function recortesOriginais` e que uma imagem do novo acervo é servida. A rotina do banco fará a conferência de todas as imagens.
7. Encerre sua parte informando o commit publicado e o resultado do deploy. Não declare o banco atualizado sem os comprovantes da seção seguinte.

## Importação já preparada

A função **PreparacaoBanco**, no Railway, já contém a rotina completa com as credenciais recebidas pelas variáveis existentes. O responsável pelo Render não precisa preparar SQL, extrair PDFs nem receber senhas do banco.

- Projeto Railway: `17289eb2-f99d-4bef-a828-3baab021fc4e`.
- Ambiente: `c94f6079-c405-4327-9aeb-7a3ea8a6bf10`.
- Função: `f9b5cdac-8c1d-4779-ac45-4a2a4fde9904`.
- Cópia completa, sem placeholders: [scripts/railway_substituicao_concursos_pronta.ts](../../scripts/railway_substituicao_concursos_pronta.ts).

Se sua sessão também tiver acesso autorizado a esse projeto Railway, leia a função atual, confira se corresponde ao script pronto e reexecute somente essa função. Se só tiver acesso ao Render, conclua apenas a publicação; a continuação do banco fica com a rotina preparada no chat de Eduardo.

A rotina valida o JavaScript e todas as imagens antes de gravar. Faz simulação com rollback, substituição em uma transação e reexecução para confirmar idempotência. O acervo está fixado no commit `a7b4ede0c087abfcabc18b951884d1252a535027`, com SHA-256 `ffba2ee124765ceab6fc166b9547047a6383a75355999b90261e85df30806372`.

## Critério de conclusão do banco

Somente declare a importação concluída após encontrar os eventos **ASSETS_PUBLICADOS**, **SUBSTITUICAO_CONCURSOS_RECORTADOS** e **REEXECUCAO_CONFIRMADA**, com os resultados esperados:

- 10 provas da categoria CONCURSO.
- 364 questões cadastradas, sendo 363 ativas e uma anulada (Primavera, questão 18).
- 1.616 alternativas.
- ETEC, usuários, respostas e snapshots preservados.
- Provas antigas fora do catálogo ativo; exclusão física somente dos registros sem vínculos.
- AEDECCA/FACHUCA identifica o gabarito preliminar na correção.

Um deploy Railway com status SUCCESS, sozinho, não comprova importação. Se houver “A aplicação ainda não publicou o novo visual”, a rotina não alterou o banco e está aguardando a publicação correta no Render.
