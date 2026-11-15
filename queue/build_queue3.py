"""
One-off helper: writes queued articles 11-20 and APPENDS them to queue/queue.json
(it never touches the items that are already there). Numbers checked 2026-11-15.
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


def T(head_cells, rows):
    th = "".join(f"<th>{c}</th>" for c in head_cells)
    tr = "".join("<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>\n" for r in rows)
    return f'<div class="table-scroll"><table>\n<thead><tr>{th}</tr></thead>\n<tbody>\n{tr}</tbody>\n</table></div>'


def a(name, href):
    return f'<a href="{href}">{name}</a>'


SRC = '<p class="note">Sources: the official pricing and help pages of each tool, read by GenCost. Checked 2026-11-15. Prices and rules change often. Always confirm on the official sites.</p>'
A, CARDS = {}, {}

# 11 Do AI credits expire? -------------------------------------------------------------------------
A["do-ai-credits-expire-rollover-rules-2026"] = page(
    "Do AI Credits Expire? Rollover Rules for 21 AI Tools (2026)",
    "Most AI video, voice, image and music tools reset your credits every month. We checked which ones roll over, which expire and what happens to bought credits.",
    "Do AI credits expire?",
    f"""
<h1>Do AI Credits Expire? Rollover Rules for 21 AI Tools (2026)</h1>
<p class="lead">You pay for credits every month, but what happens to the ones you don't use? On most AI tools they simply disappear on your billing date. A few let them build up, and some even take them away when you cancel. Here is what each tool does with your unused credits.</p>
<div class="box">
<strong>Quick answer</strong><br/>
On most AI tools, <strong>unused monthly credits expire</strong> at the end of each billing period.<br/>
Only a few roll over: <strong>Cartesia</strong> (up to 2× your monthly amount), <strong>Captions</strong> (up to 3×), <strong>HeyGen</strong> (one month) and <strong>Runway Max</strong> (one month). Leonardo keeps unused tokens in a bank, up to a cap.<br/>
Credits you <strong>buy separately</strong> usually last longer: 365 days on Pika and Ideogram, forever on Recraft.<br/>
Last checked: 2026-11-15
</div>
<h2>Monthly credits: kept or lost?</h2>
{T(["Tool", "What happens to unused plan credits"], [
 [a("Cartesia", "/pages/voice/cartesia.html"), "Roll over, up to 2× your monthly amount"],
 [a("Captions", "/pages/captions.html"), "Roll over, up to 3× your monthly amount"],
 [a("HeyGen", "/pages/heygen.html"), "Roll over for one month (yearly plans: until renewal); lost when you cancel"],
 [a("Runway", "/pages/runway.html"), "Reset every month on Standard and Pro; only Max rolls over one month"],
 [a("Leonardo", "/pages/leonardo.html"), "Paid plans keep unused tokens in a bank, up to a cap per plan"],
 [a("Freepik", "/pages/freepik.html"), "Credits are given per year and last the whole year"],
 [a("ElevenLabs", "/pages/voice/elevenlabs.html"), "Paid credits expire if you downgrade or cancel"],
 [a("Synthesia", "/pages/synthesia.html"), "Unused minutes and credits don't roll over"],
 [a("Pika", "/pages/pika.html"), "Plan credits don't roll over"],
 [a("PixVerse", "/pages/pixverse.html"), "Expire every 30 days"],
 [a("Viggle", "/pages/viggle.html"), "Expire on your billing date"],
 [a("InVideo", "/pages/invideo.html"), "Don't roll over"],
 [a("Krea", "/pages/krea.html"), "Monthly units don't roll over"],
 [a("Colossyan", "/pages/colossyan.html"), "Unused video minutes don't roll over"],
 [a("Midjourney", "/pages/midjourney.html"), "Unused fast hours expire each month"],
 [a("Ideogram", "/pages/ideogram.html"), "Monthly credits don't roll over"],
 [a("Adobe Firefly", "/pages/firefly.html"), "Reset on your billing date, no rollover"],
 [a("Recraft", "/pages/recraft.html"), "Monthly credits don't roll over"],
 [a("Suno", "/pages/music/suno.html"), "Monthly credits don't carry over"],
 [a("Udio", "/pages/music/udio.html"), "Don't roll over"],
 [a("Fish Audio", "/pages/fish-audio.html"), "Unused minutes don't roll over"],
])}
<h2>Credits you buy on top of your plan</h2>
{T(["Tool", "Top-up credits"], [
 [a("Recraft", "/pages/recraft.html"), "Never expire"],
 [a("Suno", "/pages/music/suno.html"), "Don't expire, but only work while you have an active plan"],
 [a("Pika", "/pages/pika.html"), "Expire after 365 days"],
 [a("Ideogram", "/pages/ideogram.html"), "Last 365 days, used after your monthly credits"],
 [a("Krea", "/pages/krea.html"), "Expire after 90 days"],
 [a("Viggle", "/pages/viggle.html"), "Only work while you have a paid plan"],
 [a("Runway", "/pages/runway.html"), "Minimum purchase 1,000 credits"],
])}
<h2>What this means for your budget</h2>
<h3>Pick the plan for your normal month, not your busiest</h3>
<p>If credits expire, every credit you don't use is money gone. A plan that covers a normal month, plus a top-up in a busy one, is often cheaper than a big plan you only fill now and then. This works best on tools where top-ups last a long time, such as Recraft, Pika or Ideogram.</p>
<h3>Tools that forgive a quiet month</h3>
<p>If your use goes up and down, Cartesia and Captions are the most forgiving: unused credits build up to two or three months' worth. HeyGen keeps them for one extra month.</p>
<h3>Use your credits before you cancel</h3>
<p>On HeyGen and ElevenLabs, unused credits are lost the moment you cancel or downgrade. Use them first, then cancel.</p>
<p>Compare what each plan includes on the <a href="/compare.html">Compare page</a>, or see <a href="/pages/cheapest-way-to-pay-for-ai-tools-yearly-vs-monthly-2026.html">whether paying yearly is worth it</a>.</p>
{SRC}
""")
CARDS["do-ai-credits-expire-rollover-rules-2026"] = ("guide", "Guide", "Do AI credits expire?", "Rollover rules for 21 tools")

# 12 HeyGen tested -----------------------------------------------------------------------------------
A["heygen-cost-per-minute-tested-2026"] = page(
    "What Does a HeyGen Avatar Video Really Cost? We Tested It (2026)",
    "We made three HeyGen avatar videos and counted the credits: about 39 credits per minute. Here is what that means in dollars on every HeyGen plan.",
    "HeyGen cost per minute",
    f"""
