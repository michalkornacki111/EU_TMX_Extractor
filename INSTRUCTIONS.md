# EU Translation Memory Extractor (DGT-TM / Euramis) 🇪🇺

> **Author:** Michał Kornacki, PhD, University of Łódź, ORCID: [https://orcid.org/0000-0002-0694-004X](https://orcid.org/0000-0002-0694-004X) *(in Antigravity, 2026)*  
> **License:** MIT License (2026) – full text in the [`LICENSE`](file:///home/michal/Data/TMX%20Extract/---%20APP%20---/LICENSE) file or enter `L` in the application  
> **Base Tools:** Developed based on:
> - `TMXtract.jar` – official tool from the Directorate-General for Translation (DGT) / Joint Research Centre (JRC) of the **European Commission** (2013)
> - `tmxtract` – open-source project by **Rodrigo Nepomuceno** (2019, MIT, https://github.com/Nepomuceno/tmxtract)

A modern, fast, and beginner-friendly Python tool for extracting ready-to-use Translation Memories (TMX) and bilingual sentence databases in any selected EU language pair from the official European Union legislative corpus.

---

## 📜 MIT License

This program is 100% free and open-source under the **MIT License**:
* View the full license inside the application:
  * In the interactive wizard: choose option **`[L]`**
  * From the command line: run `python3 tmx_extractor.py --license`
  * Text file: [**`LICENSE`**](file:///home/michal/Data/TMX%20Extract/---%20APP%20---/LICENSE)
  * Visual interactive manual: [**`INSTRUCTIONS.html`**](file:///home/michal/Data/TMX%20Extract/---%20APP%20---/INSTRUCTIONS.html)

---

## 🚀 Quick Start (No Terminal Experience Needed)

Ready-to-use 1-click launchers are included. Simply **double-click the file for your operating system**:

* **Windows**: Double-click [`run_windows.bat`](file:///home/michal/Data/TMX%20Extract/---%20APP%20---/run_windows.bat)
* **Mac (macOS)**: Double-click [`run_mac.command`](file:///home/michal/Data/TMX%20Extract/---%20APP%20---/run_mac.command)
* **Linux**: Double-click [`run_linux.sh`](file:///home/michal/Data/TMX%20Extract/---%20APP%20---/run_linux.sh) *(or run `python3 tmx_extractor.py` in terminal)*

> 📘 **Visual User Guide:** Open [**`INSTRUCTIONS.html`**](file:///home/michal/Data/TMX%20Extract/---%20APP%20---/INSTRUCTIONS.html) in your browser for a visual step-by-step installation guide and CAT import instructions for SDL Trados Studio, memoQ, and OmegaT.

---

## ✨ Features in Version 2.6

### 1. 🌐 Download the ENTIRE Official DGT-TM Repository (File by File)
Instead of downloading individual volumes manually:
- In the download menu, select option:  
  👉 **`[W] DOWNLOAD ENTIRE REPOSITORY AT ONCE (all 87 ZIP files, 2004–2025, file by file) [RECOMMENDED]`**
- You can also download all parts of a specific year (e.g., all 5 parts of year 2025).

### 2. 📊 Disk Space Calculation & Pre-flight Summary
Before any download begins, the program displays an exact storage summary:
- Total volumes in the repository (87 ZIP files)
- Files already downloaded locally (detected, verified for ZIP integrity, and skipped)
- Exact number of new files to download
- Estimated download size (~**7.6 GB** for the entire 2004–2025 repository)
- Available free disk space on your drive
- Safety status: `[OK] Sufficient free space available` or critical warning if disk is full.

### 3. 🎯 Post-Download Action Choice: Immediate Extraction or Exit
After downloads finish, the application asks:
- **`[1] Proceed directly to TMX extraction (Batch mode across all files) [Recommended]`** – immediately configures your language pair (e.g. English ➔ Polish) and extracts all downloaded archives.
- **`[2] Finish and exit here`** – cleanly saves all ZIP archives in your folder for future use.

### 4. 🗂️ Unified Multi-ZIP Batch Extraction (Merged Output + Global Deduplication)
If you have multiple ZIP files in your directory (up to all 87 DGT-TM volumes):
- Select option **`[W]`** in Step 1 of the wizard or run with `--batch`.
- The wizard asks for **one destination folder and one base output filename** (e.g., `dgt_en_pl.tmx`), streaming all archives into a single unified output with **global 96-bit `blake2b` deduplication** across all volumes.
- Instead of hundreds of fragmented per-ZIP files, you get clean domain subfolders (`legal/`, `finance/`, ...) chunked only when a category exceeds your chosen segment limit (`_part01.tmx`, `_part02.tmx`, ...).
- Corrupted archives are safely skipped without halting the rest of the batch. *(Legacy per-ZIP output remains available in CLI via `--batch --per-zip`.)*

### 5. 🛡️ CAT Tool RAM Protection & File Chunking
Huge translation memories (>100,000 segments) can freeze or crash SDL Trados Studio and memoQ.
- Step 3 offers quick presets for **50,000**, **100,000**, **200,000**, or **300,000 segments per file**, plus a custom limit or no splitting.
- Files are neatly numbered (`*_part01.tmx`, `*_part02.tmx`, ...), and each chunk is a standalone, valid TMX 1.4 XML document.

### 6. 🔄 Smooth Auto-Scrolling Terminal Interface
- The interactive wizard clears the console at each step, displaying a prominent breadcrumb banner of your active choices at line 0.
- Before each prompt, the console viewport is scrolled down to ensure the prompt is never hidden below the fold in Windows CMD/conhost or long terminal buffers.

### 7. 🏷️ 10-Category Domain Classification & Splitting
- Filter segments or automatically split extraction into **10 translation-market verticals**:
  - `legal` – Law, Judiciary, EU Legislation & Treaties
  - `finance` – Finance, Banking (CRR/ECB), Accounting (IFRS) & Tax
  - `trade` – International Trade, Customs, Procurement, Competition & Business
  - `it_telecom` – IT, Software, Cybersecurity (NIS2), AI & Telecommunications
  - `engineering` – Engineering, Automotive, Transport, Aviation & Machinery
  - `energy_env` – Energy, Climate, Emissions (EU ETS), Waste & Environment
  - `medical` – Medicine, Pharmaceuticals, Medical Devices & Veterinary
  - `chemicals` – Chemicals, REACH/CLP, Safety Data Sheets (SDS) & Biocides
  - `agri_food` – Agriculture, Food Safety (EFSA), Animal Feed & Fisheries
  - `general` – General, Administrative & Unclassified (fallback)
- Uses a zero-dependency two-stage multi-label classifier combining tiered collocation rules, TF-IDF/bigram similarity, and dominant-only document-title context priors (Step 5 in the wizard or `--categories` / `--split-by-category` in CLI).
- **Language Scope (`EN`/`PL` + DGT-TM `EN` Pivot):** Classification dictionaries are built for **English (`EN`) and Polish (`PL`)**. For pairs that include neither `EN` nor `PL` (such as `FR ➔ DE`), categorization works **only on official multilingual DGT-TM archives** (by inspecting the sibling `<tuv lang="EN">` inside each translation unit) and **will not work** on standalone bilingual `.tmx` files lacking `EN` or `PL`.
- **Note:** Domain filtering is automated (machine-based) and is not 100% accurate. If a segment matches two or more categories, it is placed in all matching files.

---

## 🛠️ Command-Line Interface (CLI)

```bash
# Interactive wizard mode
python3 tmx_extractor.py

# Single archive extraction with 50,000 segment chunking
python3 tmx_extractor.py -i Vol_2025.new_1.zip -s EN -t PL -o memory_en_pl.tmx --split 50000

# Split output into separate TMX files across the 10 domain categories
python3 tmx_extractor.py -i Vol_2025.new_1.zip -s EN -t PL -o memory_en_pl.tmx --split-by-category

# Extract only legal, finance, and medical segments into separate files
python3 tmx_extractor.py -i Vol_2025.new_1.zip -s EN -t PL -o memory_en_pl.tmx --categories legal,finance,medical --split-by-category

# Batch extraction across all ZIP files in a folder
python3 tmx_extractor.py -i ../TMX --batch -s EN -t PL --output-dir ./results

# Download entire DGT-TM repository from CLI
python3 tmx_extractor.py --download-repo --dest-dir ../TMX

# View MIT license
python3 tmx_extractor.py --license
```

---

## 📥 Importing into CAT Tools

* **SDL Trados Studio**: Open or create a Translation Memory (`.sdltm`) ➔ Click **Import** ➔ Select the generated `.tmx` files ➔ Finish.
* **memoQ**: Open **Resource Console** ➔ **Translation Memories** ➔ Create/select TM ➔ Click **Import from TMX/CSV** ➔ Select file ➔ OK.
* **OmegaT**: Place the generated `.tmx` files directly into your project's `/tm` folder.
* **Microsoft Excel**: Choose **TSV** format in Step 4 and open directly in Excel for tabular analysis.
