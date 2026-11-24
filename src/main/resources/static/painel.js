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
  const ia = perfil.objetivo === "ETEC" && perfil.iaDisponivel;
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
      const concluidos = rows.filter(s => s.concluido && (s.tipo || "ETEC") === perfil.objetivo);
      const total = concluidos.length * 40, acertos = concluidos.reduce((s, item) => s + item.acertos, 0);
      $("percentual").textContent = (total ? acertos / total * 100 : 0).toFixed(1).replace(".", ",");
      $("totalRespostas").textContent = total; $("acertos").textContent = acertos; $("erros").textContent = total - acertos;
      $("situacaoDesempenho").textContent = concluidos.length ? "Cada simulado concluído conta para sua evolução." : "Conclua seu primeiro simulado para começar seu histórico.";
    }).catch(() => { if (rodada === versao) $("situacaoDesempenho").textContent = "Não foi possível carregar seu histórico. Atualize a página para tentar novamente."; }),
    requisicao("/api/simulados-semanais/acervo?tipo=" + encodeURIComponent(perfil.objetivo)).then(data => {
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

async function carregarNotificacoes() {
  try {
    const dados = await requisicao("/api/notificacoes");
    const contador = $("contadorNotificacoes");
    contador.textContent = dados.naoLidas;
    contador.hidden = dados.naoLidas === 0;
    const lista = $("listaNotificacoes");
    lista.replaceChildren();
    if (!dados.notificacoes.length) {
      lista.append(elemento("p", "Você ainda não tem avisos. Quando uma nova etapa do seu plano semanal estiver disponível, ela aparecerá aqui.", "muted"));
      return;
    }
    dados.notificacoes.forEach(item => {
      const card = elemento("article", undefined, "notification-item" + (item.lida ? "" : " unread"));
      const conteudo = elemento("div");
      conteudo.append(elemento("strong", item.titulo), elemento("p", item.mensagem));
      const a = elemento("a", "Continuar minha preparação →");
      a.href = item.link || "/simulados.html";
      a.onclick = async event => {
        event.preventDefault();
        try {
          if (!item.lida) await requisicao("/api/notificacoes/"+item.id+"/lida", {
            method:"POST", headers:{"X-Evolua-Request":"notificacoes"}
          });
        } finally { window.location.assign(a.href); }
      };
      conteudo.append(a);
      card.append(conteudo);
      if (!item.lida) {
        const btn = elemento("button", "Marcar como lida", "notification-read");
        btn.type = "button";
        btn.onclick = async () => {
          btn.disabled = true;
          try {
            await requisicao("/api/notificacoes/"+item.id+"/lida", {
              method:"POST", headers:{"X-Evolua-Request":"notificacoes"}
            });
            await carregarNotificacoes();
          } catch (_) { btn.disabled = false; }
        };
        card.append(btn);
      }
      lista.append(card);
    });
  } catch (e) {
    if (e.message && !e.message.includes("Entre novamente"))
      $("listaNotificacoes").replaceChildren(elemento("p", "Não foi possível carregar seus avisos agora. Tente novamente.", "muted"));
  }
}

function chavePushParaBytes(chave) {
  const padding = "=".repeat((4 - chave.length % 4) % 4);
  const base64 = (chave + padding).replace(/-/g, "+").replace(/_/g, "/");
  const raw = window.atob(base64);
  return Uint8Array.from([...raw].map(caractere => caractere.charCodeAt(0)));
}

async function prepararPush() {
  const botao = $("ativarPush");
  const estado = $("estadoPush");
  if (!botao || !estado) return;
  if (!window.isSecureContext || !("serviceWorker" in navigator) ||
      !("PushManager" in window) || !("Notification" in window)) {
    botao.disabled = true;
    estado.textContent = "Seu navegador ou esta conexão não oferece avisos em segundo plano. Use o Evolua+ em uma conexão HTTPS e um navegador compatível.";
    return;
  }
  try {
    const config = await requisicao("/api/notificacoes/push/config");
    if (!config.ativo || !config.chavePublica) {
      botao.disabled = true;
      estado.textContent = "Os avisos no dispositivo ainda não foram configurados pelo servidor. Os avisos dentro do painel continuam disponíveis.";
      return;
    }
    const registro = await navigator.serviceWorker.register("/sw.js");
    const assinaturaAtual = await registro.pushManager.getSubscription();
    if (Notification.permission === "denied") {
      botao.disabled = true;
      estado.textContent = "As notificações estão bloqueadas nas permissões do navegador. Altere essa permissão para ativá-las.";
      return;
    }
    botao.textContent = assinaturaAtual ? "Desativar avisos" : "Ativar avisos";
    estado.textContent = assinaturaAtual
      ? "Este dispositivo está inscrito para receber lembretes do Evolua+."
      : "Receba lembretes de estudo mesmo quando não estiver com o Evolua+ aberto.";
    botao.onclick = async () => {
      botao.disabled = true;
      try {
        const atual = await registro.pushManager.getSubscription();
        if (atual) {
          await requisicao("/api/notificacoes/push/assinatura", {
            method:"DELETE",
            headers:{"Content-Type":"application/json","X-Evolua-Request":"notificacoes"},
            body:JSON.stringify({endpoint:atual.endpoint})
          });
          await atual.unsubscribe();
          estado.textContent = "Avisos desativados neste dispositivo.";
          botao.textContent = "Ativar avisos";
          return;
        }
        const permissao = await Notification.requestPermission();
        if (permissao !== "granted") {
          estado.textContent = "Permissão não concedida. Você ainda pode consultar os avisos dentro do painel.";
          return;
        }
        const nova = await registro.pushManager.subscribe({
          userVisibleOnly:true,
          applicationServerKey:chavePushParaBytes(config.chavePublica)
        });
        try {
          await requisicao("/api/notificacoes/push/assinatura", {
            method:"POST",
            headers:{"Content-Type":"application/json","X-Evolua-Request":"notificacoes"},
            body:JSON.stringify(nova.toJSON())
          });
        } catch (erro) {
          await nova.unsubscribe();
          throw erro;
        }
        estado.textContent = "Pronto! Este dispositivo receberá os lembretes do Evolua+.";
        botao.textContent = "Desativar avisos";
      } catch (e) {
        estado.textContent = "Não foi possível atualizar os avisos. Verifique a conexão e tente novamente.";
      } finally { botao.disabled = false; }
    };
  } catch (e) {
    botao.disabled = true;
    estado.textContent = "Não foi possível preparar os avisos neste navegador. Os avisos dentro do painel continuam disponíveis.";
  }
}

$("abrirNotificacoes").onclick = async () => {
  const abrir = $("centralNotificacoes").hidden;
  $("centralNotificacoes").hidden = !abrir;
  $("abrirNotificacoes").setAttribute("aria-expanded", String(abrir));
  if (abrir) {
    await carregarNotificacoes();
    await prepararPush();
  }
};
$("marcarTodasNotificacoes").onclick = async () => {
  const botao = $("marcarTodasNotificacoes");
  botao.disabled = true;
  try {
    await requisicao("/api/notificacoes/lidas", {
      method:"POST", headers:{"X-Evolua-Request":"notificacoes"}
    });
    await carregarNotificacoes();
  } finally { botao.disabled = false; }
};

async function iniciar() {
  $("carregamento").hidden = false; $("tentarNovamente").hidden = true; erro("");
  try {
    perfil = await requisicao("/api/perfil");
    renderizar();
    carregarNotificacoes();
    if (window.location.hash === "#notificacoes") {
      $("centralNotificacoes").hidden = false;
      $("abrirNotificacoes").setAttribute("aria-expanded", "true");
      prepararPush();
    }
  } catch (error) { erro(error.message); $("tentarNovamente").hidden = false; }
  finally { $("carregamento").hidden = true; }
}
$("tentarNovamente").onclick = iniciar;
window.setInterval(() => {
  if (document.visibilityState === "visible") carregarNotificacoes();
}, 60000);
iniciar();
