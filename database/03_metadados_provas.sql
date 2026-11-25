-- Migracao ADITIVA para bancos que usavam a primeira versao de 01_estrutura.sql.
-- Execute UMA VEZ. Em banco novo criado com o 01 atualizado, NAO execute este arquivo.
-- Nao apaga nem substitui usuarios, questoes, respostas ou provas existentes.

ALTER TABLE prova
    ADD COLUMN tipo VARCHAR(20) NOT NULL DEFAULT 'ETEC',
    ADD COLUMN codigo VARCHAR(160) DEFAULT NULL,
    ADD COLUMN edicao VARCHAR(80) DEFAULT NULL,
    ADD COLUMN ano SMALLINT DEFAULT NULL,
    ADD COLUMN semestre TINYINT DEFAULT NULL,
    ADD COLUMN etapa VARCHAR(50) DEFAULT NULL,
    ADD COLUMN caderno VARCHAR(80) DEFAULT NULL,
    ADD COLUMN orgao VARCHAR(150) DEFAULT NULL,
    ADD COLUMN cargo VARCHAR(150) DEFAULT NULL,
    ADD COLUMN banca VARCHAR(100) DEFAULT NULL,
    ADD COLUMN url_prova VARCHAR(1500) DEFAULT NULL,
    ADD COLUMN url_gabarito VARCHAR(1500) DEFAULT NULL,
    ADD COLUMN status_importacao VARCHAR(20) NOT NULL DEFAULT 'RASCUNHO',
    ADD UNIQUE KEY uq_prova_codigo (codigo),
    ADD KEY idx_prova_tipo_edicao (tipo, edicao),
    ADD CONSTRAINT chk_prova_tipo CHECK (tipo IN ('ETEC', 'ENEM', 'FUVEST', 'CONCURSO')),
    ADD CONSTRAINT chk_prova_status CHECK (status_importacao IN ('RASCUNHO', 'VALIDADA')),
    ADD CONSTRAINT chk_prova_semestre CHECK (semestre IS NULL OR semestre IN (1, 2));

ALTER TABLE questao
    ADD COLUMN numero_original INT DEFAULT NULL,
    ADD COLUMN imagem_url VARCHAR(1500) DEFAULT NULL,
    ADD COLUMN anulada TINYINT(1) NOT NULL DEFAULT 0,
    ADD UNIQUE KEY uq_questao_numero (id_prova, numero_original);

ALTER TABLE alternativa
    ADD COLUMN letra CHAR(1) DEFAULT NULL,
    ADD UNIQUE KEY uq_alternativa_letra (id_questao, letra);
