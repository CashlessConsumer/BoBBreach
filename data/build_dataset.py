#!/usr/bin/env python3
"""
Build the bobbreach dataset: BoB IFSC codes + branch info + breach impact.
Outputs JSON files for the website.
"""
import json, re, os, sys
from pathlib import Path
from collections import defaultdict

BASE = Path("/home/workspace/BoBHack")
IFSC_RAZORPAY = Path("/home/workspace/Projects/card-block-api/data/IFSC-list.json")
INVENTORY_L5 = BASE / "crawl/inventories/boob-dump-inventory_L5.md"
OUT_DIR = BASE / "site/data"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# ── 1. Load BoB IFSC codes from Razorpay dataset ──
print("[1] Loading BoB IFSC codes from Razorpay...")
with open(IFSC_RAZORPAY) as f:
    all_ifsc = json.load(f)
bob_codes = sorted([c for c in all_ifsc if c.startswith("BARB0")])
print(f"  → {len(bob_codes)} BoB IFSC codes")

# ── 2. Load Razorpay IFSC→branch details if available ──
# Try loading cached branch details, or use Razorpay API to build a cache
IFSC_CACHE = BASE / "site/data/ifsc_branches.json"
branch_map = {}  # ifsc -> {branch, bank, city, district, state, address, contact}

if IFSC_CACHE.exists():
    with open(IFSC_CACHE) as f:
        branch_map = json.load(f)
    print(f"  → Loaded {len(branch_map)} cached branch details")
else:
    # We'll fetch on-the-fly from Razorpay API
    print("  → No cache found. Will create a minimal dataset from IFSC codes.")
    print("  → Branch names can be resolved client-side via Razorpay API.")

# ── 3. Parse inventory to extract exposed data categories ──
print("\n[2] Parsing inventory for exposed data categories...")

# Known signal categories from the investigation
EXPOSURE_DIRS = {
    "CUSTOMER_PII": [
        "CUSTOMER", "KYC", "EKYC", "CKYC", "REKYC", "PII", "ekyc", "LFAR",
        "CUSTOMER_DOCUMENT", "CUSTOMER_DOC", "IDENTITY", "AADHAAR", "VOTER",
        "PASSPORT", "PAN", "DRIVING", "PHOTO", "SIGNATURE"
    ],
    "TRANSACTION": [
        "TRANSACTION", "BALANCE", "STATEMENT", "LEDGER", "RECON", "RECONCILIATION",
        "EOD", "DAYEND", "IRAC", "NPA", "BSR", "RETURN", "FIU"
    ],
    "LOAN": [
        "LOAN", "GOLD_LOAN", "HOME_LOAN", "PERSONAL_LOAN", "CAR_LOAN",
        "EDUCATION_LOAN", "NPA", "RECOVERY", "LIMIT", "CREDIT", "OVERDRAFT",
        "ADVANCE"
    ],
    "FRAUD": [
        "FRAUD", "MULE", "FRAUD_MULE", "SCAM", "FRAUDULENT", "DISPUTE",
        "CHARGEBACK"
    ],
    "AUDIT_REPORT": [
        "AUDIT", "VAPT", "PENETRATION", "VULNERABILITY", "SECURITY_TEST",
        "TESTING_OBSERVATION", "PEN_TEST", "KPMG", "IS_AUDIT", "CONCURRENT_AUDIT"
    ],
    "INTERNATIONAL": [
        "BOTSWANA", "UGANDA", "GUYANA", "FIJI", "SEYCHELLES", "UAE", "LONDON",
        "NEW_YORK", "SINGAPORE", "DUBAI", "KENYA", "INTERNATIONAL"
    ],
    "BRANCH_DATA": [
        "BRANCH", "BRANCH_MASTER", "BRANCH_CONTACTS", "SOL ", "BRANCHBRANDING",
        "BRANCHQR", "BRANCH_EOD"
    ],
    "TECH_CONFIG": [
        "SERVER", "DATABASE", "FINACLE", "FIREWALL", "VPN", "CONFIG",
        "httpd.conf", "THREAT_MODEL", "SIEM", "BACKUP_POLICY", "ARCHITECTURE",
        "TECHNICAL", "SOP", "RFC", "PASSWORD", "CREDENTIAL", "ROUTER", "SWITCH"
    ],
    "MOBILE_APP": [
        "APK", "IPA", "ANDROID", "IOS", "BOB_WORLD", "BOBWORLD", "MOBILE",
        "BOB WORLD"
    ],
    "LEGAL": [
        "CBI", "FIR", "LEGAL", "NOTICE", "COURT", "LITIGATION", "HITACHI",
        "BIDDOC", "BID_DOC"
    ]
}

