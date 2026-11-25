# Concursos no padrão ENEM — revisão aprovada

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

## Aprovação e publicação

Eduardo aprovou a prévia e autorizou a integração (“certo, manda bala pae”).
`aprovacao.json` fixa o dataset e os SHA-256 das 395 imagens aprovadas. O build
Docker usa as mesmas bibliotecas fixadas da prévia e empacota as imagens sem
alterar o arquivo original de 364 questões nem seus pacotes antigos.
As mudanças posteriores da ETEC na main são preservadas; esta revisão não
modifica HTML, CSS, JavaScript de produção ou esquema.

A nova rotina `atualizar_recortes_concursos.py` exige que os 10 cadernos PCI já
estejam validados. Confere os números, enunciados, alternativas, gabaritos e
hashes originais/revisados antes de modificar apenas `conteudo_json` e
`hash_fonte` nas mesmas linhas. Não insere nem exclui registros. Os snapshots
existentes continuam com os recortes antigos, mantidos no mesmo JAR.

O workflow `revisar-recortes-concursos.yml` usa os segredos já existentes do
ambiente GitHub `concursos`, sem ampliar permissões ou configurar credenciais.
O alvo é exclusivamente o MySQL `thomas.proxy.rlwy.net:23871/evoluamais` do
projeto Railway `17289eb2-f99d-4bef-a828-3baab021fc4e`, ambiente
`c94f6079-c405-4327-9aeb-7a3ea8a6bf10`. A função `PreparacaoBanco` não é
modificada nem reimplantada; sua referência imutável permanece intacta.

Antes de ler credenciais/conectar, a rotina baixa as 395 imagens públicas do
Render e compara os hashes com a prévia aprovada. Publicação pendente ou bytes
diferentes interrompem a carga. Não se deve contornar essa condição.

A transação usa as mesmas duas travas das cargas anteriores. Faz simulação
revertida, aplicação e reexecução com zero alterações. Compara os registros de
respostas, estudantes, simulados e snapshots, alternativas, provas e questões de
outras categorias; não consulta senhas e não escreve em usuários. Os testes em
MySQL isolado também comparam integralmente os usuários e demais registros.

Para reversão, `python scripts/atualizar_recortes_concursos.py --reverter`
confere os recursos originais publicados e restaura somente os metadados/hash
dos mesmos IDs. Também é transacional e idempotente. Não executar a reversão
sem uma solicitação específica. A automação antiga de concursos deve permanecer
pausada; não reexecutar importadores antigos após aplicar esta revisão.

## Comparação de produção

A rotina faz uma transação somente leitura antes de migrar e emite um resumo
de equivalência das 364 questões, sem dados pessoais. O hash de origem continua
obrigatoriamente igual ao original ou ao revisado aprovado. A comparação JSON
aceita apenas representações equivalentes do mesmo número (`56` e `56.0`),
sem confundir números com booleanos ou strings. Textos, URLs, campos extras,
ordem de listas e mudanças no valor de coordenadas continuam bloqueando a carga.
Os hashes dos arquivos/imagens aprovados não são recalculados nem relaxados.
O relatório identifica os caminhos JSON divergentes e bloqueia qualquer escrita
se encontrar diferença real. Testes reproduzem a serialização numérica JavaScript
e verificam que uma coordenada realmente diferente continua rejeitada.