<h1>What Does a HeyGen Avatar Video Really Cost? We Tested It (2026)</h1>
<p class="lead">HeyGen sells credits, not minutes, so it's hard to know what a video will cost before you make it. So we tested it ourselves: three short videos with one of HeyGen's ready-made avatars, and we counted exactly how many credits they used.</p>
<div class="box">
<strong>Quick answer</strong><br/>
Our three videos (32, 28 and 39 seconds, 99 seconds in total) used <strong>65 credits</strong>: about <strong>39 credits per minute</strong>.<br/>
That is about <strong>$1.90 per minute</strong> of finished video on Creator and Pro, or about <strong>$1 for a 30-second video</strong>.<br/>
Creator's 600 credits make about 15 minutes of video a month; Pro's 1,000 about 25 minutes.<br/>
Tested: 2026-11-15
</div>
<h2>Our test</h2>
{T(["Video", "Length", "Avatar"], [
 ["1", "32 seconds", "Kurt (public avatar)"],
 ["2", "28 seconds", "Kurt (public avatar)"],
 ["3", "39 seconds", "Kurt (public avatar)"],
 ["<strong>Total</strong>", "<strong>99 seconds</strong>", "<strong>65 credits used</strong>"],
])}
<p class="note no-live">Credits counted from the balance in HeyGen before and after (1,025 → 1,090 used). Vertical 9:16 videos with a script and simple on-screen text.</p>
<h2>What that costs on each plan</h2>
{T(["Plan", "Monthly price", "Credits", "About this much video a month", "Per minute"], [
 [a("Creator", "/pages/heygen.html"), live("HeyGen", "Creator", "$29/mo"), "600", "about 15 minutes", "about $1.89"],
 [a("Creator, paid yearly", "/pages/heygen.html"), live("HeyGen", "Creator", "$24/mo", bill="yearly"), "600", "about 15 minutes", "about $1.57"],
 [a("Pro", "/pages/heygen.html"), live("HeyGen", "Pro", "$49/mo"), "1,000", "about 25 minutes", "about $1.91"],
])}
<p class="note no-live">Worked out on 2026-11-15 from our measured 39 credits per minute and each plan's price and credits.</p>
<h2>What we learned</h2>
<h3>Pro is not cheaper per minute</h3>
<p>Pro gives more credits, but at almost exactly the same price per credit as Creator. Choose Pro for its features or the bigger monthly amount, not to save per minute.</p>
<h3>Short videos are cheap, long ones add up</h3>
<p>A 30-second social video costs about 20 credits, so Creator covers around 30 of them a month. A 10-minute training video would use about 390 credits, two thirds of Creator in one go.</p>
<h3>Other avatars can cost more</h3>
<p>We used a ready-made public avatar. Custom avatars, premium avatar engines and translation use credits faster, so check the cost HeyGen shows before you generate.</p>
<h2>Watch out</h2>
<ul>
<li><strong>Credits roll over only one month</strong> on monthly plans, so don't save them up for long.</li>
<li><strong>Unused credits are lost when you cancel.</strong> Use them first.</li>
<li><strong>Free videos are watermarked.</strong> The free plan gives 3 videos a month.</li>
</ul>
<p>Compare HeyGen with other avatar tools: <a href="/pages/cheapest-ai-avatar-tools-in-2026.html">cheapest AI avatar tools</a> and <a href="/pages/heygen-vs-synthesia-pricing-2026.html">HeyGen vs Synthesia</a>.</p>
<p class="note">Sources: our own test in HeyGen on 2026-11-15, and HeyGen's official pricing page, checked 2026-11-15. Prices change often. Always confirm on the official site.</p>
""")
CARDS["heygen-cost-per-minute-tested-2026"] = ("avatar", "Avatar", "HeyGen: we tested it", "What one minute of avatar video costs")

# 13 Bigger plan better deal? -------------------------------------------------------------------------
A["is-the-bigger-ai-plan-cheaper-price-per-credit-2026"] = page(
    "Is the Bigger AI Plan Really Cheaper? Price per Credit on 20 Tools (2026)",
    "Bigger AI plans usually cost less per credit, but not always. On some tools the bigger plan is the same or even worse per credit. We worked it out plan by plan.",
    "Is the bigger plan cheaper?",
    f"""
