# create-comparisons.ps1
# Creates all 10 detailed comparison pages with the same structure

$pages = "pages"
if (-not (Test-Path $pages)) { New-Item -ItemType Directory -Path $pages | Out-Null }

function Write-ComparisonPage {
    param($filename, $html)
    $path = Join-Path $pages $filename
    $html | Out-File -FilePath $path -Encoding utf8 -Force
    Write-Host "Created: $path"
}

$style = @"
<style>
body { font-family: system-ui, sans-serif; background:#0a0a0f; color:#e0e0e0; margin:0; padding:40px 20px; line-height:1.6; }
.container { max-width:900px; margin:0 auto; }
a { color:#00d4ff; text-decoration:none; }
a:hover { text-decoration:underline; }
h1 { font-size:2.2em; margin-bottom:8px; }
h2 { margin-top:40px; font-size:1.4em; color:#aaa; }
.box { background:rgba(255,255,255,0.04); border:1px solid rgba(255,255,255,0.08); border-radius:16px; padding:24px; margin:20px 0; }
table { width:100%; border-collapse:collapse; margin:16px 0; }
th, td { padding:12px; text-align:left; border-bottom:1px solid rgba(255,255,255,0.1); }
th { color:#00d4ff; }
.note { font-size:0.85em; opacity:0.7; margin-top:40px; }
</style>
"@

# 1. Runway vs Kling
Write-ComparisonPage "runway-vs-kling-pricing-2026.html" @"
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Runway vs Kling Pricing Comparison 2026 | GenCost</title>
$style
</head>
<body>
<div class="container">
<a href="/">← Back to GenCost</a>
<h1>Runway vs Kling AI Pricing Comparison 2026</h1>
<p>Real dollar cost comparison for AI video generation.</p>

<div class="box">
<strong>Quick summary</strong><br>
Cheapest paid: Kling Standard ~`$10/mo<br>
Best free tier: Runway (125 credits)<br>
Best for short clips: Kling<br>
Best for quality: Runway<br>
Last checked: 2026-11-06
</div>

<h2>Side-by-side pricing</h2>
<table>
<tr><th>Plan</th><th>Price</th><th>Credits</th><th>5s</th><th>10s</th><th>30s</th></tr>
<tr><td>Kling Standard</td><td>~`$10/mo</td><td>660</td><td>~`$0.08</td><td>~`$0.15</td><td>~`$0.45</td></tr>
<tr><td>Runway Standard</td><td>`$12/mo</td><td>625</td><td>~`$0.10</td><td>~`$0.19</td><td>~`$0.58</td></tr>
<tr><td>Kling Pro</td><td>~`$37/mo</td><td>3000</td><td>~`$0.06</td><td>~`$0.12</td><td>~`$0.37</td></tr>
<tr><td>Runway Pro</td><td>`$28/mo</td><td>2250</td><td>~`$0.06</td><td>~`$0.12</td><td>~`$0.37</td></tr>
</table>

<div class="box">
<strong>Real-world example</strong><br>
10 × 10-second videos per month:<br>
Kling Standard ≈ `$1.50 &nbsp;|&nbsp; Runway Standard ≈ `$1.90
</div>

<div class="box">
<strong>Verdict</strong><br>
Kling is usually cheaper for the same amount of video. Runway is better if you want higher quality and more consistent results. Check current prices before buying.
</div>

<p><a href="/pages/runway.html">Runway pricing →</a> &nbsp;|&nbsp; <a href="/pages/kling.html">Kling pricing →</a></p>
<p class="note">Prices change often. Always confirm on the official sites.</p>
</div>
</body>
</html>
"@

# 2. Pika vs Luma
Write-ComparisonPage "pika-vs-luma-pricing-2026.html" @"
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Pika vs Luma Pricing Comparison 2026 | GenCost</title>
$style
</head>
<body>
<div class="container">
<a href="/">← Back to GenCost</a>
<h1>Pika vs Luma Pricing Comparison 2026</h1>
<p>Real dollar cost comparison for AI video generation.</p>

<div class="box">
<strong>Quick summary</strong><br>
Cheapest paid: Pika Starter ~`$10/mo<br>
Best free tier: Pika<br>
Best for short clips: Luma<br>
Best for volume: Luma<br>
Last checked: 2026-11-06
</div>

<h2>Side-by-side pricing</h2>
<table>
<tr><th>Plan</th><th>Price</th><th>Credits</th><th>5s</th><th>10s</th><th>30s</th></tr>
<tr><td>Pika Starter</td><td>`$10/mo</td><td>600</td><td>~`$0.08</td><td>~`$0.17</td><td>~`$0.50</td></tr>
<tr><td>Luma Plus</td><td>`$30/mo</td><td>10000</td><td>~`$0.01</td><td>~`$0.03</td><td>~`$0.09</td></tr>
<tr><td>Pika Creator</td><td>`$35/mo</td><td>2600</td><td>~`$0.07</td><td>~`$0.13</td><td>~`$0.40</td></tr>
<tr><td>Luma Pro</td><td>`$90/mo</td><td>40000</td><td>~`$0.01</td><td>~`$0.02</td><td>~`$0.07</td></tr>
</table>

<div class="box">
<strong>Real-world example</strong><br>
20 × 10-second videos per month:<br>
Pika Starter ≈ `$3.40 &nbsp;|&nbsp; Luma Plus ≈ `$0.60
</div>

<div class="box">
<strong>Verdict</strong><br>
Luma is significantly cheaper per second once you are on a paid plan. Pika is better if you only need a small amount of video or want a lower entry price.
</div>

<p><a href="/pages/pika.html">Pika pricing →</a> &nbsp;|&nbsp; <a href="/pages/luma.html">Luma pricing →</a></p>
<p class="note">Prices change often. Always confirm on the official sites.</p>
</div>
</body>
</html>
"@

# 3. HeyGen vs Synthesia
Write-ComparisonPage "heygen-vs-synthesia-pricing-2026.html" @"
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>HeyGen vs Synthesia Pricing Comparison 2026 | GenCost</title>
$style
</head>
<body>
<div class="container">
<a href="/">← Back to GenCost</a>
<h1>HeyGen vs Synthesia Pricing Comparison 2026</h1>
<p>Real dollar cost comparison for AI avatar video tools.</p>

<div class="box">
<strong>Quick summary</strong><br>
Cheapest paid: Synthesia Starter ~`$19/mo<br>
Best free tier: HeyGen<br>
Best for volume: Synthesia<br>
Best for flexibility: HeyGen<br>
Last checked: 2026-11-06
</div>

<h2>Side-by-side pricing</h2>
<table>
<tr><th>Plan</th><th>Price</th><th>Credits</th><th>5s</th><th>10s</th><th>30s</th></tr>
<tr><td>HeyGen Creator</td><td>`$29/mo</td><td>600</td><td>~`$0.24</td><td>~`$0.48</td><td>~`$1.45</td></tr>
<tr><td>Synthesia Starter</td><td>~`$19/mo</td><td>1250</td><td>~`$0.08</td><td>~`$0.15</td><td>~`$0.46</td></tr>
<tr><td>HeyGen Pro</td><td>`$49/mo</td><td>1000</td><td>~`$0.24</td><td>~`$0.49</td><td>~`$1.47</td></tr>
<tr><td>Synthesia Pro</td><td>~`$89/mo</td><td>6000</td><td>~`$0.07</td><td>~`$0.15</td><td>~`$0.45</td></tr>
</table>

<div class="box">
<strong>Real-world example</strong><br>
10 × 30-second avatar videos per month:<br>
HeyGen Creator ≈ `$14.50 &nbsp;|&nbsp; Synthesia Starter ≈ `$4.60
</div>

<div class="box">
<strong>Verdict</strong><br>
Synthesia is cheaper for avatar videos. HeyGen has a more usable free tier and is better if you need more flexibility or higher quality.
</div>

<p><a href="/pages/heygen.html">HeyGen pricing →</a> &nbsp;|&nbsp; <a href="/pages/synthesia.html">Synthesia pricing →</a></p>
<p class="note">Prices change often. Always confirm on the official sites.</p>
</div>
</body>
</html>
"@

# 4. ElevenLabs vs Cartesia
Write-ComparisonPage "elevenlabs-vs-cartesia-pricing-2026.html" @"
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>ElevenLabs vs Cartesia Pricing Comparison 2026 | GenCost</title>
$style
</head>
<body>
<div class="container">
<a href="/">← Back to GenCost</a>
<h1>ElevenLabs vs Cartesia Pricing Comparison 2026</h1>
<p>Real dollar cost comparison for AI voice tools.</p>

<div class="box">
<strong>Quick summary</strong><br>
Cheapest paid: Cartesia Pro ~`$5/mo<br>
Best free tier: Both have usable free tiers<br>
Best for quality: ElevenLabs<br>
Best for price: Cartesia<br>
Last checked: 2026-11-06
</div>

<h2>Side-by-side pricing</h2>
<table>
<tr><th>Plan</th><th>Price</th><th>Credits / Minutes</th><th>Notes</th></tr>
<tr><td>Cartesia Pro</td><td>~`$5/mo</td><td>100k credits</td><td>Very cheap for volume</td></tr>
<tr><td>ElevenLabs Starter</td><td>~`$5–6/mo</td><td>30k credits</td><td>Higher quality voices</td></tr>
<tr><td>Cartesia Startup</td><td>~`$49/mo</td><td>1.25M credits</td><td>Best for high volume</td></tr>
<tr><td>ElevenLabs Creator</td><td>~`$22/mo</td><td>121k credits</td><td>Professional cloning</td></tr>
</table>

<div class="box">
<strong>Real-world example</strong><br>
30 minutes of voiceover per month:<br>
Cartesia Pro is usually cheaper. ElevenLabs costs more but is often preferred for quality.
</div>

<div class="box">
<strong>Verdict</strong><br>
Cartesia is the cheaper option for most users. ElevenLabs is better if voice quality is the priority.
</div>

<p><a href="/pages/elevenlabs.html">ElevenLabs pricing →</a> &nbsp;|&nbsp; <a href="/pages/cartesia.html">Cartesia pricing →</a></p>
<p class="note">Prices change often. Always confirm on the official sites.</p>
</div>
</body>
</html>
"@

# 5. Suno vs Udio
Write-ComparisonPage "suno-vs-udio-pricing-2026.html" @"
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Suno vs Udio Pricing Comparison 2026 | GenCost</title>
$style
</head>
<body>
<div class="container">
<a href="/">← Back to GenCost</a>
<h1>Suno vs Udio Pricing Comparison 2026</h1>
<p>Real dollar cost comparison for AI music generators.</p>

<div class="box">
<strong>Quick summary</strong><br>
Cheapest paid: Both start around `$8–10/mo<br>
Best free tier: Both offer free generations<br>
Best for songs: Suno<br>
Best for instrumentals: Udio<br>
Last checked: 2026-11-06
</div>

<h2>Side-by-side pricing</h2>
<table>
<tr><th>Plan</th><th>Price</th><th>Songs / Credits</th><th>Notes</th></tr>
<tr><td>Suno Pro</td><td>~`$10/mo</td><td>~500 songs</td><td>Strong songwriting</td></tr>
<tr><td>Udio Pro</td><td>~`$10/mo</td><td>~600 songs</td><td>Good for instrumentals</td></tr>
<tr><td>Suno Premier</td><td>~`$30/mo</td><td>~2000 songs</td><td>Higher volume</td></tr>
<tr><td>Udio Pro+</td><td>~`$30/mo</td><td>~2000+ songs</td><td>Higher volume</td></tr>
</table>

<div class="box">
<strong>Real-world example</strong><br>
50 full songs per month:<br>
Both tools are in a similar price range. Test both free tiers first.
</div>

<div class="box">
<strong>Verdict</strong><br>
Prices are close. Choose based on sound quality and style preference rather than cost.
</div>

<p><a href="/pages/suno.html">Suno pricing →</a> &nbsp;|&nbsp; <a href="/pages/udio.html">Udio pricing →</a></p>
<p class="note">Prices change often. Always confirm on the official sites.</p>
</div>
</body>
</html>
"@

# 6–10 (same structure)
$comparisons = @(
    @{
        file = "kling-vs-hailuo-pricing-2026.html"
        title = "Kling vs Hailuo Pricing Comparison 2026"
        tool1 = "Kling"; tool2 = "Hailuo"
        summary = "Cheapest paid: Kling Standard ~`$10/mo<br>Best free tier: Both limited<br>Best for price: Kling<br>Best for quality: Hailuo"
        table = @"
<tr><td>Kling Standard</td><td>~`$10/mo</td><td>660</td><td>~`$0.08</td><td>~`$0.15</td><td>~`$0.45</td></tr>
<tr><td>Hailuo Standard</td><td>~`$15/mo</td><td>1000</td><td>~`$0.07</td><td>~`$0.14</td><td>~`$0.42</td></tr>
"@
        example = "20 × 10-second videos: Kling ≈ `$3.00 &nbsp;|&nbsp; Hailuo ≈ `$2.80"
        verdict = "Very close in price. Hailuo can be slightly better value on higher plans."
    },
    @{
        file = "runway-vs-luma-pricing-2026.html"
        title = "Runway vs Luma Pricing Comparison 2026"
        tool1 = "Runway"; tool2 = "Luma"
        summary = "Cheapest paid: Runway Standard `$12/mo<br>Best free tier: Runway<br>Best for quality: Runway<br>Best for volume: Luma"
        table = @"
<tr><td>Runway Standard</td><td>`$12/mo</td><td>625</td><td>~`$0.10</td><td>~`$0.19</td><td>~`$0.58</td></tr>
<tr><td>Luma Plus</td><td>`$30/mo</td><td>10000</td><td>~`$0.01</td><td>~`$0.03</td><td>~`$0.09</td></tr>
"@
        example = "30 × 10-second videos: Runway ≈ `$5.70 &nbsp;|&nbsp; Luma ≈ `$0.90"
        verdict = "Luma is much cheaper per second. Runway is better for higher quality output."
    },
    @{
        file = "playht-vs-elevenlabs-pricing-2026.html"
        title = "PlayHT vs ElevenLabs Pricing Comparison 2026"
        tool1 = "PlayHT"; tool2 = "ElevenLabs"
        summary = "Cheapest paid: ElevenLabs ~`$5/mo<br>Best free tier: ElevenLabs<br>Best for quality: ElevenLabs<br>Best for API: PlayHT"
        table = @"
<tr><td>ElevenLabs Starter</td><td>~`$5/mo</td><td>30k credits</td><td>—</td><td>—</td><td>—</td></tr>
<tr><td>PlayHT Creator</td><td>~`$19/mo</td><td>Varies</td><td>—</td><td>—</td><td>—</td></tr>
"@
        example = "30 minutes of voiceover: ElevenLabs is usually cheaper at entry level."
        verdict = "ElevenLabs is the better starting point for most users. PlayHT can be competitive at higher volumes."
    },
    @{
        file = "heygen-vs-capcut-pricing-2026.html"
        title = "HeyGen vs CapCut Pricing Comparison 2026"
        tool1 = "HeyGen"; tool2 = "CapCut"
        summary = "Cheapest paid: HeyGen Creator `$29/mo<br>Best free tier: Both have free plans<br>Best for avatars: HeyGen<br>Best for editing: CapCut"
        table = @"
<tr><td>HeyGen Creator</td><td>`$29/mo</td><td>600</td><td>~`$0.24</td><td>~`$0.48</td><td>~`$1.45</td></tr>
<tr><td>CapCut Pro</td><td>`$399/mo</td><td>1200</td><td>~`$1.66</td><td>~`$3.33</td><td>~`$9.98</td></tr>
"@
        example = "10 × 30-second videos: HeyGen ≈ `$14.50 &nbsp;|&nbsp; CapCut is significantly more expensive."
        verdict = "HeyGen is far cheaper for avatar-style videos. CapCut is a full editor and priced much higher."
    },
    @{
        file = "stable-audio-vs-beatoven-pricing-2026.html"
        title = "Stable Audio vs Beatoven Pricing Comparison 2026"
        tool1 = "Stable Audio"; tool2 = "Beatoven"
        summary = "Cheapest paid: Stable Audio ~`$12/mo<br>Best free tier: Both have free options<br>Best for instrumentals: Stable Audio<br>Best for video background: Beatoven"
        table = @"
<tr><td>Stable Audio</td><td>~`$12/mo</td><td>Varies</td><td>—</td><td>—</td><td>—</td></tr>
<tr><td>Beatoven</td><td>Free + paid</td><td>Varies</td><td>—</td><td>—</td><td>—</td></tr>
"@
        example = "Background tracks for 10 videos: Both are affordable. Test free tiers first."
        verdict = "Stable Audio is better for pure instrumentals. Beatoven is often preferred for royalty-free video background music."
    }
)

foreach ($c in $comparisons) {
    $html = @"
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>$($c.title) | GenCost</title>
$style
</head>
<body>
<div class="container">
<a href="/">← Back to GenCost</a>
<h1>$($c.title)</h1>
<p>Real dollar cost comparison.</p>

<div class="box">
<strong>Quick summary</strong><br>
$($c.summary)<br>
Last checked: 2026-11-06
</div>

<h2>Side-by-side pricing</h2>
<table>
<tr><th>Plan</th><th>Price</th><th>Credits</th><th>5s</th><th>10s</th><th>30s</th></tr>
$($c.table)
</table>

<div class="box">
<strong>Real-world example</strong><br>
$($c.example)
</div>

<div class="box">
<strong>Verdict</strong><br>
$($c.verdict)
</div>

<p><a href="/pages/$($c.tool1.ToLower().Replace(' ','-')).html">$($c.tool1) pricing →</a> &nbsp;|&nbsp; <a href="/pages/$($c.tool2.ToLower().Replace(' ','-')).html">$($c.tool2) pricing →</a></p>
<p class="note">Prices change often. Always confirm on the official sites.</p>
</div>
</body>
</html>
"@
    Write-ComparisonPage $c.file $html
}

Write-Host ""
Write-Host "Done. All 10 detailed comparison pages created."
Write-Host "Next commands:"
Write-Host "git add pages/*pricing-2026.html"
Write-Host 'git commit -m "Add 10 detailed comparison pages"'
Write-Host "git push origin main"