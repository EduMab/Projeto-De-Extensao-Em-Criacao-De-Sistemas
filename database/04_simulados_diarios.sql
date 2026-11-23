-- Banco existente: executar apenas uma vez, apos 01_estrutura.sql (versao anterior).
-- Instalacao nova: 01_estrutura.sql ja inclui estas duas colunas.
ALTER TABLE questao ADD COLUMN conteudo_json JSON DEFAULT NULL;
ALTER TABLE questao ADD COLUMN hash_fonte CHAR(64) DEFAULT NULL;

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
