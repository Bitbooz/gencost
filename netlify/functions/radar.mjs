// The live AI radar's feed: the AI visits of the last 20 minutes, for /radar.html.
// Public and anonymous on purpose: it only holds which AI read which GenCost page (or which tool of the AI
// connector was asked) and when. Nothing about people. The CDN keeps each answer for 15 seconds, so many
// viewers cost about one function run per 15 seconds.
import { getStore } from "@netlify/blobs";

const MINUTES = 20;
const MAX = 80;
const LANGS = ["es", "pt", "de", "fr", "ar", "he", "it", "ja", "ru", "zh-tw", "ko", "id", "tr", "hi", "vi", "pl", "uk", "zh", "no", "sv", "da", "fi", "nl", "th", "tl", "bn"];

// "AI answers today": every live read while answering someone (ChatGPT-User, Claude-User, ...) plus every
// question to the GenCost AI connector, since midnight UTC. Counted from the visitor counter's keys and kept
// for 5 minutes, so it costs one extra list now and then.
let today = { day: "", n: 0, at: 0 };
async function answersToday(now) {
  const day = new Date(now).toISOString().slice(0, 10);
  if (today.day === day && now - today.at < 300000) return today.n;
  const stats = getStore("stats");
  const [ai, mcp] = await Promise.all([stats.list({ prefix: day + "/ai|" }), stats.list({ prefix: day + "/mcp|" })]);
  const n = ai.blobs.filter((b) => /a.user.asked/i.test(b.key.split("|")[1] || "")).length + mcp.blobs.length;
  today = { day, n, at: now };
  return n;
}

export default async () => {
  const store = getStore("radar");
  const now = Date.now();
  const prefixes = [];
  for (let i = 0; i < MINUTES; i++) prefixes.push(new Date(now - i * 60000).toISOString().slice(0, 16) + "/");
  const lists = await Promise.all(prefixes.map((p) => store.list({ prefix: p }).catch(() => ({ blobs: [] }))));
  const events = [];
  for (const { blobs } of lists) {
    for (const b of blobs) {
      const [who, path, stamp] = b.key.slice(17).split("|");
      const t = parseInt((stamp || "").slice(0, -3), 36);
      if (!t) continue;
      const page = decodeURIComponent(path || "");
      const seg = (page.split("/")[1] || "").toLowerCase();
      const connector = who === "GenCost_AI_connector";
      events.push({ t, who: who.replace(/_/g, " "), page: connector ? "" : page, tool: connector ? page : "",
                    lang: connector ? "" : (LANGS.includes(seg) ? seg : "en"), asked: /a user asked/i.test(who.replace(/_/g, " ")) || connector });
    }
  }
  events.sort((a, b) => b.t - a.t);
  // tidy up: now and then, delete the keys of two days ago (each run clears one minute)
  if (Math.random() < 0.2) {
    const old = new Date(now - 2 * 86400000).toISOString().slice(0, 16) + "/";
    store.list({ prefix: old }).then(({ blobs }) => Promise.all(blobs.map((b) => store.delete(b.key)))).catch(() => {});
  }
  const answers = await answersToday(now).catch(() => null);
  return new Response(JSON.stringify({ now, minutes: MINUTES, total: events.length, answers_today: answers, events: events.slice(0, MAX) }), {
    headers: {
      "Content-Type": "application/json; charset=utf-8",
      "Cache-Control": "public, max-age=0, must-revalidate",
      "Netlify-CDN-Cache-Control": "public, durable, s-maxage=15, stale-while-revalidate=30",
      "Access-Control-Allow-Origin": "*",
      "X-Robots-Tag": "noindex",
    },
  });
};

export const config = { path: "/api/radar" };