<h1>Is the Bigger AI Plan Really Cheaper? Price per Credit on 20 Tools (2026)</h1>
<p class="lead">"Upgrade and save" is the oldest line on any pricing page. We divided every plan's price by its credits to see if it's true. Often it is, and on some tools the savings are big. But on several tools the bigger plan costs the same per credit, and on a few it's even worse.</p>
<div class="box">
<strong>Quick answer</strong><br/>
The biggest savings for upgrading: <strong>Runway</strong> (Max is 58% cheaper per credit than Standard), <strong>Hailuo</strong> (Max 55%), <strong>CapCut</strong> (Ultra 45%) and <strong>InVideo</strong> (Plus 40%).<br/>
Almost <strong>no saving</strong>: HeyGen, Synthesia, Krea, Captions, Ideogram, Dreamina and Magic Hour.<br/>
<strong>Worse per credit</strong> on the bigger plan: Udio Pro and PixVerse Ultra.<br/>
Last checked: 2026-11-15
</div>
<h2>Big savings when you upgrade</h2>
{T(["Tool", "Smallest plan", "Biggest plan", "Saving per credit"], [
 [a("Runway", "/pages/runway.html"), "Standard " + live("Runway", "Standard", "$15/mo") + ", $24 per 1,000 credits", "Max " + live("Runway", "Max", "$95/mo") + ", $10 per 1,000", "58%"],
 [a("Hailuo", "/pages/hailuo.html"), "Standard " + live("Hailuo AI", "Standard", "$14.99/mo") + ", $14.99 per 1,000", "Max $6.81 per 1,000", "55%"],
 [a("CapCut", "/pages/capcut.html"), "Pro " + live("CapCut", "Pro", "$19.99/mo") + ", $16.66 per 1,000", "Ultra " + live("CapCut", "Ultra", "$79/mo") + ", $9.14 per 1,000", "45%"],
 [a("InVideo", "/pages/invideo.html"), "Starter " + live("InVideo", "Starter", "$20/mo") + ", $50 per 1,000", "Plus and Max, $30 per 1,000", "40%"],
 [a("Higgsfield", "/pages/higgsfield.html"), "Starter " + live("Higgsfield", "Starter", "$19/mo") + ", $70 per 1,000", "Ultra " + live("Higgsfield", "Ultra", "$129/mo") + ", $43 per 1,000", "39%"],
 [a("LTX Studio", "/pages/ltx.html"), "Lite, $1.88 per 1,000", "Pro, $1.14 per 1,000", "39%"],
 [a("OpenArt", "/pages/openart.html"), "Starter, $3.50 per 1,000", "Wonder, $2.26 per 1,000", "35%"],
 [a("Pika", "/pages/pika.html"), "Starter " + live("Pika", "Starter", "$10/mo") + ", $16.67 per 1,000", "Fancy, $11.11 per 1,000", "33%"],
 [a("Luma", "/pages/luma.html"), "Plus " + live("Luma", "Plus", "$30/mo") + ", $3 per 1,000", "Ultra, $2 per 1,000", "33%"],
 [a("Kling AI", "/pages/kling.html"), "Standard " + live("Kling AI", "Standard", "$8.80/mo") + ", $13.33 per 1,000", "Ultra+, $9.56 per 1,000", "28%"],
])}
<h2>Little or no saving</h2>
{T(["Tool", "Price per 1,000 credits, smallest → biggest plan", "Saving"], [
 [a("HeyGen", "/pages/heygen.html"), "Creator $48.33 → Pro $49.00", "none (Pro is slightly more)"],
 [a("Synthesia", "/pages/synthesia.html"), "Starter $15.20 → Pro $14.83", "2%"],
 [a("Krea", "/pages/krea.html"), "Basic $1.80 → Max $1.75", "3%"],
 [a("Captions", "/pages/captions.html"), "$50 on every plan", "none"],
 [a("Ideogram", "/pages/ideogram.html"), "Plus $8.33 → Pro $8.00", "4%"],
 [a("Dreamina", "/pages/dreamina.html"), "Basic $9.52 → Ultra $8.81", "7%"],
 [a("Magic Hour", "/pages/magic-hour.html"), "Creator $1.58 → Business $1.41", "11%"],
 [a("Midjourney", "/pages/midjourney.html"), "Standard, Pro and Mega all cost the same per fast hour", "none above Standard"],
])}
<h2>Bigger plan, worse price per credit</h2>
<ul>
<li><strong><a href="/pages/music/udio.html">Udio</a>:</strong> Standard gives 2,400 credits for {live("Udio", "Standard", "$10/mo")} ($4.17 per 1,000); Pro gives 6,000 for {live("Udio", "Pro", "$30/mo")} ($5.00 per 1,000). Pro costs 20% more per credit.</li>
<li><strong><a href="/pages/pixverse.html">PixVerse</a>:</strong> Premium is the best value at $4 per 1,000 credits. Ultra costs about $10 per 1,000, so check what extra it includes before you pay for it.</li>
</ul>
<p class="note no-live">Worked out on 2026-11-15 from each plan's monthly price and monthly credits. Per-credit prices are rounded.</p>
<h2>How to use this</h2>
<h3>Upgrade only where it pays</h3>
<p>On Runway, Hailuo, CapCut and InVideo, moving up one plan can cut the cost of every clip by a third or more, if you really use the credits. On HeyGen, Synthesia, Krea or Captions you pay the same per credit either way, so pick the plan that fits your month.</p>
<h3>A "price cut" can be a smaller plan</h3>
<p>When a plan suddenly costs less, check the credits too. In November 2026 Dreamina's Advanced plan went from $159 to $79 a month, but its credits went from 17,600 to 8,645, so the price per credit hardly changed.</p>
<p>See what one clip costs on every plan in the <a href="/clip.html">cheapest clip finder</a>.</p>
{SRC}
""")
CARDS["is-the-bigger-ai-plan-cheaper-price-per-credit-2026"] = ("guide", "Guide", "Is the bigger plan cheaper?", "Price per credit on 20 tools")

# 14 Audiobook / voiceover per hour ---------------------------------------------------------------
A["ai-voice-cost-per-hour-audiobook-voiceover-2026"] = page(
    "What Does an Hour of AI Voice Cost? Audiobooks and Voiceovers (2026)",
    "We worked out what one hour of AI narration costs on ElevenLabs, Cartesia, Fish Audio, Murf and Fliki, and what a 10-hour audiobook would cost.",
    "AI voice cost per hour",
    f"""
