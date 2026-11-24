# Notificações semanais e avisos no dispositivo — Evolua+

## Objetivo pedagógico

As notificações fazem parte da experiência de acompanhamento do Evolua+. Elas ajudam o estudante a manter constância na preparação, lembrando-o de uma etapa semanal sem usar linguagem de cobrança. O texto reforça autonomia, continuidade e evolução individual, em alinhamento à proposta de apoio ao aprendizado e à ODS 4.

## Regras da tarefa semanal

O agendador faz uma verificação assim que a aplicação inicia e, depois, diariamente às 9h, no fuso `America/Sao_Paulo`:
- **Primeiro acesso:** se o estudante tem objetivo com simulado disponível e ainda não iniciou uma seleção, cria um aviso para começar a etapa semanal de 40 questões.
- **Lembrete:** após três dias da abertura, se o simulado ainda não foi concluído, cria um lembrete único para retomar de onde parou.
- **Nova etapa:** sete dias após a data de abertura, cria um aviso para a nova seleção semanal, independentemente de o simulado anterior ter sido concluído (regra compatível com o intervalo de liberação do módulo de simulados).

A restrição única `(id_estudante, chave)` evita duplicidades inclusive se mais de uma instância do servidor executar o agendador. Os objetivos atualmente elegíveis são ETEC e CONCURSO, de acordo com o motor semanal existente; ENEM/FUVEST só devem ser incluídos quando seus simulados estiverem efetivamente habilitados.

## Canais

1. **Central no painel:** histórico persistente com contador de não lidas, link para continuar a preparação e ações para marcar como lida.
2. **Web Push:** após consentimento explícito, o navegador registra o dispositivo. O Service Worker exibe o aviso mesmo com a aba fechada, desde que o navegador/sistema operacional permita a entrega.

O site não solicita permissão automaticamente. O estudante ativa os avisos no sininho do painel. Se negar a permissão, a central interna continua funcionando.

## Instalação do banco

No MySQL do ambiente, execute nesta ordem, uma única vez:
1. `database/05_notificacoes.sql`
2. `database/06_push_notificacoes.sql`

A segunda migração adiciona o controle de entrega e cria a tabela de assinaturas por dispositivo. Faça backup antes de executar migrações no banco compartilhado ou de produção.

## Configuração VAPID no servidor

Web Push exige chaves VAPID. Gere um par em ambiente seguro com a ferramenta `web-push`:

```bash
npx web-push generate-vapid-keys
```

Cadastre as três variáveis de ambiente no servidor (Render ou outro host):
- `VAPID_PUBLIC_KEY`: chave pública gerada.
- `VAPID_PRIVATE_KEY`: chave privada gerada; nunca commitar nem compartilhar no front-end.
- `VAPID_SUBJECT`: identificador de contato válido, por exemplo `mailto:email-real-da-equipe`.

A chave pública é entregue ao navegador por `GET /api/notificacoes/push/config`; a privada permanece somente no servidor. Não coloque nenhuma dessas chaves em arquivos versionados.

O projeto inclui um manifesto PWA (`manifest.webmanifest`) e ícone vetorial para facilitar a instalação em dispositivos compatíveis. A aplicação precisa estar publicada em HTTPS. O navegador precisa suportar Service Worker e Push API. Alguns dispositivos móveis exigem que o site seja instalado/adicionado à tela inicial para receber Web Push.

## Rotas autenticadas

- `GET /api/notificacoes` — lista até 30 avisos e contador de não lidas.
- `POST /api/notificacoes/{id}/lida` — marca um aviso como lido.
- `POST /api/notificacoes/lidas` — marca todos como lidos.
- `GET /api/notificacoes/push/config` — informa se o servidor está pronto e retorna a chave pública.
- `POST /api/notificacoes/push/assinatura` — registra o dispositivo autenticado.
- `DELETE /api/notificacoes/push/assinatura` — remove a inscrição daquele dispositivo.

As operações de escrita exigem a sessão do estudante e o cabeçalho `X-Evolua-Request: notificacoes`. O servidor valida o endpoint HTTPS contra domínios conhecidos de serviços de push para reduzir risco de SSRF. Assinaturas expiradas (HTTP 404/410) são removidas automaticamente.

## Teste manual

1. Execute as duas migrações no banco de desenvolvimento.
2. Configure as três variáveis VAPID no ambiente local/host.
3. Inicie o Spring Boot e acesse o site por HTTPS (ou `localhost`).
4. Entre com uma conta de estudante cujo objetivo tenha simulados disponíveis.
5. Abra o sininho e clique em **Ativar avisos**; aceite a permissão do navegador.
6. Verifique se o dispositivo foi inscrito e se a central interna lista os avisos.
7. Para testar as regras de datas sem esperar uma semana, use uma base de teste com datas de simulado controladas. Não altere datas de alunos reais.
8. Feche a aba e teste uma notificação Web Push com uma notificação de teste em ambiente de desenvolvimento.

## Limites e operação

- O agendador depende de a aplicação estar ligada às 9h. Se o host suspender o processo, a execução ocorrerá quando a aplicação voltar e o agendador chegar ao próximo horário programado; para operação garantida, usar um scheduler externo/worker sempre ativo.
- O push depende do serviço do navegador e das permissões do dispositivo; não há garantia de entrega imediata. A central no painel permanece como fonte persistente.
- O servidor só marca uma notificação como enviada por push após receber resposta 2xx de pelo menos uma inscrição. Falhas temporárias ficam registradas para nova tentativa.
- A implementação não lê localização, contatos ou dados pessoais além do identificador de conta e do endpoint/credenciais técnicas da inscrição push.
