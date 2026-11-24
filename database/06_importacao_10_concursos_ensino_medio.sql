-- ================================================================
-- Evolua+ - cadastro inicial de 10 provas de concursos de nível médio
-- Compatibilidade: MySQL 8.0 (schema do projeto)
--
-- Pré-requisito: executar database/01_estrutura.sql atualizado ou, em
-- banco antigo, confirmar que database/03_metadados_provas.sql já foi
-- aplicado. Este arquivo NÃO cria tabelas paralelas.
--
-- O projeto usa a tabela `prova` para metadados e as tabelas `questao` e
-- `alternativa` para conteúdo que já tenha sido revisado/importado.
-- Esta carga cadastra os 10 cadernos e seus links de prova/gabarito.
-- Não copia o texto integral das questões dos PDFs.
--
-- Todas as linhas entram como RASCUNHO, porque as questões ainda não foram
-- transcritas/revisadas no banco. O seletor de simulados do projeto ignora
-- provas em rascunho. Depois da importação das questões e da revisão do
-- gabarito, o responsável pode mudar status_importacao para VALIDADA.
--
-- INSERT IGNORE + uq_prova_codigo impede duplicar cadernos ao executar
-- novamente. IDs internos são gerados pelo MySQL (não são definidos aqui).
-- ================================================================

START TRANSACTION;

INSERT IGNORE INTO prova
    (nome, descricao, tipo, codigo, edicao, ano, etapa, caderno,
     orgao, cargo, banca, url_prova, url_gabarito, status_importacao)
