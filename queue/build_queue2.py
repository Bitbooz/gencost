"""
One-off helper: writes queued articles 06-10 and APPENDS them to queue/queue.json
(it never touches the items that are already there).
"""
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
raw = open(os.path.join(ROOT, "pages", "cheapest-way-to-use-kling-4-0-2026.html"), encoding="utf-8").read()
head = raw[:raw.index('<article class="prose">') + len('<article class="prose">')]
tail = raw[raw.index("</article>"):]
tail = re.sub(r'<section class="related".*?</section>', "", tail, flags=re.S)
head = re.sub(r"<!-- SEO:START.*?<!-- SEO:END -->\n?", "", head, flags=re.S)
head = re.sub(r"<!-- HREFLANG:START.*?<!-- HREFLANG:END -->\n?", "", head, flags=re.S)
head = re.sub(r'<details class="lang-menu".*?</details>', "", head, flags=re.S)


def live(tool, plan, text, bill="monthly", fmt="/mo"):
    return (f'<span class="live-price" data-approx="0" data-bill="{bill}" data-fmt="{fmt}" data-plan="{plan}" '
            f'data-tool="{tool}" title="Updated automatically every day">{text}</span>')


def page(title, desc, crumb, body):
    h = re.sub(r"<title>.*?</title>", f"<title>{title} | GenCost</title>", head, flags=re.S)
    h = re.sub(r'<meta name="description" content="[^"]*">', f'<meta name="description" content="{desc}">', h)
    h = re.sub(r"<span>Cheapest Kling 4.0</span></nav>", f"<span>{crumb}</span></nav>", h)
    return h + "\n" + body.strip() + "\n" + tail


A, CARDS = {}, {}

