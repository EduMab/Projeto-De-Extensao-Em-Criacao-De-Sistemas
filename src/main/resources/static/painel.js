"use strict";
const $ = id => document.getElementById(id);
const siglas = { ETEC: "E", ENEM: "EN", CONCURSO: "C", FUVEST: "F" };
let perfil = null, salvando = false, versao = 0;

function elemento(tag, texto, classe) {
  const node = document.createElement(tag);
  if (texto !== undefined) node.textContent = texto;
  if (classe) node.className = classe;
  return node;
}
function erro(texto) { $("erro").textContent = texto; $("erro").hidden = !texto; }
async function requisicao(url, options = {}) {
  const response = await fetch(url, { credentials: "same-origin", cache: "no-store", ...options });
  const body = await response.json().catch(() => ({}));
  if (response.status === 401) { window.location.replace("/login.html"); throw new Error("Entre novamente na sua conta."); }
  if (!response.ok) throw new Error(body.message || "Não foi possível concluir. Tente novamente.");
  return body;
}

function criarOpcao(objetivo, inicial) {
  const card = elemento(inicial ? "label" : "button", undefined, "goal-option");
  if (inicial) {
    const input = elemento("input"); input.type = "radio"; input.name = "objetivo"; input.value = objetivo.codigo;
    input.required = true; input.setAttribute("aria-label", objetivo.nome);
    input.onchange = () => { $("continuar").disabled = salvando || !input.checked; };
    card.append(input);
  } else {
    card.type = "button"; card.dataset.objetivo = objetivo.codigo;
    card.setAttribute("aria-label", objetivo.nome);
    card.setAttribute("aria-pressed", String(perfil.objetivo === objetivo.codigo));
    card.onclick = () => salvarObjetivo(objetivo.codigo);
  }
  const icon = elemento("span", siglas[objetivo.codigo], "goal-icon"); icon.setAttribute("aria-hidden", "true");
  const selecionado = !inicial && perfil.objetivo === objetivo.codigo;
  card.append(icon, elemento("strong", objetivo.nome), elemento("span", objetivo.descricao, "goal-description"),
    elemento("span", selecionado ? "Seu objetivo" : objetivo.simuladoDisponivel ? "Simulados disponíveis" : "Em preparação",
      "goal-status" + (objetivo.simuladoDisponivel ? " ready" : "")));
  return card;
}

function renderizar() {
  const atual = perfil.objetivos.find(o => o.codigo === perfil.objetivo);
  $("nomeUsuario").textContent = perfil.nome || "estudante";
  $("boasVindas").hidden = Boolean(atual); $("painel").hidden = !atual;
  if (!atual) {
    $("escolhasIniciais").replaceChildren(...perfil.objetivos.map(o => criarOpcao(o, true)));
    $("continuar").disabled = true;
    return;
  }
  const rodada = ++versao;
  $("objetivosPainel").replaceChildren(...perfil.objetivos.map(o => criarOpcao(o, false)));
  $("siglaObjetivo").textContent = siglas[atual.codigo];
  $("tituloPainel").textContent = `Seu foco agora é ${atual.nome}.`;
  $("tituloSimulado").textContent = atual.simuladoDisponivel ? `Simulado semanal ${atual.nome}` : `Sua preparação para ${atual.nome}`;
  $("estadoAcervo").textContent = atual.simuladoDisponivel ? "SIMULADO SEMANAL" : "CONTEÚDO EM PREPARAÇÃO";
  $("descricaoSimulado").textContent = atual.simuladoDisponivel
    ? "40 questões mescladas de edições oficiais. Pratique no seu ritmo e continue de onde parou. Uma nova seleção é liberada a cada 7 dias."
    : `Seu objetivo ${atual.nome} já está salvo. As provas e os gabaritos desta categoria estão em preparação. Quando os simulados estiverem disponíveis, este será seu ponto de partida.`;
  $("abrirSimulado").hidden = !atual.simuladoDisponivel;
  $("numerosAcervo").hidden = !atual.simuladoDisponivel;
  $("acervoQuestoes").textContent = "—"; $("acervoEdicoes").textContent = "—";
  $("tituloDesempenho").textContent = `Desempenho · ${atual.nome}`;
  $("descricaoDesempenho").textContent = atual.simuladoDisponivel
    ? "Acertos nos últimos 30 simulados concluídos deste objetivo."
    : "Seus resultados aparecerão aqui quando os simulados desta categoria estiverem disponíveis.";
  ["percentual", "totalRespostas", "acertos", "erros"].forEach(id => $(id).textContent = "—");
  $("situacaoDesempenho").textContent = atual.simuladoDisponivel ? "Carregando seu histórico…" : "Seu histórico de outros objetivos continua preservado.";
  const ia = atual.simuladoDisponivel && perfil.iaDisponivel;
  $("disciplina").disabled = !ia;
  $("gerarRecomendacao").disabled = !ia;
  $("gerarRecomendacao").textContent = ia ? "Gerar recomendação" : "Em preparação";
  $("recomendacao").textContent = ia ? "A recomendação aparecerá aqui." : "As recomendações para este objetivo estarão disponíveis em breve.";
  if (atual.simuladoDisponivel) carregarDados(rodada);
}