VALUES
    (
      'INSS - Tecnico do Seguro Social (2022)',
      'Nivel medio. Prova objetiva. Caderno e gabarito para consulta externa.',
      'CONCURSO', 'INSS-2022-TECNICO-SEGURO-SOCIAL', 'INSS-2022', 2022,
      'OBJETIVA', 'CADERNO OBJETIVO',
      'Instituto Nacional do Seguro Social (INSS)', 'Tecnico do Seguro Social', 'CEBRASPE',
      'https://arquivos.qconcursos.com/prova/arquivo_prova/89730/cespe-cebraspe-2022-inss-tecnico-do-seguro-social-prova.pdf',
      'https://arquivos.qconcursos.com/prova/arquivo_gabarito/89730/cespe-cebraspe-2022-inss-tecnico-do-seguro-social-gabarito.pdf',
      'RASCUNHO'
    ),
    (
      'TJ-SP - Escrevente Tecnico Judiciario (2023)',
      'Nivel medio. Prova objetiva aplicada em 28/05/2023. Caderno e gabarito para consulta externa.',
      'CONCURSO', 'TJSP-2023-ESCREVENTE-TECNICO', 'TJSP-2023', 2023,
      'OBJETIVA', 'VERSAO 3',
      'Tribunal de Justica do Estado de Sao Paulo (TJ-SP)', 'Escrevente Tecnico Judiciario', 'VUNESP',
      'https://arquivos.qconcursos.com/prova/arquivo_prova/94462/vunesp-2023-tj-sp-escrevente-tecnico-judiciario-prova.pdf',
      'https://arquivos.qconcursos.com/prova/arquivo_gabarito/94462/vunesp-2023-tj-sp-escrevente-tecnico-judiciario-gabarito.pdf',
      'RASCUNHO'
    ),
    (
      'Policia Federal - Agente Administrativo (2014)',
      'Nivel intermediario. Prova objetiva do Plano Especial de Cargos. PDF e gabarito oficial da PF.',
      'CONCURSO', 'PF-2014-AGENTE-ADMINISTRATIVO', 'PF-2014', 2014,
      'OBJETIVA', 'CARGO 9 - AGENTE ADMINISTRATIVO',
      'Departamento de Policia Federal', 'Agente Administrativo', 'CESPE/CEBRASPE',
      'https://www.gov.br/pf/pt-br/acesso-a-informacao/servidores/concursos/provas-e-gabaritos-de-concursos-anteriores/Concurso%20Plano%20Especial%20de%20Cargos%20-%202013/Prova%20de%20Agente%20Administrativo.pdf/@@download/file',
      'https://www.gov.br/pf/pt-br/acesso-a-informacao/servidores/concursos/provas-e-gabaritos-de-concursos-anteriores/Concurso%20Plano%20Especial%20de%20Cargos%20-%202013/Gabarito%20Agente%20Administrativo.PDF/@@download/file',
      'RASCUNHO'
    ),
    (
      'Fortaleza - Guarda Municipal (2023)',
      'Nivel medio. Concurso da Prefeitura de Fortaleza. Caderno tipo A e gabarito para consulta externa.',
      'CONCURSO', 'FORTALEZA-2023-GUARDA-MUNICIPAL', 'FORTALEZA-2023', 2023,
      'OBJETIVA', 'TIPO A',
      'Prefeitura Municipal de Fortaleza (CE)', 'Guarda Municipal', 'IDECAN',
      'https://arquivos.qconcursos.com/prova/arquivo_prova/95032/idecan-2023-prefeitura-de-fortaleza-ce-guarda-municipal-prova.pdf',
      'https://arquivos.qconcursos.com/prova/arquivo_gabarito/95032/idecan-2023-prefeitura-de-fortaleza-ce-guarda-municipal-gabarito.pdf',
      'RASCUNHO'
    ),
    (
      'TJ-RN - Tecnico Judiciario - Area Judiciaria (2023)',
      'Nivel medio. Prova objetiva tipo 1 - branca. Gabarito definitivo.',
      'CONCURSO', 'TJRN-2023-TECNICO-JUDICIARIO-JUDICIARIA', 'TJRN-2023', 2023,
      'OBJETIVA', 'TIPO 1 - BRANCA',
      'Tribunal de Justica do Estado do Rio Grande do Norte (TJ-RN)', 'Tecnico Judiciario - Area Judiciaria', 'FGV',
      'https://arquivos.qconcursos.com/prova/arquivo_prova/94852/fgv-2023-tj-rn-tecnico-judiciario-area-judiciaria-prova.pdf',
      'https://arquivos.qconcursos.com/prova/arquivo_gabarito/94852/fgv-2023-tj-rn-tecnico-judiciario-area-judiciaria-gabarito.pdf',
      'RASCUNHO'
    ),
    (
      'Campinas - Agente Administrativo (2019)',
      'Nivel medio. Concurso publico - edital 09/2019. Prova objetiva e gabarito para consulta externa.',
      'CONCURSO', 'CAMPINAS-2019-AGENTE-ADMINISTRATIVO', 'CAMPINAS-2019', 2019,
      'OBJETIVA', 'CODIGO 002',
      'Prefeitura Municipal de Campinas (SP)', 'Agente Administrativo', 'VUNESP',
      'https://arquivos.qconcursos.com/prova/arquivo_prova/65678/vunesp-2019-prefeitura-de-campinas-sp-agente-administrativo-prova.pdf',
      'https://arquivos.qconcursos.com/prova/arquivo_gabarito/65678/vunesp-2019-prefeitura-de-campinas-sp-agente-administrativo-gabarito.pdf',
      'RASCUNHO'
    ),
    (
      'DPE-RS - Tecnico - Area Administrativa (2023)',
      'Nivel medio. Prova objetiva tipo 4 - azul. Gabarito definitivo.',
      'CONCURSO', 'DPE-RS-2023-TECNICO-ADMINISTRATIVA', 'DPE-RS-2023', 2023,
      'OBJETIVA', 'TIPO 4 - AZUL',
      'Defensoria Publica do Estado do Rio Grande do Sul (DPE-RS)', 'Tecnico - Area Administrativa', 'FGV',
      'https://arquivos.qconcursos.com/prova/arquivo_prova/95770/fgv-2023-dpe-rs-tecnico-area-administrativa-prova.pdf',
      'https://arquivos.qconcursos.com/prova/arquivo_gabarito/95770/fgv-2023-dpe-rs-tecnico-area-administrativa-gabarito.pdf',
      'RASCUNHO'
    ),
    (
      'UFRJ - Assistente em Administracao (2017)',
      'Nivel medio. Edital 455/2017. Caderno assistente em administracao e gabarito A.',
      'CONCURSO', 'UFRJ-2017-ASSISTENTE-ADMINISTRACAO-B206', 'UFRJ-2017', 2017,
      'OBJETIVA', 'B-206 - GABARITO A',
      'Universidade Federal do Rio de Janeiro (UFRJ)', 'Assistente em Administracao - Geral', 'PR-4 UFRJ',
      'https://arquivos.qconcursos.com/prova/arquivo_prova/56189/pr-4-ufrj-2017-ufrj-assistente-em-administracao-prova.pdf',
      'https://arquivos.qconcursos.com/prova/arquivo_gabarito/56189/pr-4-ufrj-2017-ufrj-assistente-em-administracao-gabarito.pdf',
      'RASCUNHO'
    ),
    (
      'BNB - Analista Bancario 1 (2018)',
      'Nivel medio. Caderno de prova CEBRASPE. Gabarito definitivo publicado pelo Banco do Nordeste.',
      'CONCURSO', 'BNB-2018-ANALISTA-BANCARIO-1', 'BNB-2018', 2018,
      'OBJETIVA', 'CADERNO OBJETIVO',
      'Banco do Nordeste do Brasil (BNB)', 'Analista Bancario 1', 'CESPE/CEBRASPE',
      'https://arquivos.qconcursos.com/prova/arquivo_prova/59579/cespe-2018-bnb-analista-bancario-prova.pdf',
      'https://www.bnb.gov.br/documents/45807/73822/Gabarito%2BAnalista%2BBanc%C3%A1rio%2B1%2B2018.pdf/e7b0486b-d482-3af9-f36f-6695b0d4534a?t=1642167566229&version=1.0',
      'RASCUNHO'
    ),
    (
      'Caixa - Tecnico Bancario Novo (2024)',
      'Nivel medio. Edital 01/2024/NM. Caderno objetivo e gabarito 3.',
      'CONCURSO', 'CAIXA-2024-TECNICO-BANCARIO-NOVO', 'CAIXA-2024', 2024,
      'OBJETIVA', 'PROVA 1 - GABARITO 3',
      'Caixa Economica Federal', 'Tecnico Bancario Novo', 'Fundacao Cesgranrio',
      'https://arquivos.qconcursos.com/prova/arquivo_prova/109980/cesgranrio-2024-caixa-tecnico-bancario-novo-prova.pdf',
      'https://arquivos.qconcursos.com/prova/arquivo_gabarito/109980/cesgranrio-2024-caixa-tecnico-bancario-novo-gabarito.pdf',
      'RASCUNHO'
    );

COMMIT;

-- Conferencia: devem aparecer 10 codigos diferentes apos a primeira execucao.
SELECT id_prova, nome, orgao, cargo, banca, ano, tipo, status_importacao,
       (url_prova IS NOT NULL AND url_prova <> '') AS possui_link_prova,
       (url_gabarito IS NOT NULL AND url_gabarito <> '') AS possui_link_gabarito
FROM prova
WHERE codigo IN (
    'INSS-2022-TECNICO-SEGURO-SOCIAL',
    'TJSP-2023-ESCREVENTE-TECNICO',
    'PF-2014-AGENTE-ADMINISTRATIVO',
    'FORTALEZA-2023-GUARDA-MUNICIPAL',
    'TJRN-2023-TECNICO-JUDICIARIO-JUDICIARIA',
    'CAMPINAS-2019-AGENTE-ADMINISTRATIVO',
    'DPE-RS-2023-TECNICO-ADMINISTRATIVA',
    'UFRJ-2017-ASSISTENTE-ADMINISTRACAO-B206',
    'BNB-2018-ANALISTA-BANCARIO-1',
    'CAIXA-2024-TECNICO-BANCARIO-NOVO'
)
ORDER BY ano, orgao, cargo;