# 06 Higgsfield vs Kling --------------------------------------------------------------------------
A["higgsfield-vs-kling-pricing-2026"] = page(
    "Higgsfield vs Kling: Which Is Cheaper for Kling Videos? (2026)",
    "Higgsfield sells Kling 3.0 and Kling 4.0 inside its own plans. We compared the price of one clip on Higgsfield and on Kling's own app, plan by plan.",
    "Higgsfield vs Kling",
    f"""
<h1>Higgsfield vs Kling: Which Is Cheaper for Kling Videos? (2026)</h1>
<p class="lead">Higgsfield is one of the most popular places to use Kling's video models, next to many others in one app. But is it cheaper than buying from Kling itself? We worked out the cost of one clip of Kling 3.0 and Kling 4.0 on every plan of both.</p>
<div class="box">
<strong>Quick answer</strong><br/>
For Kling's own models, <strong>Kling AI</strong> is about two to three times cheaper per clip than Higgsfield on every plan.<br/>
A 5-second Kling 4.0 clip at 720p: about $0.67 on Kling Standard, about $1.76 on Higgsfield Starter.<br/>
Higgsfield makes sense if you also use its other models, such as Seedance 2.5 (from about $0.65 a clip), and its editing tools.<br/>
Last checked: 2026-11-14
</div>
<h2>One clip, plan by plan</h2>
<div class="table-scroll"><table>
<thead><tr><th>Where</th><th>Plan</th><th>Monthly price</th><th>Kling 3.0</th><th>Kling 4.0, 720p</th><th>Kling 4.0, 1080p</th></tr></thead>
<tbody>
<tr><td><a href="/pages/kling.html">Kling AI</a></td><td>Standard</td><td>{live("Kling AI","Standard","$8.80/mo")}</td><td>about $0.40</td><td>about $0.67</td><td>about $1.00</td></tr>
<tr><td><a href="/pages/kling.html">Kling AI</a></td><td>Pro</td><td>{live("Kling AI","Pro","$32.56/mo")}</td><td>about $0.33</td><td>about $0.54</td><td>about $0.81</td></tr>
<tr><td><a href="/pages/higgsfield.html">Higgsfield</a></td><td>Starter</td><td>{live("Higgsfield","Starter","$19/mo")}</td><td>about $0.99</td><td>about $1.76</td><td>about $2.64</td></tr>
<tr><td><a href="/pages/higgsfield.html">Higgsfield</a></td><td>Plus</td><td>{live("Higgsfield","Plus","$59/mo")}</td><td>about $0.69</td><td>about $1.23</td><td>about $1.84</td></tr>
<tr><td><a href="/pages/higgsfield.html">Higgsfield</a></td><td>Ultra</td><td>{live("Higgsfield","Ultra","$129/mo")}</td><td>about $0.60</td><td>about $1.08</td><td>about $1.61</td></tr>
</tbody>
</table></div>
<p class="note no-live">Worked out on 2026-11-14 from each plan's monthly price and credits. Kling 3.0 on Kling: a 5-second 720p clip without sound (30 credits). Kling 3.0 on Higgsfield: Higgsfield's own estimate of about 14 credits per video; it doesn't state the clip length. Kling 4.0: about 10 / 15 credits per second on Kling (measured by testers; Kling's pricing page doesn't list it) and 25 / 37.5 credits per 5 seconds on Higgsfield (Higgsfield's Kling 4.0 page). Both include sound.</p>
<h2>What the numbers mean</h2>
<h3>For Kling models, go to the source</h3>
<p>Kling's Standard plan costs less than half of Higgsfield Starter, and every Kling clip costs about a third as much. Even Higgsfield's biggest plan, Ultra, is more expensive per Kling 4.0 clip than Kling's cheapest one.</p>
<h3>Paying yearly narrows the gap</h3>
<p>Higgsfield's yearly prices are much lower than its monthly ones: Plus costs about $35 a month billed yearly instead of $59. That brings a 720p Kling 4.0 clip down to about $0.73, close to Kling Standard's monthly price per clip. Kling's yearly plans are about 25% cheaper too.</p>
<h3>Why people still pick Higgsfield</h3>
<p>Higgsfield puts Kling, Seedance, Veo and its own tools in one app with one credit balance. Its Plus plan covers about 80 Seedance 2.5 videos, about $0.74 each, which is cheaper than Seedance 2.5 on most platforms. If you switch between models a lot, one Higgsfield plan can cost less than two or three separate subscriptions.</p>
<h2>Watch out</h2>
<ul>
<li><strong>Starter's monthly price.</strong> Higgsfield doesn't show a monthly price for Starter on its pricing page, so check the price at checkout.</li>
<li><strong>First-month discounts.</strong> Kling gives 30% off the first month of each plan; the prices above are the normal ones.</li>
<li><strong>Retries count.</strong> If you need three tries for every clip you keep, multiply each price by three.</li>
</ul>
<p>Full details: <a href="/pages/cheapest-way-to-use-kling-4-0-2026.html">where Kling 4.0 is cheapest</a>, or compare both on the <a href="/compare.html?tools=kling-ai,higgsfield">Compare page</a>.</p>
<p class="note">Sources: the official pricing pages of Kling and Higgsfield, Higgsfield's Kling 4.0 page, and Kling 4.0 credit tests by Genie Artificiel (October 16, 2026). Checked 2026-11-14. Prices change often. Always confirm on the official sites.</p>
""")
CARDS["higgsfield-vs-kling-pricing-2026"] = ("video", "Video", "Higgsfield vs Kling", "Who's cheaper for Kling videos")

