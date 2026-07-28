#!/usr/bin/env python3
"""Replace nav links div and add Vector link to footers across all BoBBreach pages."""

import re

# ── Standard nav link sets ──

NAV_ROOT = """    <div class="links" id="navLinks">
      <a href="index.html" class="active">Home</a>
      <a href="pages/overview.html">📋 Full Overview</a>
      <a href="pages/eli5.html">🧒 TL;DR / ELI5</a>
      <a href="pages/vector.html">🔬 Vector</a>
      <a href="search.html">🔍 Branches</a>
      <a href="pages/demands.html">⚖️ Demands</a>
      <a href="pages/about.html">About</a>
    </div>"""

NAV_PAGES = """    <div class="links" id="navLinks">
      <a href="../">Home</a>
      <a href="overview.html">📋 Full Overview</a>
      <a href="eli5.html">🧒 TL;DR / ELI5</a>
      <a href="vector.html">🔬 Vector</a>
      <a href="../search.html">🔍 Branches</a>
      <a href="demands.html">⚖️ Demands</a>
      <a href="about.html">About</a>
    </div>"""

# overview.html needs a different nav because it uses scroll anchors
NAV_OVERVIEW = """    <div class="links" id="navLinks">
      <a href="#overview" class="active">Overview</a>
      <a href="#breach">The Breach</a>
      <a href="#data">Data Exposed</a>
      <a href="#actor">Threat Actor</a>
      <a href="#timeline">Timeline</a>
      <a href="#consumer">Guide</a>
      <a href="../search.html">🔍 Branches</a>
      <a href="eli5.html">🧒 TL;DR</a>
      <a href="vector.html">🔬 Vector</a>
      <a href="demands.html">⚖️ Demands</a>
      <a href="about.html">About</a>
    </div>"""

ROOT_FILES = {
    'index.html': ('index.html', NAV_ROOT),
    'search.html': ('search.html', NAV_ROOT),
}

PAGES_FILES = {
    'pages/eli5.html': ('eli5.html', NAV_PAGES),
    'pages/vector.html': ('vector.html', NAV_PAGES),
    'pages/demands.html': ('demands.html', NAV_PAGES),
    'pages/about.html': ('about.html', NAV_PAGES),
}

# overview.html gets special treatment
OVERVIEW_FILE = 'pages/overview.html'

# ── Footer canonical link line pattern ──
# Root-level footers: href="pages/eli5.html">TL;DR</a> | ... | <a href="pages/about.html">About</a>
# Pages-level footers: href="eli5.html">TL;DR</a> | ... | <a href="about.html">About</a>

FOOTER_LINK_REPLACEMENTS = {
    # root-level pages: insert Vector before Branches
    '| <a href="search.html"': '| <a href="pages/vector.html">🔬 Vector</a> | <a href="search.html"',
    # pages/* level: insert Vector before Branches
    '| <a href="../search.html"': '| <a href="vector.html">🔬 Vector</a> | <a href="../search.html"',
}

def replace_nav(content, active_page, nav_html):
    """Replace the nav links div with the given standard nav, setting active class on active_page."""
    # Replace the active class on the right link
    nav_with_active = nav_html.replace(f'href="{active_page}"', f'href="{active_page}" class="active"')
    # Also find any existing active class and remove it
    nav_with_active = re.sub(r'class="active"', '', nav_with_active)
    nav_with_active = nav_with_active.replace(f'href="{active_page}"', f'href="{active_page}" class="active"')
    
    # Replace the entire nav links div
    pattern = r'<div class="links" id="navLinks">.*?</div>'
    new_content = re.sub(pattern, nav_with_active, content, count=1, flags=re.DOTALL)
    if new_content == content:
        print(f"  ⚠️  Nav replacement didn't match for {active_page}")
    return new_content

def add_vector_to_root_footer(content):
    """Add Vector link to root-level footer link line."""
    # Pattern: "| <a href=\"pages/eli5.html\">TL;DR..."
    # Insert Vector after ELI5 link
    old = '| <a href="search.html"'
    new = '| <a href="pages/vector.html">🔬 Vector</a> | <a href="search.html"'
    return content.replace(old, new, 1)

def add_vector_to_pages_footer(content):
    """Add Vector link to pages-level footer link line."""
    old = '| <a href="../search.html"'
    new = '| <a href="vector.html">🔬 Vector</a> | <a href="../search.html"'
    return content.replace(old, new, 1)

def overview_footer(content):
    """Add Vector link to overview.html footer (which uses ../ prefix)."""
    # Check what footer pattern overview.html has
    if '| <a href="../search.html"' in content:
        old = '| <a href="../search.html"'
        new = '| <a href="vector.html">🔬 Vector</a> | <a href="../search.html"'
        return content.replace(old, new, 1)
    return content

# ── Process each file ──

# 1. Root files
for fname, (active, nav) in ROOT_FILES.items():
    print(f"\n{fname} ...")
    with open(fname) as f:
        content = f.read()
    content = replace_nav(content, active, nav)
    content = add_vector_to_root_footer(content)
    with open(fname, 'w') as f:
        f.write(content)
    print(f"  ✓ written")

# 2. Pages files
for fname, (active, nav) in PAGES_FILES.items():
    print(f"\n{fname} ...")
    with open(fname) as f:
        content = f.read()
    content = replace_nav(content, active, nav)
    content = add_vector_to_pages_footer(content)
    with open(fname, 'w') as f:
        f.write(content)
    print(f"  ✓ written")

# 3. overview.html special
print(f"\n{OVERVIEW_FILE} ...")
with open(OVERVIEW_FILE) as f:
    content = f.read()
content = replace_nav(content, 'about.html', NAV_OVERVIEW)  # wait, overview uses internal anchors - special case
# Actually overview.html uses #overview as active. Let me handle differently.
# Replace the entire nav for overview.html with NAV_OVERVIEW
pattern = r'<div class="links" id="navLinks">.*?</div>'
content = re.sub(pattern, NAV_OVERVIEW, content, count=1, flags=re.DOTALL)
content = overview_footer(content)
with open(OVERVIEW_FILE, 'w') as f:
    f.write(content)
print(f"  ✓ written")

print("\nDone.")
