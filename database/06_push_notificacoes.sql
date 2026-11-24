-- Etapa complementar da central de notificacoes: fila de entrega e dispositivos Web Push.
-- Execute depois de database/05_notificacoes.sql, uma unica vez, no mesmo banco.

ALTER TABLE notificacao
    ADD COLUMN push_enviada_em DATETIME DEFAULT NULL,
    ADD COLUMN push_tentativas INT NOT NULL DEFAULT 0,
    ADD COLUMN push_ultimo_erro VARCHAR(255) DEFAULT NULL;

CREATE TABLE IF NOT EXISTS push_subscription (
    id_assinatura BIGINT NOT NULL AUTO_INCREMENT,
    id_estudante INT NOT NULL,
    endpoint TEXT NOT NULL,
    endpoint_hash CHAR(64) NOT NULL,
    p256dh VARCHAR(200) NOT NULL,
    auth VARCHAR(100) NOT NULL,
    criada_em DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    atualizada_em DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id_assinatura),
    UNIQUE KEY uq_push_endpoint_hash (endpoint_hash),
    KEY idx_push_estudante (id_estudante),
    CONSTRAINT fk_push_estudante FOREIGN KEY (id_estudante)
        REFERENCES estudante(id_estudante) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
