#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
End-to-End (E2E) Test Suite for EU TMX Extractor
================================================
Testuje:
1. Kompatybilność konsoli (Windows VT processing, fallback gdy brak ANSI, bezpieczne kodowanie).
2. Obsługę skryptów uruchomieniowych (Windows .bat, macOS .command, Linux .sh).
3. Poprawność generowania i parsowania standardu TMX 1.4 XML.
4. Ochronę pamięci RAM dla CAT (dzielenie plików na części part01, part02... z poprawną strukturą XML).
5. Ekstrakcję z pojedynczego archiwum ZIP.
6. Nową funkcję: Ekstrakcję seryjną ze WSZYSTKICH plików ZIP w folderze jeden po drugim (batch).
7. Odporność na błędy (uszkodzone archiwa w serii).
8. Wywołania przez interfejs CLI oraz symulację kreatora interaktywnego.
"""

import os
import sys
import shutil
import tempfile
import unittest
import subprocess
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

# Dodaj katalog główny projektu do sys.path
PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_DIR not in sys.path:
    sys.path.insert(0, PROJECT_DIR)

import tmx_extractor


def create_sample_tmx_content(pairs=None):
    """Generuje poprawną składniowo treść pliku TMX z przykładowymi danymi wielojęzycznymi."""
    if pairs is None:
        pairs = [
            ("The Commission adopts the proposal.", "Komisja przyjmuje wniosek.", "Die Kommission nimmt den Vorschlag an."),
            ("Protection of the European environment is vital.", "Ochrona środowiska europejskiego jest kluczowa.", "Der Schutz der europäischen Umwelt ist entscheidend."),
            ("Article 1 & Article 2 <definitions>.", "Artykuł 1 i Artykuł 2 <definicje>.", "Artikel 1 und Artikel 2 <Definitionen>."),
            ("Prices starting at €100 / 100 zł.", "Ceny rozpoczynające się od 100 EUR / 100 zł.", "Preise ab 100 EUR."),
            ("Final provisions and signatures.", "Postanowienia końcowe i podpisy.", "Schlussbestimmungen und Unterschriften.")
        ]

    tu_blocks = []
    for idx, (en, pl, de) in enumerate(pairs, 1):
        tu = f"""    <tu tuid="tu_{idx}">
      <prop type="Txt::DocId">CELEX_32025R000{idx}</prop>
      <tuv xml:lang="EN-GB"><seg>{en}</seg></tuv>
      <tuv xml:lang="PL-01"><seg>{pl}</seg></tuv>
      <tuv xml:lang="DE-01"><seg>{de}</seg></tuv>
    </tu>"""
        tu_blocks.append(tu)

    return f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE tmx SYSTEM "tmx14.dtd">
<tmx version="1.4">
  <header creationtool="DGT-TM" creationtoolversion="1.0" datatype="PlainText" segtype="sentence" adminlang="EN" srclang="EN" o-tmf="unknown"/>
  <body>
{chr(10).join(tu_blocks)}
  </body>
</tmx>"""


def create_mock_zip(zip_path: str, tmx_filename: str = "sample_dgt.tmx", pairs=None):
    """Tworzy testowe archiwum ZIP zawierające plik .tmx."""
    tmx_content = create_sample_tmx_content(pairs)
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(tmx_filename, tmx_content.encode("utf-8"))