# Reverse map: category name -> keywords
EXPOSURE_KEYWORDS = {}
for cat, keywords in EXPOSURE_DIRS.items():
    for kw in keywords:
        EXPOSURE_KEYWORDS[kw.upper()] = cat

def classify_exposure(path):
    """Classify what type of exposure a directory/file represents."""
    upper = path.upper()
    found = set()
    for kw, cat in EXPOSURE_KEYWORDS.items():
        if kw in upper:
            found.add(cat)
    return sorted(found)

# Parse inventory for zones/cities/branches and exposure categories
exposed_zones = set()
exposed_cities = set()
exposure_by_category = defaultdict(int)
exposure_details = []

# City detection patterns
KNOWN_CITIES = [
    "AHMEDABAD", "BENGALURU", "BHOPAL", "BHUBANESWAR", "CHANDIGARH", "CHENNAI",
    "COIMBATORE", "DELHI", "GOA", "HYDERABAD", "INDORE", "JAIPUR", "JODHPUR",
    "KOLKATA", "LUCKNOW", "MUMBAI", "NAGPUR", "PANAJI", "PATNA", "PUNE",
    "SURAT", "VARANASI", "PRAYAGRAJ", "TIRUCHIRAPALLI", "MADURAI", "SALEM",
    "BHILWARA", "HASSAN", "MANGALORE", "MYSURU", "SHIVAMOGGA", "GWALIOR",
    "JABALPUR", "REWA", "UJJAIN", "GURUGRAM", "NOIDA", "FARIDABAD",
    "RAIPUR", "CUTTACK", "ROURKELA", "LUDHIANA", "AMRITSAR", "JALANDHAR",
    "RANCHI", "JAMSHEDPUR", "DEHRADUN", "SRINAGAR", "JAMMU", "SHIMLA",
    "AGRA", "ALLAHABAD", "KANPUR", "MEERUT", "VADODARA", "RAJKOT",
    "AURANGABAD", "NASHIK", "SOLAPUR", "THANE", "NAVI_MUMBAI", "PALGHAR",
    "MANGALURU", "UDUPI", "BELGAUM", "HUBLI", "GULBARGA", "TIRUVANANTHAPURAM",
    "KOCHI", "KOZHIKODE", "THRISSUR", "MUMBAI METRO", "BARDHAMAN", "SILIGURI",
    "HOWRAH", "ASANSOL", "BHAGALPUR", "GAYA", "MUZAFFARPUR", "PURNEA",
    "GUWAHATI", "DIBRUGARH", "IMPHAL", "AIZAWL", "SHILLONG", "AGARTALA",
    "KOTA", "BIKANER", "UDAIPUR", "AJMER", "ALWAR", "JHALAWAR", "BUNDI",
    "NIZAMABAD", "WARANGAL", "KARIMNAGAR", "RANGAREDDY", "KHAMMAM"
]

