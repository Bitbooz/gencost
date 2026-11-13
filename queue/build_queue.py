"""
One-off helper: writes the queued articles (queue/*.html) from a shared page template.
Run once by hand; the daily job only uses publish_queue.py and queue/queue.json.
"""
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SRC = os.path.join(ROOT, "pages", "cheapest-way-to-use-kling-4-0-2026.html")

raw = open(SRC, encoding="utf-8").read()
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


A = {}

# 1 ---------------------------------------------------------------------------------------------
A["cheapest-way-to-make-a-60-second-ai-video-2026"] = page(
    "What Does a 60-Second AI Video Cost? 12 Tools Compared (2026)",
    "What one minute of finished AI video really costs on Veo, Vidu, Luma, Pika, Kling, CapCut, Runway and more, on each tool's cheapest plan, with and without retries.",
    "60-second AI video cost",
    f"""
<h1>What Does a 60-Second AI Video Cost? 12 Tools Compared (2026)</h1>
<p class="lead">AI video tools sell credits, not minutes, so it is hard to tell what one minute of finished video will cost. We took each tool's cheapest paid plan and worked out what 60 seconds of video costs, made of short clips, at the resolution and model listed. The cheapest options cost under $2 a minute; the most expensive cost more than ten times as much, and two plans don't even include enough credits for one minute.</p>
<div class="box">
<strong>Quick answer</strong><br/>
Cheapest per minute: <strong>Google AI Pro</strong> with Veo Lite in Flow, about $1.50, and <strong>Vidu Standard</strong> at 540p, also about $1.50.<br/>
Cheapest at 720p with a big name: <strong>Luma Plus</strong> (Ray3.2), about $3.60, and <strong>Pika Starter</strong> (Pika 2.5), about $4.00.<br/>
Most expensive: Seedance 2.5 on <strong>Dreamina Basic</strong> and <strong>InVideo Plus</strong>, about $20 to $21. <strong>Runway Standard</strong> and Dreamina Basic don't even include enough credits for a full minute.<br/>
Last checked: 2026-11-13
</div>
<h2>One minute of AI video, tool by tool</h2>
<div class="table-scroll"><table>
<thead><tr><th>Tool</th><th>Plan</th><th>Monthly price</th><th>Model</th><th>60 seconds</th><th>With 3 tries per clip</th><th>Video per month on the plan</th></tr></thead>
<tbody>
<tr><td><a href="/pages/veo.html">Google Veo</a></td><td>Google AI Pro</td><td>{live("Google Veo","Google AI Pro","$19.99/mo")}</td><td>Veo Lite in Flow</td><td>about $1.50</td><td>about $4.50</td><td>about 13 minutes</td></tr>
<tr><td><a href="/pages/vidu.html">Vidu</a></td><td>Standard</td><td>{live("Vidu","Standard","$10/mo")}</td><td>Vidu Q4, 540p</td><td>about $1.50</td><td>about $4.50</td><td>almost 7 minutes</td></tr>
<tr><td><a href="/pages/veo.html">Google Veo</a></td><td>Google AI Pro</td><td>{live("Google Veo","Google AI Pro","$19.99/mo")}</td><td>Veo Fast in Flow</td><td>about $3.00</td><td>about $9.00</td><td>almost 7 minutes</td></tr>
<tr><td><a href="/pages/luma.html">Luma</a></td><td>Plus</td><td>{live("Luma","Plus","$30/mo")}</td><td>Ray3.2, 720p</td><td>about $3.60</td><td>about $10.80</td><td>about 8 minutes</td></tr>
<tr><td><a href="/pages/pika.html">Pika</a></td><td>Starter</td><td>{live("Pika","Starter","$10/mo")}</td><td>Pika 2.5, 720p</td><td>about $4.00</td><td>about $12.00</td><td>2.5 minutes</td></tr>
<tr><td><a href="/pages/kling.html">Kling AI</a></td><td>Standard</td><td>{live("Kling AI","Standard","$8.80/mo")}</td><td>Kling 3.0, 720p, no sound</td><td>about $4.80</td><td>about $14.40</td><td>about 1.8 minutes</td></tr>
<tr><td><a href="/pages/capcut.html">CapCut</a></td><td>Pro</td><td>{live("CapCut","Pro","$19.99/mo")}</td><td>Seedance 2.0 Mini, 720p</td><td>about $5.00</td><td>about $15.00</td><td>4 minutes</td></tr>
<tr><td><a href="/pages/krea.html">Krea</a></td><td>Basic</td><td>{live("Krea","Basic","$9/mo")}</td><td>Kling 2.5</td><td>about $5.70</td><td>about $17.00</td><td>about 1.6 minutes</td></tr>
<tr><td><a href="/pages/hailuo.html">Hailuo AI</a></td><td>Standard</td><td>{live("Hailuo AI","Standard","$14.99/mo")}</td><td>MiniMax H3, 768p</td><td>about $6.30</td><td>about $18.90</td><td>about 2.4 minutes</td></tr>
<tr><td><a href="/pages/kling.html">Kling AI</a></td><td>Standard</td><td>{live("Kling AI","Standard","$8.80/mo")}</td><td>Kling 4.0, 720p, with sound</td><td>about $8.00</td><td>about $24.00</td><td>about 1.1 minutes</td></tr>
<tr><td><a href="/pages/higgsfield.html">Higgsfield</a></td><td>Starter</td><td>{live("Higgsfield","Starter","$19/mo")}</td><td>Kling 3.0</td><td>about $11.80</td><td>about $35.50</td><td>about 1.6 minutes</td></tr>
<tr><td><a href="/pages/runway.html">Runway</a></td><td>Standard</td><td>{live("Runway","Standard","$15/mo")}</td><td>Gen-4.5</td><td>about $17.30</td><td>about $51.80</td><td>about 52 seconds</td></tr>
<tr><td><a href="/pages/invideo.html">InVideo</a></td><td>Plus</td><td>{live("InVideo","Plus","$60/mo")}</td><td>Seedance 2.5, 720p</td><td>about $20.20</td><td>about $60.50</td><td>about 3 minutes</td></tr>
<tr><td><a href="/pages/dreamina.html">Dreamina</a></td><td>Basic</td><td>{live("Dreamina","Basic","$15/mo")}</td><td>Seedance 2.5, 720p</td><td>about $21.10</td><td>about $63.40</td><td>about 43 seconds</td></tr>
</tbody>
</table></div>
<p class="note no-live">Worked out on 2026-11-13 from each plan's monthly price, its monthly credits and the credits per clip that each tool lists (60 seconds = 12 five-second clips, 6 ten-second clips or the nearest clip length). Google Veo's credits per clip come from a dated review, not from Google's own page. "With 3 tries" assumes you make three clips for every one you keep. Paying yearly lowers every number in this table.</p>
<h2>What the numbers mean</h2>
<h3>The cheapest minute comes from Google and Vidu</h3>
<p>Google AI Pro includes 1,000 Flow credits a month, and Veo's lightest setting uses about 10 credits per 8-second clip, so a minute costs about $1.50 and the plan covers more than 13 minutes. Vidu Standard is just as cheap per minute, but its Q4 model makes 540p video, which is fine for phones but soft on a big screen.</p>
<h3>Luma and Pika: the best value at 720p</h3>
<p>Luma's Ray3.2 at 720p and Pika 2.5 both land under $4 a minute. Luma's $30 Plus plan covers about 8 minutes a month; Pika's $10 Starter plan only 2.5 minutes, so it suits short social clips rather than longer videos.</p>
<h3>Video with sound costs more</h3>
<p>Kling 4.0 makes sound together with the picture, and that roughly doubles the cost compared with Kling 3.0 without sound. On Kling Standard, one minute of Kling 4.0 uses almost the whole month's 660 credits.</p>
<h3>Some cheap plans can't make a whole minute</h3>
<p>Runway Standard's 625 credits give about 52 seconds of Gen-4.5 video, and Dreamina Basic's 1,575 credits about 43 seconds of Seedance 2.5 at 720p. To make a full minute on those plans you have to buy extra credits or move up a plan.</p>
<h2>Watch out</h2>
<ul>
<li><strong>Retries are the real cost.</strong> Most people throw away two clips for every one they keep. The "with 3 tries" column is closer to what a finished minute costs.</li>
<li><strong>Clip length matters.</strong> Some tools charge less per second for longer clips, others the same. A minute made of 10-second clips can be cheaper than one made of 5-second clips.</li>
<li><strong>Editing, voice and music are extra.</strong> These numbers are for the video clips only. The <a href="/project.html">project calculator</a> adds voiceover, music and images for a whole project.</li>
</ul>
<p>See every plan on the <a href="/#platforms">video price list</a>, or compare the cheapest options on the <a href="/compare.html?tools=google-veo,vidu,luma,pika">Compare page</a>.</p>
<p class="note">Sources: the official pricing pages of Google, Vidu, Luma, Pika, Kling, CapCut, Krea, Hailuo, Higgsfield, Runway, InVideo and Dreamina, and GenCost's daily price data. Veo credits per clip from a review by DIY AI (November 2026). Checked 2026-11-13. Prices change often. Always confirm on the official sites.</p>
""")