class TestTerminalAndCrossPlatformCompatibility(unittest.TestCase):
    """Testy interfejsu konsolowego, czystości wyświetlania i kompatybilności Windows/macOS/Linux."""

    def test_strip_ansi_cleans_all_escapes(self):
        colored_str = "\033[36m[INFO]\033[0m \033[1mSuccessfully processed\033[0m"
        clean = tmx_extractor.UI.strip_ansi(colored_str)
        self.assertEqual(clean, "[INFO] Successfully processed")
        self.assertNotIn("\033", clean)
        self.assertNotIn("[36m", clean)
        self.assertNotIn("[0m", clean)

    def test_ui_colors_disabled_fallback_no_garbage(self):
        """Weryfikuje, że gdy kolory są wyłączone (np. brak VT na Windows 10), żadne kody ANSI nie wyciekają."""
        original_has_color = tmx_extractor.UI._has_color
        try:
            tmx_extractor.UI._has_color = False
            formatted = tmx_extractor.UI.c("Tekst testowy", tmx_extractor.UI.CYAN + tmx_extractor.UI.BOLD)
            self.assertEqual(formatted, "Tekst testowy")
            self.assertNotIn("\033", formatted)
            self.assertNotIn("?[", formatted)
        finally:
            tmx_extractor.UI._has_color = original_has_color

    def test_header_and_section_safe_ascii_borders(self):
        """Testuje, czy nagłówki używają bezpiecznych znaków '=' i '-' niegenerujących znaków zapytania."""
        import io
        buf = io.StringIO()
        old_stdout = sys.stdout
        try:
            sys.stdout = buf
            tmx_extractor.UI.header("TEST NAGLOWKA BEZPIECZNEGO")
            tmx_extractor.UI.section("SEKCJA KROK 1")
            output = buf.getvalue()
            # Upewnij się, że nie zawiera łamiących się znaków ramkowych
            self.assertNotIn("╔", output)
            self.assertNotIn("╗", output)
            self.assertNotIn("║", output)
            self.assertNotIn("╚", output)
            self.assertIn("=", output)
            self.assertIn("--- SEKCJA KROK 1 ---", output)
        finally:
            sys.stdout = old_stdout

    def test_launchers_exist_and_syntax(self):
        """Weryfikuje istnienie i składnię skryptów uruchomieniowych dla Windows, Mac i Linux."""
        bat_file = os.path.join(PROJECT_DIR, "uruchom_windows.bat")
        mac_file = os.path.join(PROJECT_DIR, "uruchom_mac.command")
        sh_file = os.path.join(PROJECT_DIR, "uruchom.sh")
        run_bat = os.path.join(PROJECT_DIR, "run_windows.bat")
        run_mac = os.path.join(PROJECT_DIR, "run_mac.command")
        run_sh = os.path.join(PROJECT_DIR, "run_linux.sh")

        self.assertTrue(os.path.isfile(bat_file), "Brak pliku uruchom_windows.bat")
        self.assertTrue(os.path.isfile(mac_file), "Brak pliku uruchom_mac.command")
        self.assertTrue(os.path.isfile(sh_file), "Brak pliku uruchom.sh")
        self.assertTrue(os.path.isfile(run_bat), "Brak pliku run_windows.bat")
        self.assertTrue(os.path.isfile(run_mac), "Brak pliku run_mac.command")
        self.assertTrue(os.path.isfile(run_sh), "Brak pliku run_linux.sh")

        # Windows .bat powinien wymuszać UTF-8
        for bf in (bat_file, run_bat):
            with open(bf, "r", encoding="utf-8") as f:
                bat_content = f.read()
                self.assertIn("chcp 65001", bat_content)
                self.assertIn("PYTHONUTF8=1", bat_content)

        # macOS i Linux sprawdzamy bash -n (walidacja składni)
        for mf in (mac_file, run_mac):
            res_mac = subprocess.run(["bash", "-n", mf], capture_output=True, text=True)
            self.assertEqual(res_mac.returncode, 0, f"Błąd składni w {os.path.basename(mf)}: {res_mac.stderr}")

        for sf in (sh_file, run_sh):
            res_sh = subprocess.run(["bash", "-n", sf], capture_output=True, text=True)
            self.assertEqual(res_sh.returncode, 0, f"Błąd składni w {os.path.basename(sf)}: {res_sh.stderr}")


    def test_language_resolution(self):
        """Testuje rozpoznawanie kodów i nazw języków UE."""
        self.assertEqual(tmx_extractor.resolve_language_code("PL"), "PL")
        self.assertEqual(tmx_extractor.resolve_language_code("pl"), "PL")
        self.assertEqual(tmx_extractor.resolve_language_code("polski"), "PL")
        self.assertEqual(tmx_extractor.resolve_language_code("Polish"), "PL")
        self.assertEqual(tmx_extractor.resolve_language_code("EN"), "EN")
        self.assertEqual(tmx_extractor.resolve_language_code("angielski"), "EN")
        self.assertEqual(tmx_extractor.resolve_language_code("DE"), "DE")
        self.assertEqual(tmx_extractor.resolve_language_code("niemiecki"), "DE")
        self.assertEqual(tmx_extractor.resolve_language_code("FR"), "FR")
        self.assertEqual(tmx_extractor.resolve_language_code("francuski"), "FR")
        self.assertEqual(tmx_extractor.resolve_language_code("CS"), "CS")
        self.assertEqual(tmx_extractor.resolve_language_code("czeski"), "CS")


