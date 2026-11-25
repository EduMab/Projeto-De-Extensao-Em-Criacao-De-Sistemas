"""Atualiza só conteudo_json/hash_fonte dos mesmos IDs; reversível e idempotente."""
import argparse,concurrent.futures,gzip,hashlib,json,os,re,urllib.request,zipfile
from pathlib import Path
from importar_concursos import ImportacaoError,configuracao,validar_schema
from empacotar_revisao_concursos import validar
ROOT=Path(__file__).resolve().parents[1]
ORIGINAL=ROOT/'acervo/concursos/questoes-recortadas.json.gz'
SOURCE_SHA='ffba2ee124765ceab6fc166b9547047a6383a75355999b90261e85df30806372'
LOCKS=['evolua_concursos_importacao','evolua_concursos_questoes']
def canon(v):return json.dumps(v,ensure_ascii=False,sort_keys=True,separators=(',',':'),default=str)
def conjuntos():
 if hashlib.sha256(ORIGINAL.read_bytes()).hexdigest()!=SOURCE_SHA:raise ImportacaoError('Acervo original divergente.')
 old=json.loads(gzip.decompress(ORIGINAL.read_bytes()));new,_=validar()
 for p,n in zip(old['provas'],new['provas'],strict=True):
  if p['codigo']!=n['codigo']:raise ImportacaoError('Provas divergentes.')
  for a,b in zip(p['questoes'],n['questoes'],strict=True):
   for k in ['numero','enunciado','alternativas','anulada','gabarito']:
    if a[k]!=b[k]:raise ImportacaoError('Conteúdo pedagógico divergente.')
 return old,new

def publicados(data,reverter=False):
 approval=json.loads((ROOT/'acervo/concursos-previa-enem/aprovacao.json').read_text())
 expected=approval['imagens']
 if reverter:
  expected={}
  for p in data['provas']:
   with zipfile.ZipFile(ROOT/'acervo/concursos'/('recortes-'+p['slug']+'.zip')) as archive:
    for q in p['questoes']:
     for r in q['conteudo']['recortes']:expected[r['imagem']]=hashlib.sha256(archive.read(r['imagem'].lstrip('/'))).hexdigest()
 def conferir(item):
  path,expected=item
  with urllib.request.urlopen('https://evoluamais-api.onrender.com'+path,timeout=45) as r:
   if r.status!=200 or 'image/webp' not in r.headers.get('content-type','') or hashlib.sha256(r.read()).hexdigest()!=expected:raise ImportacaoError('Imagem pública ausente/divergente: '+path)
 try:
  items=list(expected.items());conferir(items[0])
  with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:list(pool.map(conferir,items[1:]))
 except Exception as e:raise ImportacaoError('Publicação no Render pendente ou imagem pública divergente; banco não foi conectado.') from e
 print(json.dumps({'status':'OK','operacao':'ASSETS_CONCURSOS_REVISADOS_PUBLICADOS','imagens':len(expected)}),flush=True)

def preservacao(cur,ids):
 # Não lê senhas. Somente fingerprints são comparados internamente, sem dados pessoais em logs.
 result={}
 for table,cols,order in [('estudante','*','id_estudante'),('resposta','*','id_resposta'),('simulado_diario','*','id_simulado'),('simulado_diario_questao','*','id_simulado,posicao'),('prova','*','id_prova'),('alternativa','*','id_alternativa')]:
  cur.execute(f'SELECT {cols} FROM {table} ORDER BY {order}');result[table]=hashlib.sha256(canon(cur.fetchall()).encode()).hexdigest()
 cur.execute('SELECT * FROM questao WHERE id_questao NOT IN ('+','.join(['%s']*len(ids))+') ORDER BY id_questao',ids)
 result['outrasQuestoes']=hashlib.sha256(canon(cur.fetchall()).encode()).hexdigest()
 return result