# Parse L5 inventory
print("  Parsing L5 inventory (92K+ entries)...")
with open(INVENTORY_L5) as f:
    for line in f:
        line = line.rstrip()
        if not line or line.startswith("#") or line.startswith("|") or line.startswith("PATH") or line.startswith("---"):
            continue
        
        m = re.match(r'^  ([A-Za-z0-9_ \\.\\-&,/()]+)\s+(DIR|FILE)\s+', line)
        if m:
            name = m.group(1).strip()
            # Check for zone/region indicators
            if 'ZONE' in name.upper() or 'REGION' in name.upper():
                exposed_zones.add(name)
            
            # Check for city mentions
            for city in KNOWN_CITIES:
                if city in name.upper():
                    exposed_cities.add(city)
            
            # Classify exposure
            cats = classify_exposure(name)
            for c in cats:
                exposure_by_category[c] += 1
            
            if cats:
                exposure_details.append({"path": name, "type": m.group(2), "categories": cats})

print(f"\n[3] Results:")
print(f"  Exposed zones/regions: {len(exposed_zones)}")
print(f"  Cities with exposed data: {len(exposed_cities)}")
print(f"  Exposed items by category:")
for cat, count in sorted(exposure_by_category.items(), key=lambda x: -x[1]):
    print(f"    {cat}: {count}")

# ── 4. Build the searchable IFSC dataset ──
print("\n[4] Building IFSC search dataset...")

# Get branch names from IFSC codes using the first characters of the IFSC code
# BARB0XXXXXX - the last 6 chars encode branch
# We can extract branch names from the IFSC codes themselves
# But full data needs Razorpay API

# Build a simple mapping from IFSC to meaningful info
ifsc_dataset = []
for code in bob_codes:
    # Extract branch code (last 6 chars after BARB0)
    branch_code = code[5:] if code.startswith("BARB0") else code
    
    # Create readable branch name from code
    # Many codes map to city+branch abbreviations
    entry = {
        "ifsc": code,
        "branch_code": branch_code,
        "impacted": "UNKNOWN",  # Will be updated below
        "exposure": []
    }
    
    if code in branch_map:
        entry["branch"] = branch_map[code].get("BRANCH", "")
        entry["city"] = branch_map[code].get("CITY", branch_map[code].get("city", ""))
        entry["district"] = branch_map[code].get("district", "")
        entry["state"] = branch_map[code].get("state", "")
        entry["address"] = branch_map[code].get("address", "")
        entry["contact"] = branch_map[code].get("contact", "")
    else:
        entry["branch"] = ""
        entry["city"] = ""
        entry["district"] = ""
        entry["state"] = ""
        entry["address"] = ""
        entry["contact"] = ""
    
    ifsc_dataset.append(entry)

# ── 5. Cross-reference IFSC codes with inventory data ──
print("\n[5] Cross-referencing with inventory...")

# Extract IFSC patterns from inventory
ifsc_in_inventory = defaultdict(list)
ifsc_pat = re.compile(r'BARB0[A-Z0-9]{6}')

with open(INVENTORY_L5) as f:
    for line in f:
        matches = ifsc_pat.findall(line)
        for m in matches:
            ifsc_in_inventory[m].append(line.strip()[:150])

impacted_ifscs = set(ifsc_in_inventory.keys())
print(f"  IFSC codes found directly in inventory metadata: {len(impacted_ifscs)}")

# Mark impacted branches in dataset
for entry in ifsc_dataset:
    if entry["ifsc"] in impacted_ifscs:
        entry["impacted"] = "CONFIRMED"
        # Get exposure details from inventory
        contexts = ifsc_in_inventory[entry["ifsc"]]
        for ctx in contexts:
            cats = classify_exposure(ctx)
            for c in cats:
                if c not in entry["exposure"]:
                    entry["exposure"].append(c)
    else:
        # Check if branch is in an exposed zone/city
        city_upper = entry["city"].upper()
        for city in exposed_cities:
            if city in city_upper:
                entry["impacted"] = "SUSPECTED"
                break

impacted_count = len([e for e in ifsc_dataset if e["impacted"] == "CONFIRMED"])
suspected_count = len([e for e in ifsc_dataset if e["impacted"] == "SUSPECTED"])
print(f"  Confirmed impacted IFSCs: {impacted_count}")
print(f"  Suspected (in exposed zone): {suspected_count}")

