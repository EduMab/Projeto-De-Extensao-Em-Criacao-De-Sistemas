-- OPCIONAL: execute somente em um banco NOVO e VAZIO, depois da estrutura.
-- Nao execute se voce importou os dados do banco existente do grupo.
-- Questoes autorais de demonstracao; nao sao questoes oficiais da ETEC.
-- O MVP usa id_prova=1 e id_disciplina=1 para Matematica.
-- Nenhum usuario ou senha e criado por este arquivo: use a tela de cadastro.

START TRANSACTION;

INSERT INTO prova (id_prova, nome, descricao) VALUES
    (1, 'ETEC', 'Simulado demonstrativo do MVP Evolua+');

INSERT INTO disciplina (id_disciplina, nome) VALUES
    (1, 'Matemática');

INSERT INTO questao
    (id_questao, enunciado, dificuldade, id_disciplina, id_prova)
VALUES
    (1, 'Uma mochila custa R$ 120,00 e recebeu desconto de 25%. Qual é o preço final?', 'Fácil', 1, 1),
    (2, 'Qual é a solução da equação 3x + 6 = 21?', 'Fácil', 1, 1),
    (3, 'Um retângulo mede 8 cm de comprimento e 5 cm de largura. Qual é sua área?', 'Fácil', 1, 1);

INSERT INTO alternativa (id_alternativa, texto, correta, id_questao) VALUES
    (1, 'R$ 30,00', 0, 1),
    (2, 'R$ 90,00', 1, 1),
    (3, 'R$ 95,00', 0, 1),
    (4, 'R$ 100,00', 0, 1),
    (5, '3', 0, 2),
    (6, '4', 0, 2),
    (7, '5', 1, 2),
    (8, '9', 0, 2),
    (9, '13 cm²', 0, 3),
    (10, '26 cm²', 0, 3),
    (11, '35 cm²', 0, 3),
    (12, '40 cm²', 1, 3);

COMMIT;
