#!/usr/bin/env python3
"""Carga ENEM isolada, transacional e idempotente; não altera esquema/históricos."""
from pathlib import Path
import argparse,concurrent.futures,gzip,hashlib,json,os,re,time,urllib.request,zipfile
from importar_concursos import configuracao,ImportacaoError,validar_schema

ROOT=Path(__file__).resolve().parents[1]
ACERVO=ROOT/'acervo/enem'
ORIGIN='https://evoluamais-api.onrender.com'
LOCK='evolua_enem_importacao'
LETRAS='ABCDE'
ALVO=('thomas.proxy.rlwy.net',23871,'evoluamais')

def canon(v):return json.dumps(v,sort_keys=True,ensure_ascii=False,separators=(',',':'))
def validar():
    data=json.loads(gzip.decompress((ACERVO/'questoes-recortadas.json.gz').read_bytes()))
    approval=json.loads((ACERVO/'aprovacao.json').read_text())
    if hashlib.sha256(canon(data).encode()).hexdigest()!=approval['sha256DatasetCanonico']:
        raise ImportacaoError('Acervo diverge da prévia aprovada.')
    provas=data['provas'];qs=[q for p in provas for q in p['questoes']]
    if (data['tipo'],len(provas),len(qs),sum(not q['anulada'] for q in qs),sum(len(q['alternativas']) for q in qs))!=('ENEM',20,1850,1839,9250):
        raise ImportacaoError('Contagens ENEM divergentes.')
    expected_images=json.loads((ACERVO/'imagens-aprovadas.json').read_text())
    images=set()
    for p in provas:
        if p['codigo']!=f"ENEM-{p['ano']}-DIA-{p['dia']}-AMARELO" or not 2017<=p['ano']<=2026 or p['dia'] not in (1,2):raise ImportacaoError('Caderno inválido.')
        if len({q['numero'] for q in p['questoes']})!=len(p['questoes']):raise ImportacaoError('Numeração interna duplicada.')
        with zipfile.ZipFile(ACERVO/f"recortes-{p['ano']}-dia-{p['dia']}.zip") as z:
            for q in p['questoes']:
                if ''.join(a['letra'] for a in q['alternativas'])!=LETRAS or q['anulada']!=(q['gabarito'] is None):raise ImportacaoError('Alternativas/gabarito inválidos.')
                if not q['anulada'] and q['gabarito'] not in LETRAS:raise ImportacaoError('Gabarito inválido.')
                for r in q['conteudo']['recortes']:
                    path=r['imagem']
                    if not re.fullmatch(r'/questoes/enem/enem-20\d\d-dia-[12]-amarelo/[a-z0-9-]+\.webp',path):raise ImportacaoError('Caminho de imagem inválido.')
                    if r['tipo']=='apoio' and r.get('necessario') is not True:raise ImportacaoError('Apoio sem necessidade confirmada.')
                    if path not in images:
                        if hashlib.sha256(z.read(path.lstrip('/'))).hexdigest()!=expected_images.get(path):raise ImportacaoError('Imagem diverge da prévia: '+path)
                        images.add(path)
    if images!=set(expected_images):raise ImportacaoError('Conjunto de imagens divergente.')
    return provas,sorted(images)

def publicacao(images,espera=0):
    until=time.monotonic()+espera
    while True:
        try:
            with urllib.request.urlopen(ORIGIN+'/simulados.js',timeout=60) as r:script=r.read().decode()
            ready='function escolherIdiomaEnem' in script and '(concursos|enem)' in script
        except Exception:ready=False
        print(json.dumps({'status':'VERIFICACAO_PUBLICACAO_ENEM','novoVisual':ready}),flush=True)
        if ready:break
        if time.monotonic()>=until:raise ImportacaoError('A aplicação ainda não publicou o suporte ENEM.')
        time.sleep(10)
    def head(path):
        req=urllib.request.Request(ORIGIN+path,method='HEAD')
        with urllib.request.urlopen(req,timeout=30) as r:
            if r.status!=200 or 'image/webp' not in r.headers.get('content-type',''):raise ImportacaoError('Imagem não publicada: '+path)
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:list(pool.map(head,images))
    print(json.dumps({'status':'OK','operacao':'ASSETS_ENEM_PUBLICADOS','imagens':len(images)}),flush=True)

