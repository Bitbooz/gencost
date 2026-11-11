/* GenCost in other languages (Spanish /es/, Portuguese /pt/): translates the words that the page's JavaScript writes (price tables,
   calculators, buttons), and points links to the Spanish pages. The page text itself is
   translated when the site is built (translate_site.py). */
(function () {
  var LANGS = ["es", "pt"];
  var code = (document.documentElement.lang || "").slice(0, 2).toLowerCase();
  if (LANGS.indexOf(code) < 0) return;
  var PREFIX = new RegExp("^/(" + LANGS.join("|") + ")/");
  var NUM = /[$€£]?\d(?:[\d,.]*\d)?/g;
  var dict = null, pages = {};
  var SKIP = "script,style,textarea,pre,code,svg,.notranslate,.logo,.lang-switch,[translate=no]";

  function tr(s) {
    var t = (s || "").replace(/\s+/g, " ").trim();
    if (!t || !/[A-Za-z]{2}/.test(t)) return null;
    var nums = [];
    var key = t.replace(NUM, function (m) { nums.push(m); return "[[" + (nums.length - 1) + "]]"; });
    var v = dict[key];
    if (v == null) return null;
    v = v.replace(/\[\[(\d+)\]\]/g, function (_, i) { return nums[+i] != null ? nums[+i] : ""; })
         .replace(/&amp;/g, "&").replace(/&lt;/g, "<").replace(/&gt;/g, ">");
    var lead = s.match(/^\s*/)[0], trail = s.match(/\s*$/)[0];
    return lead + v + trail;
  }

  function fixLink(a) {
    var h = a.getAttribute("href");
    if (!h || h.charAt(0) !== "/" || PREFIX.test(h) || h.indexOf("//") === 0) return;
    var path = h.split("#")[0].split("?")[0] || "/";
    if (pages[path]) a.setAttribute("href", (path === "/" || path === "/index.html" ? "/" + code + "/" : "/" + code + path) + h.slice(path.length));
  }

  function run(root) {
    if (!root || (root.nodeType === 1 && root.closest(SKIP))) return;
    if (root.nodeType === 3) {
      var v = tr(root.nodeValue);
      if (v != null && v !== root.nodeValue) root.nodeValue = v;
      return;
    }
    var w = document.createTreeWalker(root, NodeFilter.SHOW_TEXT), t, list = [];
    while ((t = w.nextNode())) list.push(t);
    list.forEach(function (n) {
      if (n.parentElement && n.parentElement.closest(SKIP)) return;
      var v = tr(n.nodeValue);
      if (v != null && v !== n.nodeValue) n.nodeValue = v;
    });
    var els = root.querySelectorAll ? root.querySelectorAll("[placeholder],[title],[aria-label],a[href]") : [];
    Array.prototype.forEach.call(els, function (el) {
      if (el.closest(SKIP)) return;
      ["placeholder", "title", "aria-label"].forEach(function (a) {
        var x = el.getAttribute(a);
        if (x) { var v = tr(x); if (v != null && v !== x) el.setAttribute(a, v); }
      });
      if (el.tagName === "A") fixLink(el);
    });
    if (root.tagName === "A") fixLink(root);
  }

  function start(data) {
    dict = data.ui || {};
    (data.pages || []).forEach(function (p) { pages[p] = 1; });
    run(document.body);
    new MutationObserver(function (muts) {
      muts.forEach(function (m) {
        if (m.type === "characterData") run(m.target);
        else m.addedNodes.forEach(function (n) { run(n); });
      });
    }).observe(document.body, { childList: true, subtree: true, characterData: true });
  }

  function load() {
    fetch("/data/i18n/" + code + "-ui.json").then(function (r) { return r.json(); }).then(start).catch(function () {});
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", load);
  else load();
})();
