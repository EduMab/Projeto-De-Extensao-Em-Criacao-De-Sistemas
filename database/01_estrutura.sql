-- Estrutura do MVP, baseada em doc/EvoluaMais_MER.mwb.
-- Selecione o banco de destino no Workbench antes de executar.
-- Na nuvem, use o nome do banco fornecido pela hospedagem.
-- Este arquivo cria tabelas ausentes; nao substitui uma migracao nem importa
-- os dados que existem no computador de um integrante.

CREATE TABLE IF NOT EXISTS usuario (
    id_usuario INT NOT NULL AUTO_INCREMENT,
    nome VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL,
    senha VARCHAR(255) NOT NULL,
    PRIMARY KEY (id_usuario)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS prova (
    id_prova INT NOT NULL AUTO_INCREMENT,
    nome VARCHAR(100) NOT NULL,
    descricao VARCHAR(255) DEFAULT NULL,
    tipo VARCHAR(20) NOT NULL DEFAULT 'ETEC',
    codigo VARCHAR(160) DEFAULT NULL,
    edicao VARCHAR(80) DEFAULT NULL,
    ano SMALLINT DEFAULT NULL,
    semestre TINYINT DEFAULT NULL,
    etapa VARCHAR(50) DEFAULT NULL,
    caderno VARCHAR(80) DEFAULT NULL,
    orgao VARCHAR(150) DEFAULT NULL,
    cargo VARCHAR(150) DEFAULT NULL,
    banca VARCHAR(100) DEFAULT NULL,
    url_prova VARCHAR(1500) DEFAULT NULL,
    url_gabarito VARCHAR(1500) DEFAULT NULL,
    status_importacao VARCHAR(20) NOT NULL DEFAULT 'RASCUNHO',
    PRIMARY KEY (id_prova),
    UNIQUE KEY uq_prova_codigo (codigo),
    KEY idx_prova_tipo_edicao (tipo, edicao),
    CONSTRAINT chk_prova_tipo CHECK (tipo IN ('ETEC', 'ENEM', 'FUVEST', 'CONCURSO')),
    CONSTRAINT chk_prova_status CHECK (status_importacao IN ('RASCUNHO', 'VALIDADA')),
    CONSTRAINT chk_prova_semestre CHECK (semestre IS NULL OR semestre IN (1, 2))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS disciplina (
    id_disciplina INT NOT NULL AUTO_INCREMENT,
    nome VARCHAR(100) NOT NULL,
    PRIMARY KEY (id_disciplina)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS estudante (
    id_estudante INT NOT NULL AUTO_INCREMENT,
    id_usuario INT NOT NULL,
    id_prova INT NOT NULL,
    objetivo_prova VARCHAR(20) DEFAULT NULL,
    PRIMARY KEY (id_estudante),
    KEY id_usuario (id_usuario),
    KEY id_prova (id_prova),
    CONSTRAINT estudante_ibfk_1 FOREIGN KEY (id_usuario)
        REFERENCES usuario (id_usuario),
    CONSTRAINT estudante_ibfk_2 FOREIGN KEY (id_prova)
        REFERENCES prova (id_prova)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS questao (
    id_questao INT NOT NULL AUTO_INCREMENT,
    enunciado TEXT NOT NULL,
    dificuldade VARCHAR(30) DEFAULT NULL,
    id_disciplina INT NOT NULL,
    id_prova INT NOT NULL,
    numero_original INT DEFAULT NULL,
    imagem_url VARCHAR(1500) DEFAULT NULL,
    anulada TINYINT(1) NOT NULL DEFAULT 0,
    conteudo_json JSON DEFAULT NULL,
    hash_fonte CHAR(64) DEFAULT NULL,
    PRIMARY KEY (id_questao),
    UNIQUE KEY uq_questao_numero (id_prova, numero_original),
    KEY id_disciplina (id_disciplina),
    KEY id_prova (id_prova),
    CONSTRAINT questao_ibfk_1 FOREIGN KEY (id_disciplina)
        REFERENCES disciplina (id_disciplina),
    CONSTRAINT questao_ibfk_2 FOREIGN KEY (id_prova)
        REFERENCES prova (id_prova)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS alternativa (
    id_alternativa INT NOT NULL AUTO_INCREMENT,
    texto TEXT NOT NULL,
    correta TINYINT(1) NOT NULL,
    id_questao INT NOT NULL,
    letra CHAR(1) DEFAULT NULL,
    PRIMARY KEY (id_alternativa),
    UNIQUE KEY uq_alternativa_letra (id_questao, letra),
    KEY id_questao (id_questao),
    CONSTRAINT alternativa_ibfk_1 FOREIGN KEY (id_questao)
        REFERENCES questao (id_questao)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS resposta (
    id_resposta INT NOT NULL AUTO_INCREMENT,
    id_estudante INT NOT NULL,
    id_questao INT NOT NULL,
    id_alternativa INT NOT NULL,
    acertou TINYINT(1) NOT NULL,
    data_resposta DATETIME DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id_resposta),
    KEY id_estudante (id_estudante),
    KEY id_questao (id_questao),
    KEY id_alternativa (id_alternativa),
    CONSTRAINT resposta_ibfk_1 FOREIGN KEY (id_estudante)
        REFERENCES estudante (id_estudante),
    CONSTRAINT resposta_ibfk_2 FOREIGN KEY (id_questao)
        REFERENCES questao (id_questao),
    CONSTRAINT resposta_ibfk_3 FOREIGN KEY (id_alternativa)
        REFERENCES alternativa (id_alternativa)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS desempenho (
    id_desempenho INT NOT NULL AUTO_INCREMENT,
    id_estudante INT NOT NULL,
    id_disciplina INT NOT NULL,
    percentual_acerto DECIMAL(5,2) NOT NULL,
    PRIMARY KEY (id_desempenho),
    KEY id_estudante (id_estudante),
    KEY id_disciplina (id_disciplina),
    CONSTRAINT desempenho_ibfk_1 FOREIGN KEY (id_estudante)
        REFERENCES estudante (id_estudante),
    CONSTRAINT desempenho_ibfk_2 FOREIGN KEY (id_disciplina)
        REFERENCES disciplina (id_disciplina)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS recomendacao_ia (
    id_recomendacao INT NOT NULL AUTO_INCREMENT,
    id_estudante INT NOT NULL,
    analise TEXT NOT NULL,
    data_recomendacao DATETIME DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id_recomendacao),
    KEY id_estudante (id_estudante),
    CONSTRAINT recomendacao_ia_ibfk_1 FOREIGN KEY (id_estudante)
        REFERENCES estudante (id_estudante)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS simulado_diario (
    id_simulado BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    id_estudante INT NOT NULL,
    tipo VARCHAR(20) NOT NULL,
    data_simulado DATE NOT NULL,
    criado_em DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    concluido_em DATETIME DEFAULT NULL,
    UNIQUE KEY uq_simulado_estudante_dia (id_estudante, data_simulado),
    CONSTRAINT fk_simulado_estudante FOREIGN KEY (id_estudante) REFERENCES estudante(id_estudante)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS simulado_diario_questao (
    id_simulado BIGINT NOT NULL,
    posicao TINYINT NOT NULL,
    id_questao INT NOT NULL,
    snapshot_json JSON NOT NULL,
    id_alternativa INT DEFAULT NULL,
    acertou TINYINT(1) DEFAULT NULL,
    respondida_em DATETIME DEFAULT NULL,
    PRIMARY KEY (id_simulado, posicao),
    UNIQUE KEY uq_simulado_questao (id_simulado, id_questao),
    KEY idx_historico_questao (id_questao, id_simulado),
    CONSTRAINT fk_diario_simulado FOREIGN KEY (id_simulado) REFERENCES simulado_diario(id_simulado),
    CONSTRAINT fk_diario_questao FOREIGN KEY (id_questao) REFERENCES questao(id_questao),
    CONSTRAINT chk_diario_posicao CHECK (posicao BETWEEN 1 AND 40)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