# 2 ---------------------------------------------------------------------------------------------
A["kling-4-0-vs-seedance-2-5-cost-per-clip-2026"] = page(
    "Kling 4.0 vs Seedance 2.5: Which Is Cheaper per Clip? (2026)",
    "Kling 4.0 and Seedance 2.5 both make clips with sound. Here is what one 5-second clip costs on every platform that sells them, and where each model is cheapest.",
    "Kling 4.0 vs Seedance 2.5",
    f"""
<h1>Kling 4.0 vs Seedance 2.5: Which Is Cheaper per Clip? (2026)</h1>
<p class="lead">Kling 4.0 from Kuaishou and Seedance 2.5 from ByteDance are the two video models most people compare this autumn. Both make clips with sound generated together with the picture, and both are sold inside many different tools. We put the price of one 5-second 720p clip side by side, platform by platform.</p>
<div class="box">
<strong>Quick answer</strong><br/>
Cheapest Kling 4.0: <strong>Kling AI Standard</strong>, about $0.67 a clip.<br/>
Cheapest Seedance 2.5: <strong>CapCut Pro</strong>, about $0.60 a clip, but only in the first month; after that <strong>Higgsfield Plus</strong>, about $0.74.<br/>
On the same platform, Kling 4.0 is usually the cheaper of the two: on Luma Plus it costs about $0.80 against $1.17 for Seedance 2.5.<br/>
Last checked: 2026-11-13
</div>
<h2>One 5-second 720p clip, model by model</h2>
<div class="table-scroll"><table>
<thead><tr><th>Where</th><th>Plan</th><th>Monthly price</th><th>Kling 4.0</th><th>Seedance 2.5</th></tr></thead>
<tbody>
<tr><td><a href="/pages/kling.html">Kling AI</a></td><td>Standard</td><td>{live("Kling AI","Standard","$8.80/mo")}</td><td>about $0.67</td><td>not offered</td></tr>
<tr><td><a href="/pages/capcut.html">CapCut</a></td><td>Pro</td><td>{live("CapCut","Pro","$19.99/mo")}</td><td>not offered</td><td>about $0.60 (first month)</td></tr>
<tr><td><a href="/pages/higgsfield.html">Higgsfield</a></td><td>Starter / Plus</td><td>{live("Higgsfield","Starter","$19/mo")}</td><td>about $1.76 (Starter)</td><td>about $0.74 (Plus, $59/mo)</td></tr>
<tr><td><a href="/pages/luma.html">Luma</a></td><td>Plus</td><td>{live("Luma","Plus","$30/mo")}</td><td>about $0.80</td><td>about $1.17</td></tr>
<tr><td><a href="/pages/pika.html">Pika</a></td><td>Starter</td><td>{live("Pika","Starter","$10/mo")}</td><td>about $1.97 (1080p only)</td><td>about $2.03</td></tr>
<tr><td><a href="/pages/invideo.html">InVideo</a></td><td>Plus</td><td>{live("InVideo","Plus","$60/mo")}</td><td>not offered</td><td>about $1.68</td></tr>
<tr><td><a href="/pages/dreamina.html">Dreamina</a></td><td>Basic</td><td>{live("Dreamina","Basic","$15/mo")}</td><td>not offered</td><td>about $1.76</td></tr>
<tr><td><a href="/pages/krea.html">Krea</a></td><td>Basic</td><td>{live("Krea","Basic","$9/mo")}</td><td>not offered</td><td>about $1.80</td></tr>
<tr><td><a href="/pages/runway.html">Runway</a></td><td>Standard</td><td>{live("Runway","Standard","$15/mo")}</td><td>about $2.83 (1080p only)</td><td>not listed</td></tr>
<tr><td>fal.ai (API)</td><td>Pay per use</td><td>none</td><td>about $0.79</td><td>not compared here</td></tr>
</tbody>
</table></div>
<p class="note no-live">Worked out from each plan's monthly price and the credits per clip on each tool's pricing page (2026-11-10 to 2026-11-13). CapCut's Seedance 2.5 price is a first-month offer. Kling's own app doesn't print Kling 4.0's credit cost on its pricing page; the rate comes from testers. Full details: <a href="/pages/cheapest-way-to-use-kling-4-0-2026.html">where Kling 4.0 is cheapest</a> and <a href="/pages/cheapest-way-to-use-seedance-2-5-2026.html">where Seedance 2.5 is cheapest</a>.</p>
<h2>What the numbers mean</h2>
<h3>Buy each model at the source, or from Luma</h3>
<p>Kling 4.0 is cheapest in Kling's own app. Seedance 2.5 is cheapest on CapCut in the first month and on Higgsfield after that. If you want both models in one subscription, Luma Plus has them side by side at fixed credits per clip, with Kling 4.0 the cheaper of the two.</p>
<h3>Higgsfield flips the order</h3>
<p>Higgsfield is the one platform where Seedance 2.5 is clearly cheaper than Kling 4.0: its Plus plan covers about 80 Seedance 2.5 videos, while a Kling 4.0 clip on Starter costs more than twice as much.</p>
<h3>Google's Gemini Omni is cheaper than both, through the API</h3>
<p>Gemini Omni 1.2 Flash, released on November 5, 2026, costs $0.07 per second at 720p on the Gemini API, about $0.35 for a 5-second clip. It is aimed at developers; in the Gemini app it is rolling out to Google AI Ultra subscribers. See <a href="/pages/veo.html">Google's AI plans</a>.</p>
<h2>Watch out</h2>
<ul>
<li><strong>Same model, different settings.</strong> Platforms don't always use the same resolution, audio and clip length for "one clip". Compare at the same settings before you decide.</li>
<li><strong>First-month prices.</strong> CapCut and Dreamina show much lower prices for the first month. Plan your budget on the price from month two.</li>
<li><strong>Retries.</strong> If you need three tries for a clip you keep, multiply every price above by three.</li>
</ul>
<p class="note">Sources: the official pricing pages of Kling, CapCut, Higgsfield, Luma, Pika, InVideo, Dreamina, Krea and Runway; fal.ai's published API prices; Google's Gemini API pricing for Gemini Omni 1.2 Flash. Checked 2026-11-13. Prices change often. Always confirm on the official sites.</p>
""")