class TestExtractionAndCatProtectionE2E(unittest.TestCase):
    """Testy procesu ekstrakcji, dzielenia dla RAM/CAT i walidacji XML."""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp(prefix="e2e_tmx_test_")

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_single_zip_extraction_valid_tmx(self):
        """Weryfikuje poprawność ekstrakcji z pojedynczego archiwum ZIP do TMX 1.4 XML."""
        zip_path = os.path.join(self.test_dir, "test_vol_1.zip")
        create_mock_zip(zip_path)

        out_tmx = os.path.join(self.test_dir, "wynik_en_pl.tmx")
        stats = tmx_extractor.run_extraction(
            input_path=zip_path,
            source_lang="EN",
            target_lang="PL",
            output_path=out_tmx,
            output_format="tmx",
            quiet=True
        )

        self.assertEqual(stats["extracted_pairs"], 5)
        self.assertTrue(os.path.isfile(out_tmx))

        # Walidacja składni XML TMX
        tree = ET.parse(out_tmx)
        root = tree.getroot()
        self.assertEqual(root.tag, "tmx")
        self.assertEqual(root.attrib.get("version"), "1.4")

        body = root.find("body")
        self.assertIsNotNone(body)
        tus = body.findall("tu")
        self.assertEqual(len(tus), 5)

        # Sprawdź pierwszy segment
        first_tu = tus[0]
        tuvs = first_tu.findall("tuv")
        self.assertEqual(len(tuvs), 2)
        lang_set = {t.attrib.get("{http://www.w3.org/XML/1998/namespace}lang", t.attrib.get("xml:lang")) for t in tuvs}
        self.assertTrue("en" in lang_set or "EN" in lang_set)
        self.assertTrue("pl" in lang_set or "PL" in lang_set)

        # Sprawdź istnienie raportu
        report_path = os.path.join(self.test_dir, "wynik_en_pl_raport.txt")
        self.assertTrue(os.path.isfile(report_path))
        with open(report_path, "r", encoding="utf-8") as rf:
            rep_text = rf.read()
            self.assertIn("5", rep_text)
            self.assertIn("EN", rep_text)
            self.assertIn("PL", rep_text)

    def test_cat_ram_protection_chunking(self):
        """Weryfikuje dzielenie na mniejsze pliki (_part01.tmx, _part02.tmx...) dla stabilności CAT."""
        pairs = [
            (f"Sentence {i} in English.", f"Zdanie {i} po polsku.", f"Satz {i} auf Deutsch.")
            for i in range(1, 11)
        ]
        zip_path = os.path.join(self.test_dir, "ten_pairs.zip")
        create_mock_zip(zip_path, pairs=pairs)

        out_tmx = os.path.join(self.test_dir, "split_cat.tmx")
        # Dzielenie co 4 segmenty: 10 par powinno dać 3 pliki: part01 (4), part02 (4), part03 (2)
        stats = tmx_extractor.run_extraction(
            input_path=zip_path,
            source_lang="EN",
            target_lang="PL",
            output_path=out_tmx,
            split_size=4,
            quiet=True
        )

        parts = stats["output_parts"]
        self.assertEqual(len(parts), 3)

        part_files = [p.file_path for p in parts]
        self.assertTrue(part_files[0].endswith("_part01.tmx"))
        self.assertTrue(part_files[1].endswith("_part02.tmx"))
        self.assertTrue(part_files[2].endswith("_part03.tmx"))

        # Każdy plik partXX.tmx MUSI być w pełni poprawnym dokumentem XML
        total_counted = 0
        for p_file in part_files:
            self.assertTrue(os.path.isfile(p_file))
            tree = ET.parse(p_file)
            body = tree.getroot().find("body")
            tus = body.findall("tu")
            total_counted += len(tus)

        self.assertEqual(total_counted, 10)


