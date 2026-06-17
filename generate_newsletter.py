#!/usr/bin/env python3
"""
Daily Read — Newsletter Generator
Fetches current news via RSS, generates newsletter with Claude API.
"""

import os
import re
from datetime import datetime
from zoneinfo import ZoneInfo

import anthropic

try:
    import feedparser
    HAS_FEEDPARSER = True
except ImportError:
    HAS_FEEDPARSER = False

# ── Date ──────────────────────────────────────────────────────────────────────
pacific = ZoneInfo("America/Los_Angeles")
today = datetime.now(pacific)
DATE_STR  = today.strftime("%A, %B %d, %Y")
DAY_STR   = today.strftime("%A").upper()
DATE_UPPER = DATE_STR.upper()

# ── RSS helpers ────────────────────────────────────────────────────────────────
def fetch_rss(url, max_items=8, label=""):
    if not HAS_FEEDPARSER:
        return ""
    try:
        feed = feedparser.parse(url)
        lines = []
        for entry in feed.entries[:max_items]:
            title   = entry.get("title", "").strip()
            summary = entry.get("summary", entry.get("description", "")).strip()
            summary = re.sub(r"<[^>]+>", "", summary)[:220]
            lines.append(f"• {title}: {summary}")
        return "\n".join(lines)
    except Exception as e:
        print(f"  RSS warning ({label}): {e}")
        return ""

print("Fetching news feeds...")
world_news  = fetch_rss("http://feeds.bbci.co.uk/news/world/rss.xml",        label="BBC World")
us_politics = fetch_rss("https://rss.politico.com/politics-news.xml",         label="Politico")
tech_news   = fetch_rss("https://feeds.feedburner.com/TechCrunch",    max_items=6, label="TechCrunch")
sci_news    = fetch_rss("https://www.sciencedaily.com/rss/top/science.xml", max_items=6, label="ScienceDaily")

NEWS_CONTEXT = f"""
WORLD NEWS (BBC):
{world_news or '(unavailable)'}

US POLITICS (Politico):
{us_politics or '(unavailable)'}

TECH NEWS (TechCrunch):
{tech_news or '(unavailable)'}

SCIENCE & HEALTH (ScienceDaily):
{sci_news or '(unavailable)'}
"""

