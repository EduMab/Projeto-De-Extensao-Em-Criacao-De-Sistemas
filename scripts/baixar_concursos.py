"""Baixa exatamente as fontes versionadas; uma mudança de hash exige revisão."""
import hashlib,json,urllib.request
from pathlib import Path
import fitz
ROOT=Path(__file__).resolve().parents[1]
manifest=json.loads((ROOT/'acervo/concursos/fontes.json').read_text())
work=ROOT/'tmp/pdfs/concursos';work.mkdir(parents=True,exist_ok=True)
(work/'fontes.json').write_text(json.dumps(manifest['provas'],ensure_ascii=False))
for item in manifest['arquivos']:
    path=work/item['codigo']/item['arquivo'];path.parent.mkdir(parents=True,exist_ok=True)
    if not path.exists():
        with urllib.request.urlopen(item['url'],timeout=60) as response:data=response.read()
        if hashlib.sha256(data).hexdigest()!=item['sha256']:raise ValueError('Fonte alterada: '+item['codigo']+'/'+item['arquivo'])
        path.write_bytes(data)
    if hashlib.sha256(path.read_bytes()).hexdigest()!=item['sha256']:raise ValueError('Hash local divergente')
    path.with_suffix('.txt').write_text('\n\f\n'.join(page.get_text(sort=True) for page in fitz.open(path)))
    print(item['codigo'],item['arquivo'])
