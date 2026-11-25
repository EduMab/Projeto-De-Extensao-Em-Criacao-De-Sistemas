# Concursos no padrão ENEM — prévia aguardando aprovação

Pedido de Eduardo: apresentar as perguntas como recortes originais, com a mesma
semântica do ENEM, preservar o layout e entregar prévia antes de publicar.

Base: `48a57f12455ab1f0a083835e521217bcb43dacbc`. O acervo original permanece
idêntico, SHA-256 `ffba2ee124765ceab6fc166b9547047a6383a75355999b90261e85df30806372`.

- Mantidas as mesmas 10 provas, 364 questões, 363 ativas e 1.616 alternativas.
- Mantidos números, enunciados, alternativas, gabaritos e Primavera Q18 anulada.
- Revisados 29 vínculos dispensáveis de apoio. Cada decisão consta em `revisao.json`.
- Oito textos exclusivos foram reunidos à pergunta na própria imagem.
- Removidos títulos de matéria e rodapés residuais das regiões de questão.
- Os recortes vêm dos mesmos PDFs; figuras, destaques e fórmulas não são reescritos.
- Apoios necessários a interpretação, referência ou contexto permanecem visíveis.

Nenhum arquivo HTML/CSS/JS de produção foi alterado. A prévia usa exatamente o
HTML e o CSS atuais, com uma faixa exclusiva de revisão e um adaptador local de
dados; não faz autenticação ou requisições de gravação. A conferência de resposta
é demonstrativa, mantém a identificação de gabaritos preliminares e o estado de
questão anulada. A prévia mostra cadernos completos para revisão; no sistema
permanece o simulado de 40 questões por semana.

## Reproduzir

```sh
python scripts/preparar_previa_concursos_enem.py
python scripts/gerar_previa_concursos_enem.py
node scripts/test_previa_concursos_enem.cjs
```

Dependências: PyMuPDF, Pillow e ReportLab. Saída: `tmp/previa-concursos-enem/`.
O HTML é autocontido e contém todas as 364 questões. O PDF resume 14 casos,
cobrindo todas as provas, apoio dispensável/necessário, texto integrado, figuras,
fórmulas, mudança de coluna e a questão anulada.

## Limite desta proposta

Não publicar, mesclar em `main`, executar importadores ou modificar a função
Railway antes da confirmação de Eduardo sobre esta nova prévia.
Depois da aprovação, preparar a integração e a migração dos metadados/imagens
preservando usuários, respostas e snapshots existentes. Esta prévia não executa
nenhuma alteração no banco e não presume que a migração posterior já está pronta.
