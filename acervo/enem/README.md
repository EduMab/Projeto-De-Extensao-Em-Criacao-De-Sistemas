# ENEM amarelo — prévia para revisão

Escopo confirmado por Eduardo: **10 edições completas (2017–2026), 20 cadernos
físicos, ambos os dias da aplicação regular**, cadernos 2 e 5 amarelos.
Os PDFs e gabaritos vêm do domínio oficial `download.inep.gov.br`.

## Estado

**PREVIA_NAO_APROVADA. Nenhuma publicação, habilitação de ENEM ou escrita no banco
foi realizada por esta preparação.** O acervo será integrado após a revisão da
prévia solicitada por Eduardo. Não executar os importadores de concurso para
este acervo: o contrato ENEM tem idioma e numeração original próprios.

- 1.850 questões distintas, incluindo as 50 versões adicionais de espanhol.
- 1.839 não anuladas considerando os dois idiomas no acervo.
- 1.789 não anuladas para cada escolha de idioma (Inglês ou Espanhol).
- 9.250 alternativas; 11 anuladas preservadas, fora do sorteio final.
- 20 cadernos físicos, sem duplicar as 85 questões comuns de cada primeiro dia.
- Simulado pretendido: 40 questões por semana, retomada, correção e histórico,
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
idiomas). A seleção final precisa filtrar `idioma` e exibir o número impresso.

## Reproduzir e verificar

```sh
python scripts/preparar_enem_amarelo.py --baixar --somente-validar
python scripts/renderizar_enem_amarelo.py
python -m unittest discover -s scripts -p test_enem_amarelo.py -v
python scripts/gerar_previa_enem.py
```

Dependências da preparação: Python 3, PyMuPDF e Pillow; ReportLab para PDF da
prévia. O gerador não lê credenciais nem conecta ao banco.

As validações automáticas não substituem a revisão editorial dos recortes.
Para aprovação, conferir a prévia visual e os casos de apoio, figuras e
continuação. Só depois preparar a publicação e a carga ENEM isolada,
transacional e idempotente, preservando todas as outras categorias e históricos.
