"use strict";
const $ = id => document.getElementById(id);
const categorias = { ENEM: "ENEM", ETEC: "ETEC", CONCURSO: "Concurso público", FUVEST: "FUVEST" };
let simulado = null, indice = 0, ocupado = false, objetivo = "ETEC";
function element(tag, text, className) { const node = document.createElement(tag); if (text !== undefined) node.textContent = text; if (className) node.className = className; return node; }
function aviso(text) { $("mensagem").textContent = text; $("mensagem").hidden = !text; }
async function api(path, method = "GET", data) {
  const response = await fetch("/api/simulados-semanais" + path, { method, credentials: "same-origin", headers: { "Content-Type": "application/json", "X-Evolua-Request": "simulado" }, body: data === undefined ? undefined : JSON.stringify(data) });
  const body = await response.json().catch(() => ({}));
  if (!response.ok) { const error = new Error(response.status === 401 ? "Entre na sua conta para acessar seus simulados." : body.message || "Não foi possível concluir. Tente novamente."); error.status = response.status; throw error; }
  return body;
}
function bloquear(value) { ocupado = value; $("respostas").disabled = value || Boolean(simulado?.concluido); $("anterior").disabled = value || indice === 0; $("proxima").disabled = value || indice === 39; $("finalizar").disabled = value || Boolean(simulado?.concluido); document.querySelectorAll(".numbers button").forEach(b => b.disabled = value); }
function progresso() {
  const count = simulado.questoes.filter(q => q.alternativaSelecionada !== null).length;
  $("andamento").textContent = `${count} de 40`; $("progresso").value = count;
  $("progresso").textContent = `${count} de 40`;
  $("numeros").replaceChildren();
  simulado.questoes.forEach((q, i) => { const b = element("button", String(i + 1), (q.alternativaSelecionada !== null ? "done " : "") + (indice === i ? "active" : "")); b.type = "button"; b.setAttribute("aria-label", `Questão ${i + 1}${q.alternativaSelecionada !== null ? ", respondida" : ""}`); if (indice === i) b.setAttribute("aria-current", "step"); b.onclick = () => { if (!ocupado) { indice = i; mostrar(); $("titulo").scrollIntoView({ block: "start", behavior: "smooth" }); } }; $("numeros").append(b); });
}
function pagina(p, q, container, foco, principal = false) {
  if (!/^\/questoes\/(etec|fuvest)\/[a-z0-9-]+\/pagina-\d+\.webp$/.test(p.imagem || "")) return;
  const label = element("p", `Página ${p.numero} do caderno original${foco ? " · questão indicada em roxo" : principal && p.numero > q.conteudo.pagina ? " · página seguinte" : " · apoio"}`, "page-label");
  const scroll = element("div", undefined, "page-scroll"), stage = element("div", undefined, "page-stage");
  const image = element("img"); image.src = p.imagem; image.alt = `${q.prova}, página ${p.numero}.${foco ? ` Questão original ${q.numeroOriginal}.` : ""}`; image.loading = "lazy";
  image.onerror = () => { image.hidden = true; stage.append(element("p", "Página indisponível. Use o link para abrir o caderno oficial.", "page-error")); };
  stage.append(image);
  if (foco && q.conteudo.caixaTitulo) { const [x, y, x2, y2] = q.conteudo.caixaTitulo; const marker = element("span", undefined, "focus-marker"); marker.style.left = `${Math.max(0, (x - 7) / q.conteudo.larguraPagina * 100)}%`; marker.style.top = `${Math.max(0, (y - 5) / q.conteudo.alturaPagina * 100)}%`; marker.style.width = `${Math.max(100, x2 - x + 30) / q.conteudo.larguraPagina * 100}%`; marker.style.height = `${(y2 - y + 10) / q.conteudo.alturaPagina * 100}%`; stage.append(marker); }
  scroll.append(stage); container.append(label, scroll);
}
function caixaEtecValida(fragment) {
  if (!Array.isArray(fragment.caixa) || fragment.caixa.length !== 4 || !fragment.caixa.every(Number.isFinite)) return false;
  const [x,y,x2,y2] = fragment.caixa;
  return Number.isFinite(fragment.larguraPagina) && Number.isFinite(fragment.alturaPagina)
    && x >= 0 && y >= 0 && x2 > x && y2 > y && x2 <= fragment.larguraPagina && y2 <= fragment.alturaPagina;
}
function recortesOriginais(q, container) {
  const fragments = q.conteudo.recortes;
  if (!Array.isArray(fragments) || !fragments.length || !fragments.some(r => r.tipo === "questao")) {
    container.append(element("p", "Recorte indisponível. Abra o caderno oficial para consultar a questão.", "page-error"));
    return;
  }
  const scroll = element("div", undefined, "crop-scroll");
  for (const fragment of fragments) {
    const etec = /^\/questoes\/etec\/\d{4}-[12]\/pagina-\d+\.webp$/.test(fragment.imagem || "");
    if ((!/^\/questoes\/(concursos|enem|fuvest)\/[a-z0-9-]+\/[a-z0-9-]+\.webp$/.test(fragment.imagem || "") && !etec)
        || !["apoio", "questao"].includes(fragment.tipo)) continue;
    if (etec && !caixaEtecValida(fragment)) continue;
    if (fragment.imagem.startsWith("/questoes/enem/") && fragment.tipo === "apoio" && fragment.necessario !== true) continue;
    const card = element("section", undefined, "question-crop-card");
    if (Number.isFinite(fragment.larguraOriginal) && fragment.larguraOriginal > 0) {
      card.style.setProperty("--crop-width", `${Math.min(650, Math.max(400, fragment.larguraOriginal * 1.3))}px`);
    }
    if (Number($("zoom").value) > 100) card.style.maxWidth = "none";
    card.append(element("p", fragment.tipo === "apoio" ? "TEXTO DE APOIO" : "QUESTÃO", "crop-heading"));
    const img = element("img"); img.src = fragment.imagem;
    img.alt = `${fragment.tipo === "apoio" ? "Texto de apoio da questão" : "Enunciado e alternativas da questão"} ${q.numeroOriginal}, ${q.prova}.`;
    img.loading = "lazy";
    img.onerror = () => { img.hidden = true; card.append(element("p", "Imagem indisponível. Consulte o caderno oficial.", "page-error")); };
    if (etec) {
      const [x, y, x2, y2] = fragment.caixa, width = x2 - x, height = y2 - y;
      const frame = element("div", undefined, "etec-crop-frame");
      frame.style.aspectRatio = `${width} / ${height}`;
      img.style.width = `${fragment.larguraPagina / width * 100}%`;
      img.style.left = `${-x / width * 100}%`; img.style.top = `${-y / height * 100}%`;
      frame.append(img); card.append(frame);
    } else card.append(img);
    scroll.append(card);
  }
  container.append(scroll);
}
// As seleções anteriores conservam o conteúdo e as respostas originais.
// Exibe seu enunciado individualmente, sem incorporar o caderno inteiro.
function questaoIndividual(q, container) {
  const scroll = element("div", undefined, "crop-scroll");
  if (q.conteudo.textoApoio?.trim()) {
    const support = element("section", undefined, "question-crop-card legacy-question");
    support.append(element("p", "TEXTO DE APOIO", "crop-heading"),
      element("p", q.conteudo.textoApoio, "question-text"));
    scroll.append(support);
  }
  const card = element("section", undefined, "question-crop-card legacy-question");
  card.append(element("p", `QUESTÃO ${String(q.numeroOriginal).padStart(2, "0")}`, "crop-heading"),
    element("p", q.enunciado, "question-text"));
  const alternatives = element("div", undefined, "original-alternatives");
  for (const a of q.alternativas) alternatives.append(element("p", `${a.letra}) ${a.texto}`, "question-text"));
  card.append(alternatives); scroll.append(card); container.append(scroll);
}
function mostrar() {
  if (!simulado) return; const q = simulado.questoes[indice];
  $("inicio").hidden = true; $("estudo").hidden = false;
  $("periodo").hidden = false;
  $("periodo").textContent = `Seleção aberta em ${formatDate(simulado.data)}${simulado.tipo === "ENEM" ? " · " + (simulado.idioma === "ESPANHOL" ? "Espanhol" : "Inglês") : ""} · Intervalo de sete dias até ${formatDate(simulado.proximaLiberacao)}, no horário de Brasília. Consulte e continue os simulados anteriores pelo histórico.`;
  $("fonte").textContent = q.prova + (q.conteudo.idioma ? " · " + (q.conteudo.idioma === "ESPANHOL" ? "Espanhol" : "Inglês") : ""); $("titulo").textContent = `Questão ${indice + 1}`;
  $("posicao").textContent = `${indice + 1} / 40`; $("questaoOriginal").textContent = `Questão original ${String(q.numeroOriginal).padStart(2, "0")} · Edição ${q.edicao}`;
  const url = q.conteudo.pdf || q.conteudo.urlProva; $("provaOriginal").href = (url?.startsWith("https://") || /^\/questoes\/(concursos|enem)\//.test(url || "")) ? url : objetivo === "FUVEST" ? "https://www.fuvest.br/acervo-vestibular/" : "https://www.cps.sp.gov.br/etec/vestibulinho/";
  $("paginas").replaceChildren(); $("paginasApoio").replaceChildren(); $("apoio").open = false;
  (q.conteudo.paginas || []).forEach(p => pagina(p, q, $("paginas"), p.numero === q.conteudo.pagina, true));
  (q.conteudo.apoioAnterior || []).forEach(p => pagina(p, q, $("paginasApoio"), false));
  $("apoio").hidden = !q.conteudo.apoioAnterior?.length;
  const recortada = q.conteudo.modo === "recorte_original";
  $("estudo").classList.toggle("cropped-question", recortada);
  $("notaOriginal").textContent = recortada
    ? "Somente a questão atual aparece abaixo. Quando necessário, o texto de apoio é exibido antes do enunciado."
    : "As páginas originais preservam textos, gráficos e fórmulas. Responda somente a questão indicada, mesmo que outras apareçam na página.";
  if (recortada) recortesOriginais(q, $("paginas"));
  if (q.conteudo.modo === "pdf_original") {
    $("estudo").classList.add("cropped-question");
    $("notaOriginal").textContent = "Veja somente o enunciado e as alternativas da questão atual. O texto de apoio aparece antes, quando disponível.";
    questaoIndividual(q, $("paginas"));
  }
  $("opcoes").replaceChildren();
  $("respostas").querySelector("legend").textContent = "Qual alternativa você escolhe?";
  q.alternativas.forEach(a => { const label = element("label", undefined, "option"), input = element("input"), text = element("span", a.letra); input.type = "radio"; input.name = "alternativa"; input.value = a.id; input.checked = q.alternativaSelecionada === a.id; input.setAttribute("aria-label", `Alternativa ${a.letra}`); input.onchange = () => salvar(q, a.id); label.append(input, text); $("opcoes").append(label); });
  $("correcao").hidden = !simulado.concluido;
  if (simulado.concluido) $("correcao").textContent = `${q.acertou ? "Você acertou." : "Você errou."} ${q.conteudo.gabaritoPreliminar ? "Gabarito preliminar da fonte" : "Gabarito oficial"}: alternativa ${q.gabarito}.`;
  $("finalizar").hidden = simulado.concluido; progresso(); bloquear(false);
}
async function salvar(q, alternativa) {
  if (ocupado || simulado.concluido) return; bloquear(true); $("salvamento").textContent = "Salvando resposta…"; aviso("");
  try { await api(`/${simulado.id}/questoes/${q.posicao}/resposta`, "PUT", { idAlternativa: alternativa }); q.alternativaSelecionada = alternativa; $("salvamento").textContent = "Resposta salva."; progresso(); }
  catch (error) { aviso(error.message); document.querySelectorAll(".option input").forEach(input => input.checked = Number(input.value) === q.alternativaSelecionada); $("salvamento").textContent = "Resposta não salva. Tente novamente."; }
  finally { bloquear(false); }
}
function resultado() {
  $("resultado").hidden = !simulado?.concluido;
  if (!simulado?.concluido) return;
  const score = element("div", `${simulado.acertos}/40`, "score"), text = element("div");
  text.append(element("p", "MAIS UM PASSO NA SUA EVOLUÇÃO", "eyebrow"), element("h2", `${simulado.percentual.toFixed(1).replace(".", ",")}% de acertos`), element("p", "Revise as questões abaixo. Sua correção continua disponível no histórico. Uma nova seleção é liberada sete dias após a abertura da anterior."));
  $("resultado").replaceChildren(score, text);
}
function formatDate(value) { const [year, month, day] = value.split("-"); return `${day}/${month}/${year}`; }
async function historico() {
  try { const rows = (await api("/historico")).filter(r => (r.tipo || "ETEC") === objetivo); $("historico").replaceChildren(); if (!rows.length) { $("historico").append(element("p", "Seu primeiro simulado é o começo do seu histórico.", "muted")); return; }
    rows.forEach(row => { const line = element("div", undefined, "history-row"), text = element("div"), button = element("button", row.concluido ? "Revisar" : "Continuar", "secondary"); text.append(element("strong", `${row.tipo || "ETEC"} · ${formatDate(row.data)}`), element("span", row.concluido ? `${row.acertos}/40 acertos · Concluído` : `${row.respondidas}/40 respondidas · Em andamento`)); button.type = "button"; button.onclick = async () => { if (ocupado) return; try { simulado = await api(`/${row.id}`); indice = 0; aviso(""); resultado(); mostrar(); $("estudo").scrollIntoView({ behavior: "smooth", block: "start" }); } catch (error) { aviso(error.message); } }; line.append(text, button); $("historico").append(line); });
  } catch (error) { if (error.status === 401) { $("historico").replaceChildren(element("a", "Entrar para ver meu histórico")); $("historico").firstChild.href = "/login.html"; } else aviso(error.message); }
}
function escolherIdiomaEnem() {
  return new Promise(resolve => {
    $("inicio").hidden = true; $("estudo").hidden = false;
    $("fonte").textContent = "ENEM"; $("titulo").textContent = "Escolha a língua estrangeira";
    $("posicao").textContent = "Antes de começar";
    $("questaoOriginal").textContent = "Inglês ou Espanhol";
    $("notaOriginal").textContent = "O sorteio incluirá somente o idioma escolhido. Uma tentativa já aberta mantém seu idioma e suas respostas.";
    $("paginas").replaceChildren(); $("paginasApoio").replaceChildren(); $("apoio").hidden = true;
    $("correcao").hidden = true; $("respostas").disabled = false;
    $("respostas").querySelector("legend").textContent = "Qual língua estrangeira você escolhe?";
    $("provaOriginal").href = "https://www.gov.br/inep/pt-br/areas-de-atuacao/avaliacao-e-exames-educacionais/enem/provas-e-gabaritos";
    $("opcoes").replaceChildren(); $("numeros").replaceChildren();
    $("anterior").disabled = true; $("finalizar").disabled = true;
    const proxima=$("proxima"), anteriorHandler=proxima.onclick;
    proxima.disabled=true; proxima.textContent="Começar →";
    let escolha=null;
    for(const [valor,nome] of [["INGLES","Inglês"],["ESPANHOL","Espanhol"]]) {
      const label=element("label",undefined,"option"), input=element("input");
      input.type="radio"; input.name="idiomaEnem"; input.value=valor;
      input.onchange=()=>{escolha=valor;proxima.disabled=false;};
      label.append(input,element("span",nome)); $("opcoes").append(label);
    }
    proxima.onclick=()=>{if(!escolha)return;proxima.onclick=anteriorHandler;proxima.textContent="Próxima →";resolve(escolha);};
  });
}
$("comecar").onclick = async () => { if (ocupado) return; ocupado = true; $("comecar").disabled = true; $("comecar").textContent = "Preparando suas questões…"; aviso("");
  try { const idioma = objetivo === "ENEM" ? await escolherIdiomaEnem() : null;
    simulado = await api("/atual" + (idioma ? "?idioma=" + idioma : ""), "POST"); indice = Math.max(0, simulado.questoes.findIndex(q => q.alternativaSelecionada === null)); resultado(); mostrar(); await historico(); }
  catch (error) { if (error.status === 401) { window.location.href = "/login.html"; return; } $("inicio").hidden = false; $("estudo").hidden = true; aviso(error.message); }
  finally { ocupado = false; $("comecar").disabled = false; $("comecar").textContent = "Abrir simulado da semana →"; }
};
$("anterior").onclick = () => { if (!ocupado && indice > 0) { indice--; mostrar(); } };
$("proxima").onclick = () => { if (!ocupado && indice < 39) { indice++; mostrar(); } };
$("zoom").oninput = event => { $("estudo").style.setProperty("--zoom", `${event.target.value}%`); $("estudo").style.setProperty("--crop-scale", Number(event.target.value) / 100); document.querySelectorAll(".question-crop-card").forEach(card => card.style.maxWidth = Number(event.target.value) > 100 ? "none" : ""); };
$("finalizar").onclick = async () => { if (ocupado) return; const respondidas = simulado.questoes.filter(q => q.alternativaSelecionada !== null).length;
  if (respondidas < 40) { aviso(`Faltam ${40 - respondidas} questões. Responda todas antes de finalizar.`); return; }
  bloquear(true); aviso(""); try { simulado = await api(`/${simulado.id}/finalizar`, "POST"); resultado(); mostrar(); await historico(); $("resultado").scrollIntoView({ behavior: "smooth", block: "start" }); } catch (error) { aviso(error.message); } finally { bloquear(false); }
};
$("sair").onclick = async () => { await fetch("/login/sair", { method: "POST", credentials: "same-origin" }); localStorage.clear(); window.location.href = "/login.html"; };
async function inicializar() {
  $("comecar").disabled = true;
  try {
    const response = await fetch("/api/perfil", { credentials: "same-origin", cache: "no-store" });
    if (response.status === 401) { window.location.replace("/login.html"); return; }
    if (!response.ok) throw new Error("Não foi possível carregar seu objetivo. Atualize a página para tentar novamente.");
    const perfil = await response.json();
    if (!Object.hasOwn(categorias, perfil.objetivo)) { window.location.replace("/index.html"); return; }
    objetivo = perfil.objetivo;
    if(objetivo === "ENEM") {
      const footer=document.querySelector("main > footer");
      if(footer?.firstChild)footer.firstChild.textContent="Questões e gabaritos: acervo oficial do INEP. Questões anuladas ficam fora da seleção.";
    }
    if(objetivo === "FUVEST") {
      const footer=document.querySelector("main > footer");
      if(footer?.firstChild)footer.firstChild.textContent="Questões e gabaritos: acervo oficial da FUVEST. Questões anuladas ficam fora da seleção.";
    }
    document.querySelectorAll("[data-categoria]").forEach(n => n.textContent = categorias[objetivo]);
    $("comecar").disabled = false;
    await Promise.allSettled([
      api("/acervo?tipo=" + encodeURIComponent(objetivo)).then(data => { $("acervoTotal").textContent = data.questoesAtivas; $("acervoEdicoes").textContent = data.edicoes; }).catch(error => aviso(error.message)),
      historico()
    ]);
  } catch (error) { aviso(error.message); }
}
inicializar();