class TestBatchProcessingAllZipsE2E(unittest.TestCase):
    """Testy nowej funkcjonalności: Ekstrakcja TMX ze wszystkich plików ZIP w folderze jeden po drugim."""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp(prefix="e2e_batch_test_")
        self.zips_dir = os.path.join(self.test_dir, "zips_input")
        self.out_dir = os.path.join(self.test_dir, "batch_output")
        os.makedirs(self.zips_dir, exist_ok=True)
        os.makedirs(self.out_dir, exist_ok=True)

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_batch_extraction_all_zips_one_by_one(self):
        """Testuje przetworzenie 3 różnych archiwów ZIP jeden po drugim."""
        zip1 = os.path.join(self.zips_dir, "Vol_2024_1.zip")
        zip2 = os.path.join(self.zips_dir, "Vol_2024_2.zip")
        zip3 = os.path.join(self.zips_dir, "Vol_2025_1.zip")

        create_mock_zip(zip1, tmx_filename="vol_2024_1.tmx", pairs=[
            ("Hello world 1.", "Witaj świecie 1.", "Hallo Welt 1."),
            ("European Parliament meeting.", "Spotkanie Parlamentu Europejskiego.", "Treffen des Europäischen Parlaments.")
        ])
        create_mock_zip(zip2, tmx_filename="vol_2024_2.tmx", pairs=[
            ("Green energy transition.", "Transformacja zielonej energii.", "Grüne Energiewende."),
            ("Economic stability plan.", "Plan stabilności gospodarczej.", "Wirtschaftsstabilitätsplan.")
        ])
        create_mock_zip(zip3, tmx_filename="vol_2025_1.tmx", pairs=[
            ("Artificial Intelligence Act.", "Akt o sztucznej inteligencji.", "Gesetz über künstliche Intelligenz."),
            ("Data protection directive.", "Dyrektywa o ochronie danych.", "Datenschutzrichtlinie."),
            ("Digital services framework.", "Ramy usług cyfrowych.", "Rahmen für digitale Dienste.")
        ])

        zip_list = [zip1, zip2, zip3]
        batch_stats = tmx_extractor.run_batch_extraction(
            zip_paths=zip_list,
            source_lang="EN",
            target_lang="PL",
            output_dir=self.out_dir,
            output_format="tmx",
            quiet=True
        )

        self.assertEqual(batch_stats["total_zips"], 3)
        self.assertEqual(batch_stats["successful_zips"], 3)
        self.assertEqual(batch_stats["failed_zips"], 0)
        self.assertEqual(batch_stats["total_pairs"], 7)  # 2 + 2 + 3

        # Sprawdź, czy każdy plik ZIP ma swój dedykowany TMX i raport
        out1 = os.path.join(self.out_dir, "Vol_2024_1_en_pl.tmx")
        out2 = os.path.join(self.out_dir, "Vol_2024_2_en_pl.tmx")
        out3 = os.path.join(self.out_dir, "Vol_2025_1_en_pl.tmx")

        self.assertTrue(os.path.isfile(out1), "Brak pliku Vol_2024_1_en_pl.tmx")
        self.assertTrue(os.path.isfile(out2), "Brak pliku Vol_2024_2_en_pl.tmx")
        self.assertTrue(os.path.isfile(out3), "Brak pliku Vol_2025_1_en_pl.tmx")

        # Sprawdź poprawność XML każdego z wygenerowanych plików
        for f in [out1, out2, out3]:
            tree = ET.parse(f)
            self.assertEqual(tree.getroot().tag, "tmx")

        # Sprawdź raporty indywidualne (angielski _report.txt oraz kompatybilny _raport.txt)
        self.assertTrue(os.path.isfile(os.path.join(self.out_dir, "Vol_2024_1_en_pl_report.txt")))
        self.assertTrue(os.path.isfile(os.path.join(self.out_dir, "Vol_2024_1_en_pl_raport.txt")))
        self.assertTrue(os.path.isfile(os.path.join(self.out_dir, "Vol_2024_2_en_pl_report.txt")))
        self.assertTrue(os.path.isfile(os.path.join(self.out_dir, "Vol_2025_1_en_pl_report.txt")))

        # Sprawdź master raport zbiorczy (batch_summary_report_ oraz raport_zbiorczy_batch_)
        master_rep_en = os.path.join(self.out_dir, "batch_summary_report_en_pl.txt")
        master_rep_pl = os.path.join(self.out_dir, "raport_zbiorczy_batch_en_pl.txt")
        self.assertTrue(os.path.isfile(master_rep_en), "Brak raportu zbiorczego batch_summary_report_en_pl.txt")
        self.assertTrue(os.path.isfile(master_rep_pl), "Brak raportu zbiorczego raport_zbiorczy_batch_en_pl.txt")
        with open(master_rep_en, "r", encoding="utf-8") as mf:
            m_text = mf.read()
            self.assertIn("BATCH EXTRACTION MASTER REPORT", m_text)
            self.assertIn("Vol_2024_1.zip", m_text)
            self.assertIn("Vol_2024_2.zip", m_text)
            self.assertIn("Vol_2025_1.zip", m_text)
            self.assertIn("7 sentence pairs", m_text)

    def test_batch_resilience_to_corrupted_zip(self):
        """Testuje odporność: jeśli jedno archiwum jest uszkodzone, reszta plików jest przetwarzana bez wywrotki."""
        valid_zip = os.path.join(self.zips_dir, "Valid_Vol.zip")
        corrupted_zip = os.path.join(self.zips_dir, "Corrupted_Vol.zip")

        create_mock_zip(valid_zip, pairs=[("Valid sentence.", "Prawidłowe zdanie.", "Gültiger Satz.")])
        with open(corrupted_zip, "w") as f:
            f.write("To nie jest prawidłowy plik zip!")

        batch_stats = tmx_extractor.run_batch_extraction(
            zip_paths=[valid_zip, corrupted_zip],
            source_lang="EN",
            target_lang="PL",
            output_dir=self.out_dir,
            output_format="tmx",
            quiet=True
        )

        self.assertEqual(batch_stats["total_zips"], 2)
        self.assertEqual(batch_stats["successful_zips"], 1)
        self.assertEqual(batch_stats["failed_zips"], 1)
        self.assertEqual(batch_stats["total_pairs"], 1)
        self.assertTrue(os.path.isfile(os.path.join(self.out_dir, "Valid_Vol_en_pl.tmx")))


