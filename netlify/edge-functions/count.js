// GenCost's own counter (2026-11-15). Counts, without anything personal:
//  - AI assistants and AI crawlers that fetch a page (ChatGPT, Perplexity, Claude, Copilot/Bing ...)
//  - people who open a page (no IP, no cookie, no user agent kept), and where they came from
// Each visit is stored as one tiny key in Netlify Blobs (private: no public URL) and the page is
// served exactly as before. The dashboard is /api/stats (netlify/functions/stats.mjs).
import { getStore } from "@netlify/blobs";

const AI = [
  // [text in the user agent, name shown in the report]
  ["ChatGPT-User", "ChatGPT (a user asked)"],
  ["OAI-SearchBot", "ChatGPT search"],
  ["GPTBot", "OpenAI crawler"],
  ["Perplexity-User", "Perplexity (a user asked)"],
  ["PerplexityBot", "Perplexity"],
  ["Claude-User", "Claude (a user asked)"],
  ["Claude-SearchBot", "Claude search"],
  ["ClaudeBot", "Anthropic crawler"],
  ["MistralAI-User", "Mistral (a user asked)"],
  ["DuckAssistBot", "DuckDuckGo AI"],
  ["meta-externalfetcher", "Meta AI (a user asked)"],
  ["Meta-ExternalAgent", "Meta AI crawler"],
  ["Google-CloudVertexBot", "Google Vertex AI"],
  ["Amazonbot", "Amazon"],
  ["Applebot", "Apple"],
  ["YouBot", "You.com"],
  ["cohere-ai", "Cohere"],
  ["Bytespider", "ByteDance"],
  ["CCBot", "Common Crawl"],
  ["bingbot", "Bing (also feeds Copilot)"],
  ["Googlebot", "Google (also feeds AI Overviews)"],
];
const OTHER_BOT = /bot|crawl|spider|slurp|preview|monitor|headless|python|curl|wget|httpclient|go-http|java\/|axios|node-fetch/i;
const REF = [
  [/chatgpt\.com|openai\.com/i, "ChatGPT"], [/perplexity\./i, "Perplexity"], [/gemini\.google|bard\.google/i, "Gemini"],
  [/copilot\.microsoft|bing\.com/i, "Bing/Copilot"], [/claude\.ai/i, "Claude"], [/google\./i, "Google"],
  [/facebook\.com|fb\.com|instagram\.com/i, "Facebook"], [/bsky\.app/i, "Bluesky"], [/dev\.to/i, "dev.to"],
  [/youtube\.com|youtu\.be/i, "YouTube"], [/huggingface\.co/i, "Hugging Face"], [/duckduckgo\./i, "DuckDuckGo"],
  [/getgencost\.com/i, ""],
];
const clean = (s) => String(s).replace(/[|/\s]+/g, "_").slice(0, 60);

export default async (request, context) => {
  const response = await context.next();
  try {
    if (request.method !== "GET") return response;
    const url = new URL(request.url);
    const path = url.pathname;
    const ua = request.headers.get("user-agent") || "";
    const ai = AI.find(([t]) => ua.toLowerCase().includes(t.toLowerCase()));
    const isPage = path.endsWith("/") || path.endsWith(".html") || !path.split("/").pop().includes(".");
    let kind, who;
    if (ai) {
      kind = "ai"; who = ai[1];
    } else if (isPage && !OTHER_BOT.test(ua) && (request.headers.get("accept") || "").includes("text/html")) {
      kind = "person";
      const ref = request.headers.get("referer") || "";
      const hit = ref ? REF.find(([rx]) => rx.test(ref)) : null;
      who = !ref ? "Direct" : hit ? hit[1] : "Other site";
      if (who === "") return response;          // moving between GenCost pages: not a new visit
      if (url.searchParams.get("source") === "app" || url.searchParams.get("source") === "android") who = "GenCost app";
    } else {
      return response;
    }
    const day = new Date().toISOString().slice(0, 10);
    const key = `${day}/${kind}|${clean(who)}|${encodeURIComponent(path).slice(0, 180)}|${Date.now().toString(36)}${Math.random().toString(36).slice(2, 6)}`;
    const save = getStore("stats").set(key, "1");
    if (context.waitUntil) context.waitUntil(save.catch(() => {}));
    else await save.catch(() => {});
  } catch (_) { /* counting must never break the site */ }
  return response;
};

export const config = {
  path: "/*",
  excludedPath: ["/assets/*", "/data/*", "/api/*", "/mcp", "/.netlify/*", "/*.png", "/*.jpg", "/*.ico", "/*.css", "/*.js", "/*.json", "/*.webmanifest", "/*.mp4"],
};
