import copy,json,os,unittest
from pathlib import Path
from atualizar_recortes_concursos import conjuntos,migrar,ImportacaoError,ROOT,canon,comparar,diferencas_json

@unittest.skipUnless(os.getenv('RUN_MYSQL_TESTS')=='1','Exige MySQL isolado de teste')
class RevisaoTest(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  import pymysql
  if os.getenv('DB_HOST')!='127.0.0.1' or os.getenv('DB_NAME')!='evolua_revisao_test':raise RuntimeError('Somente banco de teste local.')
  cls.conn=pymysql.connect(host='127.0.0.1',port=int(os.getenv('DB_PORT','3306')),user='root',password=os.getenv('DB_SENHA',''),database='evolua_revisao_test',autocommit=False,charset='utf8mb4',cursorclass=pymysql.cursors.DictCursor)
  cls.old,cls.new=conjuntos()
 @classmethod
 def tearDownClass(cls):cls.conn.close()
 def setUp(self):
  with self.conn.cursor() as cur:
   cur.execute('SET FOREIGN_KEY_CHECKS=0');cur.execute('SHOW TABLES')
   for t in cur.fetchall():cur.execute('DROP TABLE `'+next(iter(t.values()))+'`')
   cur.execute('SET FOREIGN_KEY_CHECKS=1')
   for file in ['01_estrutura.sql','02_dados_demonstracao.sql']:
    sql='\n'.join(l for l in (ROOT/'database'/file).read_text().splitlines() if not l.lstrip().startswith('--'))
    for stmt in sql.split(';'):
     if stmt.strip():cur.execute(stmt)
   for p in self.old['provas']:
    cur.execute("INSERT INTO prova(nome,tipo,codigo,status_importacao) VALUES(%s,'CONCURSO',%s,'VALIDADA')",(p['nome'],p['codigo']));pid=cur.lastrowid
    for q in p['questoes']:
     cur.execute('INSERT INTO questao(enunciado,id_disciplina,id_prova,numero_original,anulada,conteudo_json,hash_fonte) VALUES(%s,1,%s,%s,%s,%s,%s)',(q['enunciado'],pid,q['numero'],q['anulada'],json.dumps(q['conteudo'],ensure_ascii=False),q['hashFonte']));qid=cur.lastrowid
     cur.executemany('INSERT INTO alternativa(texto,letra,correta,id_questao) VALUES(%s,%s,%s,%s)',[(a['texto'],a['letra'],a['letra']==q['gabarito'],qid) for a in q['alternativas']])
   cur.execute("INSERT INTO usuario(id_usuario,nome,email,senha) VALUES(1,'Preservar','teste@example.invalid','hash-local')")
   cur.execute('INSERT INTO estudante(id_estudante,id_usuario,id_prova) VALUES(1,1,1)')
   cur.execute("INSERT INTO simulado_diario(id_simulado,id_estudante,tipo,data_simulado) VALUES(1,1,'CONCURSO','2026-11-25')")
   cur.execute('SELECT id_questao FROM questao WHERE numero_original=1 ORDER BY id_questao LIMIT 1');qid=cur.fetchone()['id_questao']
   cur.execute('SELECT id_alternativa FROM alternativa WHERE id_questao=%s LIMIT 1',(qid,));aid=cur.fetchone()['id_alternativa']
   cur.execute('INSERT INTO resposta(id_estudante,id_questao,id_alternativa,acertou) VALUES(1,%s,%s,1)',(qid,aid))
   cur.execute('INSERT INTO simulado_diario_questao(id_simulado,posicao,id_questao,snapshot_json,id_alternativa) VALUES(1,1,%s,%s,%s)',(qid,json.dumps({'conteudo':self.old['provas'][0]['questoes'][0]['conteudo'],'original':'Não substituir o snapshot'}),aid))
  self.conn.commit()
 def estado(self):
  result={}
  with self.conn.cursor() as c:
   for table in ['usuario','estudante','resposta','simulado_diario','simulado_diario_questao','alternativa','prova','questao']:
    c.execute('SELECT * FROM '+table);result[table]=c.fetchall()
  self.conn.rollback()
  return canon(result)
 def test_simular_aplicar_repetir_reverter_preserva_todos_os_ids_e_historicos(self):
  before=self.estado();self.assertEqual(migrar(self.conn,self.old,self.new)['status'],'SIMULACAO_REVERTIDA');self.assertEqual(before,self.estado())
  result=migrar(self.conn,self.old,self.new,True);self.assertEqual(result['atualizadas'],364);self.assertTrue(result['usuariosRespostasSnapshotsPreservados'])
  applied=self.estado();self.assertEqual(migrar(self.conn,self.old,self.new,True)['atualizadas'],0);self.assertEqual(applied,self.estado())
  self.assertEqual(migrar(self.conn,self.old,self.new,True,True)['atualizadas'],364);self.assertEqual(before,self.estado())
  self.assertEqual(migrar(self.conn,self.old,self.new,True,True)['atualizadas'],0)
 def test_divergencia_na_ultima_questao_bloqueia_sem_sobrescrever(self):
  with self.conn.cursor() as c:c.execute("UPDATE questao SET hash_fonte=REPEAT('f',64) ORDER BY id_questao DESC LIMIT 1")
  self.conn.commit();before=self.estado()
  with self.assertRaises(ImportacaoError):migrar(self.conn,self.old,self.new,True)
  self.assertEqual(before,self.estado())
 def test_erro_sql_tardio_reverte_atualizacoes_anteriores(self):
  before=self.estado()
  with self.conn.cursor() as c:
   c.execute('SELECT MAX(id_questao) id FROM questao');last=c.fetchone()['id']
   c.execute(f"CREATE TRIGGER falha_revisao BEFORE UPDATE ON questao FOR EACH ROW BEGIN IF NEW.id_questao={last} THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Falha deliberada de teste'; END IF; END")
  with self.assertRaises(Exception):migrar(self.conn,self.old,self.new,True)
  self.assertEqual(before,self.estado())
 def test_json_serializado_como_javascript_e_comparado_antes_de_atualizar(self):
  def js(v):
   if isinstance(v,float) and v.is_integer():return int(v)
   if isinstance(v,list):return [js(x) for x in v]
   if isinstance(v,dict):return {k:js(x) for k,x in v.items()}
   return v
  original=self.old['provas'][0]['questoes'][0]['conteudo']
  self.assertNotEqual(canon(js(original)),canon(original))
  self.assertEqual(diferencas_json(js(original),original),[])
  with self.conn.cursor() as cur:
   cur.execute('SELECT id_questao,conteudo_json FROM questao WHERE conteudo_json IS NOT NULL')
   for row in cur.fetchall():cur.execute('UPDATE questao SET conteudo_json=%s WHERE id_questao=%s',(json.dumps(js(json.loads(row['conteudo_json'])),ensure_ascii=False),row['id_questao']))
  self.conn.commit();before=self.estado();result=comparar(self.conn,self.old,self.new)
  self.assertEqual(result['status'],'OK');self.assertEqual(result['originaisEquivalentes'],364);self.assertTrue(result['primeiraQuestao']['hashOriginalConfere']);self.assertEqual(before,self.estado())
  self.assertEqual(migrar(self.conn,self.old,self.new,True)['atualizadas'],364)
  self.assertEqual(migrar(self.conn,self.old,self.new,True)['atualizadas'],0)
 def test_coordenada_diferente_com_hash_original_continua_bloqueada(self):
  with self.conn.cursor() as cur:
   cur.execute("SELECT id_questao,conteudo_json FROM questao WHERE conteudo_json IS NOT NULL ORDER BY id_questao LIMIT 1");row=cur.fetchone();content=json.loads(row['conteudo_json']);content['recortes'][0]['caixa'][0]+=.001
   cur.execute('UPDATE questao SET conteudo_json=%s WHERE id_questao=%s',(json.dumps(content),row['id_questao']))
  self.conn.commit();before=self.estado();report=comparar(self.conn,self.old,self.new)
  self.assertEqual(report['status'],'DIVERGENTE');self.assertIn('$.recortes[0].caixa[0]',report['divergenciasReais'][0]['camposDivergentesOriginal'])
  with self.assertRaises(ImportacaoError):migrar(self.conn,self.old,self.new,True)
  self.assertEqual(before,self.estado())

class JsonEquivalenteTest(unittest.TestCase):
 def test_ignora_so_representacao_numerica(self):
  self.assertEqual(diferencas_json({'a':[56.0,1e1]}, {'a':[56,10]}),[])
  for a,b in [(False,0),(True,1),(56,'56'),([1,2],[2,1]),({'a':1},{'a':1,'b':2}),(56,56.001),('texto','texto '),(None,False)]:self.assertTrue(diferencas_json(a,b),(a,b))

if __name__=='__main__':unittest.main()