# 3 ---------------------------------------------------------------------------------------------
A["cheapest-way-to-pay-for-ai-tools-yearly-vs-monthly-2026"] = page(
    "Yearly vs Monthly: How Much You Save on 30 AI Tools (2026)",
    "Paying yearly saves up to 60% on AI tools. See the saving on the cheapest plan of 30 AI video, image, voice and music tools, and which tools give no yearly discount at all.",
    "Yearly vs monthly",
    f"""
<h1>Yearly vs Monthly: How Much You Save on 30 AI Tools (2026)</h1>
<p class="lead">Almost every AI tool offers a lower price if you pay for a year upfront, but the discount ranges from almost nothing to more than half. We compared the monthly and yearly price of the cheapest paid plan on 47 AI video, image, voice and music tools. 30 of them give a yearly discount; 17 don't.</p>
<div class="box">
<strong>Quick answer</strong><br/>
Biggest saving: <strong>Speechify Premium</strong>, 60% (about $209 a year), then <strong>InVideo Starter</strong>, 50% (about $120 a year).<br/>
Typical saving: about 20%, the same as two or three months free. That is what Suno, Udio, Pika, Runway and Midjourney give.<br/>
Almost no saving: <strong>D-ID Lite</strong> and <strong>OpenArt Starter</strong>, 1% and 7%.<br/>
Last checked: 2026-11-13
</div>
<h2>The yearly saving on each tool's cheapest plan</h2>
<div class="table-scroll"><table>
<thead><tr><th>Tool</th><th>Plan</th><th>Paid monthly</th><th>Paid yearly (per month)</th><th>Saving</th><th>Saved in a year</th></tr></thead>
<tbody>
<tr><td><a href="/pages/voice/speechify.html">Speechify</a></td><td>Premium</td><td>{live("Speechify","Premium","$29/mo")}</td><td>{live("Speechify","Premium","$11.58/mo","yearly")}</td><td>60%</td><td>about $209</td></tr>
<tr><td><a href="/pages/invideo.html">InVideo</a></td><td>Starter</td><td>{live("InVideo","Starter","$20/mo")}</td><td>{live("InVideo","Starter","$10/mo","yearly")}</td><td>50%</td><td>$120</td></tr>
<tr><td><a href="/pages/krea.html">Krea</a></td><td>Basic</td><td>{live("Krea","Basic","$9/mo")}</td><td>{live("Krea","Basic","$5/mo","yearly")}</td><td>44%</td><td>$48</td></tr>
<tr><td><a href="/pages/hailuo.html">Hailuo AI</a></td><td>Standard</td><td>{live("Hailuo AI","Standard","$14.99/mo")}</td><td>{live("Hailuo AI","Standard","$8.40/mo","yearly")}</td><td>44%</td><td>about $79</td></tr>
<tr><td><a href="/pages/magic-hour.html">Magic Hour</a></td><td>Creator</td><td>{live("Magic Hour","Creator","$19/mo")}</td><td>{live("Magic Hour","Creator","$12/mo","yearly")}</td><td>37%</td><td>$84</td></tr>
<tr><td><a href="/pages/music/soundraw.html">Soundraw</a></td><td>Creator</td><td>{live("Soundraw","Creator","$16.99/mo")}</td><td>{live("Soundraw","Creator","$11.04/mo","yearly")}</td><td>35%</td><td>about $71</td></tr>
<tr><td><a href="/pages/voice/descript.html">Descript</a></td><td>Hobbyist</td><td>{live("Descript","Hobbyist","$24/mo")}</td><td>{live("Descript","Hobbyist","$16/mo","yearly")}</td><td>33%</td><td>$96</td></tr>
<tr><td><a href="/pages/freepik.html">Freepik</a></td><td>Premium</td><td>{live("Freepik","Premium","$20/mo")}</td><td>{live("Freepik","Premium","$14.50/mo","yearly")}</td><td>28%</td><td>$66</td></tr>
<tr><td><a href="/pages/fish-audio.html">Fish Audio</a></td><td>Plus</td><td>{live("Fish Audio","Plus","$15/mo")}</td><td>{live("Fish Audio","Plus","$11/mo","yearly")}</td><td>27%</td><td>$48</td></tr>
<tr><td><a href="/pages/kling.html">Kling AI</a></td><td>Standard</td><td>{live("Kling AI","Standard","$8.80/mo")}</td><td>{live("Kling AI","Standard","$6.60/mo","yearly")}</td><td>25%</td><td>about $26</td></tr>
<tr><td><a href="/pages/capcut.html">CapCut</a></td><td>Pro</td><td>{live("CapCut","Pro","$19.99/mo")}</td><td>{live("CapCut","Pro","$15/mo","yearly")}</td><td>25%</td><td>about $60</td></tr>
<tr><td><a href="/pages/ideogram.html">Ideogram</a></td><td>Plus</td><td>{live("Ideogram","Plus","$20/mo")}</td><td>{live("Ideogram","Plus","$15/mo","yearly")}</td><td>25%</td><td>$60</td></tr>
<tr><td><a href="/pages/runway.html">Runway</a></td><td>Standard</td><td>{live("Runway","Standard","$15/mo")}</td><td>{live("Runway","Standard","$12/mo","yearly")}</td><td>20%</td><td>$36</td></tr>
<tr><td><a href="/pages/pika.html">Pika</a></td><td>Starter</td><td>{live("Pika","Starter","$10/mo")}</td><td>{live("Pika","Starter","$8/mo","yearly")}</td><td>20%</td><td>$24</td></tr>
<tr><td><a href="/pages/midjourney.html">Midjourney</a></td><td>Basic</td><td>{live("Midjourney","Basic","$10/mo")}</td><td>{live("Midjourney","Basic","$8/mo","yearly")}</td><td>20%</td><td>$24</td></tr>
<tr><td><a href="/pages/music/suno.html">Suno</a></td><td>Pro</td><td>{live("Suno","Pro","$10/mo")}</td><td>{live("Suno","Pro","$8/mo","yearly")}</td><td>20%</td><td>$24</td></tr>
<tr><td><a href="/pages/music/udio.html">Udio</a></td><td>Standard</td><td>{live("Udio","Standard","$10/mo")}</td><td>{live("Udio","Standard","$8/mo","yearly")}</td><td>20%</td><td>$24</td></tr>
<tr><td><a href="/pages/luma.html">Luma</a></td><td>Plus</td><td>{live("Luma","Plus","$30/mo")}</td><td>{live("Luma","Plus","$25/mo","yearly")}</td><td>17%</td><td>$60</td></tr>
<tr><td><a href="/pages/heygen.html">HeyGen</a></td><td>Creator</td><td>{live("HeyGen","Creator","$29/mo")}</td><td>{live("HeyGen","Creator","$24/mo","yearly")}</td><td>17%</td><td>$60</td></tr>
<tr><td><a href="/pages/voice/elevenlabs.html">ElevenLabs</a></td><td>Starter</td><td>{live("ElevenLabs","Starter","$6/mo")}</td><td>{live("ElevenLabs","Starter","$5/mo","yearly")}</td><td>17%</td><td>$12</td></tr>
<tr><td><a href="/pages/openart.html">OpenArt</a></td><td>Starter</td><td>{live("OpenArt","Starter","$14/mo")}</td><td>{live("OpenArt","Starter","$13/mo","yearly")}</td><td>7%</td><td>$12</td></tr>
</tbody>
</table></div>
<p class="note no-live">Cheapest paid plan of each tool, in US dollars, from GenCost's daily price data. The savings were worked out on 2026-11-13; the prices in the table update every day. The other tools with a yearly discount on their cheapest plan: Viggle, PixVerse, LTX Studio and Leonardo (20%), Vidu (18%), Google AI Pro and Recraft (17%), Pictory (14%) and D-ID (1%).</p>
<h2>Tools with no yearly discount on the cheapest plan</h2>
<p>These tools charge the same per month whether you pay monthly or not, or only sell their cheapest plan month by month: Higgsfield, Synthesia, Dreamina, VEED, Captions, OpusClip, Colossyan, Murf AI, Cartesia, WellSaid Labs, Fliki, Adobe Firefly, NightCafe, Stable Audio, Mureka, AIVA and Boomy. For some of them a yearly discount starts on a bigger plan.</p>
<h2>Is paying yearly worth it?</h2>
<h3>Yes, if you already know the tool</h3>
<p>If you have used a tool for a month or two and know you will keep it, a yearly plan is the easiest saving there is. On a 20% discount you get the equivalent of more than two months free. On Speechify, InVideo, Krea and Hailuo the discount is so big that a year costs about the same as five to seven months paid monthly.</p>
<h3>No, if prices are moving fast</h3>
<p>AI tool prices change often. In the past week alone Higgsfield lowered its yearly prices and InVideo cut its Max plan. A tool you pay a year for can get cheaper, or a rival can get better, before the year is over. Check the <a href="/changelog.html">price changes log</a> before you commit.</p>
<h2>Watch out</h2>
<ul>
<li><strong>Yearly credits can work differently.</strong> Some tools give a whole year's credits upfront, others refill every month. See <a href="/credits.html">credits and residuals</a>.</li>
<li><strong>Refunds are rare.</strong> Most AI tools don't refund a yearly plan if you stop using it.</li>
<li><strong>First-month deals are not yearly discounts.</strong> A cheap first month (CapCut, Dreamina, Kling) only lowers one month.</li>
</ul>
<p class="note">Sources: the official pricing pages of every tool listed, read every morning by GenCost. Checked 2026-11-13. Prices change often. Always confirm on the official sites.</p>
""")

