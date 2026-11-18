---
title: AI Price Finder by GenCost
emoji: 💸
colorFrom: green
colorTo: blue
sdk: gradio
sdk_version: SDK_VERSION
app_file: app.py
pinned: false
license: cc-by-4.0
short_description: Today's prices of 50 AI video, image, voice and music tools
datasets:
  - Bitbooz/ai-tool-prices
tags:
  - mcp-server
  - pricing
  - ai-tools
  - text-to-video
  - text-to-image
  - text-to-speech
---

# AI Price Finder by GenCost

Today's prices of 50 AI video, image, voice and music tools, in US dollars: Runway, Kling, Pika, Luma, Higgsfield, ElevenLabs, Suno, Midjourney and more.

- **Cost of video clips:** what 10 clips of Kling 4.0 or Seedance 2.5 cost on each platform that sells the model, cheapest first.
- **Cheapest plans** in each category.
- **Every plan of one tool**, with the official pricing page.

The numbers come live from the [Bitbooz/ai-tool-prices](https://huggingface.co/datasets/Bitbooz/ai-tool-prices) dataset, which [GenCost](https://getgencost.com) updates every morning from each tool's official pricing page. A price change is only published after it has been seen on two different days. No affiliate links; tools do not pay to be listed.

## Use it from an AI assistant (MCP)

This Space is also an MCP server with three tools: `clip_cost`, `cheapest_plans` and `tool_prices`.
Add `https://bitbooz-ai-price-finder.hf.space/gradio_api/mcp/sse` to an MCP client, or use GenCost's own connector: https://getgencost.com/ai.html

Data: GenCost (https://getgencost.com), CC BY 4.0.