# ── 6. Write output files ──
print(f"\n[6] Writing dataset files to {OUT_DIR}...")

# IFSC search dataset (for branch lookup + impact check)
# Trim to keep only necessary fields
search_dataset = []
for entry in ifsc_dataset:
    search_dataset.append({
        "i": entry["ifsc"],
        "b": entry["branch"][:80] if entry["branch"] else entry["branch_code"],
        "c": entry["city"][:40],
        "s": entry["state"][:40],
        "a": entry["impacted"],
        "e": entry["exposure"]
    })

with open(OUT_DIR / "ifsc_search.json", "w") as f:
    json.dump(search_dataset, f, separators=(",", ":"))
print(f"  → ifsc_search.json: {len(search_dataset)} entries ({os.path.getsize(OUT_DIR / 'ifsc_search.json') / 1024:.1f} KB)")

# Impact summary (for dashboard)
summary = {
    "total_ifsc": len(bob_codes),
    "confirmed_impacted": impacted_count,
    "suspected_impacted": suspected_count,
    "exposed_zones": sorted(list(exposed_zones)),
    "exposed_cities": sorted(list(exposed_cities)),
    "exposure_by_category": dict(sorted(exposure_by_category.items(), key=lambda x: -x[1])),
    "total_inventory_files": 92347,
    "total_inventory_dirs": 9783,
    "total_downloads_analyzed": 242,  # MB of analyzed data
    "onion_url": "http://6qqz6m3b6htudohg2mlf5gdcalonxy3sh5g4dix4mpyirjcgelqqufad.onion/bankofbaroda.bank.in/"
}

with open(OUT_DIR / "impact_summary.json", "w") as f:
    json.dump(summary, f, indent=2)
print(f"  → impact_summary.json")

# Timeline data
timeline = [
    {"date": "2026-05-01", "title": "Triple X ransomware group first observed", "detail": "Group established leak infrastructure. First detected by security researchers."},
    {"date": "2026-05-11", "title": "BNI (Indonesia) breach claimed", "detail": "Bank Negara Indonesia, ~2 TB of customer data allegedly stolen. Sample data published."},
    {"date": "2026-07-24", "title": "Bank of Baroda listed on Triple X leak site", "detail": "Group claims ~1 TB of data stolen. Security researchers verify listing."},
    {"date": "2026-07-25", "title": "Sample data goes live on Tor", "detail": "Dump server briefly online with sample files containing BCR forms with national ID photos."},
    {"date": "2026-07-25", "title": "CashlessConsumer begins investigation", "detail": "Systematic crawl of the Triple X dump server initiated. 92,347 file entries discovered."},
    {"date": "2026-07-26", "title": "Full inventory cataloged", "detail": "L0-L5 recursive inventory completed. 62 top-level branches, 2,671 subdirectories mapped. 242 MB of highest-signal files downloaded."},
    {"date": "2026-07-26", "title": "Intelligence reports published", "detail": "Threat actor dossiers, branch impact analysis, and exposure intelligence report completed."},
    {"date": "2026-07-27", "title": "bobbreach.cashlessconsumer.in launched", "detail": "Public information portal for affected consumers and researchers."}
]

with open(OUT_DIR / "timeline.json", "w") as f:
    json.dump(timeline, f, indent=2)
print(f"  → timeline.json")

