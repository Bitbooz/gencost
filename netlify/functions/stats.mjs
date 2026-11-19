// GenCost's private dashboard: what the counter (netlify/edge-functions/count.js) saw.
// Open https://getgencost.com/api/stats?key=YOUR-KEY  (add &days=30 for a month, &format=json for data).
// Only the SHA-256 fingerprint of the key is in this public code, never the key itself.
import { getStore } from "@netlify/blobs";

const KEY_SHA256 = "7645ccca618d5385e7ad81f66763f780d7c9054f09900adaabcdf174cf8731b6";
const KEEP_DAYS = 90;
const LANGS = { es: "Spanish", pt: "Portuguese", de: "German", fr: "French", ar: "Arabic", he: "Hebrew", it: "Italian",
  ja: "Japanese", ru: "Russian", "zh-tw": "Chinese (Traditional)", ko: "Korean", id: "Indonesian", tr: "Turkish",
  hi: "Hindi", vi: "Vietnamese", pl: "Polish", uk: "Ukrainian", zh: "Chinese (Simplified)", no: "Norwegian", sv: "Swedish",
  da: "Danish", fi: "Finnish", nl: "Dutch", th: "Thai", tl: "Filipino", bn: "Bengali" };
const langOf = (page) => LANGS[(page.split("/")[1] || "").toLowerCase()] || "English";

async function sha256(text) {
  const d = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(text));
  return [...new Uint8Array(d)].map((b) => b.toString(16).padStart(2, "0")).join("");
}
const esc = (s) => String(s).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" })[c]);
const label = (s) => s.replace(/_/g, " ");
const count = (map, k) => map.set(k, (map.get(k) || 0) + 1);
const top = (map, n = 8) => [...map.entries()].sort((a, b) => b[1] - a[1]).slice(0, n);

export default async (req) => {
  const url = new URL(req.url);
  if ((await sha256(url.searchParams.get("key") || "")) !== KEY_SHA256)
    return new Response("Not found", { status: 404, headers: { "X-Robots-Tag": "noindex" } });
  const days = Math.min(Math.max(parseInt(url.searchParams.get("days") || "7", 10) || 7, 1), 60);
  const store = getStore("stats");
  const today = new Date();
  const rows = [];
  const total = { ai: new Map(), src: new Map(), aiPages: new Map(), pages: new Map(), mcp: new Map(), aiLang: new Map(), lang: new Map() };
  for (let i = 0; i < days; i++) {
    const day = new Date(today.getTime() - i * 86400000).toISOString().slice(0, 10);
    const { blobs } = await store.list({ prefix: day + "/" });
    const r = { day, people: 0, ai: 0, mcp: 0 };
    for (const b of blobs) {
      const [kind, who, path] = b.key.slice(11).split("|");
      const page = decodeURIComponent(path || "");
      if (kind === "person") { r.people++; count(total.src, label(who)); count(total.pages, page); count(total.lang, langOf(page)); }
      else if (kind === "ai") { r.ai++; count(total.ai, label(who)); count(total.aiPages, page); count(total.aiLang, langOf(page)); }
      else if (kind === "mcp") { r.mcp++; count(total.mcp, label(who)); }
    }
    rows.push(r);
  }
  // tidy up: forget days older than KEEP_DAYS (a few hundred keys per visit to this page at most)
  try {
    const old = new Date(today.getTime() - KEEP_DAYS * 86400000).toISOString().slice(0, 7);
    const { blobs } = await store.list({ prefix: old });
    await Promise.all(blobs.slice(0, 300).map((b) => store.delete(b.key)));
  } catch (_) {}
  const data = { days: rows, ai_by_assistant: top(total.ai, 20), people_by_source: top(total.src, 20),
                 pages_read_by_ai: top(total.aiPages, 15), ai_by_language: top(total.aiLang, 21), people_by_language: top(total.lang, 21), pages_people_landed_on: top(total.pages, 15), mcp_tools: top(total.mcp, 10) };
  if (url.searchParams.get("format") === "json")
    return Response.json(data, { headers: { "Cache-Control": "no-store", "X-Robots-Tag": "noindex" } });
  const list = (pairs) => pairs.length ? "<table>" + pairs.map(([k, v]) => `<tr><td>${esc(k || "/")}</td><td class=n>${v}</td></tr>`).join("") + "</table>" : "<p class=m>Nothing yet.</p>";
  const sum = (k) => rows.reduce((a, r) => a + r[k], 0);
  const html = `<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex,nofollow"><title>GenCost counter</title>
<style>body{font:16px/1.45 system-ui,sans-serif;background:#07070c;color:#e8e8f0;margin:0;padding:18px;max-width:760px}
h1{font-size:1.4rem;margin:0 0 4px}h2{font-size:1.05rem;margin:22px 0 6px;color:#9ad}table{border-collapse:collapse;width:100%}
td,th{padding:6px 8px;border-bottom:1px solid #222;text-align:left}td.n,th.n{text-align:right}.m{opacity:.7}
.big{display:flex;gap:10px;flex-wrap:wrap}.big div{background:#12121c;border:1px solid #23233a;border-radius:12px;padding:10px 14px;min-width:120px}
.big b{display:block;font-size:1.6rem}</style></head><body>
<h1>GenCost counter</h1><p class=m>Last ${days} days · counted on Netlify, nothing personal stored · <a style="color:#9ad" href="?key=${esc(url.searchParams.get("key"))}&days=${days === 7 ? 30 : 7}">show ${days === 7 ? 30 : 7} days</a></p>
<div class=big><div><b>${sum("people")}</b>visits by people</div><div><b>${sum("ai")}</b>pages read by AI and search bots</div><div><b>${sum("mcp")}</b>questions to the GenCost AI connector</div></div>
<h2>Day by day</h2><table><tr><th>Day</th><th class=n>People</th><th class=n>AI and bots</th><th class=n>AI connector</th></tr>
${rows.map((r) => `<tr><td style="white-space:nowrap">${new Date(r.day + "T12:00:00Z").toLocaleDateString("en-GB", { weekday: "short", day: "numeric", month: "short" })}</td><td class=n>${r.people}</td><td class=n>${r.ai}</td><td class=n>${r.mcp}</td></tr>`).join("")}</table>
<h2>Which AI read GenCost</h2>${list(data.ai_by_assistant)}
<h2>Where people came from</h2>${list(data.people_by_source)}
<h2>Language: pages read by AI</h2>${list(data.ai_by_language)}
<h2>Language: visits by people</h2>${list(data.people_by_language)}
<h2>Pages AI read most</h2>${list(data.pages_read_by_ai)}
<h2>Pages people landed on</h2>${list(data.pages_people_landed_on)}
<h2>AI connector: tools asked</h2>${list(data.mcp_tools)}
<p class=m>"A user asked" means an assistant fetched the page while answering someone. Counting started 2026-11-15.</p></body></html>`;
  return new Response(html, { headers: { "Content-Type": "text/html; charset=utf-8", "Cache-Control": "no-store", "X-Robots-Tag": "noindex" } });
};

export const config = { path: "/api/stats" };
