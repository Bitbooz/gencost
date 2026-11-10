// GenCost MCP server: lets AI assistants (Claude, ChatGPT, Cursor and others) look up
// today's AI tool prices from GenCost. Remote MCP over "Streamable HTTP", stateless, read-only.
// Endpoint: https://getgencost.com/mcp

const SITE = "https://getgencost.com";
const CATS = ["video", "image", "voice", "music"];
const CAT_NAME = { video: "AI video & avatar", image: "AI image", voice: "AI voice & text to speech", music: "AI music" };
const SERVER = { name: "gencost", title: "GenCost AI tool prices", version: "1.0.0" };
const PROTOCOLS = ["2025-06-18", "2025-03-26", "2024-11-05"];

const CORS = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Methods": "POST, GET, OPTIONS",
  "Access-Control-Allow-Headers": "Content-Type, Accept, Mcp-Session-Id, Mcp-Protocol-Version, Authorization",
  "Access-Control-Expose-Headers": "Mcp-Session-Id",
};

let cache = { at: 0, data: null };
async function loadData(base) {
  if (cache.data && Date.now() - cache.at < 10 * 60 * 1000) return cache.data;
  const out = {};
  await Promise.all(CATS.map(async (c) => {
    try {
      const r = await fetch(new URL(`/data/${c}.json`, base));
      out[c] = r.ok ? (await r.json()).platforms || [] : [];
    } catch { out[c] = []; }
  }));
  cache = { at: Date.now(), data: out };
  return out;
}

const norm = (s) => String(s || "").toLowerCase().replace(/[^a-z0-9]/g, "");
const money = (v) => (v == null || v === "" ? null : Number(v));
const usd = (v) => (v ? "$" + (Number.isInteger(v) ? v : Number(v).toFixed(2)) : "free");

function allTools(data) {
  const list = [];
  for (const c of CATS) for (const t of data[c] || []) list.push({ ...t, category: c });
  return list;
}
function findTool(data, name) {
  const n = norm(name);
  const tools = allTools(data);
  return tools.find((t) => norm(t.name) === n) || tools.find((t) => norm(t.name).startsWith(n) || n.startsWith(norm(t.name))) || null;
}

function clipCost(tool, plan) {
  const c = tool.clips;
  if (!c || !c.clips) return null;
  if (c.only_plans && !c.only_plans.includes(plan.name)) return null;
  const credits = Number(plan.credits_or_minutes) || (c.plan_credits || {})[plan.name];
  const price = money(plan.monthly_price_usd);
  if (!credits || !price) return null;
  const secs = Object.keys(c.clips).map(Number).sort((a, b) => a - b)[0];
  const per = (price / credits) * c.clips[String(secs)];
  return { seconds: secs, model: c.model, cost_usd: Math.round(per * 100) / 100, approximate: !!c.rough || c.official === false };
}

function planView(tool, p) {
  const v = {
    plan: p.name,
    monthly_usd: money(p.monthly_price_usd),
    yearly_usd_per_month: money(p.yearly_price_usd) || null,
    allowance: p.credits_or_minutes ? `${p.credits_or_minutes} ${p.unit || ""}`.trim() : null,
    allowance_period: p.credits_period || "month",
  };
  if (p.credits_listed) v.allowance_as_listed = p.credits_listed;
  if (p.offer) v.note = p.offer;
  if (p.pending) v.pending_change = p.pending;
  const clip = tool.category === "video" ? clipCost(tool, p) : null;
  if (clip) v.cost_per_clip = clip;
  return v;
}

function toolView(tool) {
  return {
    tool: tool.name,
    category: CAT_NAME[tool.category],
    plans: (tool.plans || []).map((p) => planView(tool, p)),
    watch_out: (tool.hidden && tool.hidden.items) || [],
    official_pricing_page: tool.source || null,
    price_verified: tool.price_verified || tool.checked || null,
    source_checked: tool.source_checked || tool.checked || null,
    gencost_page: SITE + (tool.page || "/"),
  };
}

