/* =========================================================
   GenCost shared script
   - mobile menu, active nav link, scroll reveal
   - loads prices from /data/<category>.json and fills any of
     these elements if the page has them:
       #budgetSeg + #budgetRows  budget demo card
       #board                    leaderboard (data-limit="8")
       #content                  plan cards for every tool
       #normTable                small "in dollars" table
       #statTools #statPlans #statCheapest #heroCount #bestValue
       .js-updated               last-updated timestamp
   ========================================================= */
(function () {
  const GC = (window.GenCost = window.GenCost || {});

  /* ---------- helpers ---------- */
  const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const num = (v) => (typeof v === "number" && isFinite(v) ? v : null);
  GC.esc = esc;
  GC.money = (v) => "$" + (Number.isInteger(v) ? v : v.toFixed(2));
  GC.amount = (v) => (num(v) !== null ? v.toLocaleString("en-US") : String(v ?? "").trim());
  GC.price = (p) => num(p.monthly_price_usd) ?? 0;

  /* Cost estimate per category. Kept identical to the old pages:
     video assumes 1 credit = 1 second, voice per 1k characters, music per unit. */
  GC.estimate = function (plan, category) {
    const price = GC.price(plan);
    const credits = num(plan.credits_or_minutes);
    if (!price || !credits || credits <= 0) return "";
    const unit = String(plan.unit || "").toLowerCase();
    if (category === "video") {
      const cps = price / credits;
      return `est. 5s $${(cps * 5).toFixed(2)} · 10s $${(cps * 10).toFixed(2)} · 30s $${(cps * 30).toFixed(2)}`;
    }
    if (category === "voice") {
      if (unit.includes("character")) return `~$${((price / credits) * 1000).toFixed(3)} / 1k chars`;
      if (unit.includes("minute")) return `~$${(price / credits).toFixed(2)} / minute`;
      if (unit.includes("hour")) return `~$${(price / credits).toFixed(2)} / hour`;
      return "";
    }
    if (category === "music") {
      const per = price / credits;
      if (per < 0.01) return "";
      const label = unit.replace(/s$/, "") || "unit";
      return `~$${per.toFixed(2)} / ${label}`;
    }
    return "";
  };

  GC.load = function (category) {
    return fetch(`/data/${category}.json`, { cache: "no-cache" }).then((r) => {
      if (!r.ok) throw new Error("HTTP " + r.status);
      return r.json();
    });
  };

  /* ---------- page chrome ---------- */
  function initChrome() {
    const menuBtn = document.getElementById("menuBtn");
    const navLinks = document.getElementById("navLinks");
    if (menuBtn && navLinks) {
      const setOpen = (open) => {
        navLinks.classList.toggle("open", open);
        menuBtn.setAttribute("aria-expanded", open);
        menuBtn.textContent = open ? "✕" : "☰";
      };
      menuBtn.addEventListener("click", () => setOpen(!navLinks.classList.contains("open")));
      navLinks.addEventListener("click", (e) => { if (e.target.tagName === "A") setOpen(false); });
    }
    // Highlight the current section in the nav
    const path = location.pathname.replace(/index\.html$/, "");
    document.querySelectorAll(".nav-links a").forEach((a) => {
      const href = a.getAttribute("href") || "";
      const sections = (a.dataset.section || "").split(",").filter(Boolean);
      if (sections.some((s) => path.startsWith(s)) || href === path) a.classList.add("active");
    });
    // Animated waveforms on explore cards
    document.querySelectorAll(".wave[data-k]").forEach((el) => {
      const k = Number(el.dataset.k) || 0;
      el.innerHTML = Array.from({ length: 28 }, (_, i) => `<i style="animation-delay:${((i * 97 + k * 31) % 140) / 100}s"></i>`).join("");
    });
  }

  /* ---------- scroll reveal ---------- */
  const io = "IntersectionObserver" in window
    ? new IntersectionObserver((entries) => {
        entries.forEach((en) => {
          if (!en.isIntersecting) return;
          en.target.classList.add("in");
          en.target.querySelectorAll("[data-w]").forEach((b) => (b.style.width = b.dataset.w + "%"));
          io.unobserve(en.target);
        });
      }, { threshold: 0.08 })
    : null;
  GC.observe = function (root) {
    (root || document).querySelectorAll(".reveal:not(.in)").forEach((el) => {
      if (io) io.observe(el);
      else { el.classList.add("in"); el.querySelectorAll("[data-w]").forEach((b) => (b.style.width = b.dataset.w + "%")); }
    });
  };

  /* ---------- price rendering ---------- */
  GC.renderPrices = function (data) {
    const category = data.category;
    const platforms = data.platforms || [];
    const allPlans = [];
    platforms.forEach((pf) => (pf.plans || []).forEach((p) => allPlans.push({ tool: pf.name, page: pf.page, ...p })));
    const paid = allPlans.filter((p) => GC.price(p) > 0);
    const $ = (id) => document.getElementById(id);
    const set = (id, v) => { const el = $(id); if (el) el.textContent = v; };

    document.querySelectorAll(".js-updated").forEach((el) => (el.textContent = data.updated || ""));

    // Stats
    const cheapest = paid.reduce((a, b) => (!a || GC.price(b) < GC.price(a) ? b : a), null);
    set("heroCount", platforms.length);
    set("statTools", platforms.length);
    set("statPlans", allPlans.length);
    set("statCheapest", cheapest ? GC.money(GC.price(cheapest)) : "–");
    if ($("bestValue") && cheapest)
      $("bestValue").textContent = `Best value right now: ${cheapest.tool} ${cheapest.name} at ${GC.money(GC.price(cheapest))}/mo. Full details below.`;

    // Budget demo card
    const rowsEl = $("budgetRows");
    const seg = $("budgetSeg");
    if (rowsEl && seg) {
      const render = (budget) => {
        const fits = paid
          .filter((p) => GC.price(p) <= budget)
          .sort((a, b) => GC.price(b) - GC.price(a) || a.tool.localeCompare(b.tool))
          .slice(0, 5);
        if (!fits.length) {
          rowsEl.innerHTML = `<div class="row"><span class="name">No paid plans at this budget yet</span></div>`;
          return;
        }
        rowsEl.innerHTML = fits.map((p, i) => {
          const amt = GC.amount(p.credits_or_minutes);
          const meta = [amt && amt !== "0" ? `${amt} ${esc(p.unit || "")}` : "", p.offer ? esc(p.offer) : ""].filter(Boolean).join(" · ") || "See plan details";
          return `<a class="row" href="${esc(p.page)}" style="animation-delay:${i * 70}ms">
            <span class="name">${esc(p.tool)}<small>${esc(p.name)}</small></span>
            <span class="price">${GC.money(GC.price(p))}/mo</span>
            <span class="bar"><i data-bw="${Math.round((GC.price(p) / budget) * 100)}"></i></span>
            <span class="meta">${meta}</span></a>`;
        }).join("");
        requestAnimationFrame(() => requestAnimationFrame(() =>
          rowsEl.querySelectorAll("[data-bw]").forEach((b) => (b.style.width = b.dataset.bw + "%"))));
      };
      seg.addEventListener("click", (e) => {
        const btn = e.target.closest("button");
        if (!btn) return;
        seg.querySelectorAll("button").forEach((b) => b.classList.toggle("active", b === btn));
        render(Number(btn.dataset.b));
      });
      const active = seg.querySelector("button.active") || seg.querySelector("button");
      if (active) render(Number(active.dataset.b));
    }

    // Lowest paid plan per tool
    const entry = platforms.map((pf) => {
      const p = (pf.plans || []).filter((x) => GC.price(x) > 0).sort((a, b) => GC.price(a) - GC.price(b))[0];
      return p ? { tool: pf.name, page: pf.page, plan: p.name, price: GC.price(p) } : null;
    }).filter(Boolean).sort((a, b) => a.price - b.price);

    if ($("normTable"))
      $("normTable").innerHTML = entry.slice(0, 5)
        .map((e) => `<tr><td>${esc(e.tool)}<small>${esc(e.plan)}</small></td><td>${GC.money(e.price)}/mo</td></tr>`).join("");

    const board = $("board");
    if (board) {
      const limit = Number(board.dataset.limit) || entry.length;
      const top = entry.slice(0, limit);
      const maxP = Math.max(...top.map((e) => e.price), 1);
      board.innerHTML = top.map((e, i) => `
        <a class="board-row" href="${esc(e.page)}">
          <span class="rank">${String(i + 1).padStart(2, "0")}</span>
          <span class="board-name">${esc(e.tool)}<small>${esc(e.plan)}</small></span>
          <span class="board-bar"><i data-w="${Math.max(6, Math.round((e.price / maxP) * 100))}"></i></span>
          <span class="board-price">${GC.money(e.price)}</span>
        </a>`).join("");
      if (board.classList.contains("in")) board.querySelectorAll("[data-w]").forEach((b) => (b.style.width = b.dataset.w + "%"));
    }

    // Plan cards
    const content = $("content");
    if (content) {
      content.innerHTML = platforms.map((pf) => {
        const plans = (pf.plans || []).map((plan) => {
          const price = GC.price(plan);
          const amt = GC.amount(plan.credits_or_minutes);
          const credits = amt && amt !== "0" ? `${amt} ${esc(plan.unit || "")}` : esc(plan.unit && plan.unit !== "credits" ? plan.unit : "Limited");
          const est = GC.estimate(plan, category);
          const offer = plan.offer && !/^(none|n\/a|-)$/i.test(String(plan.offer).trim()) ? `<br><span class="offer">${esc(plan.offer)}</span>` : "";
          return `<div class="plan-row">
            <div class="plan-line"><b>${esc(plan.name)}</b><span class="pr ${price === 0 ? "free" : ""}">${price === 0 ? "Free" : GC.money(price) + "/mo"}</span></div>
            <div class="plan-sub">${credits}${est ? `<br><span class="cost">${est}</span>` : ""}${offer}</div>
          </div>`;
        }).join("");
        const source = pf.source ? ` · <a href="${esc(pf.source)}" target="_blank" rel="noopener">Source</a>` : "";
        return `<div class="plat reveal">
          <div class="plat-top"><a href="${esc(pf.page)}">${esc(pf.name)} →</a><span>Checked ${esc(pf.checked || data.updated || "")}${source}</span></div>
          ${plans}
        </div>`;
      }).join("");
    }
    GC.observe();
  };

  GC.start = function (category) {
    GC.load(category)
      .then(GC.renderPrices)
      .catch(() => {
        const c = document.getElementById("content");
        if (c) c.innerHTML = `<p class="loading">Prices could not be loaded right now. Please refresh the page.</p>`;
      });
  };

  /* ---------- sample packages (homepage, order page) ---------- */
  GC.loadPackages = function (targetId, limit) {
    const grid = document.getElementById(targetId);
    if (!grid) return;
    fetch("/pages/samples/packages.json", { cache: "no-cache" })
      .then((r) => r.json())
      .then((packages) => {
        if (!Array.isArray(packages) || !packages.length) return;
        grid.innerHTML = packages.slice(0, limit || packages.length).map((p) => `
          <a class="pkg" href="${esc(p.url)}">
            <div class="k">SAMPLE PACKAGE</div>
            <div class="t">${esc(p.title)}</div>
            <div class="d">${esc(p.description || "")}</div>
          </a>`).join("");
      })
      .catch(() => {});
  };

  /* ---------- live prices on single tool pages ----------
     <div class="live-plans" data-cat="video" data-tool="Kling AI"> ...old static plans as fallback... </div> */
  GC.renderLive = function () {
    const boxes = document.querySelectorAll(".live-plans[data-cat][data-tool]");
    const cache = {};
    boxes.forEach((box) => {
      const cat = box.dataset.cat;
      cache[cat] = cache[cat] || GC.load(cat);
      cache[cat].then((data) => {
        const pf = (data.platforms || []).find((p) => p.name === box.dataset.tool);
        if (!pf || !(pf.plans || []).length) return; // keep the old list
        const rows = pf.plans.map((plan) => {
          const price = GC.price(plan);
          const amt = GC.amount(plan.credits_or_minutes);
          const credits = amt && amt !== "0" ? `${amt} ${esc(plan.unit || "")}` : esc(plan.unit || "");
          const est = GC.estimate(plan, cat);
          const offer = plan.offer && !/^(none|n\/a|-)$/i.test(String(plan.offer).trim()) ? ` · <span class="offer">${esc(plan.offer)}</span>` : "";
          return `<div class="plan-row">
            <div class="plan-line"><b>${esc(plan.name)}</b><span class="pr ${price === 0 ? "free" : ""}">${price === 0 ? "Free" : GC.money(price) + "/mo"}</span></div>
            <div class="plan-sub">${credits}${est ? ` · <span class="cost">${est}</span>` : ""}${offer}</div>
          </div>`;
        }).join("");
        const source = pf.source ? ` · <a href="${esc(pf.source)}" target="_blank" rel="noopener">Official pricing</a>` : "";
        box.innerHTML = rows + `<p class="live-note"><span class="dot"></span>Live prices · checked ${esc(pf.checked || data.updated || "")}${source}</p>`;
        box.classList.add("is-live");
      }).catch(() => {});
    });
  };

  document.addEventListener("DOMContentLoaded", () => {
    initChrome();
    GC.observe();
    const cat = document.body.dataset.prices;
    if (cat) GC.start(cat);
    GC.renderLive();
  });
})();
