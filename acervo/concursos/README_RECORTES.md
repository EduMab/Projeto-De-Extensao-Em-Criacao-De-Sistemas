# Concurso: questões recortadas

Preparado em 24/11/2026, seguindo o modelo aprovado na prévia.

- 10 provas do índice de ensino médio do PCI Concursos.
- 364 questões, 1 anulada (Primavera, questão 18) e 363 disponíveis para seleção.
- Uma questão por tela; apoio necessário exibido em recorte separado antes dela.
- Figuras, tabelas, fórmulas e alternativas preservadas como imagens do caderno.
- Imagens proporcionais, com tamanho inicial compacto e controle de ampliação.
- AEDECCA/FACHUCA: o arquivo de gabarito fornecido pelo acervo é preliminar;
  essa condição consta dos metadados e da tela de correção.

## Fontes e reprodução

`fontes-recortes.json` identifica cada caderno, banca, ano, URL e página correta
do gabarito. `fontes-recortes.zip` preserva os PDFs baixados. Coordenadas e vínculos
entre textos de apoio e questões ficam em `layout-recortes.json`.

```bash
python -m pip install -r scripts/requirements-concursos.txt
python scripts/preparar_recortes_concursos.py
python scripts/conferir_gabaritos_recortes.py
python scripts/preparar_recortes_concursos.py --build
python -m unittest discover -s scripts -p test_recortes_concursos.py -v
```

Os pacotes `recortes-*.zip` contêm as imagens e os cadernos publicados. O Maven
os extrai para os recursos estáticos durante a construção da aplicação. Isso
mantém as mesmas URLs e permite validar o pacote completo antes da publicação.

Os gabaritos em tabelas são lidos pela posição das células. As duas grades
escaneadas têm marcações verificadas por pixels e conferência manual independente.
A numeração, quantidade de opções, resposta correta e existência/proporção de todas
as imagens são verificadas antes da importação. `validacao-recortes.json` registra
contagens e hashes dos documentos.

O caderno publicado oculta o cabeçalho técnico de download por CropBox. Os recortes
são renderizados do original, sem reescrita de texto: isso preserva as fontes
matemáticas incorporadas que não têm mapeamento Unicode.

## Publicação e substituição

Primeiro publique a aplicação com os arquivos estáticos. Somente após confirmar
`recorte_original` no JavaScript público e a disponibilidade das imagens execute:

```bash
bun scripts/substituir_concursos.ts          # simulação com rollback
bun scripts/substituir_concursos.ts --aplicar
```

Credenciais são recebidas exclusivamente por variáveis de ambiente. A rotina
adquire os mesmos bloqueios das cargas anteriores e faz toda a substituição numa
única transação. Reexecutar não duplica registros. As alternativas são vinculadas
às letras da imagem; a questão anulada não entra na seleção semanal.

A lista explícita dos dez códigos antigos restringe as exclusões. Questões e
provas antigas sem vínculos são excluídas; registros usados por respostas,
simulados ou estudantes ficam somente no histórico, com a prova em RASCUNHO.
Nenhuma resposta, conta ou simulado é apagado. O acervo ETEC é conferido antes e
depois, sem alterações. Os PDFs antigos continuam acessíveis ao histórico.

O workflow testa reversão, falha no último caderno, preservação de FKs e snapshots,
remoção de conteúdo antigo sem uso e idempotência num MySQL 8 isolado.

## Estado

Arquivos preparados; publicação e importação devem ser confirmadas pelos
respectivos comprovantes. Os comprovantes antigos referem-se à carga anterior
(830 questões), não à substituição por recortes.