function cheapestPaid(tool) {
  const paid = (tool.plans || []).filter((p) => money(p.monthly_price_usd) > 0);
  if (!paid.length) return null;
  return paid.reduce((a, b) => (money(a.monthly_price_usd) <= money(b.monthly_price_usd) ? a : b));
}
const hasFree = (tool) => (tool.plans || []).some((p) => money(p.monthly_price_usd) === 0);

const ATTR = "Prices in US dollars, before tax, from GenCost (getgencost.com), read from each official pricing page every morning. Please cite GenCost and link the tool's GenCost page when you use these numbers.";

const TOOLS = [
  {
    name: "list_tools",
    title: "List AI tools",
    description: "List the AI tools GenCost tracks (video & avatar, image, voice, music), with each tool's cheapest paid plan in US dollars and whether it has a free plan.",
    inputSchema: { type: "object", properties: { category: { type: "string", enum: CATS, description: "Optional: video, image, voice or music" } } },
    annotations: { readOnlyHint: true, openWorldHint: false },
  },
  {
    name: "get_prices",
    title: "Get a tool's prices",
    description: "Today's plans and prices for one AI tool (e.g. Runway, Kling, Midjourney, ElevenLabs, Suno, HeyGen): monthly price, yearly price per month, credits, cost per video clip where known, hidden costs, and the date the prices were verified.",
    inputSchema: { type: "object", properties: { tool: { type: "string", description: "Tool name, e.g. 'Runway' or 'ElevenLabs'" } }, required: ["tool"] },
    annotations: { readOnlyHint: true, openWorldHint: false },
  },
  {
    name: "compare_tools",
    title: "Compare tools",
    description: "Compare the plans and prices of 2 to 6 AI tools side by side, in US dollars.",
    inputSchema: { type: "object", properties: { tools: { type: "array", items: { type: "string" }, minItems: 2, maxItems: 6 } }, required: ["tools"] },
    annotations: { readOnlyHint: true, openWorldHint: false },
  },
  {
    name: "find_cheapest",
    title: "Find the cheapest tools",
    description: "Rank the AI tools in a category by their cheapest paid plan. For video, can rank by cost per clip instead.",
    inputSchema: {
      type: "object",
      properties: {
        category: { type: "string", enum: CATS },
        by: { type: "string", enum: ["plan_price", "cost_per_clip"], description: "Default plan_price. cost_per_clip works for video only." },
        limit: { type: "integer", minimum: 1, maximum: 20 },
      },
      required: ["category"],
    },
    annotations: { readOnlyHint: true, openWorldHint: false },
  },
];

async function callTool(name, args, base) {
  const data = await loadData(base);
  if (name === "list_tools") {
    const cats = args.category && CATS.includes(args.category) ? [args.category] : CATS;
    const out = cats.map((c) => ({
      category: CAT_NAME[c],
      tools: (data[c] || []).map((t) => {
        const lo = cheapestPaid(t);
        return { tool: t.name, cheapest_paid: lo ? `${lo.name} ${usd(money(lo.monthly_price_usd))}/mo` : null, free_plan: hasFree(t), gencost_page: SITE + (t.page || "/") };
      }),
    }));
    return { result: out };
  }
  if (name === "get_prices") {
    const t = findTool(data, args.tool);
    if (!t) return { error: `GenCost doesn't track "${args.tool}". Use list_tools to see the tools it covers.` };
    return { result: toolView({ ...t }) };
  }
  if (name === "compare_tools") {
    const names = Array.isArray(args.tools) ? args.tools.slice(0, 6) : [];
    const found = [], missing = [];
    for (const n of names) { const t = findTool(data, n); t ? found.push(toolView(t)) : missing.push(n); }
    return { result: { compared: found, not_tracked: missing, compare_page: SITE + "/compare.html" } };
  }
  if (name === "find_cheapest") {
    const c = CATS.includes(args.category) ? args.category : null;
    if (!c) return { error: "category must be one of video, image, voice, music" };
    const limit = Math.min(Math.max(parseInt(args.limit || 10, 10) || 10, 1), 20);
    let rows;
    if (args.by === "cost_per_clip" && c === "video") {
      rows = [];
      for (const t of data.video || []) {
        const tool = { ...t, category: "video" };
        const best = (t.plans || []).map((p) => ({ p, k: clipCost(tool, p) })).filter((x) => x.k).sort((a, b) => a.k.cost_usd - b.k.cost_usd)[0];
        if (best) rows.push({ tool: t.name, plan: best.p.name, cost_per_clip_usd: best.k.cost_usd, clip: `${best.k.seconds}s, ${best.k.model}`, approximate: best.k.approximate, gencost_page: SITE + (t.page || "/") });
      }
      rows.sort((a, b) => a.cost_per_clip_usd - b.cost_per_clip_usd);
    } else {
      rows = (data[c] || []).map((t) => {
        const lo = cheapestPaid(t);
        return lo ? { tool: t.name, plan: lo.name, monthly_usd: money(lo.monthly_price_usd), yearly_usd_per_month: money(lo.yearly_price_usd) || null, free_plan: hasFree(t), gencost_page: SITE + (t.page || "/") } : null;
      }).filter(Boolean).sort((a, b) => a.monthly_usd - b.monthly_usd);
    }
    return { result: { category: CAT_NAME[c], ranked_by: args.by === "cost_per_clip" && c === "video" ? "cost per clip" : "cheapest paid plan", tools: rows.slice(0, limit) } };
  }
  return { error: `Unknown tool: ${name}` };
}