# 07 Runway alternatives ---------------------------------------------------------------------------
A["best-runway-alternatives-2026"] = page(
    "Best Runway Alternatives in 2026: Cheaper AI Video per Clip",
    "Runway's Gen-4.5 costs about $1.44 per 5-second clip on its cheapest plan. These Runway alternatives make a clip for a fraction of that: Luma, Pika, Kling, Hailuo, Vidu and Google Veo.",
    "Runway alternatives",
    f"""
<h1>Best Runway Alternatives in 2026: Cheaper AI Video per Clip</h1>
<p class="lead">Runway is one of the best-known AI video tools, but also one of the most expensive per clip. On its $15 Standard plan, a 5-second Gen-4.5 clip uses 60 of the plan's 625 credits, about $1.44. These are the alternatives that make a clip for less, on their cheapest paid plan.</p>
<div class="box">
<strong>Quick answer</strong><br/>
Cheapest big-name alternatives: <strong>Luma Plus</strong> (Ray3.2), about $0.30 per 5-second 720p clip, and <strong>Pika Starter</strong> (Pika 2.5), about $0.33.<br/>
Best value with Kling quality: <strong>Kling AI Standard</strong>, about $0.40 per 5-second Kling 3.0 clip.<br/>
Runway Standard with Gen-4.5: about $1.44 per 5-second clip, three to five times as much.<br/>
Last checked: 2026-11-14
</div>
<h2>One clip on Runway and its alternatives</h2>
<div class="table-scroll"><table>
<thead><tr><th>Tool</th><th>Plan</th><th>Monthly price</th><th>Model</th><th>One clip</th></tr></thead>
<tbody>
<tr><td><a href="/pages/vidu.html">Vidu</a></td><td>Standard</td><td>{live("Vidu","Standard","$10/mo")}</td><td>Vidu Q4, 540p</td><td>about $0.10 (4 seconds)</td></tr>
<tr><td><a href="/pages/luma.html">Luma</a></td><td>Plus</td><td>{live("Luma","Plus","$30/mo")}</td><td>Ray3.2, 720p</td><td>about $0.30 (5 seconds)</td></tr>
<tr><td><a href="/pages/pika.html">Pika</a></td><td>Starter</td><td>{live("Pika","Starter","$10/mo")}</td><td>Pika 2.5, 720p</td><td>about $0.33 (5 seconds)</td></tr>
<tr><td><a href="/pages/veo.html">Google Veo</a></td><td>Google AI Pro</td><td>{live("Google Veo","Google AI Pro","$19.99/mo")}</td><td>Veo Fast in Flow</td><td>about $0.40 (8 seconds)</td></tr>
<tr><td><a href="/pages/kling.html">Kling AI</a></td><td>Standard</td><td>{live("Kling AI","Standard","$8.80/mo")}</td><td>Kling 3.0, 720p, no sound</td><td>about $0.40 (5 seconds)</td></tr>
<tr><td><a href="/pages/hailuo.html">Hailuo AI</a></td><td>Standard</td><td>{live("Hailuo AI","Standard","$14.99/mo")}</td><td>MiniMax H3, 768p</td><td>about $0.63 (6 seconds)</td></tr>
<tr><td><a href="/pages/runway.html">Runway</a></td><td>Standard</td><td>{live("Runway","Standard","$15/mo")}</td><td>Gen-4.5</td><td>about $1.44 (5 seconds)</td></tr>
</tbody>
</table></div>
<p class="note no-live">Worked out on 2026-11-14 from each plan's monthly price, its credits and the credits per clip each tool lists. Google Veo's credits per clip come from a dated review, not from Google's own page. Clip lengths differ, so compare the price per second if you need longer videos: see <a href="/pages/cheapest-ai-video-cost-per-second-2026.html">AI video cost per second</a>.</p>
<h2>Which alternative fits you</h2>
<h3>Luma: closest to Runway, at a fifth of the price</h3>
<p>Luma's Ray3.2 is a cinematic model like Runway's, with clear per-second pricing and commercial use on every plan. Its $30 Plus plan is twice Runway Standard's price, but covers about eight minutes of 720p video a month instead of under one.</p>
<h3>Pika and Vidu: cheapest for short social clips</h3>
<p>Pika Starter and Vidu Standard both cost $10. Pika 2.5 makes 720p clips; Vidu Q4 is even cheaper per clip but makes 540p video, which is fine for phones.</p>
<h3>Kling: best quality for the money</h3>
<p>Kling 3.0 costs about $0.40 per 5-second clip on the $8.80 Standard plan, and Kling 4.0, with sound, about $0.67. See <a href="/pages/runway-vs-kling-pricing-2026.html">Runway vs Kling</a> for a closer look.</p>
<h2>When Runway is still worth it</h2>
<p>Runway's strength is editing: Aleph 2.0 can change an existing video, and Runway hosts other models such as Kling 4.0 and Seedance next to its own. On Max, up to one month of unused credits rolls over. If you need those tools, the higher price per clip can pay off.</p>
<h2>Watch out</h2>
<ul>
<li><strong>Retries cost the same as keepers.</strong> If you need three tries per clip, multiply each price by three.</li>
<li><strong>Resolution and sound change the price.</strong> 1080p usually costs about 1.5 to 4 times as much as 720p.</li>
<li><strong>Commercial use.</strong> Check the plan; see <a href="/pages/cheapest-ai-video-tools-for-commercial-use-2026.html">cheapest AI video for commercial use</a>.</li>
</ul>
<p class="note">Sources: the official pricing pages of Runway, Luma, Pika, Vidu, Kling, Hailuo and Google; Veo credits per clip from a review by DIY AI (November 2026). Checked 2026-11-14. Prices change often. Always confirm on the official sites.</p>
""")
CARDS["best-runway-alternatives-2026"] = ("video", "Video", "Best Runway Alternatives", "Same clip, a fraction of the price")

