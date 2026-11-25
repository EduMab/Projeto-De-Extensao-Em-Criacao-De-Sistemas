const CACHE_NAME = "evoluamais-shell-v1";

self.addEventListener("install", event => {
  self.skipWaiting();
});

self.addEventListener("activate", event => {
  event.waitUntil(self.clients.claim());
});

self.addEventListener("push", event => {
  let dados = {};
  try { dados = event.data ? event.data.json() : {}; }
  catch (_) { dados = { body: event.data ? event.data.text() : "" }; }

  const titulo = dados.title || "Evolua+";
  const opcoes = {
    body: dados.body || "Sua preparação tem uma nova etapa disponível.",
    tag: dados.tag || "evoluamais-tarefa",
    renotify: false,
    data: { url: dados.url || "/index.html" }
  };
  event.waitUntil(self.registration.showNotification(titulo, opcoes));
});

self.addEventListener("notificationclick", event => {
  event.notification.close();
  const destino = new URL(event.notification.data?.url || "/index.html", self.location.origin);
  if (destino.origin !== self.location.origin) return;
  event.waitUntil((async () => {
    const abas = await self.clients.matchAll({ type: "window", includeUncontrolled: true });
    for (const aba of abas) {
      if ("focus" in aba) {
        await aba.focus();
        if ("navigate" in aba) await aba.navigate(destino.href);
        return;
      }
    }
    if (self.clients.openWindow) await self.clients.openWindow(destino.href);
  })());
});
