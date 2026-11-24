# ENEM: coleta do acervo oficial

## Escopo definido

- Edicoes: 2017 a 2026.
- Aplicacao regular, primeiro e segundo dias.
- Caderno azul: caderno 1 no primeiro dia e caderno 7 no segundo.
- Lingua estrangeira: ingles.
- Fonte: [portal oficial de provas e gabaritos do Inep](https://www.gov.br/inep/pt-br/areas-de-atuacao/avaliacao-e-exames-educacionais/enem/provas-e-gabaritos).

## Etapa 1: localizar e baixar as fontes

O script `scripts/importar_enem.py` visita a pagina oficial de cada ano, localiza os links de prova e gabarito da aplicacao regular azul, baixa os PDFs e registra URL, tamanho e SHA-256 no manifesto. Ele falha se nao encontrar exatamente um par de arquivos por dia, em vez de escolher um link duvidoso.

Instalacao:

```bash
python -m pip install -r scripts/requirements-enem.txt
```

Gerar somente o manifesto de links:

```bash
python scripts/importar_enem.py --inicio 2017 --fim 2026 --somente-manifesto
```

Baixar os PDFs:

```bash
python scripts/importar_enem.py --inicio 2017 --fim 2026
```

Reutilizar os PDFs ja baixados:

```bash
python scripts/importar_enem.py --inicio 2017 --fim 2026 --usar-cache
```

Os PDFs ficam em `tmp/pdfs/enem/` e o manifesto em `acervo/enem/manifesto.json`. A pasta `tmp` nao deve ser versionada.

## Etapa 2: extracao e validacao (nao automatizar no escuro)

A importacao para o MySQL ainda nao deve ser executada nesta etapa. O caderno do primeiro dia contem blocos alternativos de ingles e espanhol, com gabaritos distintos para as questoes de lingua estrangeira. A extracao precisa preservar somente o bloco de ingles e associar a coluna de gabarito de ingles; as questoes comuns de Linguagens e Ciencias Humanas permanecem. Graficos, textos-base, tabelas e formulas devem continuar acessiveis como imagem da pagina original.

Antes de marcar uma prova como `VALIDADA`, conferir:
1. ano, dia, aplicacao regular, cor e numero do caderno;
2. bloco de ingles (nao espanhol) e correspondencia com a coluna inglesa do gabarito;
3. numeracao completa, sem duplicidade;
4. alternativas A-E e exatamente uma correta, exceto anuladas;
5. imagens, textos de apoio, formulas e questoes anuladas;
6. hashes e URLs oficiais registrados no manifesto.

A tabela `prova` aceita `tipo='ENEM'`; `questao` e `alternativa` ja suportam o conteudo necessario. O importador definitivo deve usar transacoes por caderno, lock de importacao, codigo unico e protecao contra divergencia de hash, seguindo o padrao de `scripts/importar_banco_etec.ts`. Nao usar alternativas ficticias nem marcar o acervo como validado automaticamente.

## Observacao sobre simulados

O motor semanal de 40 questoes documentado em `doc/ETEC_E_SIMULADOS.md` ainda seleciona ETEC. Depois de importar e revisar o ENEM, sera necessario adaptar o seletor para montar 40 questoes ENEM, equilibrando as quatro areas e impedindo duplicidade. A distribuicao por area deve ser definida e testada separadamente da coleta.
