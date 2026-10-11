// The app opens without a network: the shell and libraries come from the cache, the panels' data
// from the network when it can and the last reading when it can't.
const SHELL = "surya-app-v1";
const FILES = ["./", "index.html", "app.css", "app.js", "manifest.webmanifest", "icon-192.png", "../config.js"];

self.addEventListener("install", (e) => e.waitUntil(caches.open(SHELL).then((c) => c.addAll(FILES)).then(() => self.skipWaiting())));
self.addEventListener("activate", (e) => e.waitUntil(caches.keys().then((keys) => Promise.all(keys.filter((k) => k !== SHELL).map((k) => caches.delete(k)))).then(() => self.clients.claim())));
self.addEventListener("fetch", (e) => {
  const url = new URL(e.request.url);
  if (e.request.method !== "GET") return;
  const api = url.pathname.endsWith("/plant") || url.pathname.endsWith("/places");
  if (api) {  // fresh when online, the last answer when not
    e.respondWith(fetch(e.request).then((r) => { const copy = r.clone(); caches.open(SHELL).then((c) => c.put(e.request, copy)); return r; })
      .catch(() => caches.match(e.request)));
    return;
  }
  e.respondWith(caches.match(e.request).then((hit) => hit || fetch(e.request).then((r) => {
    if (r.ok && (url.origin === location.origin || url.hostname.endsWith("jsdelivr.net") || url.hostname.endsWith("gstatic.com") || url.hostname.endsWith("googleapis.com"))) {
      const copy = r.clone(); caches.open(SHELL).then((c) => c.put(e.request, copy));
    }
    return r;
  })));
});