# 08 Suno alternatives -----------------------------------------------------------------------------
A["best-suno-alternatives-2026"] = page(
    "Best Suno Alternatives in 2026: Udio, Mureka, Stable Audio and More",
    "Suno Pro costs $10 a month. These Suno alternatives give you songs, downloads and commercial rights for a similar price or less: Mureka, Udio, Stable Audio, Boomy, Soundraw and AIVA.",
    "Suno alternatives",
    f"""
<h1>Best Suno Alternatives in 2026: Udio, Mureka, Stable Audio and More</h1>
<p class="lead">Suno is the best-known AI song generator, and its Pro plan costs $10 a month for 2,500 credits and 20 song downloads, with commercial use. If you need more downloads, different rights or a lower price, these are the alternatives, compared on their cheapest paid plan.</p>
<div class="box">
<strong>Quick answer</strong><br/>
Cheapest: <strong>Mureka Pro</strong>, $8 a month, with unlimited downloads and commercial rights, also for songs you made before upgrading.<br/>
Closest to Suno: <strong>Udio Standard</strong>, $10 a month for 2,400 credits.<br/>
Commercial use for free: <strong>Stable Audio</strong>'s free plan includes a commercial license.<br/>
Last checked: 2026-11-14
</div>
<h2>Suno and its alternatives, cheapest paid plan</h2>
<div class="table-scroll"><table>
<thead><tr><th>Tool</th><th>Plan</th><th>Monthly price</th><th>What you get</th><th>Good to know</th></tr></thead>
<tbody>
<tr><td><a href="/pages/mureka.html">Mureka</a></td><td>Pro</td><td>{live("Mureka","Pro","$8/mo")}</td><td>5,000 Gold credits, unlimited downloads</td><td>Commercial rights for all songs, also older ones</td></tr>
<tr><td><a href="/pages/music/boomy.html">Boomy</a></td><td>Creator</td><td>{live("Boomy","Creator","$9.99/mo")}</td><td>WAV downloads every month</td><td>You may release songs on Spotify and other platforms</td></tr>
<tr><td><a href="/pages/music/suno.html">Suno</a></td><td>Pro</td><td>{live("Suno","Pro","$10/mo")}</td><td>2,500 credits, 20 song downloads</td><td>Commercial use; credits don't carry over</td></tr>
<tr><td><a href="/pages/music/udio.html">Udio</a></td><td>Standard</td><td>{live("Udio","Standard","$10/mo")}</td><td>2,400 credits, no daily limit</td><td>Credits don't roll over</td></tr>
<tr><td><a href="/pages/stable-audio.html">Stable Audio</a></td><td>Solo</td><td>{live("Stable Audio","Solo","$12/mo")}</td><td>About 165 full mixes a month</td><td>Even the free plan has a commercial license</td></tr>
<tr><td><a href="/pages/music/aiva.html">AIVA</a></td><td>Standard</td><td>{live("AIVA","Standard","$12.29/mo")}</td><td>15 downloads a month</td><td>You own the copyright only on Pro; billed in euros</td></tr>
<tr><td><a href="/pages/music/soundraw.html">Soundraw</a></td><td>Creator</td><td>{live("Soundraw","Creator","$16.99/mo")}</td><td>Unlimited mp3 downloads</td><td>For people and companies under 10 employees</td></tr>
</tbody>
</table></div>
<p class="note no-live">Cheapest paid plan of each tool, monthly billing, in US dollars, from GenCost's daily price data (2026-11-14). AIVA's price is converted from euros. Prices in the table update every day.</p>
<h2>Which alternative fits you</h2>
<h3>Mureka: the cheapest way to sell your songs</h3>
<p>Mureka Pro costs less than Suno Pro and gives unlimited downloads. Its paid plans also give commercial rights to songs you made on the free plan, which Suno and Udio don't promise.</p>
<h3>Udio: the closest match</h3>
<p>Udio Standard costs the same as Suno Pro and gives a similar number of credits. Many people use both and keep the songs they like best.</p>
<h3>Stable Audio and Soundraw: background music</h3>
<p>For music under videos and podcasts rather than full songs with vocals, Stable Audio and Soundraw are made for the job. Stable Audio even allows commercial use on its free plan, and Soundraw Creator has unlimited downloads.</p>
<h2>Watch out</h2>
<ul>
<li><strong>Free plans usually can't be monetized.</strong> Suno's free plan has no downloads or commercial rights, and on AIVA's free plan AIVA owns the copyright.</li>
<li><strong>Credits don't carry over</strong> on Suno and Udio, so an unused month is lost.</li>
<li><strong>Read the terms for streaming.</strong> Releasing AI songs on Spotify has its own rules on each platform.</li>
</ul>
<p>See every music plan on the <a href="/music.html">music price list</a>, or read <a href="/pages/suno-vs-udio-pricing-2026.html">Suno vs Udio</a>.</p>
<p class="note">Sources: the official pricing pages of Suno, Udio, Mureka, Stable Audio, Boomy, Soundraw and AIVA. Checked 2026-11-14. Prices change often. Always confirm on the official sites.</p>
""")
CARDS["best-suno-alternatives-2026"] = ("music", "Music", "Best Suno Alternatives", "Songs and rights for $10 or less")

