"""
Shared page parts for GenCost: <head>, navigation bar and footer.

Used by restyle_pages.py (and copied into Aureo's package_generator.py).
Change the menu or footer here, then run:  python restyle_pages.py --refresh
to push the change into every content page.
"""
import html

GA_ID = "G-6DHTT2ZTBK"
SITE = "https://getgencost.com"

FONTS = (
    '<link rel="preconnect" href="https://fonts.googleapis.com">\n'
    '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
    '<link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@600;700'
    '&family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">'
)

ANALYTICS = f"""<script async src="https://www.googletagmanager.com/gtag/js?id={GA_ID}"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){{dataLayer.push(arguments);}}
  gtag('js', new Date());
  gtag('config', '{GA_ID}');
</script>"""


def head(title, description="", extra=""):
    """Everything inside <head>. `extra` is raw HTML (canonical, JSON-LD, page styles)."""
    desc = f'\n<meta name="description" content="{html.escape(description, quote=True)}">' if description else ""
    return f"""<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{html.escape(title)}</title>{desc}
{ANALYTICS}
{FONTS}
<link rel="stylesheet" href="/assets/gencost.css">
<script>document.documentElement.classList.add('js');</script>
<script defer src="/assets/gencost.js"></script>{(chr(10) + extra) if extra else ""}"""


NAV = """<nav class="top">
  <div class="wrap">
    <a class="logo grad-text" href="/">GENCOST</a>
    <ul class="nav-links" id="navLinks">
      <li><a href="/#platforms">Video</a></li>
      <li><a href="/voice.html" data-section="/voice,/pages/voice/">Voice</a></li>
      <li><a href="/music.html" data-section="/music,/pages/music/">Music</a></li>
      <li><a href="/compare.html">Compare</a></li>
      <li><a href="/calculator.html">Calculator</a></li>
      <li><a href="/#articles">Articles</a></li>
    </ul>
    <div class="nav-right">
      <a class="btn btn-primary" href="/order.html">Order package</a>
      <button class="menu-btn" id="menuBtn" aria-label="Open menu" aria-expanded="false">☰</button>
    </div>
  </div>
</nav>"""


FOOTER = """<footer class="site">
  <div class="wrap">
    <div class="foot-grid">
      <div>
        <a class="logo grad-text" href="/">GENCOST</a>
        <p class="foot-about">Price comparison for AI video, avatar, voice and music tools, in real dollars and updated automatically.</p>
      </div>
      <div>
        <h4>Compare</h4>
        <ul>
          <li><a href="/#platforms">Video &amp; avatar</a></li>
          <li><a href="/voice.html">Voice</a></li>
          <li><a href="/music.html">Music</a></li>
          <li><a href="/compare.html">Compare any tools</a></li>
          <li><a href="/pages/emerging.html">Emerging tools</a></li>
          <li><a href="/calculator.html">Budget calculator</a></li>
        </ul>
      </div>
      <div>
        <h4>Guides</h4>
        <ul>
          <li><a href="/pages/cheapest-ai-video-tools-in-2026.html">Cheapest video tools</a></li>
          <li><a href="/pages/cheapest-ai-voice-tools-in-2026.html">Cheapest voice tools</a></li>
          <li><a href="/pages/cheapest-ai-music-tools-in-2026.html">Cheapest music tools</a></li>
          <li><a href="/pages/cheapest-ai-avatar-tools-in-2026.html">Cheapest avatar tools</a></li>
          <li><a href="/credits.html">Credits &amp; residuals</a></li>
        </ul>
      </div>
      <div>
        <h4>GenCost</h4>
        <ul>
          <li><a href="/order.html">Order a package</a></li>
          <li><a href="/how-we-verify.html">How we verify prices</a></li>
          <li><a href="/changelog.html">Price changes log</a></li>
          <li><a href="mailto:bitbooz@protonmail.com">Contact</a></li>
        </ul>
      </div>
    </div>
    <div class="foot-bottom">
      <span>Created by Grok &amp; Bitbooz · <a href="mailto:bitbooz@protonmail.com">bitbooz@protonmail.com</a></span>
      <span>Prices change often. Always confirm inside each tool before you pay.</span>
    </div>
  </div>
</footer>"""


def crumbs(items):
    """items: list of (label, href or None). Returns breadcrumb HTML."""
    parts = []
    for i, (label, href) in enumerate(items):
        if i:
            parts.append('<span class="sep">/</span>')
        parts.append(f'<a href="{href}">{html.escape(label)}</a>' if href else f"<span>{html.escape(label)}</span>")
    return '<nav class="crumbs" aria-label="Breadcrumb">' + "".join(parts) + "</nav>"


ORDER_CTA = """<div class="page-cta">
  <div><h3>Need this as an article or YouTube video?</h3><p>Done-for-you SEO article + YouTube assets built on real GenCost pricing.</p></div>
  <a class="btn btn-primary" href="/order.html">Order a package <span class="arrow">→</span></a>
</div>"""


def page(title, description, body_html, crumb_items, kind="article", extra_head="", after_html="", scripts=""):
    """Full content page in the shared design."""
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
{head(title, description, extra_head)}
</head>
<body class="page-{kind}">
{NAV}
<header class="page-head">
  <div class="wrap narrow">
    {crumbs(crumb_items)}
  </div>
</header>
<main class="page">
  <div class="wrap narrow">
    <article class="prose">
{body_html}
    </article>
{after_html}
  </div>
</main>
{FOOTER}
{scripts}
</body>
</html>
"""
