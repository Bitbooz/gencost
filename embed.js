/* GenCost price box for other websites. Free to use.
   Paste this where the box should appear:

   <div class="gencost-prices" data-tool="Runway" data-cat="video">
     <a href="https://getgencost.com/pages/runway.html">Runway pricing</a> by GenCost
   </div>
   <script src="https://getgencost.com/embed.js" async></script>

   Options: data-theme="dark" for dark sites. The prices update every morning. */
(function () {
  "use strict";
  var BASE = "https://getgencost.com";
  var cache = {};

  function money(v) {
    if (v === null || v === undefined || v === "") return "&ndash;";
    v = Number(v);
    if (!v) return "Free";
    return "$" + (v % 1 ? v.toFixed(2) : String(v));
  }
  function esc(s) {
    return String(s == null ? "" : s).replace(/[&<>"]/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c];
    });
  }
  function load(cat) {
    if (!cache[cat]) {
      cache[cat] = fetch(BASE + "/data/" + cat + ".json", { cache: "no-cache" }).then(function (r) {
        if (!r.ok) throw new Error("GenCost: could not load prices");
        return r.json();
      });
    }
    return cache[cat];
  }
  function render(el, tool, dark) {
    var plans = (tool.plans || []).slice().sort(function (a, b) {
      return (a.monthly_price_usd || 0) - (b.monthly_price_usd || 0);
    });
    var hasYearly = plans.some(function (p) { return p.yearly_price_usd && p.yearly_price_usd < p.monthly_price_usd; });
    var rows = plans.map(function (p) {
      var inc = p.credits_or_minutes ? Number(p.credits_or_minutes).toLocaleString("en-US") + " " + esc(p.unit || "") : "";
      return "<tr><td>" + esc(p.name) + "</td><td>" + money(p.monthly_price_usd) + (p.monthly_price_usd ? "/mo" : "") + "</td>" +
        (hasYearly ? "<td>" + (p.yearly_price_usd ? money(p.yearly_price_usd) + "/mo" : "&ndash;") + "</td>" : "") +
        "<td>" + inc + "</td></tr>";
    }).join("");
    var page = BASE + (tool.page || "/");
    var c = dark
      ? { bg: "#111318", fg: "#e8eaf0", mute: "#9aa3b2", line: "#262a33", head: "#181b22", link: "#5cc8ff" }
      : { bg: "#ffffff", fg: "#1b1f27", mute: "#5b6472", line: "#e3e6eb", head: "#f5f7fa", link: "#0a66c2" };
    var css =
      ":host{all:initial;display:block}" +
      ".b{font:14px/1.45 -apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Arial,sans-serif;color:" + c.fg + ";background:" + c.bg +
      ";border:1px solid " + c.line + ";border-radius:10px;padding:14px 16px;max-width:640px;box-sizing:border-box}" +
      "h4{margin:0 0 8px;font-size:15px}" +
      ".w{overflow-x:auto}table{border-collapse:collapse;width:100%}" +
      "th,td{text-align:left;padding:6px 8px;border-bottom:1px solid " + c.line + ";white-space:nowrap}" +
      "th{background:" + c.head + ";font-weight:600;font-size:12px;color:" + c.mute + "}" +
      ".f{margin-top:8px;font-size:12px;color:" + c.mute + "}a{color:" + c.link + "}";
    var html =
      "<style>" + css + "</style><div class='b'><h4>" + esc(tool.name) + " pricing today</h4><div class='w'><table>" +
      "<thead><tr><th>Plan</th><th>Paid monthly</th>" + (hasYearly ? "<th>Paid yearly</th>" : "") + "<th>Includes</th></tr></thead>" +
      "<tbody>" + rows + "</tbody></table></div>" +
      "<div class='f'>In US dollars, checked " + esc((tool.checked || "").slice(0, 10)) + " &middot; Prices by <a href='" + page +
      "' target='_blank' rel='noopener'>GenCost</a></div></div>";
    var host = document.createElement("div");
    var root = host.attachShadow ? host.attachShadow({ mode: "open" }) : host;
    root.innerHTML = html;
    el.insertBefore(host, el.firstChild);
    // keep the plain link below for readers without JavaScript, but hide it visually once the box is shown
    Array.prototype.forEach.call(el.childNodes, function (n) {
      if (n !== host && n.nodeType === 1) n.style.display = "none";
      if (n !== host && n.nodeType === 3) n.textContent = "";
    });
  }
  function init() {
    var els = document.querySelectorAll(".gencost-prices[data-tool]:not([data-gc-done])");
    Array.prototype.forEach.call(els, function (el) {
      el.setAttribute("data-gc-done", "1");
      var name = el.getAttribute("data-tool");
      var cat = el.getAttribute("data-cat") || "video";
      load(cat).then(function (d) {
        var tool = (d.platforms || []).filter(function (t) { return t.name.toLowerCase() === name.toLowerCase(); })[0];
        if (tool) render(el, tool, el.getAttribute("data-theme") === "dark");
      }).catch(function () {});
    });
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init);
  else init();
})();