<h1>What Does an Hour of AI Voice Cost? Audiobooks and Voiceovers (2026)</h1>
<p class="lead">AI voice tools sell characters or credits, but what you really want to know is: what does an hour of finished narration cost? We converted every plan into hours of speech, and worked out what a 10-hour audiobook would cost.</p>
<div class="box">
<strong>Quick answer</strong><br/>
The cheapest per hour: <strong>Cartesia</strong> (about $1.80 to $2.40 an hour) and <strong>Fish Audio</strong> (about $1.80 to $2.20 an hour).<br/>
<strong>ElevenLabs</strong>, the best-known, costs about <strong>$8 to $10 an hour</strong>.<br/>
A 10-hour audiobook: about <strong>$20</strong> on Cartesia or Fish Audio, about <strong>$80</strong> on ElevenLabs.<br/>
Last checked: 2026-11-15
</div>
<h2>Hours of speech per plan</h2>
{T(["Tool", "Plan", "Monthly price", "About this much speech", "Per hour"], [
 [a("Cartesia", "/pages/voice/cartesia.html"), "Pro", live("Cartesia", "Pro", "$5/mo"), "about 2 hours", "about $2.40"],
 [a("Cartesia", "/pages/voice/cartesia.html"), "Startup", live("Cartesia", "Startup", "$49/mo"), "about 26 hours", "about $1.90"],
 [a("Fish Audio", "/pages/fish-audio.html"), "Plus", live("Fish Audio", "Plus", "$15/mo"), "about 7 hours", "about $2.20"],
 [a("Fish Audio", "/pages/fish-audio.html"), "Pro", live("Fish Audio", "Pro", "$100/mo"), "about 54 hours", "about $1.85"],
 [a("ElevenLabs", "/pages/voice/elevenlabs.html"), "Starter", live("ElevenLabs", "Starter", "$6/mo"), "about 37 minutes", "about $9.60"],
 [a("ElevenLabs", "/pages/voice/elevenlabs.html"), "Creator", live("ElevenLabs", "Creator", "$22/mo"), "about 2.5 hours", "about $8.70"],
 [a("ElevenLabs", "/pages/voice/elevenlabs.html"), "Pro", live("ElevenLabs", "Pro", "$99/mo"), "about 12.5 hours", "about $7.90"],
 [a("Murf AI", "/pages/voice/murf.html"), "Creator", live("Murf AI", "Creator", "$19/mo"), "about 2 hours (24 hours a year)", "about $9.50"],
 [a("Fliki", "/pages/voice/fliki.html"), "Standard", live("Fliki", "Standard", "$28/mo"), "about 3 hours of content", "about $9.30"],
])}
<p class="note no-live">Worked out on 2026-11-15. Cartesia and ElevenLabs: about 1 credit per character and about 48,000 characters in an hour of speech (Cartesia says 750 to 800 credits per minute). Fish Audio: about 600 to 625 credits per minute. Murf: 24 hours of voice a year on Creator. Fliki: credits are roughly minutes of content. Real numbers depend on the voice, the model and how fast it speaks.</p>
<h2>What a 10-hour audiobook costs</h2>
{T(["Tool", "Plan that covers it", "About"], [
 [a("Cartesia", "/pages/voice/cartesia.html"), "Startup (one month)", "$49, or about $19 worth of credits"],
 [a("Fish Audio", "/pages/fish-audio.html"), "Plus for two months, or Pro", "about $18 to $22 worth of credits"],
 [a("ElevenLabs", "/pages/voice/elevenlabs.html"), "Pro (one month)", "$99, or about $79 worth of credits"],
 [a("Murf AI", "/pages/voice/murf.html"), "Creator (five months of hours)", "about $95"],
])}
<p class="note no-live">A 10-hour book is roughly 90,000 words. You usually pay for a whole plan, so the real cost is the plan you need, not just the credits used.</p>
<h2>What the numbers mean</h2>
<h3>Price isn't the only thing</h3>
<p>ElevenLabs costs four times as much per hour, but it has the biggest choice of voices and languages and very natural speech. For a long audiobook, listen to samples from each tool before you choose: the cheapest voice is only cheap if you're happy with it.</p>
<h3>Retakes cost credits too</h3>
<p>Every time you regenerate a sentence, you pay again. Plan for 10 to 30% extra on a long project.</p>
<h3>Check the rules where you publish</h3>
<p>All the paid plans above include commercial use, but free plans don't. Audiobook stores have their own rules about AI narration, so check them before you start.</p>
<p>More voice tools: <a href="/pages/cheapest-ai-voice-tools-in-2026.html">cheapest AI voice tools</a> and <a href="/pages/elevenlabs-vs-cartesia-pricing-2026.html">ElevenLabs vs Cartesia</a>.</p>
{SRC}
""")
CARDS["ai-voice-cost-per-hour-audiobook-voiceover-2026"] = ("voice", "Voice", "AI voice cost per hour", "Audiobooks and voiceovers")

# 15 Are your AI images public? -------------------------------------------------------------------
A["are-your-ai-images-public-2026"] = page(
    "Are Your AI Images Public? Privacy on Midjourney, Leonardo, Ideogram and More (2026)",
    "On several AI image tools, the pictures you make can be seen by everyone. We checked which plans keep your images private, and what that costs.",
    "Are your AI images public?",
    f"""
