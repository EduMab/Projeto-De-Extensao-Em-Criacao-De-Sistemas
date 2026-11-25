"""Regressões da carga FUVEST no banco de teste configurado pelo CI."""
import copy
import os
from pathlib import Path
import re
import unittest

from importar_fuvest import importar, validar_acervo, ImportacaoError, configuracao_fuvest



class ConfiguracaoFuvestTest(unittest.TestCase):
    def test_remove_quebras_de_linha_dos_campos_de_conexao(self):
        for sufixo in ("\n", "\r\n", r"\n", r"\r\n", "  "):
            with self.subTest(sufixo=sufixo):
                env = {
                    "DB_HOST": "localhost" + sufixo,
                    "DB_PORT": "3306" + sufixo,
                    "DB_NAME": "fuvest_test" + sufixo,
                    "DB_USUARIO": "editor_test" + sufixo,
                    "DB_SENHA": "senha com espaços  " + sufixo,
                    "DB_SSL_MODE": "DISABLED",
                }
                config = configuracao_fuvest(env)
                self.assertEqual("localhost", config["host"])
                self.assertEqual(3306, config["port"])
                self.assertEqual("fuvest_test", config["database"])
                self.assertEqual("editor_test", config["user"])
                self.assertEqual(env["DB_SENHA"], config["password"])
                self.assertEqual("localhost" + sufixo, env["DB_HOST"])


@unittest.skipUnless(os.environ.get("RUN_MYSQL_TESTS") == "1", "Banco de teste não habilitado")
class ImportarFuvestTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import pymysql
        from importar_concursos import configuracao
        # Protege a execução acidental sobre o banco compartilhado.
        if not os.environ.get("DB_NAME", "").endswith("_test"):
            raise RuntimeError("Use um banco dedicado com nome terminado em _test.")
        cls.conn = pymysql.connect(**configuracao(os.environ),
                                   cursorclass=pymysql.cursors.DictCursor)
        source = (Path(__file__).resolve().parents[1] / "database/01_estrutura.sql").read_text()
        source = re.sub(r"(?m)^--[^\n]*", "", source)
        with cls.conn.cursor() as cur:
            for statement in source.split(";"):
                if statement.strip():
                    cur.execute(statement)
            cur.execute("SELECT COUNT(*) AS total FROM prova")
            if cur.fetchone()["total"]:
                raise RuntimeError("O teste exige um banco vazio.")
        cls.conn.commit()
        cls.edicoes = validar_acervo()

    @classmethod
    def tearDownClass(cls):
        cls.conn.close()

    def test_carga_reexecucao_e_conflito(self):
        importar(self.conn, self.edicoes, aplicar=False)
        with self.conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) AS total FROM prova")
            self.assertEqual(0, cur.fetchone()["total"])
        importar(self.conn, self.edicoes, aplicar=True)
        importar(self.conn, self.edicoes, aplicar=True)
        with self.conn.cursor() as cur:
            for tabela, esperado in (("prova", 10), ("questao", 890), ("alternativa", 4450)):
                cur.execute(f"SELECT COUNT(*) AS total FROM {tabela}")
                self.assertEqual(esperado, cur.fetchone()["total"])
            cur.execute("""SELECT COUNT(*) AS total FROM questao q
                WHERE q.anulada=0 AND
                (SELECT COUNT(*) FROM alternativa a WHERE a.id_questao=q.id_questao AND a.correta=1)=1""")
            self.assertEqual(886, cur.fetchone()["total"])
        divergente = copy.deepcopy(self.edicoes[:1])
        divergente[0]["questoes"][0]["hashFonte"] = "0" * 64
        with self.assertRaises(ImportacaoError):
            importar(self.conn, divergente, aplicar=True)
        with self.conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) AS total FROM questao WHERE hash_fonte=%s", ("0" * 64,))
            self.assertEqual(0, cur.fetchone()["total"])
