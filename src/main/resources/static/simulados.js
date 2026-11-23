"use strict";
const $ = id => document.getElementById(id);
let simulado = null, indice = 0, ocupado = false;
function element(tag, text, className) { const node = document.createElement(tag); if (text !== undefined) node.textContent = text; if (className) node.className = className; return node; }
function aviso(text) { $("mensagem").textContent = text; $("mensagem").hidden = !text; }
async function api(path, method = "GET", data) {
  const response = await fetch("/api/simulados-diarios" + path, { method, credentials: "same-origin", headers: { "Content-Type": "application/json", "X-Evolua-Request": "simulado" }, body: data === undefined ? undefined : JSON.stringify(data) });
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
function pagina(p, q, container, foco) {
  if (!p.imagem?.startsWith("/questoes/etec/")) return;
  const label = element("p", `Página ${p.numero} do caderno original${foco ? " · questão indicada em roxo" : " · apoio"}`, "page-label");
  const scroll = element("div", undefined, "page-scroll"), stage = element("div", undefined, "page-stage");
  const image = element("img"); image.src = p.imagem; image.alt = `ETEC ${q.edicao}, página ${p.numero}. Responda a questão original ${q.numeroOriginal}.`; image.loading = "lazy";
  image.onerror = () => { image.hidden = true; stage.append(element("p", "Página indisponível. Use o link para abrir o caderno oficial.", "page-error")); };
  stage.append(image);
  if (foco && q.conteudo.caixaTitulo) { const [x, y, x2, y2] = q.conteudo.caixaTitulo; const marker = element("span", undefined, "focus-marker"); marker.style.left = `${Math.max(0, (x - 7) / q.conteudo.larguraPagina * 100)}%`; marker.style.top = `${Math.max(0, (y - 5) / q.conteudo.alturaPagina * 100)}%`; marker.style.width = `${Math.max(100, x2 - x + 30) / q.conteudo.larguraPagina * 100}%`; marker.style.height = `${(y2 - y + 10) / q.conteudo.alturaPagina * 100}%`; stage.append(marker); }
  scroll.append(stage); container.append(label, scroll);
}
function mostrar() {
  if (!simulado) return; const q = simulado.questoes[indice];
  $("inicio").hidden = true; $("estudo").hidden = false;
  $("fonte").textContent = q.prova; $("titulo").textContent = `Questão ${indice + 1}`;
  $("posicao").textContent = `${indice + 1} / 40`; $("questaoOriginal").textContent = `Responda a questão ${String(q.numeroOriginal).padStart(2, "0")} da edição ${q.edicao}.`;
  const url = q.conteudo.urlProva; $("provaOriginal").href = url?.startsWith("https://") ? url : "https://www.cps.sp.gov.br/etec/vestibulinho/";
  $("paginas").replaceChildren(); $("paginasApoio").replaceChildren(); $("apoio").open = false;
  (q.conteudo.paginas || []).forEach(p => pagina(p, q, $("paginas"), p.numero === q.conteudo.pagina));
  (q.conteudo.apoioAnterior || []).forEach(p => pagina(p, q, $("paginasApoio"), false));
  $("apoio").hidden = !q.conteudo.apoioAnterior?.length;
  $("opcoes").replaceChildren();
  q.alternativas.forEach(a => { const label = element("label", undefined, "option"), input = element("input"), text = element("span", a.letra); input.type = "radio"; input.name = "alternativa"; input.value = a.id; input.checked = q.alternativaSelecionada === a.id; input.setAttribute("aria-label", `Alternativa ${a.letra}`); input.onchange = () => salvar(q, a.id); label.append(input, text); $("opcoes").append(label); });
  $("correcao").hidden = !simulado.concluido;
  if (simulado.concluido) $("correcao").textContent = `${q.acertou ? "Você acertou." : "Você errou."} Gabarito oficial: alternativa ${q.gabarito}.`;
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
  text.append(element("p", "MAIS UM PASSO NA SUA EVOLUÇÃO", "eyebrow"), element("h2", `${simulado.percentual.toFixed(1).replace(".", ",")}% de acertos`), element("p", "Revise as questões abaixo. A próxima seleção diária estará disponível amanhã."));
  $("resultado").replaceChildren(score, text);
}
function formatDate(value) { const [year, month, day] = value.split("-"); return `${day}/${month}/${year}`; }
async function historico() {
  try { const rows = await api("/historico"); $("historico").replaceChildren(); if (!rows.length) { $("historico").append(element("p", "Seu primeiro simulado é o começo do seu histórico.", "muted")); return; }
    rows.forEach(row => { const line = element("div", undefined, "history-row"), text = element("div"), button = element("button", row.concluido ? "Revisar" : "Continuar", "secondary"); text.append(element("strong", `ETEC · ${formatDate(row.data)}`), element("span", row.concluido ? `${row.acertos}/40 acertos · Concluído` : `${row.respondidas}/40 respondidas · Em andamento`)); button.type = "button"; button.onclick = async () => { if (ocupado) return; try { simulado = await api(`/${row.id}`); indice = 0; aviso(""); resultado(); mostrar(); $("estudo").scrollIntoView({ behavior: "smooth", block: "start" }); } catch (error) { aviso(error.message); } }; line.append(text, button); $("historico").append(line); });
  } catch (error) { if (error.status === 401) { $("historico").replaceChildren(element("a", "Entrar para ver meu histórico")); $("historico").firstChild.href = "/login.html"; } else aviso(error.message); }
}
$("comecar").onclick = async () => { if (ocupado) return; ocupado = true; $("comecar").disabled = true; $("comecar").textContent = "Preparando suas questões…"; aviso("");
  try { simulado = await api("/hoje", "POST"); indice = Math.max(0, simulado.questoes.findIndex(q => q.alternativaSelecionada === null)); resultado(); mostrar(); await historico(); }
  catch (error) { if (error.status === 401) { window.location.href = "/login.html"; return; } aviso(error.message); }
  finally { ocupado = false; $("comecar").disabled = false; $("comecar").textContent = "Abrir simulado de hoje →"; }
};
$("anterior").onclick = () => { if (!ocupado && indice > 0) { indice--; mostrar(); } };
$("proxima").onclick = () => { if (!ocupado && indice < 39) { indice++; mostrar(); } };
$("zoom").oninput = event => $("estudo").style.setProperty("--zoom", `${event.target.value}%`);
$("finalizar").onclick = async () => { if (ocupado) return; const respondidas = simulado.questoes.filter(q => q.alternativaSelecionada !== null).length;
  if (respondidas < 40) { aviso(`Faltam ${40 - respondidas} questões. Responda todas antes de finalizar.`); return; }
  bloquear(true); aviso(""); try { simulado = await api(`/${simulado.id}/finalizar`, "POST"); resultado(); mostrar(); await historico(); $("resultado").scrollIntoView({ behavior: "smooth", block: "start" }); } catch (error) { aviso(error.message); } finally { bloquear(false); }
};
$("sair").onclick = async () => { await fetch("/login/sair", { method: "POST", credentials: "same-origin" }); localStorage.clear(); window.location.href = "/login.html"; };
api("/acervo").then(data => { $("acervoTotal").textContent = data.questoesAtivas; $("acervoEdicoes").textContent = data.edicoes; }).catch(error => aviso(error.message));
historico();
