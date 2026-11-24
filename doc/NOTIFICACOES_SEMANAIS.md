# Notificações semanais do Evolua+

## O que o recurso faz

A central de notificações do painel avisa o estudante quando:
- a primeira tarefa semanal fica disponível;
- uma nova tarefa é liberada, sete dias após a abertura do simulado anterior;
- o simulado segue incompleto depois de três dias.

A verificação automática ocorre diariamente às 9h, no fuso de São Paulo. A chave única por estudante/ciclo impede que a mesma notificação seja criada mais de uma vez. O aluno pode abrir a tarefa pelo aviso, marcar avisos como lidos ou limpar o contador marcando todos como lidos.

## Instalação

Execute uma vez no banco MySQL do projeto:

```sql
SOURCE database/05_notificacoes.sql;
```

A aplicação deve estar executando para que o agendador diário rode. As rotas usam a sessão autenticada do aluno:
- `GET /api/notificacoes`
- `POST /api/notificacoes/{id}/lida`
- `POST /api/notificacoes/lidas`

## Limites desta versão

Esta entrega implementa notificações persistentes dentro do painel (sininho), não notificações push do sistema operacional quando o navegador está fechado. Push em segundo plano exige Service Worker, consentimento explícito do aluno, assinatura Push e chaves VAPID configuradas no servidor. A permissão nunca deve ser solicitada automaticamente.