# ── Prompt ────────────────────────────────────────────────────────────────────
PROMPT = f"""Today is {DATE_STR}. Generate Dillon's Daily Read newsletter as a complete, self-contained HTML page.

Use these current news headlines as your source material:
{NEWS_CONTEXT}

ABOUT DILLON: Tech-focused engineer/entrepreneur, late 20s, Aliso Viejo CA. Wants depth over fluff. Direct, no sugarcoating. Highlight things that matter for someone building in the tech world. Tailor everything to be relevant and intellectually stimulating for him.

NEWSLETTER SECTIONS:

1. HISTORICAL LEADER (500-700 words, the meatiest section)
Choose ONE person from this list — pick whoever feels most thematically relevant to today's news or would make the most compelling read:
Napoleon Bonaparte, Catherine the Great, Alexander Hamilton, Abraham Lincoln, Winston Churchill, Genghis Khan, Cleopatra, Otto von Bismarck, Nikola Tesla, Benjamin Franklin, Margaret Thatcher, Machiavelli, Frederick the Great, Saladin, Augustus Caesar, Harriet Tubman, Simon Bolivar, Sun Tzu, Peter the Great, Andrew Carnegie, John D. Rockefeller, Theodore Roosevelt, Mao Zedong, Gandhi, Lenin, Ataturk, Ada Lovelace, Hannibal Barca, Alexander the Great, Elizabeth I
DO NOT pick Julius Caesar.
Cover: origin/rise, key strategy or turning point, greatest achievement, downfall/legacy. Include a pullquote (their actual words) and a "Why it matters today" box tying them to something in today's headlines.

2. GEOPOLITICS (~150 words)
Lead with the biggest world story from the news above. Include an "Also watching" pullquote with 2-3 other hot spots.

3. US POLITICS (~120 words)
Most important domestic story from today's headlines. Yesterday + today angle.

4. WORTH KNOWING (7-8 items)
Best picks from tech, science, world news. Each item: emoji + bold 1-line headline + 1-2 sentence "why it matters" explanation. Feel like "you need to know this" — not generic trend pieces.

OUTPUT RULES:
- Output ONLY the complete HTML document. No markdown, no code fences, no explanation.
- Start with <!DOCTYPE html> and end with </html>.
- Use this exact CSS and structure:

<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>The Daily Read</title>
  <link rel="apple-touch-icon" href="./apple-touch-icon.png">
  <link rel="icon" type="image/png" href="./apple-touch-icon.png">
  <meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate">
  <meta http-equiv="Pragma" content="no-cache">
  <meta http-equiv="Expires" content="0">
  <style>
    :root {{ color-scheme: light; }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{ font-family: 'Georgia', serif; background: #fafaf8; color: #1a1a1a; line-height: 1.7; }}
    .masthead {{ background: #111; color: #fff; text-align: center; padding: 28px 32px 22px; border-bottom: 3px solid #c8a96e; }}
    .masthead .edition {{ font-family: 'Helvetica Neue', Arial, sans-serif; font-size: 0.68rem; letter-spacing: 0.3em; text-transform: uppercase; color: #c8a96e; margin-bottom: 8px; }}
    .masthead h1 {{ font-size: 2.6rem; letter-spacing: 0.08em; font-weight: 900; line-height: 1; text-transform: uppercase; }}
    .masthead .tagline {{ font-style: italic; color: #888; font-size: 0.82rem; margin-top: 8px; }}
    .content {{ max-width: 680px; margin: 0 auto; padding: 36px 24px 48px; }}
    .section {{ margin-bottom: 44px; padding-bottom: 44px; border-bottom: 1px solid #e8e5de; }}
    .section:last-child {{ border-bottom: none; margin-bottom: 0; }}
    .section-eyebrow {{ display: flex; align-items: center; gap: 10px; margin-bottom: 12px; }}
    .tag {{ font-family: 'Helvetica Neue', Arial, sans-serif; font-size: 0.6rem; letter-spacing: 0.25em; text-transform: uppercase; padding: 4px 9px; border-radius: 2px; color: #fff; font-weight: 700; }}
    .tag.history {{ background: #7a5c1a; }}
    .tag.geo {{ background: #1a4a7a; }}
    .tag.us {{ background: #7a1a1a; }}
    .tag.now {{ background: #1a5c3a; }}
    .section-label {{ font-family: 'Helvetica Neue', Arial, sans-serif; font-size: 0.7rem; letter-spacing: 0.15em; text-transform: uppercase; color: #888; }}
    .section h2 {{ font-size: 1.55rem; font-weight: 700; line-height: 1.25; margin-bottom: 16px; color: #111; }}
    .section p {{ font-size: 0.94rem; color: #2d2d2d; margin-bottom: 14px; }}
    .section p:last-child {{ margin-bottom: 0; }}
    .pullquote {{ border-left: 3px solid #c8a96e; background: #f7f4ec; padding: 14px 18px; margin: 18px 0; font-style: italic; font-size: 0.9rem; color: #555; line-height: 1.6; }}
    .pullquote strong {{ display: block; font-style: normal; color: #333; margin-top: 6px; font-size: 0.85rem; }}
    .news-list {{ list-style: none; padding: 0; }}
    .news-list li {{ display: flex; gap: 14px; padding: 13px 0; border-bottom: 1px solid #f0ede6; align-items: flex-start; }}
    .news-list li:last-child {{ border-bottom: none; }}
    .news-list .emoji {{ font-size: 1.1rem; flex-shrink: 0; line-height: 1.5; }}
    .news-list .item-text strong {{ display: block; font-size: 0.92rem; font-weight: 700; color: #111; margin-bottom: 3px; line-height: 1.3; }}
    .news-list .item-text span {{ font-size: 0.87rem; color: #444; line-height: 1.55; }}
    .footer {{ text-align: center; font-family: 'Helvetica Neue', Arial, sans-serif; font-size: 0.72rem; color: #bbb; letter-spacing: 0.08em; padding: 24px; border-top: 1px solid #e8e5de; }}
    b {{ color: #111; }}
  </style>
</head>
<body>
<div class="masthead">
  <div class="edition">{DAY_STR} · {DATE_UPPER}</div>
  <h1>The Daily Read</h1>
  <div class="tagline">Five minutes. Know more than you did yesterday.</div>
</div>
<div class="content">
  [4 sections here — .section divs with .section-eyebrow, .tag, h2, paragraphs, .pullquote, .news-list as appropriate]
</div>
<div class="footer">THE DAILY READ &nbsp;·&nbsp; Curated by Claude &nbsp;·&nbsp; Every morning at 7:00 AM</div>
</body>
</html>
"""

# ── Generate ───────────────────────────────────────────────────────────────────
print("Generating newsletter with Claude...")
client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

response = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=8096,
    messages=[{"role": "user", "content": PROMPT}]
)

html = response.content[0].text.strip()

# Strip accidental code fences
if html.startswith("```"):
    html = re.sub(r"^```[a-z]*\n?", "", html)
    html = re.sub(r"\n?```$", "", html).strip()

# ── Save ───────────────────────────────────────────────────────────────────────
with open("index.html", "w", encoding="utf-8") as f:
    f.write(html)

print(f"Done! Newsletter generated for {DATE_STR} ({len(html):,} chars)")
