/* 함 제작도면 작성기 — 오프라인 캐시 */
const V = "hamdo-d12b4a20";
const CORE = ["./", "./index.html", "./manifest.webmanifest", "./icon-180.png", "./icon-512.png"];
const EXT = [
  "https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.umd.min.js",
  "https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600&family=IBM+Plex+Sans+KR:wght@400;500;600;700&display=swap"
];
self.addEventListener("install", e => {
  e.waitUntil((async () => {
    const c = await caches.open(V);
    await c.addAll(CORE).catch(() => {});
    await Promise.all(EXT.map(u =>
      fetch(u, { mode: "no-cors" }).then(r => c.put(u, r)).catch(() => {})));
    self.skipWaiting();
  })());
});
self.addEventListener("activate", e => {
  e.waitUntil((async () => {
    const ks = await caches.keys();
    await Promise.all(ks.filter(k => k !== V).map(k => caches.delete(k)));
    self.clients.claim();
  })());
});
self.addEventListener("fetch", e => {
  const req = e.request;
  if (req.method !== "GET") return;
  /* 화면(HTML)은 네트워크 먼저 — 수정본이 바로 반영되게 */
  if (req.mode === "navigate") {
    e.respondWith(fetch(req).then(r => {
      caches.open(V).then(c => c.put("./index.html", r.clone()));
      return r;
    }).catch(() => caches.match("./index.html")));
    return;
  }
  /* 나머지는 캐시 먼저 — 오프라인에서 바로 뜨게 */
  e.respondWith(caches.match(req).then(hit => hit || fetch(req).then(r => {
    if (r && (r.ok || r.type === "opaque")) {
      const cp = r.clone();
      caches.open(V).then(c => c.put(req, cp));
    }
    return r;
  }).catch(() => hit)));
});