# 4 ---------------------------------------------------------------------------------------------
A["cheapest-ai-video-tools-for-commercial-use-2026"] = page(
    "Cheapest AI Video Tools You Can Use Commercially (2026)",
    "Many free AI video plans don't allow commercial use. See the cheapest plan with commercial rights on Kling, Pika, Vidu, D-ID, Magic Hour, Luma and LTX Studio.",
    "Commercial use",
    f"""
<h1>Cheapest AI Video Tools You Can Use Commercially (2026)</h1>
<p class="lead">If you make videos for a client, for ads or for a monetized channel, you need a plan that allows commercial use. Many AI video tools keep that out of their free plan, and some out of their cheapest paid plan too. These are the cheapest plans where the tool itself says commercial use is included.</p>
<div class="box">
<strong>Quick answer</strong><br/>
Cheapest with commercial use: <strong>Kling AI Standard</strong>, about $8.80 a month.<br/>
Also from $10: <strong>Pika Starter</strong> and <strong>Vidu Standard</strong>.<br/>
Watch out: on <strong>D-ID</strong> and <strong>LTX Studio</strong> the cheapest paid plan is personal use only; commercial use starts one plan up.<br/>
Last checked: 2026-11-13
</div>
<h2>The cheapest plan with commercial use, tool by tool</h2>
<div class="table-scroll"><table>
<thead><tr><th>Tool</th><th>Cheapest plan with commercial use</th><th>Price</th><th>Free plan</th></tr></thead>
<tbody>
<tr><td><a href="/pages/kling.html">Kling AI</a></td><td>Standard</td><td>{live("Kling AI","Standard","$8.80/mo")}</td><td>No commercial use, watermark</td></tr>
<tr><td><a href="/pages/pika.html">Pika</a></td><td>Starter</td><td>{live("Pika","Starter","$10/mo")}</td><td>No watermark, but no commercial license</td></tr>
<tr><td><a href="/pages/vidu.html">Vidu</a></td><td>Standard</td><td>{live("Vidu","Standard","$10/mo")}</td><td>No commercial use, watermark</td></tr>
<tr><td><a href="/pages/d-id.html">D-ID</a></td><td>Pro</td><td>{live("D-ID","Pro","$16/mo")}</td><td>Trial with a watermark; Lite is personal use only</td></tr>
<tr><td><a href="/pages/magic-hour.html">Magic Hour</a></td><td>Creator</td><td>{live("Magic Hour","Creator","$19/mo")}</td><td>Small free allowance</td></tr>
<tr><td><a href="/pages/luma.html">Luma</a></td><td>Plus</td><td>{live("Luma","Plus","$30/mo")}</td><td>No free plan; every plan includes commercial use</td></tr>
<tr><td><a href="/pages/ltx.html">LTX Studio</a></td><td>Standard</td><td>{live("LTX Studio","Standard","$35/mo")}</td><td>Free and Lite are personal use only</td></tr>
</tbody>
</table></div>
<p class="note no-live">Commercial-use rules as each tool states them on its own pricing page, checked by GenCost between 2026-11-07 and 2026-11-13. Prices update every day. We only list tools whose pricing page says clearly which plans include commercial use.</p>
<h2>What the rules mean</h2>
<h3>"Paid plans include commercial use"</h3>
<p>Kling, Vidu, Magic Hour and Luma include commercial use on every paid plan, so the cheapest paid plan is enough. Kling Standard is the cheapest of all, at under $9 a month.</p>
<h3>No watermark is not the same as commercial use</h3>
<p>Pika's free plan has no watermark, but it also has no commercial license. A clean video is not automatically one you are allowed to sell or use in an ad.</p>
<h3>The cheapest paid plan is not always enough</h3>
<p>D-ID Lite and LTX Studio Lite are paid plans for personal use only. For client work you need D-ID Pro or LTX Studio Standard, which cost more than three and two times as much.</p>
<h2>Watch out</h2>
<ul>
<li><strong>Read the terms for your use.</strong> Commercial use usually covers ads and client work, but some tools have extra rules for things like reselling or training other AI models.</li>
<li><strong>Videos made on a free plan stay free-plan videos.</strong> Upgrading later doesn't always give commercial rights to clips you made before.</li>
<li><strong>Models inside other tools.</strong> When you use Kling, Seedance or Veo inside another platform, that platform's rules apply.</li>
</ul>
<p>See every plan and its "Watch out" notes on the <a href="/#platforms">video price list</a>.</p>
<p class="note">Sources: the official pricing pages of Kling, Pika, Vidu, D-ID, Magic Hour, Luma and LTX Studio. Checked 2026-11-13. This is not legal advice; check each tool's terms for your exact use.</p>
""")

