"""Valida a prévia aprovada e empacota imagens sem alterar o acervo original."""
import hashlib,json,zipfile
from pathlib import Path
from preparar_previa_concursos_enem import DEST,ROOT,canon

def validar():
 data=json.loads((DEST/'dados.json').read_text());files=json.loads((DEST/'imagens.json').read_text());approval=json.loads((ROOT/'acervo/concursos-previa-enem/aprovacao.json').read_text())
 if hashlib.sha256(canon(data).encode()).hexdigest()!=approval['datasetCanonicoSha256']:raise ValueError('Dados divergem da prévia aprovada.')
 if set(files)!=set(approval['imagens']):raise ValueError('Conjunto de imagens divergente.')
 for path,f in files.items():
  if hashlib.sha256(Path(f).read_bytes()).hexdigest()!=approval['imagens'][path]:raise ValueError('Imagem diverge da prévia: '+path)
 return data,files

def main():
 _,files=validar()
 with zipfile.ZipFile(ROOT/'acervo/concursos/recortes-revisao-enem.zip','w') as z:
  for path,f in sorted(files.items()):
   info=zipfile.ZipInfo(path.lstrip('/'),date_time=(1980,1,1,0,0,0));info.external_attr=0o644<<16;z.writestr(info,Path(f).read_bytes())
 print(json.dumps({'status':'OK','operacao':'IMAGENS_CONCURSOS_APROVADAS','imagens':len(files)}))
if __name__=='__main__':main()
