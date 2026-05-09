#!/usr/bin/env python3
"""
Hacker News Scanner — New Software Releases Recap
====================================================
Scans HN for new software launches, tools, and API releases.
Runs at 9am and 6pm daily.

Usage:
  python3 scripts/hn_scan.py            # Run scan, output recap
  python3 scripts/hn_scan.py --post     # Run scan and write blog post
"""

import os, sys, json, time, argparse, subprocess, re
from datetime import datetime, date, timedelta
from pathlib import Path
import urllib.request

BLOG_DIR = "/home/ubuntu/tech-daily-blog"
POSTS_DIR = os.path.join(BLOG_DIR, "posts")
SCAN_LOG = os.path.join(BLOG_DIR, ".hn_scan_log.json")

HN_API = "https://hn.algolia.com/api/v1/search"

def search_hn(query, hits=20):
    """Search Hacker News for recent stories."""
    url = f"{HN_API}?query={query}&tags=story&hitsPerPage={hits}&numericFilters=created_at_i>{int((datetime.now()-timedelta(hours=12)).timestamp())}"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        data = json.loads(urllib.request.urlopen(req, timeout=15).read())
        return data.get("hits", [])
    except:
        return []

def search_show_hn(hits=30):
    """Search Show HN for new launches."""
    url = f"{HN_API}?tags=show_hn&hitsPerPage={hits}&numericFilters=created_at_i>{int((datetime.now()-timedelta(hours=24)).timestamp())}"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        data = json.loads(urllib.request.urlopen(req, timeout=15).read())
        return data.get("hits", [])
    except:
        return []

def search_ask_hn(hits=15):
    """Search Ask HN for recommendations."""
    url = f"{HN_API}?tags=ask_hn&hitsPerPage={hits}&numericFilters=created_at_i>{int((datetime.now()-timedelta(hours=24)).timestamp())}"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        data = json.loads(urllib.request.urlopen(req, timeout=15).read())
        return data.get("hits", [])
    except:
        return []

def format_story(story):
    """Format a HN story for display."""
    title = story.get("title", "Untitled")
    url = story.get("url") or f"https://news.ycombinator.com/item?id={story.get('objectID')}"
    points = story.get("points", 0)
    comments = story.get("num_comments", 0)
    author = story.get("author", "unknown")
    hn_url = f"https://news.ycombinator.com/item?id={story.get('objectID')}"
    return {
        "title": title,
        "url": url,
        "hn_url": hn_url,
        "points": points,
        "comments": comments,
        "author": author,
    }

def load_seen_ids():
    if os.path.exists(SCAN_LOG):
        with open(SCAN_LOG) as f:
            return set(json.load(f).get("seen_ids", []))
    return set()

def save_seen_ids(ids):
    data = {"seen_ids": list(ids), "last_scan": datetime.now().isoformat()}
    with open(SCAN_LOG, "w") as f:
        json.dump(data, f)