# 5 ---------------------------------------------------------------------------------------------
A["midjourney-vs-firefly-vs-gpt-image-cost-per-image-2026"] = page(
    "Midjourney vs Firefly vs GPT Image 2.6: Cost per Image (2026)",
    "What one AI image really costs on Midjourney, Adobe Firefly, OpenArt, Freepik and OpenAI's new GPT Image 2.6, worked out from each plan's credits.",
    "Cost per image",
    f"""
<h1>Midjourney vs Firefly vs GPT Image 2.6: Cost per Image (2026)</h1>
<p class="lead">Image generators sell plans, hours and credits, so the price of one picture is hidden. We worked out what one image costs on the cheapest paid plan of the best-known tools, and on OpenAI's new GPT Image 2.6, which you can also pay for per image.</p>
<div class="box">
<strong>Quick answer</strong><br/>
Cheapest per image: <strong>OpenArt Starter</strong>, under half a cent on its simplest models, and <strong>Adobe Firefly Standard</strong>, about half a cent.<br/>
Midjourney Basic: about 1.25 cents an image (about 5 cents per grid of four).<br/>
GPT Image 2.6 on the API: about 3 to 5 cents per 1024×1024 image, with no subscription.<br/>
Last checked: 2026-11-13
</div>
<h2>One image, tool by tool</h2>
<div class="table-scroll"><table>
<thead><tr><th>Tool</th><th>Plan</th><th>Price</th><th>What the plan gives</th><th>One image</th></tr></thead>
<tbody>
<tr><td><a href="/pages/openart.html">OpenArt</a></td><td>Starter</td><td>{live("OpenArt","Starter","$14/mo")}</td><td>4,000 credits, about 1 credit per image on the simplest models</td><td>about $0.004</td></tr>
<tr><td><a href="/pages/firefly.html">Adobe Firefly</a></td><td>Firefly Standard</td><td>{live("Adobe Firefly","Firefly Standard","$9.99/mo")}</td><td>2,000 credits, about 1 credit per standard image</td><td>about $0.005</td></tr>
<tr><td><a href="/pages/midjourney.html">Midjourney</a></td><td>Basic</td><td>{live("Midjourney","Basic","$10/mo")}</td><td>about 200 fast generations of 4 images</td><td>about $0.0125</td></tr>
<tr><td>GPT Image 2.6 (API)</td><td>Pay per image</td><td>none</td><td>OpenAI API, 1024×1024, low to high quality</td><td>about $0.03 to $0.05</td></tr>
<tr><td><a href="/pages/freepik.html">Freepik</a></td><td>Premium</td><td>{live("Freepik","Premium","$20/mo")}</td><td>20,000 credits; Nano Banana 2 at 2K uses 75 per image</td><td>about $0.075</td></tr>
<tr><td><a href="/pages/ideogram.html">Ideogram</a></td><td>Plus</td><td>{live("Ideogram","Plus","$20/mo")}</td><td>2,400 priority credits, then unlimited images in the slower queue</td><td>unlimited in slow mode</td></tr>
</tbody>
</table></div>
<p class="note no-live">Worked out on 2026-11-13 from each plan's monthly price and how many images it covers according to the tool's own pricing page or plan comparison. Premium models and higher resolutions cost more credits per image on every platform. GPT Image 2.6 API prices from OpenAI's published API pricing (November 2026).</p>
<h2>What the numbers mean</h2>
<h3>Credits per image decide everything</h3>
<p>OpenArt and Firefly look cheapest because their simplest images use about one credit each. Choose a premium model on the same plan and the cost per image can be ten or twenty times higher, as Freepik's 75 credits for a 2K Nano Banana 2 image show.</p>
<h3>Midjourney: predictable, and unlimited from Standard</h3>
<p>Midjourney Basic gives about 200 fast generations, each a grid of four images. From the $30 Standard plan you can make unlimited images in the slower Relax mode, which makes Midjourney the cheapest option for heavy users who can wait.</p>
<h3>GPT Image 2.6: pay only for what you make</h3>
<p>OpenAI's GPT Image 2.6 models, released on November 4, 2026, cost about 3 to 5 cents per 1024×1024 image on the API, depending on quality. That is more per image than the subscription tools, but with no monthly fee. Inside ChatGPT the same models are available on every plan. They can also make animated GIFs, editable SVG vectors and transparent PNGs.</p>
<h2>Watch out</h2>
<ul>
<li><strong>Unused credits disappear.</strong> On most plans monthly credits don't roll over, so an unused month raises your real cost per image.</li>
<li><strong>Private images cost extra.</strong> On Midjourney, images are public unless you have Pro or Mega.</li>
<li><strong>Commercial use.</strong> Free plans often don't allow commercial use. Check each tool's page before you sell or publish.</li>
</ul>
<p>See every image plan on the <a href="/image.html">image price list</a>, or read the <a href="/pages/cheapest-ai-image-generators-2026.html">cheapest AI image generators</a> guide.</p>
<p class="note">Sources: the official pricing pages and plan comparisons of OpenArt, Adobe Firefly, Midjourney, Freepik and Ideogram; OpenAI's API pricing for GPT Image 2.6. Checked 2026-11-13. Prices change often. Always confirm on the official sites.</p>
""")

