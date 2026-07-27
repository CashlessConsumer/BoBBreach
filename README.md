# BoBBreach — Bank of Baroda Data Breach Investigation

**Website: [bobbreach.cashlessconsumer.in](https://bobbreach.cashlessconsumer.in)**

Consumer-focused investigation of the July 2026 Bank of Baroda data breach by Triple X ransomware group. This repo powers a public GitHub Pages site that helps consumers understand the breach, check their branch impact, and protect themselves.

## What This Is

- **Metadata-level analysis** of the publicly available Tor dump directory listing — no actual file contents were downloaded or analyzed
- File naming patterns, paths, and directory structures were programmatically analysed and cross-referenced against IFSC database
- **Indicative findings** — numbers are from initial ongoing analysis
- **Consumer-first** — 101 explainer, IFSC branch search, threat actor profile, timeline, protection guide

## Repo Structure

| Path | Purpose |
|------|---------|
| `index.html` | Main landing page — breach overview, explainer, data categories, timeline, consumer guide |
| `search.html` | IFSC branch search — dedicated page for checking branch impact with browsable dataset |
| `pages/about.html` | About the investigation methodology and CashlessConsumer |
| `css/style.css` | Full site stylesheet (light/dark theme) |
| `js/main.js` | Shared JS — nav toggle, theme switcher, scroll spy |
| `data/` | Branch IFSC dataset, exposure categories, timeline data (JSON) |
| `CNAME` | Custom domain: bobbreach.cashlessconsumer.in |
| `reports/` | Investigation reports and threat actor dossiers |
| `crawl/` | OSINT crawl scripts, state snapshots, inventories |
| `download_scripts/` | Automated download tooling |
| `investigation_worthy/` | Curated high-signal file references from directory listing analysis |

## Key Features

- **IFSC Branch Search** — cross-reference 1,088+ impacted branches against online Razorpay IFSC database
- **Threat Actor Profile** — Triple X ransomware group dossier
- **Timeline** — chronological breach narrative from May-July 2026
- **Consumer Guide** — actionable steps for affected BoB customers
- **Light/Dark Mode** — accessible across devices
- **Responsive** — mobile-first design

## LLM Disclosures

This investigation was produced with the assistance of large language models (LLMs) as analytical tools. All metadata-driven findings were extracted programmatically from the publicly available Tor dump directory listing. **No LLM has access to the actual contents of the dumped files.** This is early, ongoing analysis and may contain errors. Independent verification is encouraged.

## License

Published for research and educational purposes. No PII from the dump is distributed in this repo. Maintained by [CashlessConsumer](https://cashlessconsumer.in) — an independent fintech and DPI research initiative.
