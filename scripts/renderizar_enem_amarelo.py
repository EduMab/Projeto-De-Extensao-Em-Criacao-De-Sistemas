#!/usr/bin/env python3
"""Renderiza o manifesto já validado; sem rede, credenciais ou acesso ao banco."""
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor
import gzip,json,zipfile,shutil
import fitz
from PIL import Image,ImageChops
from preparar_enem_amarelo import ROOT,ACERVO,WORK,OUT

def render(proof):
    year,day=proof['ano'],proof['dia'];doc=fitz.open(WORK/f'{year}-dia{day}.pdf')
    folder=OUT/'questoes/enem'/proof['slug']
    if folder.exists():shutil.rmtree(folder)
    folder.mkdir(parents=True)
    total=0;seen=set()
    for q in proof['questoes']:
        for r in q['conteudo']['recortes']:
            if r['imagem'] in seen:continue
            seen.add(r['imagem'])
            path=OUT/r['imagem'].lstrip('/');path.parent.mkdir(parents=True,exist_ok=True)
            pix=doc[r['pagina']-1].get_pixmap(matrix=fitz.Matrix(2.2,2.2),clip=fitz.Rect(r['caixa']),alpha=False)
            im=Image.frombytes('RGB',(pix.width,pix.height),pix.samples)
            diff=ImageChops.difference(im,Image.new('RGB',im.size,'white')).convert('L').point(lambda v:255 if v>28 else 0)
            bb=diff.getbbox()
            if bb:im=im.crop((max(0,bb[0]-5),max(0,bb[1]-5),min(im.width,bb[2]+5),min(im.height,bb[3]+5)))
            im.save(path,'WEBP',quality=92,method=4);total+=1
    shutil.copyfile(WORK/f'{year}-dia{day}.pdf',folder/'prova.pdf')
    target=ACERVO/f'recortes-{year}-dia-{day}.zip'
    with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED) as z:
        for path in sorted(folder.iterdir()):z.write(path,path.relative_to(OUT))
    return proof['slug'],total,target.stat().st_size

if __name__=='__main__':
    data=json.loads(gzip.decompress((ACERVO/'questoes-recortadas.json.gz').read_bytes()))
    with ProcessPoolExecutor(max_workers=4) as pool:
        for result in pool.map(render,data['provas']):print(*result,flush=True)