CARDS = {
    "cheapest-way-to-make-a-60-second-ai-video-2026": ("video", "Video", "What a 60-Second AI Video Costs", "12 tools, from $1.50 a minute"),
    "kling-4-0-vs-seedance-2-5-cost-per-clip-2026": ("video", "Video", "Kling 4.0 vs Seedance 2.5", "Cost per clip on every platform"),
    "cheapest-way-to-pay-for-ai-tools-yearly-vs-monthly-2026": ("video", "Savings", "Yearly vs Monthly: What You Save", "Up to 60% on 30 AI tools"),
    "cheapest-ai-video-tools-for-commercial-use-2026": ("video", "Video", "Cheapest AI Video for Commercial Use", "Plans that allow client work"),
    "midjourney-vs-firefly-vs-gpt-image-cost-per-image-2026": ("image", "Image", "Midjourney vs Firefly vs GPT Image", "Real cost per image"),
}

items = []
for i, (slug, html) in enumerate(A.items(), 1):
    name = f"{i:02d}-{slug}.html"
    with open(os.path.join(HERE, name), "w", encoding="utf-8") as f:
        f.write(html)
    cls, label, h3, p = CARDS[slug]
    card = (f'<li class="reveal"><a class="art" href="/pages/{slug}.html"><span class="cat {cls}">{label}</span>'
            f"<h3>{h3}</h3><p>{p}</p></a></li>")
    items.append({"file": f"queue/{name}", "page": f"pages/{slug}.html", "card": card, "published": ""})

with open(os.path.join(HERE, "queue.json"), "w", encoding="utf-8") as f:
    json.dump({"about": "Articles waiting to be published, one a day, by publish_queue.py (oldest first). "
                        "'published' is set to the date the article went live. Add new articles to the end.",
               "items": items}, f, indent=1, ensure_ascii=False)
print(f"{len(items)} articles written to queue/")
