/* GenCost app helper (service worker).
   Rule: always ask the network first, so prices are never older than the site.
   The saved copy is only used when the phone is offline. Only GenCost's own
   files are touched; analytics and fonts go straight to the network. */
const CACHE = "gencost-v1";
const START = ["/", "/clip.html", "/assets/gencost.css", "/assets/gencost.js", "/assets/icon-192.png"];

self.addEventListener("install", (e) => {
  e.waitUntil(caches.open(CACHE).then((c) => c.addAll(START)).catch(() => {}).then(() => self.skipWaiting()));
});

self.addEventListener("activate", (e) => {
  e.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener("fetch", (e) => {
  const req = e.request;
  if (req.method !== "GET") return;
  const url = new URL(req.url);
  if (url.origin !== self.location.origin) return;
  e.respondWith(
    fetch(req)
      .then((res) => {
        if (res && res.ok && res.type === "basic") {
          const copy = res.clone();
          caches.open(CACHE).then((c) => c.put(req, copy)).catch(() => {});
        }
        return res;
      })
      .catch(() =>
        caches.match(req, { ignoreSearch: req.mode === "navigate" }).then((hit) =>
          hit || (req.mode === "navigate" ? caches.match("/") : Response.error())
        )
      )
  );
});