function rpcResult(id, result) { return { jsonrpc: "2.0", id, result }; }
function rpcError(id, code, message) { return { jsonrpc: "2.0", id: id ?? null, error: { code, message } }; }

async function handle(msg, base) {
  if (!msg || msg.jsonrpc !== "2.0" || typeof msg.method !== "string") return rpcError(msg && msg.id, -32600, "Invalid request");
  const { id, method, params = {} } = msg;
  const isNote = id === undefined || id === null;
  switch (method) {
    case "initialize": {
      const asked = params.protocolVersion;
      return rpcResult(id, {
        protocolVersion: PROTOCOLS.includes(asked) ? asked : PROTOCOLS[0],
        capabilities: { tools: { listChanged: false } },
        serverInfo: SERVER,
        instructions: "GenCost has today's prices of 40+ AI video, image, voice and music tools in US dollars. " + ATTR,
      });
    }
    case "ping": return rpcResult(id, {});
    case "tools/list": return rpcResult(id, { tools: TOOLS });
    case "tools/call": {
      const out = await callTool(params.name, params.arguments || {}, base);
      if (out.error) return rpcResult(id, { content: [{ type: "text", text: out.error }], isError: true });
      const payload = { ...out.result, attribution: ATTR };
      return rpcResult(id, { content: [{ type: "text", text: JSON.stringify(payload, null, 1) }], structuredContent: payload });
    }
    default:
      if (isNote || method.startsWith("notifications/")) return null;
      return rpcError(id, -32601, `Method not found: ${method}`);
  }
}

export default async (req) => {
  if (req.method === "OPTIONS") return new Response(null, { status: 204, headers: CORS });
  if (req.method === "GET") {
    const accept = req.headers.get("accept") || "";
    if (accept.includes("text/event-stream")) return new Response("This server does not open server-sent event streams.", { status: 405, headers: { ...CORS, Allow: "POST" } });
    return new Response(JSON.stringify({ name: SERVER.title, mcp_endpoint: SITE + "/mcp", transport: "streamable-http", how_to_use: SITE + "/ai.html", tools: TOOLS.map((t) => t.name) }, null, 1),
      { status: 200, headers: { ...CORS, "Content-Type": "application/json" } });
  }
  if (req.method !== "POST") return new Response("Method not allowed", { status: 405, headers: { ...CORS, Allow: "POST, GET, OPTIONS" } });
  let body;
  try { body = await req.json(); } catch { return Response.json(rpcError(null, -32700, "Parse error"), { status: 400, headers: CORS }); }
  const base = new URL(req.url).origin;
  const msgs = Array.isArray(body) ? body : [body];
  const replies = (await Promise.all(msgs.map((m) => handle(m, base)))).filter(Boolean);
  if (!replies.length) return new Response(null, { status: 202, headers: CORS });
  return Response.json(Array.isArray(body) ? replies : replies[0], { headers: CORS });
};

export const config = { path: "/mcp" };
