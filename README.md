# EU Translation Memory Extractor (DGT-TM)

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.8+](https://img.shields.io/badge/Python-3.8%2B-green.svg)](https://www.python.org/downloads/)
[![TMX 1.4](https://img.shields.io/badge/Standard-TMX%201.4-orange.svg)](#)
[![Zero Dependencies](https://img.shields.io/badge/Dependencies-None%20(stdlib%20only)-teal.svg)](#)

A fast, zero-dependency Python utility for extracting, filtering, and splitting bilingual **Translation Memories (`.tmx`)** and sentence datasets from the official **European Union DGT-TM / Euramis** corpus across all 24 official EU languages.

Designed for translators, terminologists, translation students, and researchers — works out-of-the-box with **1-click launchers** (no terminal knowledge required) as well as a full **CLI** for automated pipelines.

---

## ✨ Key Features

- **1-Click Launchers (Zero Terminal Setup):** Double-click launchers for Windows (`run_windows.bat`), macOS (`run_mac.command`), and Linux (`run_linux.sh`), with automatic UTF-8 & Windows Console ANSI/VT initialization.
- **5-Step Interactive Wizard:** Guided step-by-step assistant with clean top breadcrumb banners and automatic viewport scrolling.
- **Official EU Repository Downloader (`data.europa.eu`):** Download individual volumes, full years, or the entire DGT-TM repository (87 ZIP volumes, 2004–2025) file-by-file, complete with a pre-flight **disk space check**, ZIP integrity verification, and resume/skip support.
- **Sequential Batch Processing (`--batch`):** Process an entire folder of `.zip` archives one by one, resilient to corrupted archives, generating per-volume TMX files and a master summary report.
- **CAT Tool RAM Protection (`--split`):** Splits large TMX outputs into manageable, standalone TMX 1.4 XML chunks (`_part01.tmx`, `_part02.tmx`, ...; default 50,000 segments) to prevent SDL Trados Studio and memoQ from freezing during import.
- **Offline Domain Categorization & Splitting (`--categories`, `--split-by-category`):**
  - Classifies segments into **`legal`**, **`business`**, **`environment`**, **`tech`**, **`medical`**, and **`general`**.
  - Uses a two-stage pure-Python offline engine: hyphen-safe tiered terminology/collocation rules with cross-domain disambiguation + a TF-IDF/bigram statistical classifier + dominant-only document-title context prior.
  - **Multi-label routing:** Segments matching multiple domains are placed into all matching category files. *(Note: Automated machine classification is heuristic and not 100% accurate.)*
- **Multiple Export Formats:** Standard **TMX 1.4** (`.tmx`), **Excel / TSV** (`.tsv`), **JSONL** (`.jsonl` for AI/LLM fine-tuning), or all simultaneously.
- **Deduplication & Automatic Export Reports:** Removes duplicate pairs and identical source/target segments, and writes detailed `*_report.txt` summaries with segment counts and sample previews.

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
python3 tmx_extractor.py -i Vol_2009_4.zip -s EN -t PL -o memory_en_pl.tmx --split 50000

# Split extracted segments into separate TMX files by domain category
python3 tmx_extractor.py -i Vol_2006_5.zip -s EN -t PL -o memory_en_pl.tmx --split-by-category

# Filter only legal and medical segments into separate domain files
python3 tmx_extractor.py -i Vol_2006_5.zip -s EN -t PL -o memory_en_pl.tmx --categories legal,medical --split-by-category

# Batch process all ZIP archives in a directory
python3 tmx_extractor.py -i ./dgt_zips --batch -s EN -t PL --output-dir ./results --split 50000

# Download the entire official DGT-TM repository (2004–2025)
python3 tmx_extractor.py --download-repo --dest-dir ./dgt_zips

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
| `--categories LIST` | Comma-separated domain filter: `legal,business,environment,tech,medical,general` |
| `--split-by-category` | Write separate output files per domain (`_legal`, `_business`, etc.) |
| `--no-dedup` | Keep duplicate translation pairs |
| `--no-filter-identical` | Keep segments where source and target text are identical |
| `--download-repo` | Download the full DGT-TM dataset from `data.europa.eu` |

---

## 📁 Project Structure

```text
EU_TMX_Extractor/
├── tmx_extractor.py        # Core extraction engine, domain classifier, wizard & CLI
├── run_windows.bat         # 1-click Windows launcher
├── run_mac.command         # 1-click macOS launcher
├── run_linux.sh            # 1-click Linux launcher
├── INSTRUCTIONS.html       # Visual user guide (Python setup, wizard, CAT import, FAQ)
├── INSTRUCTIONS.md         # Markdown documentation
├── student_notice.html     # Embeddable HTML notice for course portals
├── LICENSE                 # MIT License
├── run_e2e_tests.py        # Automated E2E test runner
└── tests/
    └── test_e2e.py         # End-to-end test suite (21 tests)
```

---

## 🧪 Running Tests

The project uses only Python's standard library and includes a comprehensive end-to-end test suite covering TMX 1.4 XML validation, RAM-protection chunking, batch ZIP resilience, Windows/macOS/Linux console compatibility, repository downloads, and domain classification:

```bash
python3 run_e2e_tests.py
```

---

## 📜 Attribution & License

Developed by **Michał Kornacki** (in Antigravity, 2026) and released under the [**MIT License**](LICENSE).

Built upon and inspired by:
- **`TMXtract.jar`** – Official tool by the European Commission Directorate-General for Translation (DGT) / Joint Research Centre (JRC), 2013.
- **`tmxtract`** – Open-source C# tool by Rodrigo Nepomuceno (2019, MIT, [github.com/Nepomuceno/tmxtract](https://github.com/Nepomuceno/tmxtract)).
