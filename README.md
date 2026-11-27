# EU Translation Memory Extractor (DGT-TM)

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Version 2.6](https://img.shields.io/badge/Version-2.6-indigo.svg)](#)
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
- **Unified Multi-ZIP Batch Extraction (`--batch`):** Streams an entire folder of `.zip` archives (up to all 87 DGT-TM volumes) into **one unified output** using your chosen base filename, with **global 96-bit `blake2b` cross-volume deduplication** and fault-tolerant skipping of corrupted archives. *(Optional `--per-zip` flag preserves legacy one-file-per-ZIP output.)*
- **CAT Tool RAM Protection (`--split`):** Splits large TMX outputs into manageable, standalone TMX 1.4 XML chunks (`_part01.tmx`, `_part02.tmx`, ...) with built-in wizard presets for **50,000**, **100,000**, **200,000**, and **300,000** segments (or any custom limit) to prevent SDL Trados Studio and memoQ from freezing during import.
- **10-Category Market-Aligned Domain Classification (`--categories`, `--split-by-category`):**
  - Splits or filters segments into **10 translation-market verticals**: `legal`, `finance`, `trade`, `it_telecom`, `engineering`, `energy_env`, `medical`, `chemicals`, `agri_food`, and `general`, organizing each category into its own dedicated subfolder (`legal/`, `finance/`, `medical/`, ...) for effortless bulk CAT import.
  - Powered by a two-stage pure-Python offline engine combining hyphen/Unicode-safe tiered collocation rules, per-language anti-doubling scoring, TF-IDF/bigram cosine similarity, and dominant-only document-title context priors.
  - **Language Pair Scope (`EN`/`PL` + DGT-TM `EN` Pivot):** Classification dictionaries and statistical prototypes are built for **English (`EN`) and Polish (`PL`)**. Pairs without `EN` or `PL` (e.g., `FR ➔ DE`) are classified via the sibling `<tuv lang="EN">` segment **only when extracting from official multilingual DGT-TM packages**; standalone bilingual `.tmx` files lacking `EN` or `PL` (e.g., a pre-extracted `FR ➔ DE` file) **cannot** be categorized by domain.
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

### 1. Corpus Constraints, Language Scope & English-Pivot Lookup
Official DGT-TM XML files store translation units (`<tu>`) containing a document identifier (`<prop type="Txt::Doc. No.">CELEX_OR_EFTA_ID</prop>`) and parallel language segments (`<tuv lang="XX-YY"><seg>...</seg></tuv>`), **without** embedded EuroVoc descriptors or subject-matter tags. Domain classification must therefore operate directly on segment text at streaming speeds (10,000+ pairs/sec) using only the Python standard library.

> [!IMPORTANT]
> **Language Pair Availability (`EN` / `PL` Dictionaries & Multilingual Pivot):**
> The built-in rule dictionaries and TF-IDF prototypes recognize **English (`EN`)** and **Polish (`PL`)** terminology (they do not include French, German, Spanish, etc. lexicons). Domain categorization therefore operates as follows:
> - **Pairs containing `EN` or `PL` (e.g., `EN ➔ PL`, `EN ➔ DE`, `FR ➔ EN`, `DE ➔ PL`):** Supported on **all** input files (both multilingual DGT-TM archives and standalone bilingual `.tmx` files).
> - **Pairs without `EN` or `PL` (e.g., `FR ➔ DE`, `ES ➔ IT`) on official multilingual DGT-TM packages:** **Supported** via automatic *English-pivot lookup* (`capture_pivot_en=True`). Because virtually every `<tu>` in raw DGT-TM archives embeds ~24 EU languages including `<tuv lang="EN-GB">`, the parser inspects the sibling `EN` segment inside the same `<tu>` to classify the unit while writing only `FR` and `DE` to the output `.tmx`.
> - **Pairs without `EN` or `PL` (e.g., `FR ➔ DE`) on standalone bilingual `.tmx` files:** **Not available.** If the input `.tmx` contains *only* `FR` and `DE` (no `EN` or `PL` `<tuv>` inside `<tu>`), the classifier cannot match terminology, emits a warning in the console and export report, and routes segments to `general`.

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

## 📊 Full DGT-TM Corpus Extraction Statistics (2026)

As a real-world benchmark of the full official European Commission **DGT-TM** repository (**2004–2025**, all **87 ZIP archives**), a unified batch extraction was executed for **English (`EN`) ➔ Polish (`PL`)** on **27 November 2026** using **EU TMX Extractor v2.6** (`--split-by-category --split 200000`):

### Corpus Overview

| Metric | Result |
| :--- | :--- |
| **Source Corpus** | Official European Commission DGT-TM (2004–2025) |
| **Language Pair** | English (`EN`) ➔ Polish (`PL`) |
| **Archives Processed** | `87 / 87` ZIP volumes (`0` errors; `54,770` internal `.tmx` files scanned) |
| **Total Translation Units Scanned** | `10,078,172` |
| **Unique Segments Extracted** | **`5,044,373`** |
| **Global Duplicates Removed** | `3,103,116` (`38.1%` reduction across all 87 volumes) |
| **Identical Segments Filtered** | `8,832` |
| **Output Files Generated** | `33` standalone TMX 1.4 files (max 200,000 segments/file; ~3.03 GB total) |
| **Total Processing Time** | `1 h 25 min` (`5,098.02 s`) |

### Segments by Domain Category

| Category | Segments | Share of Unique Pairs | Output TMX Files |
| :--- | ---: | ---: | ---: |
| **`legal`** (Law, Judiciary & EU Legislation) | **1,671,437** | 33.1% | 9 |
| **`trade`** (International Trade, Customs, Procurement & Business) | **578,540** | 11.5% | 3 |
| **`finance`** (Banking, Accounting IFRS & Taxation) | **377,402** | 7.5% | 2 |
| **`engineering`** (Automotive, Transport, Aviation, Rail & Machinery) | **194,570** | 3.9% | 1 |
| **`agri_food`** (Agriculture, Food Safety EFSA & Fisheries) | **148,782** | 2.9% | 1 |
| **`energy_env`** (Energy, Climate, EU ETS & Environment) | **145,697** | 2.9% | 1 |
| **`it_telecom`** (IT, Software, Cybersecurity, AI & Telecom) | **73,307** | 1.5% | 1 |
| **`chemicals`** (REACH/CLP, Safety Data Sheets & Biocides) | **62,709** | 1.2% | 1 |
| **`medical`** (Pharmaceuticals, Clinical Trials, MDR/IVDR & Veterinary) | **56,457** | 1.1% | 1 |
| **`general`** (Administrative, Annexes, Entity Lists & Fallback) | **2,462,903** | 48.8% | 13 |

> [!NOTE]
> Because domain classification uses **multi-label routing** (a segment matching two or more domains is placed into each relevant category), total category placements (`5,771,804`) exceed the `5,044,373` unique translation pairs, and percentages sum to more than 100%.

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

# Merge all ZIP archives in a directory into unified category subfolders & 100,000-segment chunks
python3 tmx_extractor.py -i ../TMX --batch -s EN -t PL -o eu_dgt_en_pl.tmx --output-dir ./results --split-by-category --split 100000

# Legacy batch mode: write separate files per ZIP archive
python3 tmx_extractor.py -i ../TMX --batch --per-zip -s EN -t PL --output-dir ./results --split 50000

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
| `--batch` | Merge all `.zip` archives in `--input` into one unified output with global deduplication |
| `--per-zip` | In `--batch` mode, write separate output files for each ZIP archive instead of merging |
| `--output-dir` | Destination directory for batch mode |
| `--split N` | Split output every `N` segments (e.g. `50000`, `100000`, `200000`, `300000`) for CAT RAM protection |
| `--categories LIST` | Comma-separated domain filter: `legal,finance,trade,it_telecom,engineering,energy_env,medical,chemicals,agri_food,general` |
| `--split-by-category` | Write per-category subfolders (`legal/`, `finance/`, `trade/`, etc.) with domain-specific TMX files |
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
    └── test_e2e.py         # End-to-end test suite (26 tests)
```

---

## 🧪 Running Tests

The project uses only Python's standard library and includes an automated end-to-end test suite (26 tests) covering TMX 1.4 XML validation, RAM-protection chunking, unified multi-ZIP batch merging with global cross-volume deduplication, per-category subfolders, `--per-zip` legacy mode, Windows/macOS/Linux console compatibility, live progress bar rendering, repository downloads, and 10-category domain classification:

```bash
python3 run_e2e_tests.py
```

---

## 📜 Attribution & License

- **Author:** **Michał Kornacki, PhD**, University of Łódź, ORCID: [https://orcid.org/0000-0002-0694-004X](https://orcid.org/0000-0002-0694-004X) *(in Antigravity, 2026)*
- **License:** Released under the [**MIT License**](LICENSE).

Built upon and inspired by:
- **`TMXtract.jar`** – Official tool by the European Commission Directorate-General for Translation (DGT) / Joint Research Centre (JRC), 2013.
- **`tmxtract`** – Open-source C# tool by Rodrigo Nepomuceno (2019, MIT, [github.com/Nepomuceno/tmxtract](https://github.com/Nepomuceno/tmxtract)).

### Data License & Non-Affiliation Notice
- **Independent Open-Source Tool:** *EU TMX Extractor* is an independent, clean-room Python utility and is **not** affiliated with, endorsed by, or an official software product of the European Commission or the Directorate-General for Translation (DGT).
- **DGT-TM Dataset License:** This repository does **not** redistribute DGT-TM data files. The official DGT-TM archives downloaded by users from `data.europa.eu` / JRC are open public datasets published by the European Union (© European Union, Directorate-General for Translation) under **Commission Decision 2011/833/EU** and **Creative Commons Attribution 4.0 International (CC BY 4.0)**. Users reusing extracted translation memories should attribute the European Commission (DGT) as the data source and indicate any filtering or modifications applied.
