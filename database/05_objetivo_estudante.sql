-- Banco existente: executar uma vez antes de publicar a escolha de objetivo.
-- Contas novas e antigas com NULL escolhem o objetivo no primeiro acesso ao painel.
-- Preserva a vinculação legada a id_prova, as questões e todos os simulados.
ALTER TABLE estudante ADD COLUMN objetivo_prova VARCHAR(20) DEFAULT NULL;
