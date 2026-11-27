# EU Translation Memory Extractor (DGT-TM)

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Version 2.5](https://img.shields.io/badge/Version-2.5-indigo.svg)](#)
[![Python 3.8+](https://img.shields.io/badge/Python-3.8%2B-green.svg)](https://www.python.org/downloads/)
[![TMX 1.4](https://img.shields.io/badge/Standard-TMX%201.4-orange.svg)](#)
[![Zero Dependencies](https://img.shields.io/badge/Dependencies-None%20(stdlib%20only)-teal.svg)](#)

A fast, zero-dependency Python utility for extracting, filtering, and splitting bilingual **Translation Memories (`.tmx`)** and sentence datasets from the official **European Union DGT-TM / Euramis** corpus across all 24 official EU languages.

Designed for translators, terminologists, Language Service Providers (LSPs), translation students, and NLP researchers — works out-of-the-box with **1-click launchers** (no terminal knowledge required) as well as a full **CLI** for automated pipelines.

---

## ✨ Key Features

- **1-Click Launchers (Zero Terminal Setup):** Double-click launchers for Windows (`run_windows.bat`), macOS (`run_mac.command`), and Linux (`run_linux.sh`), with automatic UTF-8 & Windows Console ANSI/VT initialization.
- **5-Step Interactive Wizard:** Guided step-by-step assistant with clean top breadcrumb banners and automatic viewport scrolling.
- **Official EU Repository Downloader (`data.europa.eu`):** Download individual volumes, full years, or the entire DGT-TM repository (87 ZIP volumes, 2004–2025) into a selectable destination folder (default: `/TMX`), complete with a pre-flight **disk space check**, ZIP integrity verification, and resume/skip support.
- **Sequential Batch Processing (`--batch`):** Process an entire folder of `.zip` archives one by one, resilient to corrupted archives, generating per-volume TMX files and a master summary report.
- **CAT Tool RAM Protection (`--split`):** Splits large TMX outputs into manageable, standalone TMX 1.4 XML chunks (`_part01.tmx`, `_part02.tmx`, ...; default 50,000 segments) to prevent SDL Trados Studio and memoQ from freezing during import.
- **10-Category Market-Aligned Domain Classification (`--categories`, `--split-by-category`):**
  - Splits or filters segments into **10 translation-market verticals**: `legal`, `finance`, `trade`, `it_telecom`, `engineering`, `energy_env`, `medical`, `chemicals`, `agri_food`, and `general`.
  - Powered by a two-stage pure-Python offline engine combining hyphen/Unicode-safe tiered collocation rules, per-language anti-doubling scoring, TF-IDF/bigram cosine similarity, and dominant-only document-title context priors.
  - **Multi-label routing:** Segments matching two or more specialized domains are written to all matching category files. *(Note: Automated machine classification is heuristic and not 100% accurate.)*
- **Multiple Export Formats:** Standard **TMX 1.4** (`.tmx`), **Excel / TSV** (`.tsv`), **JSONL** (`.jsonl` for AI/LLM fine-tuning), or all simultaneously.
- **Deduplication & Automatic Export Reports:** Removes duplicate pairs and identical source/target segments, and generates detailed `*_report.txt` summaries with domain breakdowns and sample previews.

---

## 🏷️ Domain Categories (10 Translation-Market Verticals)

| Category Code | CLI Shorthand Aliases | Scope & Representative EU Domains |
| :--- | :--- | :--- |
| **`legal`** | — | Law, Judiciary (CJEU), Treaties, Institutional Procedures, Fundamental Rights, Criminal/Civil Law & Sanctions Frameworks |
| **`finance`** | — | Banking Supervision (CRR/CRD, ECB, LCR/NSFR), Accounting & Financial Reporting (IFRS/IAS), Capital Markets, Insurance & Taxation (VAT, Excise) |
| **`trade`** | `business`, `customs` | International Trade (FTA/WTO), Customs & Combined Nomenclature (CN), Anti-dumping, Public Procurement, Antitrust, State Aid & Corporate/SME Policy |
| **`it_telecom`** | `it`, `telecom`, `cyber` | Software & Cloud Systems, Cybersecurity (NIS2), Artificial Intelligence, Personal Data Protection (GDPR), Digital Services & Radio Spectrum/Telecom |
| **`engineering`** | `tech`, `transport`, `automotive` | Automotive & UNECE Type-Approval, Exhaust After-Treatment, Aviation (EASA), Rail (ERTMS), Maritime, Machinery, Electronics, Construction & Metrology |
| **`energy_env`** | `environment`, `energy`, `climate` | Power Grids, Renewables, Energy Efficiency, Climate Policy, Emissions Trading (EU ETS / CBAM), Waste Management, Water Protection & Biodiversity |
| **`medical`** | `pharma`, `health` | Human & Veterinary Medicinal Products (EMA), Clinical Trials, Pharmacovigilance, Medical Devices (MDR/IVDR), Epidemiology & Public Health |
| **`chemicals`** | `chem`, `reach` | Industrial Chemicals (REACH), Classification & Labelling (CLP), Safety Data Sheets (SDS), Biocides, Plant Protection Products & Toxicology |
| **`agri_food`** | `food`, `agri`, `agriculture` | Common Agricultural Policy (CAP), Food Safety & Hygiene (EFSA), Maximum Residue Levels (MRLs), Food Labelling, Animal Feed & Fisheries (CFP) |
| **`general`** | — | General Administrative Text, Dates/Signatures, Tabular Annexes, Named Entity / Sanctions Entries & Unclassified Fallback |

---

## 🧠 Domain Classification Methodology

Developing an accurate, fast, **100% offline** domain classifier for European Union translation memories required addressing both the structural properties of the DGT-TM corpus and the practical requirements of professional CAT workflows.

### 1. Corpus Constraints & English-Pivot Lookup
Official DGT-TM XML files store translation units (`<tu>`) containing a document identifier (`<prop type="Txt::Doc. No.">CELEX_OR_EFTA_ID</prop>`) and parallel language segments (`<tuv lang="XX-YY"><seg>...</seg></tuv>`), **without** embedded EuroVoc descriptors or subject-matter tags. Domain classification must therefore operate directly on segment text at streaming speeds (10,000+ pairs/sec) using only the Python standard library.

Because virtually every `<tu>` in DGT-TM contains an English segment (`EN-GB` / `EN`), whenever a user extracts a non-English pair (e.g., `DE ➔ PL` or `FR ➔ ES`), the XML parser automatically captures the sibling `EN` `<tuv>` within the same `<tu>` as an internal classification pivot (`capture_pivot_en=True`), guaranteeing consistent domain recall across all 24 EU languages.

### 2. Taxonomy Calibration: Empirical Corpus Audit + LSP Market Alignment
Rather than relying on arbitrary keyword lists, the 10-category taxonomy was designed at the intersection of two analyses:
1. **Empirical Audit of DGT-TM (`Vol_2025.new_1.zip`):** Full extraction and document-level profiling of 863 official EU acts (251,867 `<tu>` units; 164,201 unique `EN ➔ PL` pairs) revealed the actual thematic distribution of contemporary EU translation output — led by Financial Reporting, Banking & Trade (~29.6% of acts), Agri-Food & Fisheries (~11.4%), Transport, Automotive & Engineering (~11.2%), Justice, Institutional Law & Sanctions (~10.5%), Energy, Climate & Environment (~6.8%), IT, Cybersecurity & Telecom (~5.8%), Pharmaceuticals, Medical Devices & Veterinary (~4.2%), and REACH/CLP/Biocidal Chemicals (~3.7%).
2. **Translation Industry Verticals (ISO 17100 / Commercial LSP Specializations):** Coarse buckets such as a single `"tech"` or `"business"` category cause severe terminology contamination in CAT tools (e.g., mixing software UI strings with diesel engine homologation, or mixing IFRS balance-sheet terminology with customs tariff schedules). Splitting `finance` vs. `trade`, `it_telecom` vs. `engineering`, and `medical` vs. `chemicals` vs. `agri_food` mirrors how professional translation agencies maintain separate client and subject-matter Translation Memories.

### 3. Two-Stage Hybrid Offline Engine
Each translation unit is evaluated by a deterministic, zero-dependency two-stage pipeline (`DomainClassifier`):

- **Stage A1 — 3-Tier Bilingual Regex & Collocation Engine:**
  - **Weighted Evidence Tiers (`threshold = 3`):**
    - *Tier 3 (`weight = 3`):* High-precision multi-word collocations and unambiguous specialist terms (e.g., `clinical trial`, `pharmacovigilance`, `liquidity coverage`, `balance sheet`, `anti-dumping`, `exhaust after-treatment`, `safety data sheet`, `cybersecurity`). A single Tier-3 hit immediately satisfies the `>= 3` threshold.
    - *Tier 2 (`weight = 2`):* Core domain terms (`vaccine`, `customs`, `renewable`, `encryption`, `homologation`, `pesticide`) that require corroboration from another domain term, statistical boost, or dominant document context.
    - *Tier 1 (`weight = 1`):* Supporting vocabulary (`patient`, `engine`, `audit`, `network`, `livestock`) that reinforces domain context without causing standalone false positives.
  - **Unicode & Hyphen-Safe Token Boundaries:** Patterns are compiled with `(?<![^\W_]|-)(?:...)(?![^\W_]|-)` and explicit Polish inflectional suffixes (`[a-ząćęłńóśźż]*`). Prohibiting matches across hyphens prevents engineering compounds like `exhaust after-treatment` from splitting on `-` and matching `treatment` (`medical`), while Unicode-aware boundaries properly handle Polish diacritics and non-breaking spaces (`\xa0`) common in Euramis exports.
  - **Per-Language Distinct-Concept Scoring (Anti-Self-Doubling):** Source text, target text, and pivot `EN` text are scored **independently** (`max(score_source, score_target, score_pivot)`), counting only **distinct matched surface forms** within each language. Summing bilingual matches across EN + PL would otherwise double every single `weight = 2` word (`calibration` [2] + `kalibracja` [2] = `4 >= 3`), inflating false positives.
  - **Polysemy Lookarounds & Cross-Domain Suppression:** Targeted negative lookarounds resolve high-frequency EU polysemy traps — e.g., `natural(?!\s+(?:and\s+legal\s+)?persons?)` (preventing *"natural and legal persons"* from hitting `energy_env`), `technical(?!\s+assistance)`, `undertaking(?!\s+services)`, `(?<!financial\s)liabilit`, `emisj*(?!\s+akcji|\s+obligacji)` (share/bond issuance vs. pollutant emissions), and `(?<!mineral\s)(?<!aerated\s)waters?`. Furthermore, strong `engineering`, `energy_env`, or `chemicals` evidence suppresses weak (non-Tier-3) `medical` noise triggered by shared terms like `diagnostic`, `treatment`, or `exposure`.

- **Stage A2 — Statistical TF-IDF + Bigram Centroid Classifier (`OfflineTfidfBayesClassifier`):**
  - Tokenizes segments into hyphen-preserving unigrams and adjacent word bigrams, computing L2-normalized TF-IDF cosine similarity against curated EU domain centroid vectors across all 9 specialized categories.
  - Segments with at least 4 informative features receive a `+1` (`cos >= 0.13`) or `+2` (`cos >= 0.24`) score boost, allowing lexically dense domain sentences to reach threshold even when phrasing varies.

### 4. Dominant-Only Document-Title Context Prior
The classifier profiles the opening 6 segments (titles and recitals) of each document (`Txt::Doc. No.`). To prevent multi-topic regulations or annexes from leaking noise across an entire file, a conservative `+1` document prior is applied **only** when:
1. The segment itself already contains direct domain terminology (`raw_score >= 2`), and
2. The domain is a **dominant theme** of that document (`cumulative_title_score >= 5` and `>= 50%` of the document's highest-scoring domain).

Short boilerplate segments (dates, city names, article numbers, signature blocks, person/entity tables) carry `raw_score < 2` and therefore remain cleanly isolated in `general`.

### 5. Multi-Label Routing & Linguistic Verification
Regulatory sentences genuinely straddle domains (for example, *"Pursuant to Directive 2024/10, engine exhaust emission limits must prevent air pollution"* legitimately belongs to `legal`, `engineering`, and `energy_env`). Whenever multiple specialized categories reach `score >= 3`, `CategoryRouterWriter` writes the translation unit to **each** matching category file, lazily creating output files so categories with zero matches never leave empty `.tmx` files on disk.

---

## 🚀 Quick Start (For Non-Technical Users)

1. **Install Python 3** (one-time setup; on Windows make sure to check **`Add python.exe to PATH`**).
2. **Unzip** the release archive (`EU_TMX_Extractor.zip`) into a regular folder on your computer.
3. **Double-click** the launcher for your operating system:
   - **Windows:** `run_windows.bat`
   - **macOS:** `run_mac.command`
   - **Linux:** `run_linux.sh`
4. Open [`INSTRUCTIONS.html`](INSTRUCTIONS.html) in your browser for a visual step-by-step guide, including import instructions for **SDL Trados Studio**, **memoQ**, **OmegaT**, and **Microsoft Excel**.

---

## 🛠️ Command-Line Interface (CLI)

```bash
# Launch the interactive 5-step wizard
python3 tmx_extractor.py

# Extract EN -> PL from a ZIP archive, splitting every 50,000 segments for CAT stability
python3 tmx_extractor.py -i Vol_2025.new_1.zip -s EN -t PL -o memory_en_pl.tmx --split 50000

# Split extracted segments into separate TMX files across all 10 domain categories
python3 tmx_extractor.py -i Vol_2025.new_1.zip -s EN -t PL -o memory_en_pl.tmx --split-by-category

# Filter only selected categories (supports canonical names and shorthand aliases)
python3 tmx_extractor.py -i Vol_2025.new_1.zip -s EN -t PL -o memory_en_pl.tmx --categories legal,finance,medical --split-by-category

# Batch process all ZIP archives in a directory
python3 tmx_extractor.py -i ../TMX --batch -s EN -t PL --output-dir ./results --split 50000

# Download the entire official DGT-TM repository (2004–2025)
python3 tmx_extractor.py --download-repo --dest-dir ../TMX

# View MIT license
python3 tmx_extractor.py --license
```

### Main CLI Options

| Flag | Description |
| :--- | :--- |
| `-i`, `--input` | Input `.tmx` file, `.zip` archive, or directory |
| `-s`, `--source-lang` | Source language code or name (e.g. `EN`, `DE`, `Polish`) [default: `EN`] |
| `-t`, `--target-lang` | Target language code or name (e.g. `PL`, `FR`, `German`) [default: `PL`] |
| `-o`, `--output` | Base output file path |
| `-f`, `--format` | Output format: `tmx`, `tsv`, `jsonl`, or `all` [default: `tmx`] |
| `--batch` | Process all `.zip` archives in the `--input` directory sequentially |
| `--output-dir` | Destination directory for batch mode |
| `--split N` | Split output every `N` segments (e.g. `50000`) for CAT RAM protection |
| `--categories LIST` | Comma-separated domain filter: `legal,finance,trade,it_telecom,engineering,energy_env,medical,chemicals,agri_food,general` |
| `--split-by-category` | Write separate output files per domain (`_legal`, `_finance`, `_trade`, etc.) |
| `--no-dedup` | Keep duplicate translation pairs |
| `--no-filter-identical` | Keep segments where source and target text are identical |
| `--download-repo` | Download the full DGT-TM dataset from `data.europa.eu` |
| `--dest-dir DIR` | Target folder for repository downloads [default: `TMX` folder] |

---

## 📁 Project Structure

```text
EU_TMX_Extractor/
├── tmx_extractor.py        # Core extraction engine, 10-domain classifier, wizard & CLI
├── run_windows.bat         # 1-click Windows launcher
├── run_mac.command         # 1-click macOS launcher
├── run_linux.sh            # 1-click Linux launcher
├── INSTRUCTIONS.html       # Visual user guide (Python setup, wizard, CAT import, FAQ)
├── INSTRUCTIONS.md         # Markdown documentation
├── student_notice.html     # Embeddable HTML notice for course portals
├── README.md               # Project overview & domain classification methodology
├── LICENSE                 # MIT License
├── run_e2e_tests.py        # Automated E2E test runner
└── tests/
    └── test_e2e.py         # End-to-end test suite (23 tests)
```

---

## 🧪 Running Tests

The project uses only Python's standard library and includes an automated end-to-end test suite (23 tests) covering TMX 1.4 XML validation, RAM-protection chunking, batch ZIP resilience, Windows/macOS/Linux console compatibility, repository downloads, and 10-category domain classification (including polysemy disambiguation, hyphenated compounds, and multi-label routing):

```bash
python3 run_e2e_tests.py
```

---

## 📜 Attribution & License

Developed by **Michał Kornacki** (in Antigravity, 2026) and released under the [**MIT License**](LICENSE).

Built upon and inspired by:
- **`TMXtract.jar`** – Official tool by the European Commission Directorate-General for Translation (DGT) / Joint Research Centre (JRC), 2013.
- **`tmxtract`** – Open-source C# tool by Rodrigo Nepomuceno (2019, MIT, [github.com/Nepomuceno/tmxtract](https://github.com/Nepomuceno/tmxtract)).