async function carregarDados(rodada) {
  await Promise.allSettled([
    requisicao("/api/simulados-semanais/historico").then(rows => {
      if (rodada !== versao) return;
      const concluidos = rows.filter(s => s.concluido);
      const total = concluidos.length * 40, acertos = concluidos.reduce((s, item) => s + item.acertos, 0);
      $("percentual").textContent = (total ? acertos / total * 100 : 0).toFixed(1).replace(".", ",");
      $("totalRespostas").textContent = total; $("acertos").textContent = acertos; $("erros").textContent = total - acertos;
      $("situacaoDesempenho").textContent = concluidos.length ? "Cada simulado concluído conta para sua evolução." : "Conclua seu primeiro simulado para começar seu histórico.";
    }).catch(() => { if (rodada === versao) $("situacaoDesempenho").textContent = "Não foi possível carregar seu histórico. Atualize a página para tentar novamente."; }),
    requisicao("/api/simulados-semanais/acervo").then(data => {
      if (rodada !== versao) return;
      $("acervoQuestoes").textContent = data.questoesAtivas; $("acervoEdicoes").textContent = data.edicoes;
    }).catch(() => { if (rodada === versao) $("numerosAcervo").hidden = true; })
  ]);
}

function bloquearEscolhas(value) {
  document.querySelectorAll(".goal-option button,.goal-option input,#objetivosPainel button").forEach(node => node.disabled = value);
  $("continuar").disabled = value || !document.querySelector('input[name="objetivo"]:checked');
  $("continuar").textContent = value ? "Salvando…" : "Continuar →";
}

async function salvarObjetivo(codigo) {
  if (salvando || codigo === perfil.objetivo) return;
  salvando = true; erro(""); bloquearEscolhas(true); $("confirmacao").textContent = "Salvando seu objetivo…";
  try {
    perfil = await requisicao("/api/perfil/objetivo", { method: "PUT",
      headers: { "Content-Type": "application/json", "X-Evolua-Request": "perfil" }, body: JSON.stringify({ objetivo: codigo }) });
    renderizar();
    const nome = perfil.objetivos.find(o => o.codigo === perfil.objetivo).nome;
    $("confirmacao").textContent = `Objetivo salvo: ${nome}.`;
    $("tituloPainel").focus({ preventScroll: true });
  } catch (error) { erro(error.message); $("confirmacao").textContent = "Seu objetivo anterior foi mantido. Tente novamente."; }
  finally { salvando = false; bloquearEscolhas(false); }
}

$("formObjetivo").onsubmit = event => {
  event.preventDefault();
  const opcao = document.querySelector('input[name="objetivo"]:checked');
  if (opcao) salvarObjetivo(opcao.value);
};
$("gerarRecomendacao").onclick = async () => {
  if (!perfil?.iaDisponivel || perfil.objetivo !== "ETEC") return;
  const rodada = versao; $("gerarRecomendacao").disabled = true; $("recomendacao").textContent = "Gerando recomendação…";
  try {
    const params = new URLSearchParams({ idProva: perfil.idProva, disciplina: $("disciplina").value });
    const response = await fetch(`/ia/recomendacao/${perfil.idEstudante}?${params}`, { credentials: "same-origin" });
    if (response.status === 401) { window.location.replace("/login.html"); return; }
    if (!response.ok) throw new Error("Não foi possível gerar uma recomendação agora. Tente novamente.");
    const texto = await response.text(); if (rodada === versao) $("recomendacao").textContent = texto;
  } catch (error) { if (rodada === versao) $("recomendacao").textContent = error.message; }
  finally { if (rodada === versao) $("gerarRecomendacao").disabled = false; }
};
$("sair").onclick = async () => {
  $("sair").disabled = true;
  try {
    const response = await fetch("/login/sair", { method: "POST", credentials: "same-origin" });
    if (!response.ok) throw new Error("Não foi possível sair. Tente novamente.");
    localStorage.removeItem("idEstudante"); localStorage.removeItem("nomeEstudante"); window.location.replace("/login.html");
  } catch (error) { erro(error.message); $("sair").disabled = false; }
};
async function iniciar() {
  $("carregamento").hidden = false; $("tentarNovamente").hidden = true; erro("");
  try { perfil = await requisicao("/api/perfil"); renderizar(); }
  catch (error) { erro(error.message); $("tentarNovamente").hidden = false; }
  finally { $("carregamento").hidden = true; }
}
$("tentarNovamente").onclick = iniciar;
iniciar();