def migrar(conn,old,new,aplicar=False,reverter=False):
 acquired=[]
 try:
  with conn.cursor() as cur:
   for lock in LOCKS:
    cur.execute('SELECT GET_LOCK(%s,15) adquirido',(lock,))
    if cur.fetchone()['adquirido']!=1:raise ImportacaoError('Outra carga de concursos em execução.')
    acquired.append(lock)
   validar_schema(cur);conn.begin()
   try:
    pending=[];ids=[];core=[]
    for p,n in zip(old['provas'],new['provas'],strict=True):
     cur.execute('SELECT id_prova,tipo,status_importacao FROM prova WHERE codigo=%s FOR UPDATE',(p['codigo'],));proof=cur.fetchone()
     if not proof or proof['tipo']!='CONCURSO' or proof['status_importacao']!='VALIDADA':raise ImportacaoError('Catálogo PCI original ausente/não validado: '+p['codigo'])
     cur.execute('SELECT * FROM questao WHERE id_prova=%s ORDER BY numero_original FOR UPDATE',(proof['id_prova'],));rows=cur.fetchall()
     if len(rows)!=len(p['questoes']):raise ImportacaoError('Contagem por prova divergente.')
     for row,a,b in zip(rows,p['questoes'],n['questoes'],strict=True):
      number=a['numero'];qid=row['id_questao'];ids.append(qid)
      if row['numero_original']!=number or row['enunciado']!=a['enunciado'] or bool(row['anulada'])!=a['anulada']:raise ImportacaoError(f'Questão existente divergente: {p["codigo"]}/{number}')
      current=json.loads(row['conteudo_json']);state=None
      for label,q in [('original',a),('revisado',b)]:
       if row['hash_fonte']==q['hashFonte'] and canon(current)==canon(q['conteudo']):state=label
      if state is None:raise ImportacaoError(f'Hash/conteúdo existente divergente: {p["codigo"]}/{number}')
      cur.execute('SELECT letra,texto,correta FROM alternativa WHERE id_questao=%s ORDER BY letra',(qid,))
      if [(r['letra'],r['texto'],bool(r['correta'])) for r in cur.fetchall()]!=[(r['letra'],r['texto'],r['letra']==a['gabarito']) for r in a['alternativas']]:raise ImportacaoError('Alternativas/gabarito existentes divergentes.')
      target=a if reverter else b
      if row['hash_fonte']!=target['hashFonte']:pending.append((json.dumps(target['conteudo'],ensure_ascii=False),target['hashFonte'],qid,row['hash_fonte']))
      core.append({k:v for k,v in row.items() if k not in ['conteudo_json','hash_fonte']})
    before=preservacao(cur,ids)
    if pending:
     cur.executemany('UPDATE questao SET conteudo_json=%s,hash_fonte=%s WHERE id_questao=%s AND hash_fonte=%s',pending)
     if cur.rowcount!=len(pending):raise ImportacaoError('Quantidade de atualizações divergente.')
    cur.execute('SELECT * FROM questao WHERE id_questao IN ('+','.join(['%s']*len(ids))+')',ids);after={r['id_questao']:r for r in cur.fetchall()}
    for original in core:
     row=after[original['id_questao']]
     if {k:v for k,v in row.items() if k not in ['conteudo_json','hash_fonte']}!=original:raise ImportacaoError('ID ou dados pedagógicos alterados.')
    hashes=sorted(q['hashFonte'] for p in (old if reverter else new)['provas'] for q in p['questoes'])
    if sorted(r['hash_fonte'] for r in after.values())!=hashes:raise ImportacaoError('Hashes após atualização divergentes.')
    if preservacao(cur,ids)!=before:raise ImportacaoError('Preservação de usuários, respostas, snapshots ou categorias divergente.')
    conn.commit() if aplicar else conn.rollback()
    return {'status':'OK' if aplicar else 'SIMULACAO_REVERTIDA','operacao':'REVERSAO_RECORTES_CONCURSOS' if reverter else 'REVISAO_RECORTES_CONCURSOS','atualizadas':len(pending),'totais':{'provas':10,'questoes':364,'ativas':363,'alternativas':1616},'idsPreservados':True,'usuariosRespostasSnapshotsPreservados':True,'outrasCategoriasPreservadas':True}
   except Exception:conn.rollback();raise
 finally:
  with conn.cursor() as cur:
   for lock in reversed(acquired):cur.execute('SELECT RELEASE_LOCK(%s)',(lock,))

def main():
 parser=argparse.ArgumentParser(description=__doc__);group=parser.add_mutually_exclusive_group();group.add_argument('--aplicar',action='store_true');group.add_argument('--reverter',action='store_true');args=parser.parse_args()
 try:
  old,new=conjuntos()
  if not(args.aplicar or args.reverter):print(json.dumps({'status':'OK','operacao':'REVISAO_CONCURSOS_CONFERIDA','questoes':364}));return
  publicados(old if args.reverter else new,args.reverter)
  env=dict(os.environ)
  for k in ['DB_HOST','DB_PORT','DB_NAME','DB_USUARIO']:env[k]=re.sub(r'(?:\\[rn]|\s)+$','',env.get(k,'')).strip()
  conf=configuracao(env)
  if (conf['host'],conf['port'],conf['database'])!=('thomas.proxy.rlwy.net',23871,'evoluamais'):raise ImportacaoError('Alvo diferente do MySQL Railway aprovado.')
  import pymysql
  with pymysql.connect(**conf,cursorclass=pymysql.cursors.DictCursor) as conn:
   print(json.dumps(migrar(conn,old,new,False,args.reverter)),flush=True)
   print(json.dumps(migrar(conn,old,new,True,args.reverter)),flush=True)
   result=migrar(conn,old,new,True,args.reverter)
   if result['atualizadas']!=0:raise ImportacaoError('Reexecução não idempotente.')
   result['operacao']='REEXECUCAO_REVISAO_CONCURSOS_CONFIRMADA';print(json.dumps(result),flush=True)
 except Exception as e:
  code=e.args[0] if e.args and isinstance(e.args[0],int) else None
  message=str(e) if isinstance(e,(ImportacaoError,ValueError)) else 'Falha SQL/conexão na revisão dos concursos.'+(f' Código: {code}' if code else '')
  parser.exit(1,json.dumps({'status':'ERROR','etapa':message},ensure_ascii=False)+'\n')
if __name__=='__main__':main()
