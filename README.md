# EU Translation Memory Extractor (DGT-TM / Euramis) 🇪🇺

> **Author:** Michał Kornacki (in Antigravity, 2026)  
> **Licence:** MIT License (2026) – full text in the [`LICENSE`](file:///home/michal/Data/TMX%20Extract/LICENSE) file or by typing `L` in the program  
> **Base tools:** Built upon the following tools:
> - `TMXtract.jar` – the official tool of the Directorate-General for Translation (DGT) / the Joint Research Centre (JRC) of the **European Commission** (European Commission, 2013)
> - `tmxtract` – a project by **Rodrigo Nepomuceno** (2019, MIT, https://github.com/Nepomuceno/tmxtract)

A modern, lightning-fast and beginner-friendly tool written in **Python** that lets you easily extract ready-made translation memories (TMX) and sentence bases in any language pair from the multilingual corpora of European Union legal acts.

---

## 📜 MIT Licence

The program is 100% free and open-source under the **MIT License**:
* You can view the full licence text from within the program itself:
  * In the wizard: by choosing the **`[L]`** option
  * From the command line: by typing `python3 tmx_extractor.py --license`
  * In a text file: [**`LICENSE`**](file:///home/michal/Data/TMX%20Extract/LICENSE)
  * In the visual documentation: [**`INSTRUKCJA.html`**](file:///home/michal/Data/TMX%20Extract/INSTRUKCJA.html)

---

## 🚀 Quick start (for users with no terminal experience)

The program ships with ready-made launcher shortcuts – all you need to do is **double-click the file with your mouse**:

* **Windows**: Double-click [`uruchom_windows.bat`](file:///home/michal/Data/TMX%20Extract/uruchom_windows.bat)
* **Mac (macOS)**: Double-click [`uruchom_mac.command`](file:///home/michal/Data/TMX%20Extract/uruchom_mac.command)
* **Linux**: Double-click [`uruchom.sh`](file:///home/michal/Data/TMX%20Extract/uruchom.sh) *(or type `python3 tmx_extractor.py`)*

> 📘 **Full visual documentation:** Open the [**`INSTRUKCJA.html`**](file:///home/michal/Data/TMX%20Extract/INSTRUKCJA.html) file in your browser – it contains a step-by-step guide to installing Python as well as a walkthrough of importing into Trados, memoQ and Excel.

---

## ✨ New features in version 2.1

### 1. 📄 Automatic export report (`*_raport.txt`)
After every export, the program automatically creates a readable text file summarising the entire operation. It contains:
- The exact date and time of the export
- The selected language pair (language names and ISO codes)
- The source resources (the path, the number of files processed and their size in MB)
- The number of segments searched in the EU corpus
- The number of unique sentence pairs extracted
- The number and percentage of duplicates rejected
- A list of the generated files, with their size and segment counts
- 3–4 sample translated segments for quick verification.
*(This metadata is also saved automatically in the `<header><note>` header of the TMX file.)*

### 2. 🛡️ RAM protection / file splitting for CAT tools
Importing very large TMX files (>100,000 sentences) can freeze CAT tools (SDL Trados Studio, memoQ, OmegaT) or trigger an `OutOfMemory` error.
- **Recommendation:** Split every **50,000 segments** (this ensures a stable, fast import even on machines with 4–8 GB of RAM) or **100,000 segments**.
- **Name sequencing:** If splitting is active, the program automatically gives the files readable sequential names:
  - `dgt_en_pl_part01.tmx`
  - `dgt_en_pl_part02.tmx`
  - `dgt_en_pl_part03.tmx`
- If the result fits in a single file, the clean base name `dgt_en_pl.tmx` is kept.

---

## 🌐 Official source of EU resources (data.europa.eu)

The current European Union translation memory datasets are officially published at:  
👉 **[data.europa.eu – DGT Translation Memory Dataset](https://data.europa.eu/data/datasets/dgt-translation-memory?locale=en)**

On that page, in the **Distributions** section, every annual edition (from **2004** to the latest one, **2025**) provides a direct **Download URL** link to the ZIP package (e.g. `Vol_2025.new_1.zip`).

---

## 📍 WHERE TO SAVE THE DOWNLOADED ZIP / TMX FILES? (VERY IMPORTANT)

1. **Save the ZIP file directly in the program folder:**  
   Save or move the downloaded `.zip` file (e.g. `Vol_2025.new_1.zip`) directly into the program folder:  
   📂 `EU TMX Extractor` *(the folder where `tmx_extractor.py`, `uruchom_windows.bat` and `uruchom_mac.command` are located)*.  
   When the program starts, it will detect the file automatically and offer it as the first item in its menu.

2. **⛔ DO NOT UNZIP THE ZIP FILES UNDER ANY CIRCUMSTANCES!**  
   The program processes the compressed ZIP archives directly in working memory, without unpacking them to disk. Unpacking would take up a dozen or more gigabytes and is completely unnecessary.

3. **What if the file ended up in your Downloads folder?**  
   - You can simply drag it into the program folder `EU TMX Extractor`.
   - Even if you do not, the program **also scans your system's Downloads folder on its own** and will list any DGT archives it finds for you to choose from!

4. **Downloading directly from within the program:**  
   If you select the option *"Pobierz oficjalny pakiet DGT-TM z internetu" [Download the official DGT-TM package from the internet]* in the assistant menu, the program will download the file itself and save it in the right folder.

5. **Where do the generated memory files (.tmx, .tsv, reports) end up?**  
   All output files (`dgt_en_pl_part01.tmx`, the `.tsv` sheets and the `*_raport.txt` report) are saved **in the same program folder** (`EU TMX Extractor`).

---

## ⚡ Command-line usage examples (CLI for advanced users)

```bash
# Podstawowa ekstrakcja angielski ➔ polski z podziałem co 50 000 segmentów (dla CAT)
python3 tmx_extractor.py -i Vol_2009_4 -s EN -t PL -o dgt_en_pl.tmx --split 50000

# Ekstrakcja bezpośrednio z archiwum ZIP (bez rozpakowywania na dysk!)
python3 tmx_extractor.py -i Vol_2018_1.zip -s DE -t PL -o niemiecki_polski.tmx

# Zapis do Excela (TSV), TMX oraz JSONL jednocześnie
python3 tmx_extractor.py -i Vol_2009_4 -s EN -t PL -o wynik --format all

# Pobranie oficjalnego pakietu DGT-TM z serwerów Komisji Europejskiej
python3 tmx_extractor.py --download Vol_2018_1 -s EN -t PL -o dgt_2018_en_pl.tmx
```

---

*Translator's note: the menu option "Pobierz oficjalny pakiet DGT-TM z internetu" in the "WHERE TO SAVE THE DOWNLOADED ZIP / TMX FILES?" section is a literal on-screen menu string of the Polish-language program, not free prose; it has therefore been kept in Polish with an English gloss in square brackets.*
*Translator's note (flagged for the owner): the comment lines inside the bash block were preserved verbatim in Polish because code blocks had to remain byte-identical; they may be translated in a later revision if the owner wishes.*