def scan():
    """Run the full scan and return new stories."""
    seen = load_seen_ids()
    
    # Search for new software launches
    queries = [
        "Show HN",  # Already covered by show_hn tag
        "launched", "release", "new tool", "new API", "open source",
        "AI agent", "video editor", "developer tool", "CLI tool",
        "database", "framework", "language", "startup",
    ]
    
    all_new = []
    
    # Get Show HN — hottest new launches
    show_hn = search_show_hn(30)
    for s in show_hn:
        sid = s.get("objectID", "")
        if sid and sid not in seen:
            seen.add(sid)
            all_new.append(format_story(s))
    
    # Get Ask HN
    ask_hn = search_ask_hn(15)
    for s in ask_hn:
        sid = s.get("objectID", "")
        if sid and sid not in seen:
            seen.add(sid)
            all_new.append(format_story(s))
    
    # Get top stories from last 12 hours
    top_url = f"https://hn.algolia.com/api/v1/search?tags=story&hitsPerPage=30&numericFilters=points>10,created_at_i>{int((datetime.now()-timedelta(hours=12)).timestamp())}"
    req = urllib.request.Request(top_url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        data = json.loads(urllib.request.urlopen(req, timeout=15).read())
        for s in data.get("hits", []):
            sid = s.get("objectID", "")
            if sid and sid not in seen:
                seen.add(sid)
                all_new.append(format_story(s))
    except:
        pass
    
    # Search for new software launches with specific queries
    for q in queries[1:]:  # Skip "Show HN" (already covered)
        stories = search_hn(q, 10)
        for s in stories:
            sid = s.get("objectID", "")
            if sid and sid not in seen:
                seen.add(sid)
                all_new.append(format_story(s))
        time.sleep(0.3)  # Rate limit
    
    save_seen_ids(seen)
    
    # Deduplicate by title
    seen_titles = set()
    unique = []
    for s in all_new:
        t = s["title"].lower().strip()
        if t not in seen_titles:
            seen_titles.add(t)
            unique.append(s)
    
    # Sort by points
    unique.sort(key=lambda x: x["points"], reverse=True)
    
    return unique

def generate_recap(stories):
    """Generate a readable recap of new software."""
    if not stories:
        return "📭 No new software launches found in the last scan."
    
    # Categorize
    ai_tools = []
    dev_tools = []
    startups = []
    other = []
    
    for s in stories:
        t = s["title"].lower()
        if any(w in t for w in ["ai", "llm", "gpt", "agent", "model", "diffusion", "neural"]):
            ai_tools.append(s)
        elif any(w in t for w in ["api", "sdk", "cli", "library", "framework", "database", "compiler"]):
            dev_tools.append(s)
        elif any(w in t for w in ["launch", "startup", "funding", "raised", "series"]):
            startups.append(s)
        else:
            other.append(s)
    
    now = datetime.now().strftime("%B %d, %Y %I:%M %p")
    
    recap = f"""🤖 **HN Software Recap — {now}**

**New launches found: {len(stories)}**

"""
    if ai_tools:
        recap += "**🤖 AI & ML Tools**\n"
        for s in ai_tools[:5]:
            recap += f"  ⭐ {s['points']:>3} pts | {s['title']}\n"
            recap += f"     {s['url']}\n"
        recap += "\n"
    
    if dev_tools:
        recap += "**🛠️ Developer Tools**\n"
        for s in dev_tools[:5]:
            recap += f"  ⭐ {s['points']:>3} pts | {s['title']}\n"
            recap += f"     {s['url']}\n"
        recap += "\n"
    
    if startups:
        recap += "**🚀 Startups & Launches**\n"
        for s in startups[:5]:
            recap += f"  ⭐ {s['points']:>3} pts | {s['title']}\n"
            recap += f"     {s['url']}\n"
        recap += "\n"
    
    if other:
        recap += "**📌 Other Notable**\n"
        for s in other[:5]:
            recap += f"  ⭐ {s['points']:>3} pts | {s['title']}\n"
            recap += f"     {s['url']}\n"
    
    recap += f"\n💬 Discuss on HN: https://news.ycombinator.com"
    return recap

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="HN Scanner")
    parser.add_argument("--post", action="store_true", help="Write results as a blog post")
    args = parser.parse_args()
    
    print("🔍 Scanning Hacker News for new software releases...")
    stories = scan()
    
    recap = generate_recap(stories)
    print("\n" + recap)
    
    if args.post:
        # Save as blog post
        post_title = f"HN Software Recap — {datetime.now().strftime('%B %d, %Y')}"
        slug = f"hn-recap-{datetime.now().strftime('%Y-%m-%d-%H')}"
        
        post_content = f"""---
title: "{post_title}"
date: "{date.today()}"
category: "tech-news"
tags: ["hacker-news", "software-launches", "daily-recap"]
seo: "Daily recap of new software launches, AI tools, and developer tools from Hacker News"
image: ""
---

## New Software Releases Today

{recap}

---

*Auto-generated from Hacker News — {datetime.now().strftime('%Y-%m-%d %H:%M')}*
"""
        with open(os.path.join(POSTS_DIR, f"{slug}.md"), "w") as f:
            f.write(post_content)
        print(f"\n📝 Saved as blog post: posts/{slug}.md")
