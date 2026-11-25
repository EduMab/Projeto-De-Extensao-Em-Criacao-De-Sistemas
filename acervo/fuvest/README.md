# Apresentação individual da FUVEST

As dez edições de 2018 a 2027 têm 890 questões no acervo. O caderno e o gabarito
continuam vinculados aos hashes conferidos em `fontes.json`.

`scripts/preparar_fuvest.py` também gera uma imagem WebP por questão. A imagem
reúne o apoio compartilhado, o enunciado, as figuras e todas as alternativas,
incluindo continuações entre colunas. Páginas largas e a faixa inferior da última
página de questões de 2021 recebem o tratamento correspondente ao layout original.

O índice `src/main/resources/fuvest-recortes.json.gz` vincula cada imagem à edição,
página, título e URL do caderno. `ApresentacaoFuvest` aplica esse índice na leitura
dos simulados atuais e do histórico. Os snapshots, respostas e gabaritos salvos
permanecem intactos. A alteração de apresentação dispensa atualização do conteúdo
das questões no banco.

O Docker gera as imagens durante o build. Para preparar e conferir localmente,
instale Poppler e `scripts/requirements-concursos.txt`, e execute

```sh
python scripts/preparar_fuvest.py --usar-cache
python -m unittest discover -s scripts -p test_recortes_fuvest.py -v
node scripts/test_simulados_recortes.cjs
mvn test
```

A conferência automática verifica títulos vizinhos, apoios, imagens, as cinco
alternativas quando o PDF tem texto Unicode e os casos de layout especiais.
As fontes sem Unicode de 2021 e as alternativas gráficas de 2018 também foram
conferidas nas imagens. Os testes Java verificam a apresentação das 890 questões
e a preservação dos snapshots e respostas ao abrir e retomar um simulado.