<h1>Are Your AI Images Public? Privacy on Midjourney, Leonardo, Ideogram and More (2026)</h1>
<p class="lead">Many people don't know that on some AI image tools, everything they make shows up in a public gallery that anyone can browse. That matters if you're making images for a client, a product launch or anything private. Here is which plans keep your images private.</p>
<div class="box">
<strong>Quick answer</strong><br/>
<strong>Midjourney:</strong> images are public on Basic and Standard. Private images (Stealth Mode) start on <strong>Pro</strong>, {live("Midjourney", "Pro", "$60/mo")}.<br/>
<strong>Ideogram:</strong> free images are public; private from <strong>Plus</strong>, {live("Ideogram", "Plus", "$20/mo")}.<br/>
<strong>Leonardo</strong> and <strong>Recraft</strong>: free-plan images are public; paid plans are the way out.<br/>
Last checked: 2026-11-15
</div>
<h2>Which plans keep your images private</h2>
{T(["Tool", "Public", "Private from", "Price"], [
 [a("Midjourney", "/pages/midjourney.html"), "Basic and Standard", "Pro (Stealth Mode)", live("Midjourney", "Pro", "$60/mo")],
 [a("Ideogram", "/pages/ideogram.html"), "Free", "Plus", live("Ideogram", "Plus", "$20/mo")],
 [a("Leonardo", "/pages/leonardo.html"), "Free", "a paid plan, from Essential", live("Leonardo", "Essential", "$12/mo")],
 [a("Recraft", "/pages/recraft.html"), "Free", "a paid plan, from Basic", live("Recraft", "Basic", "$12/mo")],
])}
<h2>Rights come with it</h2>
<ul>
<li><strong>Midjourney:</strong> companies earning more than $1 million a year must use Pro or Mega anyway.</li>
<li><strong>Leonardo:</strong> on the free plan, Leonardo holds the rights to your images.</li>
<li><strong>Recraft:</strong> free images may not be used commercially, and commercial rights only last while you subscribe.</li>
<li><strong>OpenArt:</strong> no commercial use on Starter.</li>
</ul>
<h2>What this means</h2>
<h3>On Midjourney, privacy means a $60 plan</h3>
<p>Pro costs twice as much as Standard but also gives twice the fast hours, at the same price per hour. So privacy doesn't cost more per image, but you have to buy at least $60 a month to get it. If your images don't need to be secret, Standard is the cheaper way in.</p>
<h3>For client work, budget for the private plan</h3>
<p>A client's new logo or product photo showing up in a public gallery before launch is a real risk. The cheapest private option on this list is Leonardo Essential or Recraft Basic at about $12 a month.</p>
<p>More image tools: <a href="/pages/cheapest-ai-image-generators-2026.html">cheapest AI image generators</a> and <a href="/pages/midjourney-vs-ideogram-pricing-2026.html">Midjourney vs Ideogram</a>.</p>
{SRC}
""")
CARDS["are-your-ai-images-public-2026"] = ("image", "Image", "Are your AI images public?", "Which plans keep them private")

# 16 Who owns AI music ------------------------------------------------------------------------------
A["who-owns-your-ai-music-commercial-rights-2026"] = page(
    "Who Owns Your AI Song? Commercial Rights on Suno, Udio, AIVA and More (2026)",
    "On free plans of most AI music tools, you can't sell or even download your songs. We checked which plan gives you commercial rights on each tool, and what it costs.",
    "Who owns your AI song?",
    f"""
<h1>Who Owns Your AI Song? Commercial Rights on Suno, Udio, AIVA and More (2026)</h1>
<p class="lead">Made a great song with AI and want to put it on YouTube, Spotify or in an ad? Then the plan you made it on matters. On most free plans you can't use the music commercially, and on some you can't even download it. Here is what each tool allows.</p>
<div class="box">
<strong>Quick answer</strong><br/>
For commercial use you need a paid plan on almost every tool: <strong>Suno Pro</strong> {live("Suno", "Pro", "$10/mo")}, <strong>Udio Standard</strong> {live("Udio", "Standard", "$10/mo")}, <strong>Mureka Pro</strong> {live("Mureka", "Pro", "$8/mo")}.<br/>
<strong>Stable Audio</strong> is the exception: its free plan includes a commercial license.<br/>
On <strong>AIVA</strong> you only own the copyright on <strong>Pro</strong>.<br/>
Last checked: 2026-11-15
</div>
<h2>Free plan vs paid plan</h2>
{T(["Tool", "Free plan", "Commercial use from"], [
 [a("Suno", "/pages/music/suno.html"), "No downloads, no commercial rights", "Pro " + live("Suno", "Pro", "$10/mo") + " (20 song downloads a month)"],
 [a("Udio", "/pages/music/udio.html"), "10 credits a day, max 3 full songs a day", "a paid plan, from Standard " + live("Udio", "Standard", "$10/mo")],
 [a("Mureka", "/pages/mureka.html"), "No commercial rights", "Pro " + live("Mureka", "Pro", "$8/mo") + ", also for songs made before you upgraded"],
 [a("Stable Audio", "/pages/stable-audio.html"), "About 12 full mixes a month, <strong>with</strong> a commercial license", "Free"],
 [a("Boomy", "/pages/music/boomy.html"), "No downloads, no commercial use", "Creator " + live("Boomy", "Creator", "$9.99/mo") + ", with streaming distribution"],
 [a("AIVA", "/pages/music/aiva.html"), "AIVA owns the copyright; you must credit AIVA and can't monetize", "Pro " + live("AIVA", "Pro", "$36.86/mo") + " (you own the copyright)"],
 [a("Soundraw", "/pages/music/soundraw.html"), "No free plan in our data", "Creator " + live("Soundraw", "Creator", "$16.99/mo") + ", for individuals and companies under 10 employees"],
])}
<h2>What this means</h2>
<h3>Make it on the right plan</h3>
<p>If you plan to use a song commercially, make it while you're on a paid plan, and check the tool's terms for songs made earlier on the free plan. Mureka is clear about it: its paid plans also cover songs you made before upgrading.</p>
<h3>Owning the copyright is not the same as a license</h3>
<p>Most tools give you a license to use the music. AIVA is clear that you only own the full copyright on Pro. If owning the music matters, for example for a record release, read the tool's terms before you start.</p>
<h3>Bigger companies need bigger plans</h3>
<p>Soundraw's normal plans are for people and companies under 10 employees; bigger ones need Enterprise.</p>
<p>More music tools: <a href="/pages/cheapest-ai-music-tools-in-2026.html">cheapest AI music tools</a> and <a href="/pages/suno-vs-udio-pricing-2026.html">Suno vs Udio</a>.</p>
<p class="note">Sources: the official pricing and terms pages of each tool, read by GenCost. Checked 2026-11-15. This is a summary, not legal advice. Always read the tool's own terms before you publish or sell music.</p>
""")
CARDS["who-owns-your-ai-music-commercial-rights-2026"] = ("music", "Music", "Who owns your AI song?", "Commercial rights, tool by tool")

# 17 First-month discounts -------------------------------------------------------------------------
A["ai-tools-first-month-discount-real-price-2026"] = page(
    "AI Tool First-Month Deals: What You Really Pay After Month One (2026)",
    "Many AI tools advertise a cheap first month. We listed the first-month price and the normal price after it, so you know what your second bill will be.",
    "First-month deals",
    f"""
