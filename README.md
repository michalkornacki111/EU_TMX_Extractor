# EU Translation Memory Extractor (DGT-TM / Euramis) 🇪🇺

> **Author:** Michał Kornacki (in Antigravity, 2026)  
> **License:** MIT License (2026) – full text in the [`LICENSE`](file:///home/michal/Data/TMX%20Extract/EU_TMX_Extractor/LICENSE) file or enter `L` in the application  
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
  * Text file: [**`LICENSE`**](file:///home/michal/Data/TMX%20Extract/EU_TMX_Extractor/LICENSE)
  * Visual interactive manual: [**`INSTRUCTIONS.html`**](file:///home/michal/Data/TMX%20Extract/EU_TMX_Extractor/INSTRUCTIONS.html)

---

## 🚀 Quick Start (No Terminal Experience Needed)

Ready-to-use 1-click launchers are included. Simply **double-click the file for your operating system**:

* **Windows**: Double-click [`run_windows.bat`](file:///home/michal/Data/TMX%20Extract/EU_TMX_Extractor/run_windows.bat) (or `uruchom_windows.bat`)
* **Mac (macOS)**: Double-click [`run_mac.command`](file:///home/michal/Data/TMX%20Extract/EU_TMX_Extractor/run_mac.command) (or `uruchom_mac.command`)
* **Linux**: Double-click [`run_linux.sh`](file:///home/michal/Data/TMX%20Extract/EU_TMX_Extractor/run_linux.sh) (or `uruchom.sh`)

> 📘 **Visual User Guide:** Open [**`INSTRUCTIONS.html`**](file:///home/michal/Data/TMX%20Extract/EU_TMX_Extractor/INSTRUCTIONS.html) in your browser for a visual step-by-step installation guide and CAT import instructions for SDL Trados Studio, memoQ, and OmegaT.

---

## ✨ Features in Version 2.4

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

### 4. 🗂️ Sequential Batch Extraction from All ZIPs in a Folder
If you have multiple ZIP files in your directory:
- Select option **`[W]`** in Step 1 of the wizard or run with `--batch`.
- The program processes all archives one by one, creating individual `.tmx` files and reports, followed by a master summary report (`batch_summary_report_*.txt`).
- Corrupted archives are safely skipped without halting the rest of the batch.

### 5. 🛡️ CAT Tool RAM Protection & File Chunking
Huge translation memories (>100,000 segments) can freeze or crash SDL Trados Studio and memoQ.
- The wizard allows splitting output into manageable chunks (default: **50,000 segments per file**).
- Files are neatly numbered: `*_part01.tmx`, `*_part02.tmx`, etc.
- Each chunk is a completely standalone, valid TMX 1.4 XML document.

### 6. 🔄 Smooth Auto-Scrolling Terminal Interface
- The interactive wizard clears the console at each step, displaying a prominent breadcrumb banner of your active choices at line 0.
- Before each prompt, the console viewport is scrolled down to ensure the prompt is never hidden below the fold in Windows CMD/conhost or long terminal buffers.

---

## 🛠️ Command-Line Interface (CLI)

```bash
# Interactive wizard mode
python3 tmx_extractor.py

# Single archive extraction with 50,000 segment chunking
python3 tmx_extractor.py -i Vol_2009_4.zip -s EN -t PL -o memory_en_pl.tmx --split 50000

# Batch extraction across all ZIP files in a folder
python3 tmx_extractor.py -i ./zips --batch -s EN -t PL --output-dir ./results

# Download entire DGT-TM repository from CLI
python3 tmx_extractor.py --download-repo --dest-dir ./dgt_zips

# View MIT license
python3 tmx_extractor.py --license
```

---

## 📥 Importing into CAT Tools

* **SDL Trados Studio**: Open or create a Translation Memory (`.sdltm`) ➔ Click **Import** ➔ Select the generated `.tmx` files ➔ Finish.
* **memoQ**: Open **Resource Console** ➔ **Translation Memories** ➔ Create/select TM ➔ Click **Import from TMX/CSV** ➔ Select file ➔ OK.
* **OmegaT**: Place the generated `.tmx` files directly into your project's `/tm` folder.
* **Microsoft Excel**: Choose **TSV** format in Step 4 and open directly in Excel for tabular analysis.
