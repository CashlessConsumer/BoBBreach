# BoBBreach — AGENTS.md

Bank of Baroda data breach investigation (Triple X ransomware group, July 2026).
**Live site:** https://bobbreach.cashlessconsumer.in (GitHub Pages, static HTML/CSS/JS).

## What This Is

Consumer-facing investigation site: breach overview, IFSC branch search, threat actor dossier, timeline, consumer protection guide. Metadata-level analysis of the Tor dump directory listing — no actual file contents analyzed or distributed.

## Site Structure

| Path | What It Is |
|------|------------|
| `index.html` | Landing page — breach overview, data categories, timeline, consumer guide |
| `search.html` | IFSC branch search widget |
| `pages/about.html` | Investigation methodology + CashlessConsumer background |
| `pages/overview.html` | Full overview of breach findings |
| `pages/eli5.html` | TL;DR / ELI5 explainer |
| `pages/vector.html` | Breach vector / attack path analysis |
| `pages/demands.html` | Consumer demands / policy asks |
| `pages/why.html` | Why this matters — context and implications |
| `pages/censorship.html` | Content moderation / censorship angle |
| `css/style.css` | Single stylesheet — light + dark theme, responsive |
| `js/main.js` | Shared JS — nav toggle, theme switcher, scroll spy |
| `CNAME` | Custom domain: bobbreach.cashlessconsumer.in |
| `404.html` | GitHub Pages 404 page |

## Datasets (`data/`)

| File | Purpose |
|---|---|
| `branches.json` | Branch IFAC dataset (1,088+ entries) |
| `branches.min.json` | Minified branch dataset for search page |
| `branches_resolved.json` | Resolved IFAC data with additional metadata |
| `cities.json` | City-level branch aggregation |
| `coords.min.json` | Branch coordinates for geolocation |
| `exposure.json` | Data exposure categories + file counts |
| `ifac_cache.json` | Raw IFAC lookup cache |
| `inventory_analysis.json` | Full dump inventory analysis results |
| `priority_ifacs.txt` | High-priority IFAC codes |
| `stats.json` | Aggregate breach statistics |
| `timeline.json` | Chronological breach timeline (May–July 2026) |
| `build_dataset.py` | Dataset construction script |
| `build_impact_dataset.py` | Impact analysis dataset builder |

## Scripts (`scripts/`)

- `geocode_cities.py` — City geocoding for branch location data

## Deploy

GitHub Pages. Push to `gh-pages` branch (or root if configured). Custom domain via `CAGE`.

## Important Rules

1. **No PII anywhere.** This repo shows metadata only — file names, directory structure, dates, categories. Never include actual file contents or PII.
2. **LLM disclosure mandatory.** Every page must note that LLMs assisted in analysis. The disclosure is already baked into `index.html` as a collapsible block — replicate this pattern on new pages.
3. **Consumer-first framing.** Every page should answer: "What does this mean for a BoB customer?" Technical details serve that question, not the other way around.
4. **Evidence-linked claims.** All factual claims about the breach should trace back to the publicly available Tor dump directory listing. If a claim can't be backed, flag it as "indicative" or "pending verification."
5. **Dark/light mode.** The theme toggle in `js/main.js` should work on every page. All new pages must include the nav and theme system.

## Editing Conventions

- **Static HTML/CSS/JS only** — no frameworks, no build step, no npm
- **Single CSS file** (`css/style.css`) — add new styles at the bottom with a comment block
- **Each page is self-contained HTML** (`pages/`, `search.html`, `index.html`)
- **Nav is copy-paste** between pages. When adding/removing a page, update nav links in all HTML files
- **JSON data files** are consumed client-side by `search.html` and rendered pages
- **Images** go in `images/`, used via relative paths

## Adding a New Page

1. Copy an existing page from `pages/` as template (nav, disclosure, footer, theme logic)
2. Add content in the `<main>` section
3. Add link to nav in every HTML file that has a navigation bar
4. Test light/dark theme toggle