<h1>AI Tool First-Month Deals: What You Really Pay After Month One (2026)</h1>
<p class="lead">$1 for the first month, 30% off, half price: AI tools love first-month deals. They are a good way to try a tool, but the second bill is often a surprise. Here is the first-month price and what you pay after that.</p>
<div class="box">
<strong>Quick answer</strong><br/>
The biggest jumps after month one: <strong>Dreamina Basic</strong> ($0.29, then {live("Dreamina", "Basic", "$15/mo")}), <strong>ElevenLabs Starter</strong> ($1, then {live("ElevenLabs", "Starter", "$6/mo")}) and <strong>Synthesia Starter</strong> ($9, then {live("Synthesia", "Starter", "$19/mo")}).<br/>
<strong>Kling AI</strong> gives 30% off the first month of every plan.<br/>
Last checked: 2026-11-15
</div>
<h2>First month vs every month after</h2>
{T(["Tool", "Plan", "First month", "After that"], [
 [a("Dreamina", "/pages/dreamina.html"), "Basic", "$0.29", live("Dreamina", "Basic", "$15/mo")],
 [a("Dreamina", "/pages/dreamina.html"), "Standard", "$21.60", live("Dreamina", "Standard", "$36/mo")],
 [a("Dreamina", "/pages/dreamina.html"), "Advanced", "$31.60", live("Dreamina", "Advanced", "$79/mo")],
 [a("ElevenLabs", "/pages/voice/elevenlabs.html"), "Starter", "$1", live("ElevenLabs", "Starter", "$6/mo")],
 [a("ElevenLabs", "/pages/voice/elevenlabs.html"), "Creator", "$11", live("ElevenLabs", "Creator", "$22/mo")],
 [a("Synthesia", "/pages/synthesia.html"), "Starter", "$9", live("Synthesia", "Starter", "$19/mo")],
 [a("Synthesia", "/pages/synthesia.html"), "Pro", "$49", live("Synthesia", "Pro", "$89/mo")],
 [a("Kling AI", "/pages/kling.html"), "Standard", "$6.99", live("Kling AI", "Standard", "$8.80/mo")],
 [a("Kling AI", "/pages/kling.html"), "Pro", "$25.99", live("Kling AI", "Pro", "$32.56/mo")],
 [a("D-ID", "/pages/d-id.html"), "Lite, Pro, Advanced", "Unlimited videos in the first month", "the normal plan limits"],
 [a("CapCut", "/pages/capcut.html"), "Pro, Ultra", "Lower Seedance 2.5 per-second prices", "the normal per-second prices"],
])}
<p class="note no-live">First-month prices as shown on each official pricing page on 2026-11-15. Offers change often.</p>
<h2>How to use first-month deals well</h2>
<h3>Test hard in month one</h3>
<p>A $1 or $0.29 month is a cheap way to find out if a tool fits you. Use it fully: make the kind of clips, voices or songs you really need, and count how many credits they use.</p>
<h3>Set a reminder before the second bill</h3>
<p>All these plans renew automatically at the full price. Put a reminder in your calendar a few days before the renewal date, and cancel if you're not sure.</p>
<h3>Compare the normal prices, not the deals</h3>
<p>A tool that is cheap for one month can be expensive for a year. Dreamina Basic costs about $165 in the first year; Kling Standard about $104. GenCost always shows the normal price, so you can compare like with like.</p>
<p>Compare normal prices on the <a href="/compare.html">Compare page</a>, or see <a href="/pages/cheapest-way-to-pay-for-ai-tools-yearly-vs-monthly-2026.html">yearly vs monthly</a>.</p>
{SRC}
""")
CARDS["ai-tools-first-month-discount-real-price-2026"] = ("guide", "Guide", "First-month deals", "What you pay after month one")

# 18 720p vs 1080p and sound ----------------------------------------------------------------------
A["ai-video-720p-vs-1080p-and-sound-cost-2026"] = page(
    "720p vs 1080p AI Video: How Much More Does HD Cost? (2026)",
    "Switching from 720p to 1080p can cost 1.3 to 4 times as many credits, depending on the tool and model. We compared resolution and sound settings tool by tool.",
    "720p vs 1080p cost",
    f"""