class TestCliSubprocessE2E(unittest.TestCase):
    """Testy wywołań CLI i kreatora jako odrębnego procesu systemowego."""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp(prefix="e2e_cli_test_")

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_cli_help_flag(self):
        cmd = [sys.executable, os.path.join(PROJECT_DIR, "tmx_extractor.py"), "--help"]
        res = subprocess.run(cmd, capture_output=True, text=True)
        self.assertEqual(res.returncode, 0)
        self.assertIn("EU TMX Extractor", res.stdout)
        self.assertIn("--batch", res.stdout)

    def test_cli_license_flag(self):
        cmd = [sys.executable, os.path.join(PROJECT_DIR, "tmx_extractor.py"), "--license"]
        res = subprocess.run(cmd, capture_output=True, text=True)
        self.assertEqual(res.returncode, 0)
        self.assertIn("MIT License", res.stdout)
        self.assertIn("Michał Kornacki", res.stdout)

    def test_cli_batch_flag_execution(self):
        """Testuje wywołanie python3 tmx_extractor.py -i <katalog> --batch -s EN -t PL --output-dir <katalog>"""
        zips_dir = os.path.join(self.test_dir, "zips")
        out_dir = os.path.join(self.test_dir, "out")
        os.makedirs(zips_dir, exist_ok=True)

        zip1 = os.path.join(zips_dir, "Vol_1.zip")
        zip2 = os.path.join(zips_dir, "Vol_2.zip")
        create_mock_zip(zip1)
        create_mock_zip(zip2)

        cmd = [
            sys.executable,
            os.path.join(PROJECT_DIR, "tmx_extractor.py"),
            "-i", zips_dir,
            "--batch",
            "-s", "EN",
            "-t", "PL",
            "--output-dir", out_dir,
            "-q"
        ]
        res = subprocess.run(cmd, capture_output=True, text=True)
        self.assertEqual(res.returncode, 0, f"Błąd CLI: {res.stderr}")
        self.assertTrue(os.path.isfile(os.path.join(out_dir, "Vol_1_en_pl.tmx")))
        self.assertTrue(os.path.isfile(os.path.join(out_dir, "Vol_2_en_pl.tmx")))

    def test_interactive_wizard_batch_simulation(self):
        """Symuluje interaktywne przejście przez kreatora z wyborem trybu seryjnego [W]."""
        sim_dir = os.path.join(self.test_dir, "sim_wizard")
        os.makedirs(sim_dir, exist_ok=True)
        # Utwórz 2 pliki ZIP w folderze symulacji
        create_mock_zip(os.path.join(sim_dir, "Vol_A.zip"))
        create_mock_zip(os.path.join(sim_dir, "Vol_B.zip"))

        # Kopiujemy tmx_extractor.py do folderu symulacji, aby find_local_data_sources znalazło te pliki
        script_copy = os.path.join(sim_dir, "tmx_extractor.py")
        shutil.copy(os.path.join(PROJECT_DIR, "tmx_extractor.py"), script_copy)

        # Odpowiedzi dla kreatora:
        # KROK 1: 'W' (wybór trybu seryjnego z wykrytych ZIPów)
        # KROK 2: '1' (EN -> PL)
        # KROK 3: '4' (bez podziału)
        # KROK 4: '1' (TMX), Enter (domyślny katalog zapisu)
        # KROK 5: 't' (dedup), 't' (filter identical), Enter (bez limitu), '1' (no domain split)
        # Potwierdzenie: 't'
        # Zakończenie: Enter
        wizard_inputs = "W\n1\n4\n1\n\nt\nt\n\n1\nt\n\n"

        cmd = [sys.executable, script_copy]
        res = subprocess.run(cmd, input=wizard_inputs, cwd=sim_dir, capture_output=True, text=True)
        self.assertEqual(res.returncode, 0, f"Błąd w symulacji kreatora: {res.stderr}\nSTDOUT: {res.stdout}")
        self.assertTrue(os.path.isfile(os.path.join(sim_dir, "Vol_A_en_pl.tmx")))
        self.assertTrue(os.path.isfile(os.path.join(sim_dir, "Vol_B_en_pl.tmx")))
        self.assertTrue(os.path.isfile(os.path.join(sim_dir, "batch_summary_report_en_pl.txt")))
        self.assertTrue(os.path.isfile(os.path.join(sim_dir, "raport_zbiorczy_batch_en_pl.txt")))