# News tracker
news = [
    {"source": "DailyDarkWeb", "url": "https://x.com/DailyDarkWeb/status/", "title": "Threat Actor Claims 1 TB Bank of Baroda Data Leak", "date": "2026-07-25"},
    {"source": "ThreatAtlas", "url": "https://x.com/ThreatAtlas/status/", "title": "Triple X claims responsibility for Bank of Baroda attack", "date": "2026-07-25"},
    {"source": "CyberWatch05", "url": "https://x.com/CyberWatch05/status/", "title": "Triple X reportedly hit Bank of Baroda, up to 1TB exposed", "date": "2026-07-25"},
    {"source": "GalaxyWarden", "url": "https://www.galaxywarden.com/blog/breach/bank-of-baroda-triple-x-2026-07", "title": "Bank of Baroda Breach — Triple X (Detailed Analysis)", "date": "2026-07-25"},
    {"source": "Neuracyber Intel", "url": "https://www.neuracybintel.com/articles/triplex-strikes-indonesias-banking-giant", "title": "TripleX Strikes Indonesia's Banking Giant", "date": "2026-05-22"},
    {"source": "WatchGuard", "url": "https://www.watchguard.com/wgrd-threat-tracker", "title": "Triple X added to ransomware tracker", "date": "2026-06-01"},
]

with open(OUT_DIR / "news.json", "w") as f:
    json.dump(news, f, indent=2)
print(f"  → news.json")

# Threat actor data
threat_actor = {
    "name": "Triple X",
    "aliases": ["TripleX", "TRIPLE X", "TX"],
    "type": "Ransomware-as-a-Service / Data extortion group",
    "first_seen": "May 2026",
    "status": "Active",
    "leak_site": "http://6qqz6m3b6htudohg2mlf5gdcalonxy3sh5g4dix4mpyirjcgelqqufad.onion",
    "victims": [
        {"name": "Bank Negara Indonesia (BNI)", "country": "Indonesia", "date": "May 2026", "volume": "~2 TB"},
        {"name": "Bank of Baroda (BoB)", "country": "India", "date": "July 2026", "volume": "~1 TB"}
    ],
    "modus_operandi": [
        "Initial access via weak/compromised credentials or VPN vulnerabilities",
        "Lateral movement through Windows domain / SharePoint infrastructure",
        "Full SharePoint file server exfiltration (not core banking DB directly)",
        "Double extortion: data encryption + public leak threats",
        "Public dump server on Tor with no authentication"
    ],
    "target_sectors": ["Financial services", "Banking"],
    "geographic_focus": ["Asia-Pacific", "Indonesia", "India"],
    "tooling": ["Commodity RATs", "Rclone for exfiltration", "Custom encryption"],
    "attribution_confidence": "Low-Moderate"
}

with open(OUT_DIR / "threat_actor.json", "w") as f:
    json.dump(threat_actor, f, indent=2)
print(f"  → threat_actor.json")