<h1>720p vs 1080p AI Video: How Much More Does HD Cost? (2026)</h1>
<p class="lead">The resolution button is the easiest way to blow your credits. On some tools 1080p costs half as much again as 720p; on others it costs four times as much. Sound can add another 50%. Here is how much each setting costs, tool by tool.</p>
<div class="box">
<strong>Quick answer</strong><br/>
For <strong>Kling 4.0</strong>, 1080p costs about <strong>1.5×</strong> the credits of 720p on every platform we checked.<br/>
For <strong>Seedance 2.5</strong>, 1080p costs about <strong>1.7× to 2.5×</strong> as much.<br/>
For <strong>Luma's Ray3.2</strong>, 1080p costs <strong>4×</strong> as much as 720p.<br/>
On Kling 3.0, turning <strong>sound on</strong> adds 50%.<br/>
Last checked: 2026-11-15
</div>
<h2>Credits for one 5-second clip</h2>
{T(["Tool", "Model", "720p", "1080p", "1080p costs"], [
 [a("Kling AI", "/pages/kling.html"), "Kling 4.0 (with sound)", "50", "75", "1.5×"],
 [a("Higgsfield", "/pages/higgsfield.html"), "Kling 4.0", "25", "37.5", "1.5×"],
 [a("Elyum", "/pages/elyum.html"), "Kling 4.0", "85", "125", "1.5×"],
 [a("Luma", "/pages/luma.html"), "Kling 4.0", "265", "395", "1.5×"],
 [a("Kling AI", "/pages/kling.html"), "Kling 3.0, no sound", "30", "40", "1.3×"],
 [a("InVideo", "/pages/invideo.html"), "Seedance 2.5", "56", "96", "1.7×"],
 [a("Pika", "/pages/pika.html"), "Seedance 2.5", "122", "299", "2.5×"],
 [a("Luma", "/pages/luma.html"), "Seedance 2.5", "390", "955", "2.4×"],
 [a("Luma", "/pages/luma.html"), "Ray3.2", "100", "400", "4×"],
 [a("Hailuo", "/pages/hailuo.html"), "MiniMax H3, 768p vs 2K (6 seconds)", "42", "71", "1.7×"],
])}
<p class="note no-live">Credits per clip from each tool's official pricing page or app, 2026-11-15. Credits are different on every tool, so compare the "1080p costs" column, or see dollars per clip in the <a href="/clip.html">cheapest clip finder</a>.</p>
<h2>Sound on or off</h2>
{T(["Kling 3.0 on Kling AI, 5 seconds", "No sound", "With sound", "Sound adds"], [
 ["720p", "30 credits", "45 credits", "50%"],
 ["1080p", "40 credits", "60 credits", "50%"],
])}
<p>Kling 4.0, Seedance 2.5 and Veo 3.1 always make sound together with the picture, so you can't save by turning it off there.</p>
<h2>How to save</h2>
<h3>Draft in low resolution, finish in high</h3>
<p>Try your prompt at 720p (or 480p or 540p where offered) until you like the motion, then make the final version at 1080p. On Luma, ten Ray3.2 drafts at 720p cost the same as two and a half clips at 1080p.</p>
<h3>Ask if you really need 1080p</h3>
<p>On a phone screen, most viewers can't see the difference between 720p and 1080p in a short social clip. For TikTok, Reels and Shorts, 720p is often enough.</p>
<h3>Add sound later if it's cheaper</h3>
<p>On Kling 3.0, a silent clip plus music from a separate tool can be cheaper than generating sound with the video.</p>
<p>See what each setting costs in dollars in the <a href="/clip.html">cheapest clip finder</a>, or read <a href="/pages/cheapest-ai-video-cost-per-second-2026.html">AI video cost per second</a>.</p>
{SRC}
""")
CARDS["ai-video-720p-vs-1080p-and-sound-cost-2026"] = ("video", "Video", "720p vs 1080p", "How much more HD and sound cost")

# 19 30-second ad ------------------------------------------------------------------------------------
A["cost-of-a-30-second-ai-ad-video-voice-music-2026"] = page(
    "What Does a 30-Second AI Ad Cost? Video, Voice and Music Together (2026)",
    "A 30-second ad needs video, a voiceover and music, often from three different AI tools. We worked out the cheapest combination and a better-quality one.",
    "Cost of a 30-second AI ad",
    f"""
<h1>What Does a 30-Second AI Ad Cost? Video, Voice and Music Together (2026)</h1>
<p class="lead">One AI tool rarely does it all. A short ad needs moving pictures, a voice and music, and each comes from a different tool with its own plan. We put together a budget combination and a better-quality one, with commercial rights on every part.</p>
<div class="box">
<strong>Quick answer</strong><br/>
<strong>Budget:</strong> Kling Standard + Cartesia Pro + Stable Audio Free = about <strong>$14 a month</strong>, enough for about 3 ads (about $2.50 of credits per ad).<br/>
<strong>Better quality:</strong> Kling Pro + ElevenLabs Starter + Suno Pro = about <strong>$49 a month</strong>, enough for about 10 ads with Kling 4.0 (about $3.85 per ad, including the song).<br/>
Last checked: 2026-11-15
</div>
<h2>The budget combination</h2>
{T(["Part", "Tool and plan", "Monthly price", "One ad uses"], [
 ["Video: six 5-second clips, Kling 3.0, 720p, no sound", a("Kling AI", "/pages/kling.html") + " Standard", live("Kling AI", "Standard", "$8.80/mo"), "180 of 660 credits"],
 ["Voiceover: about 75 words", a("Cartesia", "/pages/voice/cartesia.html") + " Pro", live("Cartesia", "Pro", "$5/mo"), "about 450 of 100,000 credits"],
 ["Music: one track", a("Stable Audio", "/pages/stable-audio.html") + " Free (commercial license)", "$0", "1 of about 12 free mixes"],
])}
<h2>The better-quality combination</h2>
{T(["Part", "Tool and plan", "Monthly price", "One ad uses"], [
 ["Video: six 5-second clips, Kling 4.0, 720p", a("Kling AI", "/pages/kling.html") + " Pro", live("Kling AI", "Pro", "$32.56/mo"), "300 of 3,000 credits"],
 ["Voiceover: about 75 words", a("ElevenLabs", "/pages/voice/elevenlabs.html") + " Starter", live("ElevenLabs", "Starter", "$6/mo"), "about 450 of 30,000 credits"],
 ["Music: one song", a("Suno", "/pages/music/suno.html") + " Pro", live("Suno", "Pro", "$10/mo"), "1 of 20 song downloads"],
])}
<p class="note no-live">Worked out on 2026-11-15. Video: 30 credits per 5-second Kling 3.0 clip at 720p without sound, and about 50 credits per 5-second Kling 4.0 clip at 720p with sound. Voice: about 1 credit per character. Every plan listed includes commercial use.</p>
<h2>What the numbers mean</h2>
<h3>The video is the expensive part</h3>
<p>The voice and music cost a few cents per ad. Almost all the money goes to the video clips, so that is where to compare prices: see where your model is cheapest in the <a href="/clip.html">cheapest clip finder</a>.</p>
<h3>Plan for retries</h3>
<p>The numbers assume every clip works the first time. If you make two or three tries per clip you keep, the video part costs two or three times as much: the budget plan then covers one ad a month.</p>
<h3>Making many ads?</h3>
<p>Bigger video plans cost less per credit on most tools. See <a href="/pages/is-the-bigger-ai-plan-cheaper-price-per-credit-2026.html">is the bigger plan really cheaper</a>.</p>
<p>For a longer video, see <a href="/pages/cheapest-way-to-make-a-60-second-ai-video-2026.html">what a 60-second AI video costs</a>.</p>
{SRC}
""")
CARDS["cost-of-a-30-second-ai-ad-video-voice-music-2026"] = ("guide", "Guide", "Cost of a 30-second AI ad", "Video, voice and music together")

# 20 Credits are not comparable ---------------------------------------------------------------------
A["why-ai-credits-are-not-comparable-2026"] = page(
    "Why 1,000 AI Credits Mean Something Different on Every Tool (2026)",
    "1,000 credits cost $1.14 on one AI tool and $125 on another. We explain why credits can't be compared, and how to compare AI tools the right way.",
    "Why credits aren't comparable",
    f"""
