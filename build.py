# 아티팩트 소스 → 깃허브 페이지용 정식 웹 패키지로 빌드
# (viewport 메타 · PWA 매니페스트 · 서비스워커 · 아이콘)
import io, os, re, zlib, struct, hashlib

SRC = r"C:\Users\ujuda\Downloads\cabinet-drawing.html"
OUT = r"C:\Users\ujuda\Downloads\함도면-웹배포"
os.makedirs(OUT, exist_ok=True)

body = io.open(SRC, encoding="utf-8").read()
ver = hashlib.sha1(body.encode("utf-8")).hexdigest()[:8]

# ── 아이콘 (PNG 직접 생성) ────────────────────────────────────
def png(path, w, h, px):
    raw = b"".join(b"\x00" + bytes(px[y*w*3:(y+1)*w*3]) for y in range(h))
    def ch(t, d):
        c = t + d
        return struct.pack(">I", len(d)) + c + struct.pack(">I", zlib.crc32(c) & 0xffffffff)
    hdr = struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)
    io.open(path, "wb").write(b"\x89PNG\r\n\x1a\n" + ch(b"IHDR", hdr)
            + ch(b"IDAT", zlib.compress(raw, 9)) + ch(b"IEND", b""))

def icon(path, S):
    bg, ink, acc, gry = (0x14,0x20,0x2b), (0xff,0xff,0xff), (0xff,0x84,0x38), (0x9d,0xab,0xba)
    px = bytearray()
    for _ in range(S*S): px += bytes(bg)
    def put(x, y, c):
        if 0 <= x < S and 0 <= y < S:
            i = (y*S + x)*3
            px[i:i+3] = bytes(c)
    def rect(x0, y0, x1, y1, t, c):
        for y in range(y0, y1+1):
            for x in range(x0, x1+1):
                if x < x0+t or x > x1-t or y < y0+t or y > y1-t: put(x, y, c)
    u = S/512.0
    rect(int(96*u), int(80*u), int(416*u), int(432*u), max(1,int(9*u)), ink)     # 함 외곽
    rect(int(146*u), int(128*u), int(366*u), int(316*u), max(1,int(7*u)), acc)   # 도어
    rect(int(146*u), int(344*u), int(366*u), int(400*u), max(1,int(6*u)), gry)   # 풀박스
    png(path, S, S, px)

icon(os.path.join(OUT, "icon-180.png"), 180)
icon(os.path.join(OUT, "icon-512.png"), 512)

# ── 매니페스트 ────────────────────────────────────────────────
io.open(os.path.join(OUT, "manifest.webmanifest"), "w", encoding="utf-8").write("""{
  "name": "함 제작도면 작성기",
  "short_name": "함도면",
  "description": "전기·통신 함체 제작도면을 현장에서 바로 작성하고 공장에 전달합니다.",
  "lang": "ko",
  "start_url": "./",
  "scope": "./",
  "display": "standalone",
  "background_color": "#e7eaef",
  "theme_color": "#14202b",
  "icons": [
    { "src": "icon-180.png", "sizes": "180x180", "type": "image/png" },
    { "src": "icon-512.png", "sizes": "512x512", "type": "image/png", "purpose": "any maskable" }
  ]
}
""")

# ── 서비스워커 (오프라인) ──────────────────────────────────────
io.open(os.path.join(OUT, "sw.js"), "w", encoding="utf-8").write("""/* 함 제작도면 작성기 — 오프라인 캐시 */
const V = "hamdo-%s";
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
""" % ver)

# ── index.html (정식 문서 껍데기) ──────────────────────────────
head = """<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<!-- 모바일에서 실제 화면 폭으로 그리게 한다. 이게 없으면 980px 로 가정하고 축소되어 글씨가 아주 작아진다. -->
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="theme-color" content="#14202b">
<meta name="description" content="전기·통신 함체 제작도면을 현장에서 바로 작성하고 공장에 전달합니다.">
<meta name="format-detection" content="telephone=no">
<meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta name="apple-mobile-web-app-title" content="함도면">
<link rel="manifest" href="manifest.webmanifest">
<link rel="apple-touch-icon" href="icon-180.png">
<link rel="icon" href="icon-512.png" sizes="512x512" type="image/png">
<style>
  :root{color-scheme:light dark}
  html,body{margin:0;padding:0}
  img{max-width:100%}
  [hidden]{display:none!important}
</style>
</head>
<body>
"""
tail = """
<script>
/* 오프라인 사용 — https 로 서비스될 때만 등록 */
if ("serviceWorker" in navigator && (location.protocol === "https:" || location.hostname === "localhost")) {
  window.addEventListener("load", function () {
    navigator.serviceWorker.register("./sw.js").catch(function () {});
  });
}
</script>
</body>
</html>
"""
io.open(os.path.join(OUT, "index.html"), "w", encoding="utf-8").write(head + body + tail)

for f in sorted(os.listdir(OUT)):
    print("  %-26s %8d bytes" % (f, os.path.getsize(os.path.join(OUT, f))))
print("\n빌드 버전: %s" % ver)