class TestRepositoryBatchDownloadAndDiskSummaryE2E(unittest.TestCase):
    """
    Testy nowej funkcjonalności:
    1. Obliczanie i podsumowanie wymaganego miejsca na dysku (przed rozpoczęciem pobierania).
    2. Sekwencyjne pobieranie całego repozytorium plik po pliku.
    3. Końcowe pytanie o przejście do ekstrakcji TMX lub zakończenie pracy.
    """

    def setUp(self):
        self.test_dir = tempfile.mkdtemp(prefix="e2e_repo_dl_test_")

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_disk_space_info_and_estimation(self):
        """Weryfikuje odczyt parametrów dysku i szacowanie rozmiarów wolumenów."""
        disk_info = tmx_extractor.get_disk_space_info(self.test_dir)
        self.assertGreater(disk_info["free_bytes"], 0)
        self.assertGreater(disk_info["total_bytes"], 0)
        self.assertGreater(disk_info["free_gb"], 0.0)

        # Test szacowania rozmiaru roczników
        self.assertGreaterEqual(tmx_extractor.estimate_dgt_volume_size("Vol_2025.new_1.zip"), 250 * 1024 * 1024)
        self.assertGreaterEqual(tmx_extractor.estimate_dgt_volume_size("Vol_2024.new_1.zip"), 250 * 1024 * 1024)
        self.assertLessEqual(tmx_extractor.estimate_dgt_volume_size("Vol_2006_1.zip"), 30 * 1024 * 1024)

        # Przygotuj istniejący plik i brakujący plik
        existing_zip = os.path.join(self.test_dir, "Vol_2006_1.zip")
        create_mock_zip(existing_zip)

        mock_volumes = [
            ("Vol_2006_1.zip", "https://mock/Vol_2006_1.zip", "Część 1"),
            ("Vol_2025.new_1.zip", "https://mock/Vol_2025.new_1.zip", "Część 2")
        ]

        summary = tmx_extractor.get_repository_disk_summary(self.test_dir, mock_volumes)
        self.assertEqual(summary["total_volumes"], 2)
        self.assertEqual(summary["existing_count"], 1)
        self.assertEqual(summary["to_download_count"], 1)
        self.assertGreater(summary["to_download_bytes_est"], 0)
        self.assertTrue(summary["has_enough_space"])

    def test_batch_download_simulation_with_exit_choice(self):
        """Testuje pobranie repozytorium plik po pliku z wyborem [2] (Zakończ pracę)."""
        src_mock_zip = os.path.join(self.test_dir, "source_mock.zip")
        create_mock_zip(src_mock_zip)
        mock_file_url = f"file://{os.path.abspath(src_mock_zip)}"

        dest_dir = os.path.join(self.test_dir, "downloaded_repo")
        os.makedirs(dest_dir, exist_ok=True)

        mock_volumes = [
            ("Vol_Test_1.zip", mock_file_url, "Test Volume 1"),
            ("Vol_Test_2.zip", mock_file_url, "Test Volume 2")
        ]

        # Symulacja wejścia:
        # Pytanie 1 (potwierdzenie pobierania): 't'
        # Pytanie 2 (wybór po pobraniu): '2' (zakończ pracę)
        import io
        from unittest.mock import patch

        with patch("sys.stdin", io.StringIO("t\n2\n")):
            res = tmx_extractor.download_dgt_repository_batch(
                dest_folder=dest_dir,
                volumes=mock_volumes,
                prompt_confirmation=True,
                interactive_post_action=True
            )

        self.assertEqual(res, ("exit", None))
        self.assertTrue(os.path.isfile(os.path.join(dest_dir, "Vol_Test_1.zip")))
        self.assertTrue(os.path.isfile(os.path.join(dest_dir, "Vol_Test_2.zip")))

    def test_batch_download_simulation_with_batch_extraction_choice(self):
        """Testuje pobranie repozytorium z wyborem [1] (Przejdź do ekstrakcji TMX)."""
        src_mock_zip = os.path.join(self.test_dir, "source_mock.zip")
        create_mock_zip(src_mock_zip)
        mock_file_url = f"file://{os.path.abspath(src_mock_zip)}"

        dest_dir = os.path.join(self.test_dir, "downloaded_repo_extract")
        os.makedirs(dest_dir, exist_ok=True)

        mock_volumes = [
            ("Vol_Extract_1.zip", mock_file_url, "Tom do ekstrakcji 1"),
            ("Vol_Extract_2.zip", mock_file_url, "Tom do ekstrakcji 2")
        ]

        import io
        from unittest.mock import patch

        # Wybór 't' (potwierdzenie pobierania) oraz '1' (przejdź do ekstrakcji)
        with patch("sys.stdin", io.StringIO("t\n1\n")):
            res = tmx_extractor.download_dgt_repository_batch(
                dest_folder=dest_dir,
                volumes=mock_volumes,
                prompt_confirmation=True,
                interactive_post_action=True
            )

        self.assertIsNotNone(res)
        mode, zips = res
        self.assertEqual(mode, "batch")
        self.assertEqual(len(zips), 2)
        for z in zips:
            self.assertTrue(os.path.isfile(z))

        # Weryfikacja że zwrócone pliki można natychmiast przekazać do run_batch_extraction
        out_tmx_dir = os.path.join(dest_dir, "tmx_out")
        batch_stats = tmx_extractor.run_batch_extraction(
            zip_paths=zips,
            source_lang="EN",
            target_lang="PL",
            output_dir=out_tmx_dir,
            output_format="tmx",
            quiet=True
        )
        self.assertEqual(batch_stats["successful_zips"], 2)
        self.assertTrue(os.path.isfile(os.path.join(out_tmx_dir, "Vol_Extract_1_en_pl.tmx")))
        self.assertTrue(os.path.isfile(os.path.join(out_tmx_dir, "Vol_Extract_2_en_pl.tmx")))
        self.assertTrue(os.path.isfile(batch_stats["master_report_path"]))


