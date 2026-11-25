# ENEM amarelo — integração no layout existente

Escopo confirmado por Eduardo: **10 edições completas (2017–2026), 20 cadernos
físicos, ambos os dias da aplicação regular**, cadernos 2 e 5 amarelos.
Os PDFs e gabaritos vêm do domínio oficial `download.inep.gov.br`.

## Estado

Eduardo aprovou as questões da prévia e determinou a preservação integral do
layout atual e das mesmas imagens. A integração usa `simulados.html` e
`simulados.css` existentes, sem modificá-los. A moldura da prévia é ilustrativa
e não é publicada. `aprovacao.json` fixa o conteúdo; `imagens-aprovadas.json`
fixa os 2.002 recortes aprovados por SHA-256. O rótulo de prévia no dataset é
mantido para conservar seus bytes; a autorização fica no manifesto separado.
Não executar os importadores de concurso para este acervo: o contrato ENEM
tem idioma e numeração original próprios.

- 1.850 questões distintas, incluindo as 50 versões adicionais de espanhol.
- 1.839 não anuladas considerando os dois idiomas no acervo.
- 1.789 não anuladas para cada escolha de idioma (Inglês ou Espanhol).
- 9.250 alternativas; 11 anuladas preservadas, fora do sorteio final.
- 20 cadernos físicos, sem duplicar as 85 questões comuns de cada primeiro dia.
- Simulado integrado: 40 questões por semana, retomada, correção e histórico,
  com escolha de idioma, no mesmo padrão visual dos concursos.
- Percentual de acertos para treino; não reproduz TRI nem corrige redação.

## Conteúdo e apoio

Os recortes preservam os PDFs: textos, imagens, equações, tabelas, alternativas
e referências bibliográficas. Cabeçalhos de seção, identificação do caderno,
rascunhos e páginas de redação não são tratados como apoio.

Um texto que integra a pergunta permanece junto do enunciado. Apoio separado
existe somente nas páginas explicitamente destinadas a várias questões:

- 2025, primeiro dia, página 6: texto necessário às questões 6–10.
- 2026, primeiro dia, página 20: texto necessário às questões 46–50.

As dez perguntas foram conferidas: fazem referência à autora, ao texto ou às
linhas dessas páginas. O texto não é anexado à questão anterior.

Páginas em coluna única e duas colunas são diferenciadas. As continuações
mantêm a ordem de leitura; a Q180 de 2021 inclui a coluna de continuação.
Foi conferida visualmente a marca invisível `QUESTÃO 06` atrás da charge da
Q5 de inglês de 2022: ela não deve dividir a imagem.

## Contrato e rastreabilidade

`fontes-amarelo.json` contém as URLs e hashes SHA-256 de cada prova/gabarito,
limites físicos, páginas em coluna única e vínculos de apoio.
`questoes-recortadas.json.gz` contém conteúdo e respostas, em estado de prévia.
`validacao-previa.json` registra contagens e pendências automáticas.
`recortes-AAAA-dia-D.zip` contém imagens e o PDF daquele caderno, com caminhos
relativos seguros em `questoes/enem/`.

Em cada primeiro dia, a numeração interna 1–90 corresponde a Inglês e questões
comuns; 91–95 identifica as cinco questões de Espanhol. O número impresso é
preservado em `numeroOriginal` e `conteudo.numeroOriginal` (1–5 em ambos os
idiomas). A seleção filtra `idioma` e exibe o número impresso. Uma tentativa já aberta
mantém o idioma congelado, as perguntas e as respostas, mesmo que seja
solicitado outro idioma durante os sete dias.

## Reproduzir e verificar

```sh
python scripts/preparar_enem_amarelo.py --baixar --somente-validar
python scripts/renderizar_enem_amarelo.py
python -m unittest discover -s scripts -p test_enem_amarelo.py -v
python scripts/gerar_previa_enem.py
```

Dependências fixadas em `scripts/requirements-enem.txt`; ReportLab apenas
para o PDF ilustrativo. Os geradores não leem credenciais nem conectam ao banco.

## Publicação e carga

O Docker e a CI reproduzem os recursos a partir dos PDFs oficiais com hashes
fixados. Downloads por HTTP só são aceitos quando coincidem com o SHA-256
aprovado. A conferência rejeita qualquer alteração dos recortes da prévia.

O workflow `importar-enem.yml` testa o acervo, o front-end, o Java e a carga
em MySQL 8 isolado. Em `main`, a carga usa somente as credenciais existentes
do ambiente GitHub `enem`, sem definir segredos ou ampliar permissões.
O alvo é o MySQL do projeto Railway
`17289eb2-f99d-4bef-a828-3baab021fc4e`, ambiente
`c94f6079-c405-4327-9aeb-7a3ea8a6bf10`, serviço
`030ce092-113d-4338-aa8a-2e91a604f8f5`.
A função `PreparacaoBanco` não é alterada nem reimplantada por esta rotina.

Antes de ler credenciais/conectar, `importar_enem.py --aplicar` confere o JS
publicado no Render e as 2.002 imagens. Faz simulação revertida, carga em uma
transação e reexecução com zero questões novas. Rejeita dados existentes que
divergem, sem sobrescrevê-los. Não exclui provas e não escreve em usuários,
respostas ou snapshots. Testes conferem a preservação desses registros.

A disponibilidade ENEM no perfil só é habilitada quando os 20 cadernos estiverem
validados. Falta de credenciais, aprovação do ambiente, divergência de fonte ou
publicação pendente bloqueia a carga; não é motivo para alterar as permissões.