<h1>Why 1,000 AI Credits Mean Something Different on Every Tool (2026)</h1>
<p class="lead">Every AI tool counts in its own credits, and they are not worth the same. 1,000 credits cost as little as about $1.14 on LTX Studio's Pro plan and about $125 on Viggle Pro. That doesn't make one tool 100 times cheaper: a clip simply uses a very different number of credits on each. Here is how to compare them the right way.</p>
<div class="box">
<strong>Quick answer</strong><br/>
Credits are a different currency on every tool, so <strong>never compare credit counts between tools</strong>.<br/>
The same 5-second Kling 4.0 clip at 720p uses <strong>25 credits on Higgsfield, 50 on Kling AI, 85 on Elyum and 265 on Luma</strong>, yet the dollar cost is in the same range.<br/>
Compare <strong>dollars per clip</strong>, per minute or per image instead.<br/>
Last checked: 2026-11-15
</div>
<h2>What 1,000 credits cost</h2>
{T(["Tool", "Smallest paid plan", "Price per 1,000 credits"], [
 [a("LTX Studio", "/pages/ltx.html"), "Lite", "about $1.88"],
 [a("Krea", "/pages/krea.html"), "Basic", "about $1.80"],
 [a("Magic Hour", "/pages/magic-hour.html"), "Creator", "about $1.58"],
 [a("Luma", "/pages/luma.html"), "Plus", "about $3"],
 [a("Kling AI", "/pages/kling.html"), "Standard", "about $13.33"],
 [a("Runway", "/pages/runway.html"), "Standard", "about $24"],
 [a("HeyGen", "/pages/heygen.html"), "Creator", "about $48"],
 [a("Higgsfield", "/pages/higgsfield.html"), "Starter", "about $70"],
 [a("Viggle", "/pages/viggle.html"), "Pro", "about $125"],
])}
<h2>The same clip in credits and in dollars</h2>
{T(["Where", "Credits for one 5-second Kling 4.0 clip, 720p", "Plan used", "About in dollars"], [
 [a("Higgsfield", "/pages/higgsfield.html"), "25", "Starter " + live("Higgsfield", "Starter", "$19/mo"), "$1.76"],
 [a("Kling AI", "/pages/kling.html"), "50", "Pro " + live("Kling AI", "Pro", "$32.56/mo"), "$0.54"],
 [a("Elyum", "/pages/elyum.html"), "85", "Plus " + live("Elyum", "Plus", "$9/mo"), "$0.85"],
 [a("Luma", "/pages/luma.html"), "265", "Plus " + live("Luma", "Plus", "$30/mo"), "$0.80"],
])}
<p class="note no-live">Worked out on 2026-11-15 from each plan's monthly price, credits and the credits per clip on each platform.</p>
<p>Higgsfield uses the fewest credits for the clip but is the most expensive in dollars; Luma uses ten times as many credits and costs less than half as much. Credit counts alone tell you nothing.</p>
<h2>How to compare AI tools the right way</h2>
<ol>
<li><strong>Pick what you make:</strong> a 5-second clip, a minute of voice, one image or one song.</li>
<li><strong>Find its credits</strong> on each tool, at the same model and resolution.</li>
<li><strong>Divide the plan price by the plan's credits</strong> and multiply by the credits per clip.</li>
<li><strong>Add retries:</strong> if a clip takes two tries, double it.</li>
</ol>
<p>Or let GenCost do it: the <a href="/clip.html">cheapest clip finder</a> shows the dollar cost of one clip on every platform, with today's prices.</p>
<p>More: <a href="/pages/is-the-bigger-ai-plan-cheaper-price-per-credit-2026.html">is the bigger plan really cheaper?</a> and <a href="/pages/cheapest-ai-video-cost-per-second-2026.html">AI video cost per second</a>.</p>
{SRC}
""")
CARDS["why-ai-credits-are-not-comparable-2026"] = ("guide", "Guide", "Why credits aren't comparable", "1,000 credits: $1 or $125?")

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
