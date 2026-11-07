/* =========================================================
   GenCost shared script
   - mobile menu, active nav link, scroll reveal
   - Monthly / Yearly billing switch (any element with data-billing-toggle)
   - loads prices from /data/<category>.json and fills any of
     these elements if the page has them:
       #budgetSeg + #budgetRows  budget demo card
       #board                    leaderboard (data-limit="8")
       #content                  plan cards for every tool
       #normTable                small "in dollars" table
       #statTools #statPlans #statCheapest #heroCount #bestValue
       .js-updated               last-updated timestamp
       .live-plans               live prices on a single tool page
       #compareApp               the Compare page
   ========================================================= */
(function () {
  const GC = (window.GenCost = window.GenCost || {});

  /* ---------- helpers ---------- */
  const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const num = (v) => (typeof v === "number" && isFinite(v) ? v : null);
  GC.esc = esc;
  GC.money = (v) => "$" + (Number.isInteger(v) ? v : v.toFixed(2));
  GC.amount = (v) => (num(v) !== null ? v.toLocaleString("en-US") : String(v ?? "").trim());
  GC.slug = (s) => String(s).toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");

  /* ---------- billing: monthly or yearly ---------- */
  GC.billing = "monthly";
  try { if (localStorage.getItem("gc-billing") === "yearly") GC.billing = "yearly"; } catch (e) {}

  GC.monthlyPrice = (p) => num(p.monthly_price_usd) ?? 0;
  GC.yearlyPrice = (p) => { const y = num(p.yearly_price_usd); return y && y > 0 ? y : null; };
  /* The price used everywhere: yearly-billing price when the switch says yearly and the plan has one. */
  GC.price = (p) => (GC.billing === "yearly" && GC.yearlyPrice(p)) || GC.monthlyPrice(p);
  /* A $0 entry is only "Free" when it is really a free plan (not an API rate or a note). */
  GC.isFree = (p) => GC.monthlyPrice(p) === 0 && /free|basic|trial|starter|hobby/i.test(String(p.name || ""));
  GC.isPaid = (p) => GC.price(p) > 0;

  GC.setBilling = function (value) {
    GC.billing = value === "yearly" ? "yearly" : "monthly";
    try { localStorage.setItem("gc-billing", GC.billing); } catch (e) {}
    GC.initToggles();
    if (GC._data) GC.renderPrices(GC._data);
    GC.renderLive();
    if (GC._compareRender) GC._compareRender();
    document.dispatchEvent(new CustomEvent("gencost:billing", { detail: GC.billing }));
  };

  GC.initToggles = function (root) {
    (root || document).querySelectorAll("[data-billing-toggle]").forEach((el) => {
      if (!el.dataset.built) {
        el.dataset.built = "1";
        el.classList.add("billing");
        el.setAttribute("role", "group");
        el.setAttribute("aria-label", "Billing");
        el.innerHTML = `<span class="billing-label">Show prices</span>
          <span class="seg"><button type="button" data-billing="monthly">Paid monthly</button><button type="button" data-billing="yearly">Paid yearly</button></span>`;
        el.addEventListener("click", (e) => {
          const b = e.target.closest("button[data-billing]");
          if (b && b.dataset.billing !== GC.billing) GC.setBilling(b.dataset.billing);
        });
      }
      el.querySelectorAll("button[data-billing]").forEach((b) => {
        const on = b.dataset.billing === GC.billing;
        b.classList.toggle("active", on);
        b.setAttribute("aria-pressed", on);
      });
    });
  };

  /* Price text for one plan, e.g. "$12/mo", "Free", "See note" */
  GC.priceHtml = function (plan) {
    const price = GC.price(plan);
    if (price > 0) return `<span class="pr">${GC.money(price)}/mo</span>`;
    if (GC.isFree(plan)) return `<span class="pr free">Free</span>`;
    return `<span class="pr muted">See note</span>`;
  };

  /* Small line under a plan: the other billing option */
  GC.billingNote = function (plan) {
    const m = GC.monthlyPrice(plan), y = GC.yearlyPrice(plan);
    if (!m) return "";
    if (GC.billing === "yearly") {
      if (y && y < m) return `billed yearly · ${GC.money(m)} if paid monthly`;
      return "yearly price not listed";
    }
    if (y && y < m) return `${GC.money(y)}/mo if paid yearly`;
    return "";
  };

  /* Real credits per video clip, from data/clip-costs.json (merged into
     data/video.json as platform.clips). Returns null when the tool has no
     known clip cost, so we show nothing rather than a wrong guess. */
  GC.clipCost = function (plan, secs) {
    const info = plan && plan.__clips;
    const price = GC.price(plan);
    const credits = num(plan && plan.credits_or_minutes) || num(info && info.plan_credits && info.plan_credits[plan.name]);
    if (!info || !info.clips || !price || !credits || credits <= 0) return null;
    const known = Object.keys(info.clips).map(Number).sort((a, b) => a - b);
    if (!known.length) return null;
    let used = known.includes(secs) ? secs : null, scaled = false;
    let cr;
    if (used) cr = info.clips[String(used)];
    else {
      // not listed for this length: scale from the closest listed length
      const near = known.reduce((a, b) => (Math.abs(b - secs) < Math.abs(a - secs) ? b : a));
      cr = (info.clips[String(near)] / near) * secs;
      scaled = true;
    }
    return { usd: (price / credits) * cr, credits: cr, secs, scaled, model: info.model || "", rough: !!info.rough || scaled };
  };
  GC.clipLengths = function (plan) {
    const info = plan && plan.__clips;
    return info && info.clips ? Object.keys(info.clips).map(Number).sort((a, b) => a - b) : [];
  };

  /* "Watch out" box: watermarks, credits that expire, commercial-use rules
     (data/hidden-costs.json, merged into each tool as pf.hidden) */
  GC.hiddenHtml = function (pf) {
    const h = pf && pf.hidden;
    if (!h || !(h.items || []).length) return "";
    const from = h.official
      ? `From the official pricing page${h.source ? ` (<a href="${esc(h.source)}" target="_blank" rel="noopener">source</a>)` : ""}, checked ${esc(h.checked || "")}`
      : `From a review dated ${esc(h.checked || "")}${h.source ? ` (<a href="${esc(h.source)}" target="_blank" rel="noopener">source</a>)` : ""}; not confirmed on the official page`;
    return `<div class="watch"><div class="watch-k">Watch out</div><ul>${h.items.map((i) => `<li>${esc(i)}</li>`).join("")}</ul><div class="watch-src">${from}</div></div>`;
  };

  /* Cost estimate per category. Video uses the real clip costs above;
     voice per 1k characters / minute, music per unit. */
  GC.estimate = function (plan, category) {
    const price = GC.price(plan);
    if (category === "video") {
      if (!price || !GC.clipCost(plan, (GC.clipLengths(plan)[0] || 5))) return "";
      const lens = GC.clipLengths(plan);
      if (!lens.length) return "";
      const parts = lens.map((s) => {
        const c = GC.clipCost(plan, s);
        return c ? `${s}s clip ≈ $${c.usd.toFixed(2)}` : "";
      }).filter(Boolean);
      const info = plan.__clips;
      const tip = `${info.model}: ${lens.map((s) => `${info.clips[s]} credits per ${s}s`).join(", ")}.${info.note ? " " + info.note : ""} Source checked ${info.checked || "?"}.`;
      return `<span title="${esc(tip)}">${parts.join(" · ")} <span class="cost-model">(${esc(info.model)}${info.rough ? ", rough" : ""})</span></span>`;
    }
    const credits = num(plan.credits_or_minutes);
    if (!price || !credits || credits <= 0) return "";
    const unit = String(plan.unit || "").toLowerCase();
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

  /* One plan row (used by plan cards, tool pages and the Compare page) */
  GC.planRow = function (plan, category) {
    const amt = GC.amount(plan.credits_or_minutes);
    const parts = [];
    if (amt && amt !== "0") parts.push(`${esc(amt)} ${esc(plan.unit || "")}`.trim());
    else if (plan.unit && !/^credits?$/i.test(plan.unit)) parts.push(esc(plan.unit));
    const bn = GC.billingNote(plan);
    if (bn) parts.push(`<span class="bill">${bn}</span>`);
    const est = GC.estimate(plan, category);
    if (est) parts.push(`<span class="cost">${est}</span>`);
    const offer = String(plan.offer || "").trim();
    if (offer && !/^(none|n\/a|-)$/i.test(offer)) parts.push(`<span class="offer">${esc(offer)}</span>`);
    return `<div class="plan-row">
      <div class="plan-line"><b>${esc(plan.name)}</b>${GC.priceHtml(plan)}</div>
      <div class="plan-sub">${parts.join("<br>") || "&nbsp;"}</div>
    </div>`;
  };

  GC.checkedText = (pf) => (pf.checked ? `Checked ${esc(pf.checked)}` : "Entered by hand");

  const loads = {};
  GC.load = function (category) {
    loads[category] = loads[category] || fetch(`/data/${category}.json`, { cache: "no-cache" }).then((r) => {
      if (!r.ok) throw new Error("HTTP " + r.status);
      return r.json();
    }).then((data) => {
      // give each plan its tool's clip costs (not enumerable, so it never shows up in copies)
      (data.platforms || []).forEach((pf) => {
        if (pf.clips) (pf.plans || []).forEach((p) => Object.defineProperty(p, "__clips", { value: pf.clips, enumerable: false }));
      });
      return data;
    });
    return loads[category];
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

  /* ---------- price rendering (home, voice, music) ---------- */
  GC.renderPrices = function (data) {
    GC._data = data;
    const category = data.category;
    const platforms = data.platforms || [];
    const allPlans = [];
    platforms.forEach((pf) => (pf.plans || []).forEach((p) => allPlans.push({ tool: pf.name, page: pf.page, ...p })));
    const paid = allPlans.filter(GC.isPaid);
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
      $("bestValue").textContent = `Best value right now: ${cheapest.tool} ${cheapest.name} at ${GC.money(GC.price(cheapest))}/mo${GC.billing === "yearly" ? " (paid yearly)" : ""}. Full details below.`;

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
          const meta = [amt && amt !== "0" ? `${esc(amt)} ${esc(p.unit || "")}` : "", GC.billingNote(p)].filter(Boolean).join(" · ") || "See plan details";
          return `<a class="row" href="${esc(p.page)}" style="animation-delay:${i * 70}ms">
            <span class="name">${esc(p.tool)}<small>${esc(p.name)}</small></span>
            <span class="price">${GC.money(GC.price(p))}/mo</span>
            <span class="bar"><i data-bw="${Math.round((GC.price(p) / budget) * 100)}"></i></span>
            <span class="meta">${meta}</span></a>`;
        }).join("");
        requestAnimationFrame(() => requestAnimationFrame(() =>
          rowsEl.querySelectorAll("[data-bw]").forEach((b) => (b.style.width = b.dataset.bw + "%"))));
      };
      seg._render = render;
      if (!seg.dataset.bound) {
        seg.dataset.bound = "1";
        seg.addEventListener("click", (e) => {
          const btn = e.target.closest("button");
          if (!btn) return;
          seg.querySelectorAll("button").forEach((b) => b.classList.toggle("active", b === btn));
          seg._render(Number(btn.dataset.b));
        });
      }
      const active = seg.querySelector("button.active") || seg.querySelector("button");
      if (active) render(Number(active.dataset.b));
    }

    // Lowest paid plan per tool
    const entry = platforms.map((pf) => {
      const p = (pf.plans || []).filter(GC.isPaid).sort((a, b) => GC.price(a) - GC.price(b))[0];
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
      const wasIn = content.querySelectorAll(".plat.in").length > 0;
      content.innerHTML = platforms.map((pf) => {
        const source = pf.source ? ` · <a href="${esc(pf.source)}" target="_blank" rel="noopener">Source</a>` : "";
        return `<div class="plat reveal${wasIn ? " in" : ""}">
          <div class="plat-top"><a href="${esc(pf.page)}">${esc(pf.name)} →</a><span>${GC.checkedText(pf)}${source}</span></div>
          ${(pf.plans || []).map((plan) => GC.planRow(plan, category)).join("")}
          ${GC.hiddenHtml(pf)}
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
    document.querySelectorAll(".live-plans[data-cat][data-tool]").forEach((box) => {
      const cat = box.dataset.cat;
      GC.load(cat).then((data) => {
        const pf = (data.platforms || []).find((p) => p.name === box.dataset.tool);
        if (!pf || !(pf.plans || []).length) return; // keep the old list
        const rows = pf.plans.map((plan) => GC.planRow(plan, cat)).join("");
        const hasYearly = pf.plans.some((p) => GC.yearlyPrice(p));
        const note = pf.checked
          ? `<span class="dot"></span>Live prices · checked ${esc(pf.checked)}${pf.source ? ` · <a href="${esc(pf.source)}" target="_blank" rel="noopener">Official pricing</a>` : ""}`
          : `Prices entered by hand · not checked automatically yet`;
        box.innerHTML = (hasYearly ? `<div data-billing-toggle></div>` : "") + rows + GC.hiddenHtml(pf) + `<p class="live-note">${note}</p>`;
        box.classList.add("is-live");
        GC.initToggles(box);
      }).catch(() => {});
    });
  };

  /* ---------- Compare page ---------- */
  GC.initCompare = function () {
    const app = document.getElementById("compareApp");
    if (!app) return;
    const picks = [...app.querySelectorAll("select[data-pick]")];
    const out = document.getElementById("compareOut");
    const CAT = { video: "Video & image", voice: "Voice", music: "Music" };

    Promise.all(["video", "voice", "music"].map((c) => GC.load(c).catch(() => ({ category: c, platforms: [] }))))
      .then((sets) => {
        const tools = [];
        sets.forEach((d) => (d.platforms || []).forEach((pf) => tools.push({ id: GC.slug(pf.name), cat: d.category, pf })));
        const byId = Object.fromEntries(tools.map((t) => [t.id, t]));

        const options = (optional) =>
          (optional ? `<option value="">None</option>` : "") +
          Object.keys(CAT).map((c) => {
            const list = tools.filter((t) => t.cat === c);
            return list.length ? `<optgroup label="${CAT[c]}">${list.map((t) => `<option value="${t.id}">${esc(t.pf.name)}</option>`).join("")}</optgroup>` : "";
          }).join("");
        picks.forEach((s, i) => (s.innerHTML = options(i === 2)));

        // Start from the link (?tools=runway,pika,luma) or a default trio
        let wanted = [];
        try { wanted = (new URLSearchParams(location.search).get("tools") || "").split(",").filter((id) => byId[id]); } catch (e) {}
        if (wanted.length < 2) wanted = ["runway", "pika", "kling-ai"].filter((id) => byId[id]);
        picks.forEach((s, i) => (s.value = wanted[i] || (i === 2 ? "" : tools[i] && tools[i].id)));

        const render = () => {
          const chosen = [...new Set(picks.map((s) => s.value).filter((v) => byId[v]))].map((v) => byId[v]);
          try { history.replaceState(null, "", "?tools=" + chosen.map((t) => t.id).join(",")); } catch (e) {}
          const starts = chosen.map((t) => {
            const p = (t.pf.plans || []).filter(GC.isPaid).sort((a, b) => GC.price(a) - GC.price(b))[0];
            return p ? { t, p, price: GC.price(p) } : null;
          });
          const valid = starts.filter(Boolean);
          const best = valid.length ? valid.reduce((a, b) => (b.price < a.price ? b : a)) : null;
          const mixed = new Set(chosen.map((t) => t.cat)).size > 1;

          document.getElementById("compareSummary").innerHTML = best
            ? `Cheapest way to start: <strong>${esc(best.t.pf.name)} ${esc(best.p.name)}</strong> at <strong class="price">${GC.money(best.price)}/mo</strong>${GC.billing === "yearly" ? " (paid yearly)" : ""}.${mixed ? ` <span class="muted">These tools do different jobs, so compare what each plan includes, not just the price.</span>` : ""}`
            : "Pick at least two tools to compare.";

          out.innerHTML = chosen.map((t, i) => {
            const s = starts[i];
            const isBest = best && s && s.t === best.t && valid.length > 1;
            const freePlan = (t.pf.plans || []).some(GC.isFree);
            return `<section class="cmp-col${isBest ? " best" : ""}" aria-label="${esc(t.pf.name)}">
              ${isBest ? `<span class="cmp-badge">Cheapest start</span>` : ""}
              <div class="cmp-cat">${CAT[t.cat]}</div>
              <h2><a href="${esc(t.pf.page)}">${esc(t.pf.name)}</a></h2>
              <div class="cmp-from">${s ? `from <strong>${GC.money(s.price)}</strong>/mo` : "no paid plan listed"}</div>
              <ul class="cmp-facts">
                <li>${freePlan ? "Free plan: yes" : "Free plan: no"}</li>
                <li>${(t.pf.plans || []).filter(GC.isPaid).length} paid plans</li>
                <li>${GC.checkedText(t.pf)}</li>
              </ul>
              <div class="cmp-plans">${(t.pf.plans || []).map((p) => GC.planRow(p, t.cat)).join("")}</div>
              ${GC.hiddenHtml(t.pf)}
              <div class="cmp-links">
                <a href="${esc(t.pf.page)}">Full ${esc(t.pf.name)} page →</a>
                ${t.pf.source ? `<a href="${esc(t.pf.source)}" target="_blank" rel="noopener">Official pricing ↗</a>` : ""}
              </div>
            </section>`;
          }).join("");
          const share = document.getElementById("compareShare");
          if (share) share.dataset.url = location.href;
        };
        GC._compareRender = render;
        picks.forEach((s) => s.addEventListener("change", render));
        render();
      });

    const share = document.getElementById("compareShare");
    if (share) share.addEventListener("click", () => {
      const done = () => { share.textContent = "Link copied ✓"; setTimeout(() => (share.textContent = "Copy link to this comparison"), 2000); };
      try { navigator.clipboard.writeText(location.href).then(done, () => prompt("Copy this link:", location.href)); }
      catch (e) { prompt("Copy this link:", location.href); }
    });
  };

  document.addEventListener("DOMContentLoaded", () => {
    initChrome();
    GC.initToggles();
    GC.observe();
    const cat = document.body.dataset.prices;
    if (cat) GC.start(cat);
    GC.renderLive();
    GC.initCompare();
  });
})();