# 09 ElevenLabs vs Murf ----------------------------------------------------------------------------
A["elevenlabs-vs-murf-pricing-2026"] = page(
    "ElevenLabs vs Murf: Cost per Minute of AI Voice (2026)",
    "ElevenLabs and Murf cost about the same per minute of AI voiceover, around 14 to 17 cents. The real differences are the entry price and when you get commercial rights.",
    "ElevenLabs vs Murf",
    f"""
<h1>ElevenLabs vs Murf: Cost per Minute of AI Voice (2026)</h1>
<p class="lead">ElevenLabs sells credits, Murf sells hours of voice per year, so their plans are hard to compare. We turned both into one number: what one minute of finished voiceover costs.</p>
<div class="box">
<strong>Quick answer</strong><br/>
Per minute they are almost the same: about <strong>14 to 17 cents</strong> on both.<br/>
Cheapest start: <strong>ElevenLabs Starter</strong>, $6 a month (and $1 for the first month), with commercial use.<br/>
For business use, Murf needs its <strong>Business</strong> plan at $66 a month; ElevenLabs allows commercial use from Starter.<br/>
Last checked: 2026-11-14
</div>
<h2>One minute of voice, plan by plan</h2>
<div class="table-scroll"><table>
<thead><tr><th>Tool</th><th>Plan</th><th>Monthly price</th><th>Voice per month</th><th>One minute</th><th>Commercial use</th></tr></thead>
<tbody>
<tr><td><a href="/pages/voice/elevenlabs.html">ElevenLabs</a></td><td>Starter</td><td>{live("ElevenLabs","Starter","$6/mo")}</td><td>30,000 credits, about 30 to 40 minutes</td><td>about $0.15 to $0.20</td><td>Yes</td></tr>
<tr><td><a href="/pages/voice/elevenlabs.html">ElevenLabs</a></td><td>Creator</td><td>{live("ElevenLabs","Creator","$22/mo")}</td><td>121,000 credits, about 2 to 2.5 hours</td><td>about $0.16</td><td>Yes</td></tr>
<tr><td><a href="/pages/voice/murf.html">Murf AI</a></td><td>Creator</td><td>{live("Murf AI","Creator","$19/mo")}</td><td>24 hours a year, about 2 hours a month</td><td>about $0.16</td><td>No business license</td></tr>
<tr><td><a href="/pages/voice/elevenlabs.html">ElevenLabs</a></td><td>Pro</td><td>{live("ElevenLabs","Pro","$99/mo")}</td><td>600,000 credits, about 10 to 13 hours</td><td>about $0.14</td><td>Yes</td></tr>
<tr><td><a href="/pages/voice/murf.html">Murf AI</a></td><td>Business</td><td>{live("Murf AI","Business","$66/mo")}</td><td>96 hours a year, about 8 hours a month</td><td>about $0.14</td><td>Yes</td></tr>
</tbody>
</table></div>
<p class="note no-live">Worked out on 2026-11-14. ElevenLabs: about 1 credit per character for text to speech, which GenCost estimates at about 30 to 40 minutes of speech per 30,000 credits. Murf: the voice time each plan lists per year, divided by 12. Real minutes depend on how fast the voice speaks and on the model.</p>
<h2>What the numbers mean</h2>
<h3>Same price per minute</h3>
<p>Once you use your whole plan, both tools land at about 14 to 17 cents per minute of voice. Price alone won't decide it, so choose by voices, languages and how you work.</p>
<h3>ElevenLabs is cheaper to start</h3>
<p>ElevenLabs Starter costs $6 a month and only $1 for the first month, and includes commercial use. Its Free plan gives 10,000 credits a month, but without a commercial license.</p>
<h3>Murf charges more for business rights</h3>
<p>Murf's Creator plan has no business license; that only comes with Business at $66 a month. Its Free plan has 10 minutes of voice but no downloads.</p>
<h2>Watch out</h2>
<ul>
<li><strong>Shared credits.</strong> On ElevenLabs, all tools (voice, dubbing, sound effects) use one credit pool, so other features reduce your minutes.</li>
<li><strong>Yearly hours.</strong> Murf's hours are counted per year. Use them up early and you wait for the new year or upgrade.</li>
<li><strong>First-month prices.</strong> ElevenLabs Creator is half price only for the first month.</li>
</ul>
<p>See every voice plan on the <a href="/voice.html">voice price list</a>, or read <a href="/pages/best-elevenlabs-alternatives-2026.html">the best ElevenLabs alternatives</a>.</p>
<p class="note">Sources: the official pricing pages of ElevenLabs and Murf AI. Checked 2026-11-14. Prices change often. Always confirm on the official sites.</p>
""")
CARDS["elevenlabs-vs-murf-pricing-2026"] = ("voice", "Voice", "ElevenLabs vs Murf", "Real cost per minute of voice")

