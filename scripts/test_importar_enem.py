import copy,json,os,unittest
from pathlib import Path
from importar_enem import importar,validar,ROOT
from importar_concursos import ImportacaoError

@unittest.skipUnless(os.environ.get('RUN_MYSQL_TESTS')=='1','MySQL de teste não solicitado')
class ImportacaoEnemTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import pymysql
        if os.environ.get('DB_HOST') not in ('127.0.0.1','localhost') or os.environ.get('DB_NAME')!='evolua_enem_test':raise RuntimeError('Exige banco local isolado.')
        cls.conn=pymysql.connect(host=os.environ['DB_HOST'],port=int(os.environ.get('DB_PORT',3306)),user=os.environ['DB_USUARIO'],password=os.environ.get('DB_SENHA',''),database='evolua_enem_test',charset='utf8mb4',autocommit=False,cursorclass=pymysql.cursors.DictCursor)
        cls.provas,_=validar()

    def setUp(self):
        with self.conn.cursor() as c:
            c.execute('SET FOREIGN_KEY_CHECKS=0')
            c.execute('SHOW TABLES')
            for row in c.fetchall():c.execute('DROP TABLE `'+next(iter(row.values()))+'`')
            c.execute('SET FOREIGN_KEY_CHECKS=1')
            for name in ['01_estrutura.sql','02_dados_demonstracao.sql']:
                sql=(ROOT/'database'/name).read_text();sql='\n'.join(l for l in sql.splitlines() if not l.lstrip().startswith('--'))
                for statement in sql.split(';'):
                    if statement.strip():c.execute(statement)
            c.execute("INSERT INTO usuario(id_usuario,nome,email,senha) VALUES(1,'Teste ENEM','teste@exemplo.invalid','hash-ficticio')")
            c.execute("INSERT INTO estudante(id_estudante,id_usuario,id_prova,objetivo_prova) VALUES(1,1,1,'ETEC')")
            c.execute('INSERT INTO resposta(id_estudante,id_questao,id_alternativa,acertou) VALUES(1,1,2,1)')
            c.execute("INSERT INTO simulado_diario(id_simulado,id_estudante,tipo,data_simulado) VALUES(1,1,'ETEC','2026-11-20')")
            c.execute("INSERT INTO simulado_diario_questao(id_simulado,posicao,id_questao,snapshot_json) VALUES(1,1,1,%s)",(json.dumps({'enunciado':'Snapshot original','gabarito':'B'}),))
        self.conn.commit()

    def protected(self):
        rows={}
        with self.conn.cursor() as c:
            for table in ['usuario','estudante','resposta','simulado_diario','simulado_diario_questao']:
                c.execute('SELECT * FROM '+table);rows[table]=c.fetchall()
            c.execute("SELECT * FROM questao WHERE id_prova=1");rows['etec']=c.fetchall()
        return rows

    def test_simulacao_carga_repeticao_preservam_historicos(self):
        before=self.protected()
        simulated=importar(self.conn,self.provas,False)
        self.assertEqual(simulated['status'],'SIMULACAO_REVERTIDA')
        with self.conn.cursor() as c:
            c.execute("SELECT COUNT(*) n FROM prova WHERE tipo='ENEM'");self.assertEqual(c.fetchone()['n'],0)
        applied=importar(self.conn,self.provas,True)
        self.assertEqual(applied['totals'],{'provas':20,'questoes':1850,'ativas':1839})
        self.assertEqual(applied['alternativas'],9250)
        self.assertEqual(sum(p['novas'] for p in applied['audit']),1850)
        self.assertEqual(before,self.protected())
        repeated=importar(self.conn,self.provas,True)
        self.assertEqual(sum(p['novas'] for p in repeated['audit']),0)
        self.assertEqual(before,self.protected())

    def test_falha_no_ultimo_caderno_reverte_acervo_inteiro(self):
        bad=copy.deepcopy(self.provas);bad[-1]['questoes'][-1]['numero']=bad[-1]['questoes'][0]['numero']
        before=self.protected()
        with self.assertRaises(ImportacaoError):importar(self.conn,bad,True)
        with self.conn.cursor() as c:
            c.execute("SELECT COUNT(*) n FROM prova WHERE tipo='ENEM'");self.assertEqual(c.fetchone()['n'],0)
        self.assertEqual(before,self.protected())

    def test_conflito_nao_sobrescreve_questao_existente(self):
        importar(self.conn,self.provas,True)
        with self.conn.cursor() as c:
            c.execute("UPDATE questao q JOIN prova p ON p.id_prova=q.id_prova SET q.enunciado='Alteração que deve ser preservada' WHERE p.codigo=%s AND q.numero_original=1",(self.provas[0]['codigo'],))
        self.conn.commit()
        with self.assertRaises(ImportacaoError):importar(self.conn,self.provas,True)
        with self.conn.cursor() as c:
            c.execute("SELECT q.enunciado FROM questao q JOIN prova p ON p.id_prova=q.id_prova WHERE p.codigo=%s AND q.numero_original=1",(self.provas[0]['codigo'],));self.assertEqual(c.fetchone()['enunciado'],'Alteração que deve ser preservada')

if __name__=='__main__':unittest.main()
