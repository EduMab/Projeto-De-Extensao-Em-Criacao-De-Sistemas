-- Migracao aditiva: central de notificacoes semanais do Evolua+.
-- Execute uma unica vez no banco evoluamais, apos a estrutura principal.
CREATE TABLE IF NOT EXISTS notificacao (
    id_notificacao BIGINT NOT NULL AUTO_INCREMENT,
    id_estudante INT NOT NULL,
    chave VARCHAR(180) NOT NULL,
    tipo VARCHAR(30) NOT NULL,
    titulo VARCHAR(150) NOT NULL,
    mensagem VARCHAR(500) NOT NULL,
    link VARCHAR(255) NOT NULL DEFAULT '/simulados.html',
    criada_em DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    lida_em DATETIME DEFAULT NULL,
    PRIMARY KEY (id_notificacao),
    UNIQUE KEY uq_notificacao_estudante_chave (id_estudante, chave),
    KEY idx_notificacao_estudante_data (id_estudante, criada_em),
    CONSTRAINT fk_notificacao_estudante FOREIGN KEY (id_estudante)
        REFERENCES estudante(id_estudante) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