# 10 Kling 3.0 vs Kling 4.0 ------------------------------------------------------------------------
A["kling-3-0-vs-kling-4-0-cost-per-clip-2026"] = page(
    "Kling 3.0 vs Kling 4.0: How Much More Does the New Model Cost? (2026)",
    "Kling 4.0 makes sound with every clip. On Kling's own plans it costs about 11% to 25% more per clip than Kling 3.0 with sound, and two thirds more than Kling 3.0 without.",
    "Kling 3.0 vs 4.0",
    f"""
<h1>Kling 3.0 vs Kling 4.0: How Much More Does the New Model Cost? (2026)</h1>
<p class="lead">Kling 4.0 has been open to everyone since October 15, 2026, and Kling 3.0 is still on offer next to it. Is the new model worth the extra credits? Here is what one 5-second clip of each costs on Kling's own plans and on Higgsfield.</p>
<div class="box">
<strong>Quick answer</strong><br/>
On Kling Standard: Kling 3.0 costs about $0.40 without sound and $0.60 with sound; Kling 4.0, always with sound, about $0.67 (5 seconds, 720p).<br/>
So with sound, Kling 4.0 costs only about <strong>11% more</strong> than Kling 3.0 at 720p, and 25% more at 1080p.<br/>
On Higgsfield the jump is bigger: about $0.99 for Kling 3.0 against $1.76 for Kling 4.0 on Starter.<br/>
Last checked: 2026-11-14
</div>
<h2>One 5-second clip, Kling 3.0 vs Kling 4.0</h2>
<div class="table-scroll"><table>
<thead><tr><th>Where</th><th>Plan</th><th>Monthly price</th><th>Kling 3.0, no sound</th><th>Kling 3.0, with sound</th><th>Kling 4.0 (with sound)</th></tr></thead>
<tbody>
<tr><td><a href="/pages/kling.html">Kling AI</a>, 720p</td><td>Standard</td><td>{live("Kling AI","Standard","$8.80/mo")}</td><td>about $0.40</td><td>about $0.60</td><td>about $0.67</td></tr>
<tr><td><a href="/pages/kling.html">Kling AI</a>, 1080p</td><td>Standard</td><td>{live("Kling AI","Standard","$8.80/mo")}</td><td>about $0.53</td><td>about $0.80</td><td>about $1.00</td></tr>
<tr><td><a href="/pages/kling.html">Kling AI</a>, 720p</td><td>Pro</td><td>{live("Kling AI","Pro","$32.56/mo")}</td><td>about $0.33</td><td>about $0.49</td><td>about $0.54</td></tr>
<tr><td><a href="/pages/higgsfield.html">Higgsfield</a></td><td>Starter</td><td>{live("Higgsfield","Starter","$19/mo")}</td><td colspan="2">about $0.99 (sound and length not stated)</td><td>about $1.76 (720p)</td></tr>
</tbody>
</table></div>
<p class="note no-live">Worked out on 2026-11-14 from each plan's monthly price and credits. Kling 3.0 on Kling: 30 credits (720p) or 40 (1080p) per 5 seconds without sound, 45 or 60 with sound, from Kling's pricing page. Kling 4.0 on Kling: about 10 credits per second at 720p and 15 at 1080p, measured by testers because Kling's pricing page doesn't list it. Higgsfield: its own estimates of 14 credits per Kling 3.0 video and 25 credits per 5-second Kling 4.0 clip at 720p.</p>
<h2>What the numbers mean</h2>
<h3>If you use sound anyway, Kling 4.0 is a small step up</h3>
<p>Kling 4.0 always makes sound together with the picture. Compared with Kling 3.0 with sound switched on, it only costs a few cents more per clip on Kling's own plans.</p>
<h3>Without sound, Kling 3.0 is still the cheaper choice</h3>
<p>For silent clips you put music or a voiceover on later, Kling 3.0 without sound is about 40% cheaper than Kling 4.0, and the Standard plan's 660 credits give 22 clips instead of 13.</p>
<h3>Longer clips</h3>
<p>Kling 4.0 makes clips of 3 to 30 seconds. One 30-second 1080p clip uses about 450 credits, two thirds of the Standard plan's credits a month.</p>
<h2>Watch out</h2>
<ul>
<li><strong>Check the button.</strong> Kling shows the credit cost on the generate button before you start; check it for long or high-resolution clips.</li>
<li><strong>First-month discount.</strong> The first month of each Kling plan is 30% off; the prices above are the normal ones.</li>
<li><strong>Free accounts</strong> can try Kling 4.0, but with a watermark and no commercial use.</li>
</ul>
<p>Full details: <a href="/pages/cheapest-way-to-use-kling-4-0-2026.html">where Kling 4.0 is cheapest</a> and <a href="/pages/higgsfield-vs-kling-pricing-2026.html">Higgsfield vs Kling</a>.</p>
<p class="note">Sources: Kling's official pricing page, Higgsfield's pricing and Kling 4.0 pages, and Kling 4.0 credit tests by Genie Artificiel (October 16, 2026). Checked 2026-11-14. Prices change often. Always confirm on the official sites.</p>
""")
CARDS["kling-3-0-vs-kling-4-0-cost-per-clip-2026"] = ("video", "Video", "Kling 3.0 vs Kling 4.0", "What the new model costs extra")

qpath = os.path.join(HERE, "queue.json")
q = json.load(open(qpath, encoding="utf-8"))
have = {i["page"] for i in q["items"]}
n = len(q["items"])
for slug, html in A.items():
    if f"pages/{slug}.html" in have:
        continue
    n += 1
    name = f"{n:02d}-{slug}.html"
    with open(os.path.join(HERE, name), "w", encoding="utf-8") as f:
        f.write(html)
    cls, label, h3, p = CARDS[slug]
    card = (f'<li class="reveal"><a class="art" href="/pages/{slug}.html"><span class="cat {cls}">{label}</span>'
            f"<h3>{h3}</h3><p>{p}</p></a></li>")
    q["items"].append({"file": f"queue/{name}", "page": f"pages/{slug}.html", "card": card, "published": ""})
json.dump(q, open(qpath, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
print(len(q["items"]), "items in the queue")
