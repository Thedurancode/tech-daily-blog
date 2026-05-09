#!/usr/bin/env python3
"""
Daily Blog Publisher — Research, Write, SEO, Images
=====================================================
Asks you what to blog about → researches → writes → adds SEO + images → publishes

Usage:
  python3 scripts/blog.py ask          # Ask what to blog about today
  python3 scripts/blog.py write        # Research and write the post
  python3 scripts/blog.py publish      # Build and deploy the site
  python3 scripts/blog.py status       # Show blog stats
"""

import os, sys, json, time, argparse, subprocess, glob, re
from datetime import datetime, date
from pathlib import Path

BLOG_DIR = "/home/ubuntu/tech-daily-blog"
POSTS_DIR = os.path.join(BLOG_DIR, "posts")
ASSETS_DIR = os.path.join(BLOG_DIR, "assets")
SCRIPTS_DIR = os.path.join(BLOG_DIR, "scripts")
TOPIC_FILE = os.path.join(BLOG_DIR, ".next_topic")
SCHEDULE_FILE = os.path.join(BLOG_DIR, ".schedule")

os.makedirs(POSTS_DIR, exist_ok=True)
os.makedirs(ASSETS_DIR, exist_ok=True)
os.makedirs(SCRIPTS_DIR, exist_ok=True)

def save_topic(topic, category):
    data = {"topic": topic, "category": category, "asked_at": datetime.now().isoformat()}
    with open(TOPIC_FILE, "w") as f:
        json.dump(data, f)
    print(f"📝 Topic saved: {topic} ({category})")

def get_topic():
    if os.path.exists(TOPIC_FILE):
        with open(TOPIC_FILE) as f:
            return json.load(f)
    return None

def get_existing_tags():
    """Collect all tags from existing posts for SEO."""
    tags = set()
    for f in glob.glob(os.path.join(POSTS_DIR, "*.md")):
        content = open(f).read()
        m = re.search(r'tags:\s*\[(.*?)\]', content)
        if m:
            for t in m.group(1).split(","):
                tags.add(t.strip().strip('"').strip("'"))
    return tags

def slugify(text):
    return re.sub(r'[^a-z0-9]+', '-', text.lower()).strip('-')

def generate_post_html(title, content, date_str, tags, category, seo_keywords, image_url):
    """Generate the HTML post page."""
    tag_links = " ".join([f'<a href="/tag/{t}.html" class="tag">{t}</a>' for t in tags])
    
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} | Tech Daily Blog</title>
    <meta name="description" content="{seo_keywords[:160]}">
    <meta name="keywords" content="{', '.join(tags)}">
    <meta name="author" content="Tech Daily Blog">
    <meta property="og:title" content="{title}">
    <meta property="og:description" content="{seo_keywords[:160]}">
    <meta property="og:type" content="article">
    <meta property="og:published_time" content="{date_str}">
    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:title" content="{title}">
    <link rel="canonical" href="https://blog.emprezario.com/posts/{slugify(title)}.html">
    <link rel="stylesheet" href="../style.css">
    <!-- Schema.org Article -->
    <script type="application/ld+json">
    {{
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": "{title}",
        "datePublished": "{date_str}",
        "author": {{"@type": "Organization", "name": "Tech Daily Blog"}},
        "description": "{seo_keywords[:200]}"
    }}
    </script>
</head>
<body>
    <nav>
        <div class="nav-inner">
            <a href="/" class="logo">Tech Daily Blog</a>
            <div class="nav-links">
                <a href="/">Home</a>
                <a href="/archive.html">Archive</a>
                <a href="/about.html">About</a>
            </div>
        </div>
    </nav>

    <main>
        <article class="post-full">
            <header>
                <div class="post-meta">
                    <span class="category">{category}</span>
                    <time datetime="{date_str}">{date_str}</time>
                </div>
                <h1>{title}</h1>
                <div class="tags">{tag_links}</div>
            </header>
            
            {f'<img src="{image_url}" alt="{title}" class="post-image">' if image_url else ''}
            
            <div class="content">
{content}
            </div>
        </article>
    </main>

    <footer>
        <p>Tech Daily Blog — Daily tech news, tools, and insights</p>
    </footer>