def metrica_outras_categorias(cur):
    cur.execute("SELECT p.tipo,p.id_prova,p.codigo,p.status_importacao,COUNT(q.id_questao) questoes FROM prova p LEFT JOIN questao q ON q.id_prova=p.id_prova WHERE p.tipo<>'ENEM' GROUP BY p.tipo,p.id_prova,p.codigo,p.status_importacao ORDER BY p.id_prova")
    return cur.fetchall()

def importar(conn,provas,aplicar=False):
    audit=[]
    with conn.cursor() as cur:
        cur.execute('SELECT GET_LOCK(%s,15) adquirido',(LOCK,))
        if cur.fetchone()['adquirido']!=1:raise ImportacaoError('Importação ENEM concorrente.')
        try:
            validar_schema(cur)
            conn.begin()
            try:
                before=metrica_outras_categorias(cur)
                for p in provas:
                    cur.execute('SELECT id_prova,tipo,ano,edicao,caderno,url_prova,url_gabarito FROM prova WHERE codigo=%s FOR UPDATE',(p['codigo'],))
                    old=cur.fetchone()
                    if old:
                        expected=('ENEM',p['ano'],p['edicao'],p['caderno'],p['urlProva'],p['urlGabarito'])
                        if tuple(old[k] for k in ('tipo','ano','edicao','caderno','url_prova','url_gabarito'))!=expected:raise ImportacaoError('Prova ENEM existente divergente: '+p['codigo'])
                        pid=old['id_prova']
                    else:
                        cur.execute("INSERT INTO prova(nome,descricao,tipo,codigo,edicao,ano,etapa,caderno,banca,url_prova,url_gabarito,status_importacao) VALUES (%s,%s,'ENEM',%s,%s,%s,%s,%s,'INEP',%s,%s,'RASCUNHO')",(p['nome'],'Caderno amarelo oficial; questões objetivas em recortes originais.',p['codigo'],p['edicao'],p['ano'],f"{p['dia']}º DIA",p['caderno'],p['urlProva'],p['urlGabarito']))
                        pid=cur.lastrowid
                    novas=0
                    for q in p['questoes']:
                        cur.execute('SELECT id_disciplina FROM disciplina WHERE nome=%s ORDER BY id_disciplina LIMIT 1',(q['disciplina'],))
                        disc=cur.fetchone()
                        if disc:did=disc['id_disciplina']
                        else:
                            cur.execute('INSERT INTO disciplina(nome) VALUES (%s)',(q['disciplina'],));did=cur.lastrowid
                        cur.execute('SELECT id_questao,hash_fonte,enunciado,anulada,conteudo_json FROM questao WHERE id_prova=%s AND numero_original=%s FOR UPDATE',(pid,q['numero']))
                        oldq=cur.fetchone()
                        if oldq:
                            if (oldq['hash_fonte']!=q['hashFonte'] or oldq['enunciado']!=q['enunciado'] or bool(oldq['anulada'])!=q['anulada'] or canon(json.loads(oldq['conteudo_json']))!=canon(q['conteudo'])):raise ImportacaoError(f"Questão ENEM divergente: {p['codigo']}/{q['numero']}")
                            qid=oldq['id_questao']
                        else:
                            cur.execute('INSERT INTO questao(enunciado,id_disciplina,id_prova,numero_original,anulada,conteudo_json,hash_fonte) VALUES (%s,%s,%s,%s,%s,%s,%s)',(q['enunciado'],did,pid,q['numero'],int(q['anulada']),json.dumps(q['conteudo'],ensure_ascii=False),q['hashFonte']))
                            qid=cur.lastrowid
                            cur.executemany('INSERT INTO alternativa(texto,correta,id_questao,letra) VALUES (%s,%s,%s,%s)',[(a['texto'],int(a['letra']==q['gabarito']),qid,a['letra']) for a in q['alternativas']]);novas+=1
                        cur.execute('SELECT letra,texto,correta FROM alternativa WHERE id_questao=%s ORDER BY letra',(qid,))
                        if [(a['letra'],a['texto'],bool(a['correta'])) for a in cur.fetchall()]!=[(a['letra'],a['texto'],a['letra']==q['gabarito']) for a in q['alternativas']]:raise ImportacaoError('Alternativas ENEM divergentes.')
                    cur.execute('SELECT COUNT(*) n FROM questao WHERE id_prova=%s',(pid,))
                    if cur.fetchone()['n']!=len(p['questoes']):raise ImportacaoError('Contagem por caderno divergente.')
                    cur.execute("UPDATE prova SET status_importacao='VALIDADA' WHERE id_prova=%s",(pid,))
                    audit.append({'codigo':p['codigo'],'novas':novas,'questoes':len(p['questoes'])})
                if before!=metrica_outras_categorias(cur):raise ImportacaoError('Preservação das outras categorias divergente.')
                codes=[p['codigo'] for p in provas];slots=','.join(['%s']*len(codes))
                cur.execute(f"SELECT COUNT(DISTINCT p.id_prova) provas,COUNT(q.id_questao) questoes,SUM(q.anulada=0) ativas FROM prova p JOIN questao q ON q.id_prova=p.id_prova WHERE p.codigo IN ({slots})",codes)
                totals=cur.fetchone()
                cur.execute(f"SELECT COUNT(*) alternativas FROM alternativa a JOIN questao q ON q.id_questao=a.id_questao JOIN prova p ON p.id_prova=q.id_prova WHERE p.codigo IN ({slots})",codes)
                alts=cur.fetchone()['alternativas']
                if (int(totals['provas']),int(totals['questoes']),int(totals['ativas']),int(alts))!=(20,1850,1839,9250):raise ImportacaoError('Totais ENEM divergentes.')
                conn.commit() if aplicar else conn.rollback()
                return {'status':'OK' if aplicar else 'SIMULACAO_REVERTIDA','operacao':'IMPORTACAO_ENEM_AMARELO','totals':{k:int(v) for k,v in totals.items()},'alternativas':int(alts),'audit':audit,'outrasCategoriasPreservadas':True,'usuariosRespostasSnapshots':'sem operações de escrita pela rotina'}
            except Exception:
                conn.rollback();raise
        finally:cur.execute('SELECT RELEASE_LOCK(%s)',(LOCK,))

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--aplicar',action='store_true');parser.add_argument('--simular',action='store_true');parser.add_argument('--esperar-publicacao',type=int,default=0);args=parser.parse_args()
    try:
        provas,images=validar()
        print(json.dumps({'status':'ACERVO_ENEM_CONFERIDO','provas':20,'questoes':1850,'ativas':1839,'alternativas':9250}),flush=True)
        if not (args.aplicar or args.simular):return
        # Nunca consulta credenciais/conecta ao MySQL antes da publicação dos recursos.
        publicacao(images,args.esperar_publicacao)
        env=dict(os.environ)
        for k in ['DB_HOST','DB_PORT','DB_NAME','DB_USUARIO']:env[k]=re.sub(r'(?:\\[rn]|\s)+$','',env.get(k,'')).strip()
        config=configuracao(env)
        if (config['host'],config['port'],config['database'])!=ALVO:raise ImportacaoError('Conexão diferente do MySQL do projeto Railway aprovado.')
        import pymysql
        with pymysql.connect(**config,cursorclass=pymysql.cursors.DictCursor) as conn:
            print(json.dumps(importar(conn,provas,False),ensure_ascii=False),flush=True)
            if args.aplicar:
                print(json.dumps(importar(conn,provas,True),ensure_ascii=False),flush=True)
                repeat=importar(conn,provas,True)
                if any(p['novas'] for p in repeat['audit']):raise ImportacaoError('Reexecução ENEM criou duplicatas.')
                repeat['operacao']='REEXECUCAO_ENEM_CONFIRMADA';print(json.dumps(repeat,ensure_ascii=False),flush=True)
    except Exception as e:
        if isinstance(e,ImportacaoError):message=str(e)
        else:
            code=e.args[0] if e.args and isinstance(e.args[0],int) else None
            message='Falha na carga ENEM; confira conexão, publicação e permissões existentes.'+(f' Código SQL: {code}.' if code else '')
        parser.exit(1,json.dumps({'status':'ERROR','operacao':'IMPORTACAO_ENEM_AMARELO','etapa':message},ensure_ascii=False)+'\n')

if __name__=='__main__':main()