class TestDomainClassificationAndSplittingE2E(unittest.TestCase):
    """Tests multi-label domain classification, filtering, and splitting across 6 categories."""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp(prefix="e2e_domain_test_")
        self.sample_pairs = [
            (
                "Regulation (EC) No 1234/2025 of the European Parliament pursuant to Article 4 on infringement proceedings.",
                "Rozporządzenie (WE) nr 1234/2025 Parlamentu Europejskiego zgodnie z artykułem 4 w sprawie naruszenia.",
                "Verordnung (EG) Nr. 1234/2025."
            ),
            (
                "The undertaking received State aid and a customs tariff exemption affecting market competition and VAT.",
                "Przedsiębiorstwo otrzymało pomoc państwa i zwolnienie z cła wpływające na konkurencję na rynku i VAT.",
                "Das Unternehmen erhielt eine staatliche Beihilfe."
            ),
            (
                "Reducing greenhouse gas CO2 emissions and preventing biodiversity loss and hazardous waste pollution.",
                "Redukcja emisji dwutlenku węgla oraz ochrona bioróżnorodności i zapobieganie zanieczyszczeniu odpadami niebezpiecznymi.",
                "Verringerung der Treibhausgasemissionen."
            ),
            (
                "Approval of compression-ignition engines, adaptive front-lighting systems, and cybersecurity software encryption.",
                "Homologacja silników o zapłonie samoczynnym, reflektorów oraz oprogramowania do szyfrowania w cyberbezpieczeństwie.",
                "Genehmigung von Selbstzündungsmotoren."
            ),
            (
                "Clinical trial pharmacovigilance for medicinal products, vaccines, and veterinary antimicrobial toxicology.",
                "Badania kliniczne i nadzór nad bezpieczeństwem farmakoterapii produktów leczniczych, szczepionek i weterynarii.",
                "Klinische Prüfung von Arzneimitteln."
            ),
            (
                "12 May 2025, Brussels.",
                "12 maja 2025 r., Bruksela.",
                "12. Mai 2025, Brüssel."
            ),
            (
                "Pursuant to Directive 2024/10, engine exhaust emission limits must prevent air pollution.",
                "Zgodnie z dyrektywą 2024/10 normy emisji spalin silników muszą zapobiegać zanieczyszczeniu powietrza.",
                "Gemäß Richtlinie 2024/10."
            ),
        ]

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_classifier_multilabel_and_doc_context(self):
        clf = tmx_extractor.DomainClassifier(use_doc_context=True)
        # Multi-label sentence: legal + tech + environment
        cats = clf.classify_multi(
            self.sample_pairs[6][0],
            self.sample_pairs[6][1],
            doc_key="DOC_MULTI"
        )
        self.assertIn("legal", cats)
        self.assertIn("environment", cats)
        self.assertIn("tech", cats)
        self.assertNotIn("general", cats)

        # Boilerplate date/city falls back to general even in a typed document
        gen_cats = clf.classify_multi(
            self.sample_pairs[5][0],
            self.sample_pairs[5][1],
            doc_key="DOC_MULTI"
        )
        self.assertEqual(gen_cats, ["general"])

    def test_after_treatment_not_misclassified_as_medical(self):
        clf = tmx_extractor.DomainClassifier(use_doc_context=True)
        c1 = clf.classify_multi(
            "Diesel engines fitted with advanced exhaust after-treatment systems including deNOx catalysts and/or particulate traps, must additionally be tested on the ETC test.",
            "Silniki Diesla wyposażone w zaawansowane układy oczyszczania spalin, w tym katalizatory de NOx lub filtry cząstek stałych dodatkowo poddaje się badaniu ETC.",
            doc_key="42006X1227(05)R(01)"
        )
        self.assertIn("tech", c1)
        self.assertNotIn("medical", c1)

        c2 = clf.classify_multi(
            "For gas engines and engines with after-treatment",
            "Dla silników gazowych i silników z oczyszczaniem spalin",
            doc_key="42006X1227(05)R(01)"
        )
        self.assertIn("tech", c2)
        self.assertNotIn("medical", c2)

        c3 = clf.classify_multi(
            "Pursuant to Directive 2006/54 on the principle of equal treatment of men and women.",
            "Zgodnie z dyrektywą 2006/54 w sprawie zasady równego traktowania mężczyzn i kobiet.",
            doc_key="LEGAL_DOC"
        )
        self.assertIn("legal", c3)
        self.assertNotIn("medical", c3)

        # Level A2 statistical classifier sanity check
        stat = tmx_extractor.OfflineTfidfBayesClassifier()
        boosts = stat.score_boosts("clinical trial medicinal product pharmacovigilance dosage patients")
        self.assertGreaterEqual(boosts["medical"], 1)

    def test_split_by_category_creates_valid_tmx_files(self):
        zip_path = os.path.join(self.test_dir, "domains.zip")
        create_mock_zip(zip_path, pairs=self.sample_pairs)
        out_tmx = os.path.join(self.test_dir, "eu_mem.tmx")

        stats = tmx_extractor.run_extraction(
            input_path=zip_path,
            source_lang="EN",
            target_lang="PL",
            output_path=out_tmx,
            split_by_category=True,
            quiet=True
        )

        self.assertEqual(stats["extracted_pairs"], 7)
        for cat in ("legal", "business", "environment", "tech", "medical", "general"):
            cat_file = os.path.join(self.test_dir, f"eu_mem_{cat}.tmx")
            self.assertTrue(os.path.isfile(cat_file), f"Missing split file for category: {cat}")
            tree = ET.parse(cat_file)
            self.assertEqual(tree.getroot().tag, "tmx")
            tus = tree.getroot().find("body").findall("tu")
            self.assertGreaterEqual(len(tus), 1)

        # Verify multi-label pair #7 appears in both legal and environment
        legal_tree = ET.parse(os.path.join(self.test_dir, "eu_mem_legal.tmx"))
        env_tree = ET.parse(os.path.join(self.test_dir, "eu_mem_environment.tmx"))
        legal_texts = ["".join(s.itertext()) for s in legal_tree.getroot().iter("seg")]
        env_texts = ["".join(s.itertext()) for s in env_tree.getroot().iter("seg")]
        self.assertTrue(any("Directive 2024/10" in t for t in legal_texts))
        self.assertTrue(any("Directive 2024/10" in t for t in env_texts))

        # Check report includes domain breakdown
        with open(stats["report_path"], "r", encoding="utf-8") as rf:
            rep = rf.read()
            self.assertIn("Domain Category Breakdown", rep)

    def test_filter_categories_and_no_empty_files(self):
        zip_path = os.path.join(self.test_dir, "filter_only.zip")
        create_mock_zip(zip_path, pairs=self.sample_pairs)
        out_tmx = os.path.join(self.test_dir, "filtered.tmx")

        stats = tmx_extractor.run_extraction(
            input_path=zip_path,
            source_lang="DE",
            target_lang="PL",
            output_path=out_tmx,
            include_categories={"medical"},
            split_by_category=True,
            quiet=True
        )

        # Pivot EN text inside DE->PL pair still classifies medical segment
        self.assertGreaterEqual(stats["extracted_pairs"], 1)
        self.assertTrue(os.path.isfile(os.path.join(self.test_dir, "filtered_medical.tmx")))
        # Unselected categories must NOT be created
        self.assertFalse(os.path.isfile(os.path.join(self.test_dir, "filtered_legal.tmx")))
        self.assertFalse(os.path.isfile(os.path.join(self.test_dir, "filtered_general.tmx")))

    def test_cli_categories_and_split_flags(self):
        zip_path = os.path.join(self.test_dir, "cli_dom.zip")
        create_mock_zip(zip_path, pairs=self.sample_pairs)
        out_tmx = os.path.join(self.test_dir, "cli_out.tmx")

        cmd = [
            sys.executable,
            os.path.join(PROJECT_DIR, "tmx_extractor.py"),
            "-i", zip_path,
            "-s", "EN",
            "-t", "PL",
            "-o", out_tmx,
            "--categories", "legal,business",
            "--split-by-category",
            "-q"
        ]
        res = subprocess.run(cmd, capture_output=True, text=True)
        self.assertEqual(res.returncode, 0, res.stderr)
        self.assertTrue(os.path.isfile(os.path.join(self.test_dir, "cli_out_legal.tmx")))
        self.assertTrue(os.path.isfile(os.path.join(self.test_dir, "cli_out_business.tmx")))
        self.assertFalse(os.path.isfile(os.path.join(self.test_dir, "cli_out_medical.tmx")))


if __name__ == "__main__":
    unittest.main()