</body>
</html>"""
    return html

def generate_index_html(posts):
    """Generate the homepage with latest posts."""
    post_cards = ""
    for p in posts[:10]:
        post_cards += f"""
        <article class="post-card">
            <h2><a href="posts/{p['slug']}.html">{p['title']}</a></h2>
            <div class="post-meta">
                <span class="category">{p['category']}</span>
                <time>{p['date']}</time>
            </div>
            <p>{p['excerpt'][:150]}...</p>
            <div class="tags">{" ".join([f'<a href="/tag/{t}.html" class="tag">{t}</a>' for t in p['tags'][:3]])}</div>
        </article>"""
    
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Tech Daily Blog — Daily Tech News & Tools</title>
    <meta name="description" content="Daily curated tech news, AI tools, software launches, and developer insights.">
    <meta name="keywords" content="tech news, AI tools, software, developer, daily blog">
    <link rel="stylesheet" href="style.css">
</head>
<body>
    <nav>
        <div class="nav-inner">
            <a href="/" class="logo">Tech Daily Blog</a>
            <div class="nav-links">
                <a href="/">Home</a>
                <a href="/archive.html">Archive</a>
                <a href="/about.html">About</a>
            </div>
        </div>
    </nav>

    <main>
        <section class="hero">
            <h1>Tech Daily Blog</h1>
            <p>Daily curated tech news, AI tools, software launches, and developer insights</p>
        </section>

        <section class="posts">
            {post_cards}
        </section>
    </main>

    <footer>
        <p>Tech Daily Blog — Daily tech news, tools, and insights</p>
    </footer>
</body>
</html>"""

def generate_archive_html(posts):
    items = ""
    for p in posts:
        items += f"""
        <li>
            <time>{p['date']}</time>
            <a href="posts/{p['slug']}.html">{p['title']}</a>
            <span class="category">{p['category']}</span>
        </li>"""
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Archive | Tech Daily Blog</title>
    <link rel="stylesheet" href="style.css">
</head>
<body>
    <nav><div class="nav-inner"><a href="/" class="logo">Tech Daily Blog</a>
        <div class="nav-links"><a href="/">Home</a><a href="/archive.html">Archive</a><a href="/about.html">About</a></div></div></nav>
    <main><h1>Archive</h1><ul class="archive-list">{items}</ul></main>
    <footer><p>Tech Daily Blog</p></footer>
</body>
</html>"""

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Tech Daily Blog Publisher")
    sub = parser.add_subparsers(dest="command")
    
    sub.add_parser("ask", help="Ask what to blog about (sets topic)")
    sub.add_parser("write", help="Research and write the post")
    sub.add_parser("publish", help="Build HTML and deploy")
    sub.add_parser("status", help="Show blog stats")
    
    args = parser.parse_args()
    
    if args.command == "ask":
        print("📝 What should we blog about today?")
        print("   (I'll research, write, add SEO + images)")
        print()
        topic = input("  Topic: ").strip()
        category = input("  Category (ai-tools, dev, startup, design, etc): ").strip() or "tech"
        save_topic(topic, category)
        
    elif args.command == "status":
        posts = sorted(glob.glob(os.path.join(POSTS_DIR, "*.md")), reverse=True)
        print(f"\n📊 Blog Status")
        print(f"   Total posts: {len(posts)}")
        topic = get_topic()
        if topic:
            print(f"   Next topic: {topic['topic']} ({topic['category']})")
        else:
            print(f"   No topic queued — run 'blog ask'")
        if posts:
            print(f"\n   Latest posts:")
            for p in posts[:5]:
                name = os.path.basename(p).replace(".md", "")
                print(f"     • {name}")
        print()

    elif args.command == "publish":
        # Read all markdown posts and generate HTML
        md_posts = sorted(glob.glob(os.path.join(POSTS_DIR, "*.md")), reverse=True)
        posts_data = []
        
        for md_file in md_posts:
            content = open(md_file).read()
            # Parse frontmatter
            meta = {}
            m = re.match(r'---\n(.*?)\n---', content, re.DOTALL)
            if m:
                for line in m.group(1).strip().split('\n'):
                    if ':' in line:
                        k, v = line.split(':', 1)
                        meta[k.strip()] = v.strip().strip('"').strip("'")
            
            title = meta.get('title', os.path.basename(md_file).replace('.md',''))
            date_str = meta.get('date', str(date.today()))
            category = meta.get('category', 'tech')
            tags_str = meta.get('tags', '[]')
            seo = meta.get('seo', title)
            image = meta.get('image', '')
            
            # Extract tags
            tags = []
            try:
                tags = json.loads(tags_str)
            except:
                tags = [t.strip() for t in tags_str.strip('[]').split(',') if t.strip()]
            
            # Get body (after frontmatter)
            body = content
            if m:
                body = content[m.end():].strip()
            
            slug = slugify(title)
            excerpt = body[:200].replace('#', '').strip()
            
            html = generate_post_html(title, body, date_str, tags, category, seo, image)
            os.makedirs(os.path.join(BLOG_DIR, "posts"), exist_ok=True)
            with open(os.path.join(BLOG_DIR, "posts", f"{slug}.html"), "w") as f:
                f.write(html)
            
            posts_data.append({
                "title": title, "slug": slug, "date": date_str,
                "category": category, "tags": tags, "excerpt": excerpt
            })
        
        # Generate index
        with open(os.path.join(BLOG_DIR, "index.html"), "w") as f:
            f.write(generate_index_html(posts_data))
        
        # Generate archive
        with open(os.path.join(BLOG_DIR, "archive.html"), "w") as f:
            f.write(generate_archive_html(posts_data))
        
        print(f"✅ Published {len(posts_data)} posts to {BLOG_DIR}")
        
    else:
        parser.print_help()
