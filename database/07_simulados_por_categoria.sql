-- Aplicar uma vez em bancos com uq_simulado_estudante_dia.
-- Preserva todas as tentativas, permitindo ETEC e CONCURSO no mesmo dia.
ALTER TABLE simulado_diario
 DROP INDEX uq_simulado_estudante_dia,
 ADD UNIQUE KEY uq_simulado_estudante_tipo_dia (id_estudante,tipo,data_simulado);