# Data categories explanation (for 101 explainer)
data_categories = [
    {
        "id": "CUSTOMER_PII",
        "icon": "🔴",
        "title": "Customer KYC & Personal Data",
        "severity": "Critical",
        "description": "Aadhaar numbers, PAN cards, passport copies, voter IDs, photographs, signatures, and address proofs submitted by customers for account opening.",
        "files_found": exposure_by_category.get("CUSTOMER_PII", 0),
        "examples": ["ekyc dump.zip (53.8 MB)", "LFAR KYC done customers list.xlsx (45.9 MB)", "Re KYC UAT test cases.xlsx (35.8 MB)", "DBT BSBD Accounts Due for Rekyc.zip (26 MB)"]
    },
    {
        "id": "TRANSACTION",
        "icon": "🔴",
        "title": "Transaction Records",
        "severity": "Critical",
        "description": "Account transactions, balance statements, IRAC loan classification data, reconciliation reports, and FIU compliance data.",
        "files_found": exposure_by_category.get("TRANSACTION", 0),
        "examples": ["IRAC loan dumps", "Reconciliation data", "BBPS Recon SOP", "MAU transactions"]
    },
    {
        "id": "LOAN",
        "icon": "🟠",
        "title": "Loan Records",
        "severity": "High",
        "description": "Home loan, personal loan, car loan, education loan and gold loan files including sanction letters, repayment schedules, and NPA records.",
        "files_found": exposure_by_category.get("LOAN", 0),
        "examples": ["Gold loan files (2000+ MB)", "NPA records", "Credit limit data"]
    },
    {
        "id": "AUDIT_REPORT",
        "icon": "🔴",
        "title": "VAPT & Security Audit Reports",
        "severity": "Critical",
        "description": "Complete vulnerability assessment and penetration testing reports across all platforms — Bob World mobile apps, NEFT-RTGS, BBPS, Base24, and Uganda/Guyana international operations.",
        "files_found": exposure_by_category.get("AUDIT_REPORT", 0),
        "examples": ["VAPT Draft Report of Bob world 3.7.1 IOS", "VAPT Draft report NEFT-RTGS Application", "KPMG testing observations", "VAPT Mastersheet.xlsx"]
    },
    {
        "id": "TECH_CONFIG",
        "icon": "🔴",
        "title": "Technical Infrastructure & Credentials",
        "severity": "Critical",
        "description": "Server details, Apache httpd configs (DC+DR), database passwords, firewall rules, VPN configs, SIEM integrations, backup policies, threat models, and architectural blueprints.",
        "files_found": exposure_by_category.get("TECH_CONFIG", 0),
        "examples": ["httpd.conf_DC.txt", "httpd.conf_DR.txt", "SERVER-Details.xlsx", "ThreatModeling_BoB World.xlsx", "BACKUP_POLICY.xlsx"]
    },
    {
        "id": "MOBILE_APP",
        "icon": "🔴",
        "title": "Mobile App Source Code & Binaries",
        "severity": "Critical",
        "description": "Bob World Android APK, iOS IPA binaries, SDK source code, and build configurations — enabling reverse engineering of the bank's mobile banking platform.",
        "files_found": exposure_by_category.get("MOBILE_APP", 0),
        "examples": ["android_build_with_protect_ai_release.apk (310 MB)", "Bob World Handbook PDF", "BOB_UPI_UAT_SDK_v6.6", "Test cases for inoperative accounts"]
    },
    {
        "id": "LEGAL",
        "icon": "🔴",
        "title": "CBI Investigation & Legal Documents",
        "severity": "Critical",
        "description": "CBI First Information Report (FIR), legal notices, customer confirmations, court documents, and bid documents — revealing ongoing criminal investigations.",
        "files_found": exposure_by_category.get("LEGAL", 0),
        "examples": ["CBI FIR RC2192025E0004 (9.5 MB)", "Draft legal notices (3 parts)", "Hitachi vendor confirmation", "Customer confirmation docs"]
    },
    {
        "id": "FRAUD",
        "icon": "🟠",
        "title": "Fraud Management Data",
        "severity": "High",
        "description": "Fraud management policies, money mule account records, fraud reporting procedures, and provision statements.",
        "files_found": exposure_by_category.get("FRAUD", 0),
        "examples": ["Fraud management policies", "Mule account records", "Provision statements"]
    },
    {
        "id": "INTERNATIONAL",
        "icon": "🟠",
        "title": "International Operations Data",
        "severity": "High",
        "description": "Data from Bank of Baroda's international branches across UAE, Botswana, Fiji, Kenya, Guyana, Seychelles, Uganda, and the UK including VAPT reports for international mobile banking apps.",
        "files_found": exposure_by_category.get("INTERNATIONAL", 0),
        "examples": ["Uganda Android VAPT", "Guyana iOS/Android VAPT", "London Branch data", "Technical Architecture Manual - International"]
    },
    {
        "id": "BRANCH_DATA",
        "icon": "🟠",
        "title": "Branch Operations & Audit Reports",
        "severity": "High",
        "description": "Branch-level audit reports, EOD trackers, zone-wise inspection reports, concurrent audit findings, and branch performance data across BoB's entire network.",
        "files_found": exposure_by_category.get("BRANCH_DATA", 0),
        "examples": ["Branch EOD Tracker", "Concurrent audit reports", "Zone-wise audit findings", "BranchQR Code data"]
    }
]

with open(OUT_DIR / "data_categories.json", "w") as f:
    json.dump(data_categories, f, indent=2)
print(f"  → data_categories.json")

print(f"\n✅ Dataset build complete. Output in {OUT_DIR}/")
