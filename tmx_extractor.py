#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
EU TMX Extractor (DGT-TM / JRC-Acquis / Euramis) - Version 2.1
=============================================================
Author: Michał Kornacki (in Antigravity, 2026)
Licence: MIT License

The program was built on top of the following tools:
  - TMXtract.jar – the official tool of the European Commission (DGT / JRC, 2013)
  - tmxtract – an open-source tool by Rodrigo Nepomuceno (2019, MIT)
    (https://github.com/Nepomuceno/tmxtract)

A Python tool for easy, fast and transparent extraction of translation
memories (TMX) in a chosen language pair from European Union resources.
"""

import sys
import os
import re
import io
import time
import glob
import json
import zipfile
import argparse
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Iterator, Set
from xml.sax.saxutils import escape as xml_escape
import xml.etree.ElementTree as ET


# ==============================================================================
# PROJECT METADATA AND MIT LICENCE
# ==============================================================================

AUTHOR = "Michał Kornacki"
ENVIRONMENT = "Antigravity"
YEAR = "2026"
VERSION = "2.1"

BASE_TOOLS_INFO = (
    "• TMXtract.jar – the official tool of the European Commission (DGT / JRC, 2013)\n"
    "• tmxtract – Rodrigo Nepomuceno (https://github.com/Nepomuceno/tmxtract, 2019, MIT)"
)

MIT_LICENSE_TEXT = """MIT License

Copyright (c) 2026 Michał Kornacki (w Antigravity)

The program was built on top of the following tools:
  - TMXtract.jar (Copyright (c) 2013 Komisja Europejska / European Commission - DGT / JRC)
  - tmxtract (Copyright (c) 2019 Rodrigo Nepomuceno, https://github.com/Nepomuceno/tmxtract)

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE."""


def show_license():
    """Displays the full text of the MIT licence in a readable format."""
    UI.header("MIT LICENCE (MIT LICENSE)")
    print(UI.c(MIT_LICENSE_TEXT, UI.WHITE))
    print()
    UI.prompt("Press Enter to return to the program", default="")



# ==============================================================================
# 1. EU LANGUAGE DATABASE AND NORMALISATION
# ==============================================================================

EU_LANGUAGES: Dict[str, Dict[str, str]] = {
    "PL": {"pl": "polski", "en": "Polish", "dgt_variants": ["PL-01", "PL-PL", "PL"]},
    "EN": {"pl": "angielski", "en": "English", "dgt_variants": ["EN-GB", "EN-US", "EN-01", "EN"]},
    "DE": {"pl": "niemiecki", "en": "German", "dgt_variants": ["DE-DE", "DE-01", "DE"]},
    "FR": {"pl": "francuski", "en": "French", "dgt_variants": ["FR-FR", "FR-01", "FR"]},
    "ES": {"pl": "hiszpański", "en": "Spanish", "dgt_variants": ["ES-ES", "ES-01", "ES"]},
    "IT": {"pl": "włoski", "en": "Italian", "dgt_variants": ["IT-IT", "IT-01", "IT"]},
    "CS": {"pl": "czeski", "en": "Czech", "dgt_variants": ["CS-01", "CS-CZ", "CS"]},
    "SK": {"pl": "słowacki", "en": "Slovak", "dgt_variants": ["SK-01", "SK-SK", "SK"]},
    "NL": {"pl": "niderlandzki (holenderski)", "en": "Dutch", "dgt_variants": ["NL-NL", "NL-01", "NL"]},
    "PT": {"pl": "portugalski", "en": "Portuguese", "dgt_variants": ["PT-PT", "PT-01", "PT"]},
    "SV": {"pl": "szwedzki", "en": "Swedish", "dgt_variants": ["SV-SE", "SV-01", "SV"]},
    "DA": {"pl": "duński", "en": "Danish", "dgt_variants": ["DA-01", "DA-DK", "DA"]},
    "FI": {"pl": "fiński", "en": "Finnish", "dgt_variants": ["FI-01", "FI-FI", "FI"]},
    "EL": {"pl": "grecki", "en": "Greek", "dgt_variants": ["EL-01", "EL-GR", "EL"]},
    "HU": {"pl": "węgierski", "en": "Hungarian", "dgt_variants": ["HU-01", "HU-HU", "HU"]},
    "RO": {"pl": "rumuński", "en": "Romanian", "dgt_variants": ["RO-RO", "RO-01", "RO"]},
    "BG": {"pl": "bułgarski", "en": "Bulgarian", "dgt_variants": ["BG-01", "BG-BG", "BG"]},
    "HR": {"pl": "chorwacki", "en": "Croatian", "dgt_variants": ["HR-01", "HR-HR", "HR", "SH"]},
    "SL": {"pl": "słoweński", "en": "Slovenian", "dgt_variants": ["SL-01", "SL-SI", "SL"]},
    "ET": {"pl": "estoński", "en": "Estonian", "dgt_variants": ["ET-01", "ET-EE", "ET"]},
    "LV": {"pl": "łotewski", "en": "Latvian", "dgt_variants": ["LV-01", "LV-LV", "LV"]},
    "LT": {"pl": "litewski", "en": "Lithuanian", "dgt_variants": ["LT-01", "LT-LT", "LT"]},
    "MT": {"pl": "maltański", "en": "Maltese", "dgt_variants": ["MT-01", "MT-MT", "MT"]},
    "GA": {"pl": "irlandzki", "en": "Irish", "dgt_variants": ["GA-01", "GA-IE", "GA"]},
    "TR": {"pl": "turecki", "en": "Turkish", "dgt_variants": ["TR-01", "TR-TR", "TR"]},
    "NO": {"pl": "norweski", "en": "Norwegian", "dgt_variants": ["NO-01", "NO"]},
    "IS": {"pl": "islandzki", "en": "Icelandic", "dgt_variants": ["IS-01", "IS"]},
}

POPULAR_PAIRS = [
    ("EN", "PL", "English -> Polish (EN -> PL) [Most frequently chosen]"),
    ("PL", "EN", "Polish -> English (PL -> EN)"),
    ("DE", "PL", "German -> Polish (DE -> PL)"),
    ("PL", "DE", "Polish -> German (PL -> DE)"),
    ("FR", "PL", "French -> Polish (FR -> PL)"),
    ("ES", "PL", "Spanish -> Polish (ES -> PL)"),
    ("IT", "PL", "Italian -> Polish (IT -> PL)"),
    ("DE", "EN", "German -> English (DE -> EN)"),
    ("FR", "EN", "French -> English (FR -> EN)"),
    ("ES", "EN", "Spanish -> English (ES -> EN)"),
]

DGT_OFFICIAL_CATALOG = {
    "2025": [
        ("Vol_2025.new_1.zip", "https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/DGT-TM/Resources/DGT-TM-2025/Vol_2025.new_1.zip", "New 2025 volume, part 1/5"),
        ("Vol_2025.new_2.zip", "https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/DGT-TM/Resources/DGT-TM-2025/Vol_2025.new_2.zip", "New 2025 volume, part 2/5"),
        ("Vol_2025.new_3.zip", "https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/DGT-TM/Resources/DGT-TM-2025/Vol_2025.new_3.zip", "New 2025 volume, part 3/5"),
        ("Vol_2025.new_4.zip", "https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/DGT-TM/Resources/DGT-TM-2025/Vol_2025.new_4.zip", "New 2025 volume, part 4/5"),
        ("Vol_2025.new_5.zip", "https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/DGT-TM/Resources/DGT-TM-2025/Vol_2025.new_5.zip", "New 2025 volume, part 5/5"),
    ],
    "2024": [
        ("Vol_2024.new_1.zip", "https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/DGT-TM/Resources/DGT-TM-2024/Vol_2024.new_1.zip", "2024 volume, part 1/3"),
        ("Vol_2024.new_2.zip", "https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/DGT-TM/Resources/DGT-TM-2024/Vol_2024.new_2.zip", "2024 volume, part 2/3"),
        ("Vol_2024.new_3.zip", "https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/DGT-TM/Resources/DGT-TM-2024/Vol_2024.new_3.zip", "2024 volume, part 3/3"),
    ],
    "2023": [
        ("Vol_2023.new_1.zip", "https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/DGT-TM/Resources/DGT-TM-2023/Vol_2023.new_1.zip", "2023 volume, part 1/3"),
        ("Vol_2023.new_2.zip", "https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/DGT-TM/Resources/DGT-TM-2023/Vol_2023.new_2.zip", "2023 volume, part 2/3"),
        ("Vol_2023.new_3.zip", "https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/DGT-TM/Resources/DGT-TM-2023/Vol_2023.new_3.zip", "2023 volume, part 3/3"),
    ],
    "2022": [
        ("Vol_2022.new_1.zip", "https://wt-public.emm4u.eu/Resources/DGT-TM-2022/Vol_2022.new_1.zip", "2022 volume, part 1/3"),
        ("Vol_2022.new_2.zip", "https://wt-public.emm4u.eu/Resources/DGT-TM-2022/Vol_2022.new_2.zip", "2022 volume, part 2/3"),
        ("Vol_2022.new_3.zip", "https://wt-public.emm4u.eu/Resources/DGT-TM-2022/Vol_2022.new_3.zip", "2022 volume, part 3/3"),
    ],
    "2020": [
        ("Vol_2020_1.zip", "http://wt-public.emm4u.eu/Resources/DGT-TM-2021/Vol_2020_1.zip", "2021 volume, part 1/5"),
        ("Vol_2020_2.zip", "http://wt-public.emm4u.eu/Resources/DGT-TM-2021/Vol_2020_2.zip", "2021 volume, part 2/5"),
        ("Vol_2020_3.zip", "http://wt-public.emm4u.eu/Resources/DGT-TM-2021/Vol_2020_3.zip", "2021 volume, part 3/5"),
        ("Vol_2020_4.zip", "http://wt-public.emm4u.eu/Resources/DGT-TM-2021/Vol_2020_4.zip", "2021 volume, part 4/5"),
        ("Vol_2020_5.zip", "http://wt-public.emm4u.eu/Resources/DGT-TM-2021/Vol_2020_5.zip", "2021 volume, part 5/5"),
    ],
    "2019": [
        ("Vol_2019_1.zip", "https://wt-public.emm4u.eu/Resources/DGT-TM-2020/Vol_2019_1.zip", "2019 volume, part 1/2"),
        ("Vol_2019_2.zip", "https://wt-public.emm4u.eu/Resources/DGT-TM-2020/Vol_2019_2.zip", "2019 volume, part 2/2"),
    ],
    "2018": [
        ("Vol_2018_1.zip", "http://wt-public.emm4u.eu/Resources/DGT-TM-2019/Vol_2018_1.zip", "2018 volume, part 1/3"),
        ("Vol_2018_2.zip", "http://wt-public.emm4u.eu/Resources/DGT-TM-2019/Vol_2018_2.zip", "2018 volume, part 2/3"),
        ("Vol_2018_3.zip", "http://wt-public.emm4u.eu/Resources/DGT-TM-2019/Vol_2018_3.zip", "2018 volume, part 3/3"),
    ],
    "2017": [
        ("Vol_2017_1.zip", "http://wt-public.emm4u.eu/Resources/DGT-TM-2018/Vol_2017_1.zip", "2017 volume, part 1/2"),
        ("Vol_2017_2.zip", "http://wt-public.emm4u.eu/Resources/DGT-TM-2018/Vol_2017_2.zip", "2017 volume, part 2/2"),
    ],
    "2016": [
        ("Vol_2016_1.zip", "https://wt-public.emm4u.eu/Resources/DGT-TM-2017/Vol_2016_1.zip", "2016 volume, part 1/9"),
        ("Vol_2016_2.zip", "https://wt-public.emm4u.eu/Resources/DGT-TM-2017/Vol_2016_2.zip", "2016 volume, part 2/9"),
        ("Vol_2016_3.zip", "https://wt-public.emm4u.eu/Resources/DGT-TM-2017/Vol_2016_3.zip", "2016 volume, part 3/9"),
        ("Vol_2016_4.zip", "https://wt-public.emm4u.eu/Resources/DGT-TM-2017/Vol_2016_4.zip", "2016 volume, part 4/9"),
        ("Vol_2016_5.zip", "https://wt-public.emm4u.eu/Resources/DGT-TM-2017/Vol_2016_5.zip", "2016 volume, part 5/9"),
        ("Vol_2016_6.zip", "https://wt-public.emm4u.eu/Resources/DGT-TM-2017/Vol_2016_6.zip", "2016 volume, part 6/9"),
        ("Vol_2016_7.zip", "https://wt-public.emm4u.eu/Resources/DGT-TM-2017/Vol_2016_7.zip", "2016 volume, part 7/9"),
        ("Vol_2016_8.zip", "https://wt-public.emm4u.eu/Resources/DGT-TM-2017/Vol_2016_8.zip", "2016 volume, part 8/9"),
        ("Vol_2016_9.zip", "https://wt-public.emm4u.eu/Resources/DGT-TM-2017/Vol_2016_9.zip", "2016 volume, part 9/9"),
    ],
    "2015": [
        ("Vol_2015_1.zip", "https://wt-public.emm4u.eu/Resources/DGT-TM-2016/Vol_2015_1.zip", "2015 volume, part 1/7"),
        ("Vol_2015_2.zip", "https://wt-public.emm4u.eu/Resources/DGT-TM-2016/Vol_2015_2.zip", "2015 volume, part 2/7"),
        ("Vol_2015_3.zip", "https://wt-public.emm4u.eu/Resources/DGT-TM-2016/Vol_2015_3.zip", "2015 volume, part 3/7"),
        ("Vol_2015_4.zip", "https://wt-public.emm4u.eu/Resources/DGT-TM-2016/Vol_2015_4.zip", "2015 volume, part 4/7"),
        ("Vol_2015_5.zip", "https://wt-public.emm4u.eu/Resources/DGT-TM-2016/Vol_2015_5.zip", "2015 volume, part 5/7"),
        ("Vol_2015_6.zip", "https://wt-public.emm4u.eu/Resources/DGT-TM-2016/Vol_2015_6.zip", "2015 volume, part 6/7"),
        ("Vol_2015_7.zip", "https://wt-public.emm4u.eu/Resources/DGT-TM-2016/Vol_2015_7.zip", "2015 volume, part 7/7"),
    ],
    "2014": [
        ("Vol_2014_1.zip", "https://wt-public.emm4u.eu/Resources/DGT-TM-2015/Vol_2014_1.zip", "2014 volume, part 1/3"),
        ("Vol_2014_2.zip", "https://wt-public.emm4u.eu/Resources/DGT-TM-2015/Vol_2014_2.zip", "2014 volume, part 2/3"),
        ("Vol_2014_3.zip", "https://wt-public.emm4u.eu/Resources/DGT-TM-2015/Vol_2014_3.zip", "2014 volume, part 3/3"),
    ],
    "2013": [
        ("Vol_2013_1.zip", "https://wt-public.emm4u.eu/Resources/DGT-TM-2014/Vol_2013_1.zip", "2013 volume, part 1/7"),
        ("Vol_2013_2.zip", "https://wt-public.emm4u.eu/Resources/DGT-TM-2014/Vol_2013_2.zip", "2013 volume, part 2/7"),
        ("Vol_2013_3.zip", "https://wt-public.emm4u.eu/Resources/DGT-TM-2014/Vol_2013_3.zip", "2013 volume, part 3/7"),
        ("Vol_2013_4.zip", "https://wt-public.emm4u.eu/Resources/DGT-TM-2014/Vol_2013_4.zip", "2013 volume, part 4/7"),
        ("Vol_2013_5.zip", "https://wt-public.emm4u.eu/Resources/DGT-TM-2014/Vol_2013_5.zip", "2013 volume, part 5/7"),
        ("Vol_2013_6.zip", "https://wt-public.emm4u.eu/Resources/DGT-TM-2014/Vol_2013_6.zip", "2013 volume, part 6/7"),
        ("Vol_2013_7.zip", "https://wt-public.emm4u.eu/Resources/DGT-TM-2014/Vol_2013_7.zip", "2013 volume, part 7/7"),
    ],
    "2012": [
        ("Vol_2012_1.zip", "https://wt-public.emm4u.eu/Resources/DGT-TM-2013/Vol_2012_1.zip", "2012 volume, part 1/6"),
        ("Vol_2012_2.zip", "https://wt-public.emm4u.eu/Resources/DGT-TM-2013/Vol_2012_2.zip", "2012 volume, part 2/6"),
        ("Vol_2012_3.zip", "https://wt-public.emm4u.eu/Resources/DGT-TM-2013/Vol_2012_3.zip", "2012 volume, part 3/6"),
        ("Vol_2012_4.zip", "https://wt-public.emm4u.eu/Resources/DGT-TM-2013/Vol_2012_4.zip", "2012 volume, part 4/6"),
        ("Vol_2012_5.zip", "https://wt-public.emm4u.eu/Resources/DGT-TM-2013/Vol_2012_5.zip", "2012 volume, part 5/6"),
        ("Vol_2012_6.zip", "https://wt-public.emm4u.eu/Resources/DGT-TM-2013/Vol_2012_6.zip", "2012 volume, part 6/6"),
    ],
    "2011": [
        ("Vol_2011_1.zip", "https://wt-public.emm4u.eu/Resources/DGT-TM-2012/Vol_2011_1.zip", "2011 volume, part 1/4"),
        ("Vol_2011_2.zip", "https://wt-public.emm4u.eu/Resources/DGT-TM-2012/Vol_2011_2.zip", "2011 volume, part 2/4"),
        ("Vol_2011_3.zip", "https://wt-public.emm4u.eu/Resources/DGT-TM-2012/Vol_2011_3.zip", "2011 volume, part 3/4"),
        ("Vol_2011_4.zip", "https://wt-public.emm4u.eu/Resources/DGT-TM-2012/Vol_2011_4.zip", "2011 volume, part 4/4"),
    ],
    "2010": [
        ("Vol_2010_1.zip", "https://wt-public.emm4u.eu/Resources/DGT-TM-2011/Vol_2010_1.zip", "2010 volume, part 1/4"),
        ("Vol_2010_2.zip", "https://wt-public.emm4u.eu/Resources/DGT-TM-2011/Vol_2010_2.zip", "2010 volume, part 2/4"),
        ("Vol_2010_3.zip", "https://wt-public.emm4u.eu/Resources/DGT-TM-2011/Vol_2010_3.zip", "2010 volume, part 3/4"),
        ("Vol_2010_4.zip", "https://wt-public.emm4u.eu/Resources/DGT-TM-2011/Vol_2010_4.zip", "2010 volume, part 4/4"),
    ],
    "2009": [
        ("Vol_2009_1.zip", "https://wt-public.emm4u.eu/Resources/DGT-TM-2011/Vol_2009_1.zip", "2009 volume, part 1/4"),
        ("Vol_2009_2.zip", "https://wt-public.emm4u.eu/Resources/DGT-TM-2011/Vol_2009_2.zip", "2009 volume, part 2/4"),
        ("Vol_2009_3.zip", "https://wt-public.emm4u.eu/Resources/DGT-TM-2011/Vol_2009_3.zip", "2009 volume, part 3/4"),
        ("Vol_2009_4.zip", "https://wt-public.emm4u.eu/Resources/DGT-TM-2011/Vol_2009_4.zip", "2009 volume, part 4/4"),
    ],
    "2008": [
        ("Vol_2008_1.zip", "https://wt-public.emm4u.eu/Resources/DGT-TM-2011/Vol_2008_1.zip", "2008 volume, part 1/4"),
        ("Vol_2008_2.zip", "https://wt-public.emm4u.eu/Resources/DGT-TM-2011/Vol_2008_2.zip", "2008 volume, part 2/4"),
        ("Vol_2008_3.zip", "https://wt-public.emm4u.eu/Resources/DGT-TM-2011/Vol_2008_3.zip", "2008 volume, part 3/4"),
        ("Vol_2008_4.zip", "https://wt-public.emm4u.eu/Resources/DGT-TM-2011/Vol_2008_4.zip", "2008 volume, part 4/4"),
    ],
    "2007": [
        ("Vol_2007_1.zip", "https://wt-public.emm4u.eu/Resources/DGT-TM-2011/Vol_2007_1.zip", "2007 volume, part 1/3"),
        ("Vol_2007_2.zip", "https://wt-public.emm4u.eu/Resources/DGT-TM-2011/Vol_2007_2.zip", "2007 volume, part 2/3"),
        ("Vol_2007_3.zip", "https://wt-public.emm4u.eu/Resources/DGT-TM-2011/Vol_2007_3.zip", "2007 volume, part 3/3"),
    ],
    "2006": [
        ("Vol_2006_1.zip", "https://wt-public.emm4u.eu/Resources/DGT-TM-2011/Vol_2006_1.zip", "2006 volume, part 1/5"),
        ("Vol_2006_2.zip", "https://wt-public.emm4u.eu/Resources/DGT-TM-2011/Vol_2006_2.zip", "2006 volume, part 2/5"),
        ("Vol_2006_3.zip", "https://wt-public.emm4u.eu/Resources/DGT-TM-2011/Vol_2006_3.zip", "2006 volume, part 3/5"),
        ("Vol_2006_4.zip", "https://wt-public.emm4u.eu/Resources/DGT-TM-2011/Vol_2006_4.zip", "2006 volume, part 4/5"),
        ("Vol_2006_5.zip", "https://wt-public.emm4u.eu/Resources/DGT-TM-2011/Vol_2006_5.zip", "2006 volume, part 5/5"),
    ],
    "2005": [
        ("Vol_2005_1.zip", "https://wt-public.emm4u.eu/Resources/DGT-TM-2011/Vol_2005_1.zip", "2005 volume, part 1/3"),
        ("Vol_2005_2.zip", "https://wt-public.emm4u.eu/Resources/DGT-TM-2011/Vol_2005_2.zip", "2005 volume, part 2/3"),
        ("Vol_2005_3.zip", "https://wt-public.emm4u.eu/Resources/DGT-TM-2011/Vol_2005_3.zip", "2005 volume, part 3/3"),
    ],
    "2004": [
        ("Vol_2004_1.zip", "https://wt-public.emm4u.eu/Resources/DGT-TM-2011/Vol_2004_1.zip", "2004 volume, part 1/2"),
        ("Vol_2004_2.zip", "https://wt-public.emm4u.eu/Resources/DGT-TM-2011/Vol_2004_2.zip", ""),
    ],
}


def fetch_live_catalog_if_possible():
    """
    Tries to fetch the newest list of volumes from the data.europa.eu API.
    If no network is available, immediately returns the built-in DGT_OFFICIAL_CATALOG.
    """
    try:
        import urllib.request, json, re
        url = "https://data.europa.eu/api/hub/search/datasets/dgt-translation-memory"
        req = urllib.request.Request(url, headers={"User-Agent": "EU-TMX-Extractor/2.1"})
        with urllib.request.urlopen(req, timeout=3.5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        dists = data.get("result", {}).get("distributions", [])
        cat = {}
        for d in dists:
            t_pl = d.get("title", {}).get("pl") or d.get("title", {}).get("en") or ""
            for u in d.get("download_url", []):
                fn = u.split("/")[-1]
                m = re.search(r"Vol_(\d{4})", fn)
                y = m.group(1) if m else "Other"
                cat.setdefault(y, []).append((fn, u, t_pl))
        if cat:
            for y in cat:
                cat[y].sort(key=lambda x: x[0])
            return cat
    except Exception:
        pass
    return DGT_OFFICIAL_CATALOG


def get_flat_catalog():
    """Returns a flat list of all volumes (name, url, description)."""
    res = []
    for y in sorted(DGT_OFFICIAL_CATALOG.keys(), reverse=True):
        res.extend(DGT_OFFICIAL_CATALOG[y])
    return res



def resolve_language_code(text: str) -> Optional[str]:
    """Matches the user's input to a 2-letter ISO code (e.g. 'PL')."""
    if not text:
        return None
    raw = text.strip()
    upper = raw.upper()
    two_letter = upper.split("-")[0]
    if two_letter in EU_LANGUAGES:
        return two_letter
    clean = raw.lower()
    for code, info in EU_LANGUAGES.items():
        if clean == info["pl"].lower() or clean in info["pl"].lower():
            return code
        if clean == info["en"].lower() or clean in info["en"].lower():
            return code
    if len(upper) == 2 and upper.isalpha():
        return upper
    return None


def get_lang_display(code: str) -> str:
    """Returns a readable language name, e.g. 'PL (polski)'."""
    upper = code.upper()
    if upper in EU_LANGUAGES:
        return f"{upper} ({EU_LANGUAGES[upper]['pl']})"
    return upper


# ==============================================================================
# 2. COLOURED CONSOLE INTERFACE (TERMINAL UI)
# ==============================================================================

class UI:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    GREEN = "\033[32m"
    CYAN = "\033[36m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    RED = "\033[31m"
    WHITE = "\033[37m"
    
    _has_color = sys.stdout.isatty() and not os.environ.get("NO_COLOR")

    @classmethod
    def c(cls, text: str, color: str) -> str:
        if cls._has_color:
            return f"{color}{text}{cls.RESET}"
        return text

    @classmethod
    def header(cls, title: str):
        width = 68
        line = "═" * width
        print()
        print(cls.c(f"╔{line}╗", cls.CYAN))
        print(cls.c(f"║{title.center(width)}║", cls.BOLD + cls.CYAN))
        print(cls.c(f"╚{line}╝", cls.CYAN))
        print()

    @classmethod
    def section(cls, title: str):
        print(cls.c(f"\n▶ {title}", cls.BOLD + cls.YELLOW))
        print(cls.c("─" * (len(title) + 4), cls.DIM))

    @classmethod
    def success(cls, msg: str):
        print(f" {cls.c('✔', cls.GREEN)} {msg}")

    @classmethod
    def info(cls, msg: str):
        print(f" {cls.c('ℹ', cls.CYAN)} {msg}")

    @classmethod
    def warning(cls, msg: str):
        print(f" {cls.c('⚠', cls.YELLOW)} {msg}")

    @classmethod
    def error(cls, msg: str):
        print(f" {cls.c('✖', cls.RED)} {msg}")

    @classmethod
    def prompt(cls, text: str, default: Optional[str] = None) -> str:
        prompt_str = f" {cls.c('?', cls.MAGENTA)} {cls.c(text, cls.BOLD)}"
        if default is not None:
            prompt_str += f" {cls.c(f'[{default}]', cls.DIM)}: "
        else:
            prompt_str += ": "
        try:
            res = input(prompt_str).strip()
            return res if res else (default if default is not None else "")
        except (KeyboardInterrupt, EOFError):
            print("\nInterrupted.")
            sys.exit(0)

    @classmethod
    def prompt_yes_no(cls, text: str, default: bool = True) -> bool:
        choice_str = "[Y/n]" if default else "[y/N]"
        ans = cls.prompt(f"{text} {choice_str}", default="y" if default else "n").lower()
        return ans in ("t", "tak", "y", "yes", "1", "prawda")

    @classmethod
    def render_progress(cls, current: int, total: int, pairs_count: int, speed: float = 0.0):
        if not sys.stdout.isatty():
            return
        width = 30
        pct = (current / total) if total > 0 else 1.0
        filled = int(width * pct)
        bar = "█" * filled + "░" * (width - filled)
        pct_str = f"{int(pct * 100):3d}%"
        speed_str = f" ({speed:,.0f} pairs/s)" if speed > 0 else ""
        sys.stdout.write(
            f"\r [{cls.c(bar, cls.CYAN)}] {pct_str} | File {current}/{total} | Extracted: {cls.c(f'{pairs_count:,}', cls.GREEN)} pairs{speed_str} "
        )
        sys.stdout.flush()


# ==============================================================================
# 3. SOURCE DATA DISCOVERY
# ==============================================================================

class SourceItem:
    def __init__(self, display_name: str, file_path: str, is_zip: bool = False, zip_entry_name: str = ""):
        self.display_name = display_name
        self.file_path = file_path
        self.is_zip = is_zip
        self.zip_entry_name = zip_entry_name
        self.size_bytes = 0

    def open_stream(self):
        if self.is_zip:
            z = zipfile.ZipFile(self.file_path, "r")
            return z, z.open(self.zip_entry_name)
        else:
            return None, open(self.file_path, "rb")


def discover_sources(path: str) -> List[SourceItem]:
    p = Path(path).resolve()
    if not p.exists():
        raise FileNotFoundError(f"The given path does not exist: {path}")

    items: List[SourceItem] = []

    if p.is_file():
        if p.suffix.lower() == ".tmx":
            item = SourceItem(p.name, str(p), is_zip=False)
            item.size_bytes = p.stat().st_size
            items.append(item)
        elif p.suffix.lower() == ".zip":
            _scan_zip(str(p), items)
        else:
            raise ValueError(f"Unsupported file format: {p.name} (.tmx or .zip required)")
    elif p.is_dir():
        for tmx_file in sorted(p.rglob("*.tmx")):
            item = SourceItem(tmx_file.name, str(tmx_file), is_zip=False)
            item.size_bytes = tmx_file.stat().st_size
            items.append(item)
        for zip_file in sorted(p.rglob("*.zip")):
            _scan_zip(str(zip_file), items)

    return items


def _scan_zip(zip_path: str, out_items: List[SourceItem]):
    try:
        with zipfile.ZipFile(zip_path, "r") as z:
            for info in z.infolist():
                if info.filename.lower().endswith(".tmx") and not info.is_dir():
                    item = SourceItem(
                        display_name=f"{Path(zip_path).name}/{info.filename}",
                        file_path=zip_path,
                        is_zip=True,
                        zip_entry_name=info.filename
                    )
                    item.size_bytes = info.file_size
                    out_items.append(item)
    except zipfile.BadZipFile:
        UI.warning(f"Corrupt ZIP archive (skipping): {zip_path}")


# ==============================================================================
# 4. PARSING AND EXTRACTION
# ==============================================================================

class TranslationPair:
    __slots__ = ("source", "target", "doc_id", "src_lang", "trg_lang")

    def __init__(self, source: str, target: str, doc_id: str = "", src_lang: str = "", trg_lang: str = ""):
        self.source = source
        self.target = target
        self.doc_id = doc_id
        self.src_lang = src_lang
        self.trg_lang = trg_lang


class TMXExtractor:
    def __init__(
        self,
        source_lang: str,
        target_lang: str,
        deduplicate: bool = True,
        filter_identical: bool = True,
        min_length: int = 1,
        max_length: int = 0,
        max_translations: int = 0
    ):
        self.src_code = source_lang.upper()
        self.trg_code = target_lang.upper()
        self.deduplicate = deduplicate
        self.filter_identical = filter_identical
        self.min_length = min_length
        self.max_length = max_length
        self.max_translations = max_translations

        self.total_tus_seen = 0
        self.total_pairs_matched = 0
        self.duplicates_removed = 0
        self.identical_filtered = 0
        self.empty_filtered = 0
        self.seen_hashes: Set[Tuple[str, str]] = set()

    def matches_lang(self, tuv_lang: str, target_code: str) -> bool:
        clean = tuv_lang.strip().upper()
        prefix = clean.split("-")[0]
        if prefix == target_code:
            return True
        if target_code == "HR" and prefix == "SH":
            return True
        return False

    def parse_stream(self, stream) -> Iterator[TranslationPair]:
        try:
            for event, elem in ET.iterparse(stream, events=("end",)):
                if elem.tag == "tu":
                    self.total_tus_seen += 1

                    doc_id = ""
                    for prop in elem.findall("prop"):
                        if prop.get("type") in ("Txt::Doc. No.", "Txt::Doc.No.", "Txt::Doc No"):
                            doc_id = (prop.text or "").strip()
                            break

                    src_seg = None
                    trg_seg = None
                    src_full_lang = ""
                    trg_full_lang = ""

                    for tuv in elem.findall("tuv"):
                        lang = tuv.get("lang") or tuv.get("{http://www.w3.org/XML/1998/namespace}lang") or ""
                        if not lang:
                            continue

                        if src_seg is None and self.matches_lang(lang, self.src_code):
                            seg_elem = tuv.find("seg")
                            if seg_elem is not None:
                                src_seg = "".join(seg_elem.itertext()).strip()
                                src_full_lang = lang

                        elif trg_seg is None and self.matches_lang(lang, self.trg_code):
                            seg_elem = tuv.find("seg")
                            if seg_elem is not None:
                                trg_seg = "".join(seg_elem.itertext()).strip()
                                trg_full_lang = lang

                    if src_seg and trg_seg:
                        if len(src_seg) < self.min_length or len(trg_seg) < self.min_length:
                            self.empty_filtered += 1
                        elif self.max_length > 0 and (len(src_seg) > self.max_length or len(trg_seg) > self.max_length):
                            pass
                        elif self.filter_identical and src_seg == trg_seg:
                            self.identical_filtered += 1
                        else:
                            pair_key = (src_seg, trg_seg)
                            if self.deduplicate and pair_key in self.seen_hashes:
                                self.duplicates_removed += 1
                            else:
                                if self.deduplicate:
                                    self.seen_hashes.add(pair_key)
                                self.total_pairs_matched += 1
                                yield TranslationPair(
                                    source=src_seg,
                                    target=trg_seg,
                                    doc_id=doc_id,
                                    src_lang=src_full_lang or self.src_code,
                                    trg_lang=trg_full_lang or self.trg_code
                                )

                    elem.clear()

        except ET.ParseError:
            yield from self._parse_with_regex_fallback(stream)

    def _parse_with_regex_fallback(self, stream) -> Iterator[TranslationPair]:
        try:
            stream.seek(0)
            raw = stream.read()
            text = ""
            if raw.startswith(b"\xff\xfe"):
                text = raw.decode("utf-16le", errors="replace")
            elif raw.startswith(b"\xfe\xff"):
                text = raw.decode("utf-16be", errors="replace")
            else:
                try:
                    text = raw.decode("utf-8")
                except UnicodeDecodeError:
                    text = raw.decode("latin-1", errors="replace")

            tu_re = re.compile(r"<tu\b[^>]*>(.*?)</tu>", re.DOTALL)
            tuv_re = re.compile(r"<tuv\b[^>]*\blang=[\"\x27]([^\"]+)[\"\x27][^>]*>\s*<seg>(.*?)</seg>", re.DOTALL)
            doc_re = re.compile(r"<prop\b[^>]*type=[\"\x27]Txt::Doc\. No\.[\"\x27][^>]*>(.*?)</prop>", re.DOTALL)

            for match in tu_re.finditer(text):
                self.total_tus_seen += 1
                tu_content = match.group(1)
                doc_m = doc_re.search(tu_content)
                doc_id = doc_m.group(1).strip() if doc_m else ""

                tuvs = {}
                for tuv_m in tuv_re.finditer(tu_content):
                    l_val = tuv_m.group(1).strip()
                    s_val = tuv_m.group(2).strip()
                    tuvs[l_val] = s_val

                src_seg = None
                trg_seg = None
                for l_key, s_val in tuvs.items():
                    if src_seg is None and self.matches_lang(l_key, self.src_code):
                        src_seg = s_val
                    elif trg_seg is None and self.matches_lang(l_key, self.trg_code):
                        trg_seg = s_val

                if src_seg and trg_seg:
                    pair_key = (src_seg, trg_seg)
                    if self.deduplicate and pair_key in self.seen_hashes:
                        self.duplicates_removed += 1
                    else:
                        if self.deduplicate:
                            self.seen_hashes.add(pair_key)
                        self.total_pairs_matched += 1
                        yield TranslationPair(source=src_seg, target=trg_seg, doc_id=doc_id)
        except Exception:
            pass


# ==============================================================================
# 5. WRITING TO FILES WITH SPLITTING AND FILE-NAME SEQUENCING
# ==============================================================================

class PartFileInfo:
    def __init__(self, file_path: str, format_name: str, part_num: int):
        self.file_path = file_path
        self.format_name = format_name
        self.part_num = part_num
        self.segments_count = 0
        self.size_bytes = 0


class ChunkedWriter:
    """
    Handles intelligent saving of a single format (TMX, TSV or JSONL)
    with optional splitting into parts (file-name sequencing):
      file_part01.tmx, file_part02.tmx, etc.
    If splitting was not needed (only 1 part), the clean name is kept: file.tmx.
    """
    def __init__(
        self,
        base_path: str,
        ext: str,
        src_lang: str,
        trg_lang: str,
        split_size: int = 0,
        creation_date_str: str = ""
    ):
        self.base_path = base_path
        self.ext = ext.lstrip(".").lower()
        self.src_lang = src_lang.lower()
        self.trg_lang = trg_lang.lower()
        self.split_size = split_size
        self.creation_date_str = creation_date_str or time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())

        self.current_fp = None
        self.current_part_num = 0
        self.current_part_count = 0
        self.total_written = 0
        self.completed_parts: List[PartFileInfo] = []
        self.current_part_info: Optional[PartFileInfo] = None

    def _get_part_path(self, part_num: int) -> str:
        base, _ = os.path.splitext(self.base_path)
        if self.split_size > 0:
            return f"{base}_part{part_num:02d}.{self.ext}"
        else:
            return f"{base}.{self.ext}"

    def _open_new_part(self):
        if self.current_fp:
            self._close_current_part()

        self.current_part_num += 1
        self.current_part_count = 0
        part_path = self._get_part_path(self.current_part_num)

        self.current_fp = open(part_path, "w", encoding="utf-8", newline="\n")
        self.current_part_info = PartFileInfo(part_path, self.ext, self.current_part_num)

        # Format-dependent header
        if self.ext == "tmx":
            part_str = f"Part {self.current_part_num}. " if self.split_size > 0 else ""
            part_note = (
                f"{part_str}Export from EU resources (DGT-TM). "
                f"Prepared by: {AUTHOR} (in {ENVIRONMENT}, {YEAR}). Licence: MIT. "
                "Based on: TMXtract.jar (European Commission - DGT/JRC, 2013) and tmxtract (Rodrigo Nepomuceno, 2019)."
            )
            header = f"""<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE tmx SYSTEM "tmx14.dtd">
<tmx version="1.4">
  <header
    creationtool="EU-TMX-Extractor"
    creationtoolversion="{VERSION}"
    datatype="PlainText"
    segtype="sentence"
    adminlang="en"
    srclang="{self.src_lang}"
    o-tmf="DGT-TM"
    creationdate="{self.creation_date_str}">
    <note>{part_note}</note>
  </header>
  <body>
"""
            self.current_fp.write(header)
        elif self.ext == "tsv":
            self.current_fp.write(f"Source ({self.src_lang.upper()})\tTarget ({self.trg_lang.upper()})\tDocument_ID\n")
        elif self.ext == "csv":
            self.current_fp.write(f'"Source ({self.src_lang.upper()})","Target ({self.trg_lang.upper()})","Document_ID"\n')

    def _close_current_part(self):
        if not self.current_fp:
            return

        if self.ext == "tmx":
            self.current_fp.write("  </body>\n</tmx>\n")

        self.current_fp.close()
        self.current_fp = None

        if self.current_part_info:
            self.current_part_info.segments_count = self.current_part_count
            if os.path.exists(self.current_part_info.file_path):
                self.current_part_info.size_bytes = os.path.getsize(self.current_part_info.file_path)
            self.completed_parts.append(self.current_part_info)
            self.current_part_info = None

    def write(self, pair: TranslationPair):
        if self.current_fp is None or (self.split_size > 0 and self.current_part_count >= self.split_size):
            self._open_new_part()

        self.current_part_count += 1
        self.total_written += 1

        if self.ext == "tmx":
            s_text = xml_escape(pair.source)
            t_text = xml_escape(pair.target)
            doc_tag = f'\n      <prop type="Txt::Doc. No.">{xml_escape(pair.doc_id)}</prop>' if pair.doc_id else ""
            tu_block = (
                f'    <tu tuid="{self.current_part_count}">{doc_tag}\n'
                f'      <tuv xml:lang="{self.src_lang}">\n'
                f'        <seg>{s_text}</seg>\n'
                f'      </tuv>\n'
                f'      <tuv xml:lang="{self.trg_lang}">\n'
                f'        <seg>{t_text}</seg>\n'
                f'      </tuv>\n'
                f'    </tu>\n'
            )
            self.current_fp.write(tu_block)

        elif self.ext == "tsv":
            s = pair.source.replace("\t", " ").replace("\r", " ").replace("\n", " ")
            t = pair.target.replace("\t", " ").replace("\r", " ").replace("\n", " ")
            d = pair.doc_id.replace("\t", " ").replace("\r", " ").replace("\n", " ")
            self.current_fp.write(f"{s}\t{t}\t{d}\n")

        elif self.ext == "csv":
            def esc(txt): return '"' + txt.replace('"', '""').replace("\r", " ").replace("\n", " ") + '"'
            self.current_fp.write(f"{esc(pair.source)},{esc(pair.target)},{esc(pair.doc_id)}\n")

        elif self.ext == "jsonl":
            rec = {
                "source": pair.source,
                "target": pair.target,
                "doc_id": pair.doc_id,
                "src_lang": self.src_lang,
                "trg_lang": self.trg_lang
            }
            self.current_fp.write(json.dumps(rec, ensure_ascii=False) + "\n")

    def close(self):
        self._close_current_part()

        # If splitting produced only 1 part, rename it to the clean name without '_part01'
        if self.split_size > 0 and len(self.completed_parts) == 1:
            single = self.completed_parts[0]
            clean_path = f"{os.path.splitext(self.base_path)[0]}.{self.ext}"
            if single.file_path != clean_path:
                try:
                    if os.path.exists(clean_path):
                        os.remove(clean_path)
                    os.rename(single.file_path, clean_path)
                    single.file_path = clean_path
                except OSError:
                    pass


class MultiFormatWriter:
    """Manages parallel writing to multiple formats."""
    def __init__(self, writers: List[ChunkedWriter]):
        self.writers = writers

    def write(self, pair: TranslationPair):
        for w in self.writers:
            w.write(pair)

    def close(self):
        for w in self.writers:
            w.close()

    def get_all_parts(self) -> List[PartFileInfo]:
        parts = []
        for w in self.writers:
            parts.extend(w.completed_parts)
        return parts


# ==============================================================================
# 6. AUTOMATIC EXPORT REPORT GENERATION
# ==============================================================================

def generate_export_report(
    report_file_path: str,
    stats: Dict,
    source_lang: str,
    target_lang: str,
    input_path: str,
    sources: List[SourceItem],
    split_size: int,
    output_parts: List[PartFileInfo]
):
    """
    Creates a readable, complete text report of the translation-memory export.
    """
    now_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    total_in_mb = sum(s.size_bytes for s in sources) / (1024 * 1024)
    total_tus = stats["total_tus_seen"]
    unique_pairs = stats["extracted_pairs"]
    dup_removed = stats["duplicates_removed"]
    dup_pct = (dup_removed / (unique_pairs + dup_removed) * 100) if (unique_pairs + dup_removed) > 0 else 0.0

    lines = [
        "═" * 80,
        "          EU TRANSLATION MEMORY EXPORT REPORT (DGT-TM)",
        "═" * 80,
        "",
        "1. BASIC EXPORT DATA:",
        f"   • Date and time generated:       {now_str}",
        f"   • Tool:                          EU TMX Extractor v{VERSION}",
        f"   • Prepared by:                   {AUTHOR} (in {ENVIRONMENT}, {YEAR})",
        f"   • Licence:                       MIT License (see the LICENSE file or run with the --license flag)",
        f"   • Source tools:                  TMXtract.jar (European Commission - DGT / JRC, 2013)",
        f"                                    and tmxtract (Rodrigo Nepomuceno, 2019, MIT)",
        f"   • Language pair:                 {get_lang_display(source_lang)} ➔ {get_lang_display(target_lang)}",
        f"   • Source code (ISO / DGT):       {source_lang.upper()} (in TMX: {source_lang.lower()})",
        f"   • Target code (ISO / DGT):       {target_lang.upper()} (in TMX: {target_lang.lower()})",
        f"   • Operation duration:            {stats['elapsed_seconds']:.2f} s",
        "",
        "2. SOURCE RESOURCES:",
        f"   • Input path:                    {input_path}",
        f"   • Number of files processed:     {len(sources)} files (.tmx / .zip)",
        f"   • Total source data size:        {total_in_mb:.2f} MB",
        f"   • All TU units in the database:  {total_tus:,}",
        "",
        "3. QUALITY AND FILTERING STATISTICS:",
        f"   • Unique sentence pairs:         {unique_pairs:,}",
        f"   • Rejected duplicates:           {dup_removed:,} ({dup_pct:.1f}%)",
        f"   • Rejected identical segments:   {stats['identical_filtered']:,}",
        f"   • Rejected empty segments:       {stats['empty_filtered']:,}",
        f"   • Deduplication status:          {'ENABLED (clean memory without repetitions)' if stats.get('deduplicated', True) else 'DISABLED'}",
        "",
        "4. GENERATED OUTPUT FILES:",
        f"   • Size limit (splitting):        {'YES (max ' + str(split_size) + ' segments per file)' if split_size > 0 else 'NO (single file)'}",
        f"   • Number of files created:       {len(output_parts)}",
    ]

    for idx, p in enumerate(output_parts, 1):
        mb = p.size_bytes / (1024 * 1024)
        lines.append(f"     [{idx}] {os.path.basename(p.file_path)} (format: {p.format_name.upper()}, segments: {p.segments_count:,}, size: {mb:.2f} MB)")
        lines.append(f"         Path: {p.file_path}")

    if stats.get("sample_preview"):
        lines.extend([
            "",
            "5. SAMPLE EXTRACTED SEGMENTS (PREVIEW):"
        ])
        for s_idx, (doc, s_text, t_text) in enumerate(stats["sample_preview"], 1):
            doc_info = f" [CELEX document: {doc}]" if doc else ""
            lines.append(f"   --- Example #{s_idx}{doc_info} ---")
            lines.append(f"   [{source_lang.upper()}]: {s_text}")
            lines.append(f"   [{target_lang.upper()}]: {t_text}")

    lines.extend([
        "",
        "═" * 80,
        " The generated TMX files are 100% compliant with the TMX 1.4 standard.",
        " You can import them directly into: SDL Trados Studio, memoQ, OmegaT,",
        " Wordfast, CafeTran or a spreadsheet (in the case of TSV files).",
        "═" * 80
    ])

    report_text = "\n".join(lines)
    with open(report_file_path, "w", encoding="utf-8") as rf:
        rf.write(report_text)


# ==============================================================================
# 7. DOWNLOADING DGT-TM PACKAGES
# ==============================================================================

def download_dgt_volume(url: str, dest_folder: str) -> str:
    import urllib.request
    filename = url.split("/")[-1]
    dest_path = os.path.join(dest_folder, filename)
    os.makedirs(dest_folder, exist_ok=True)

    if os.path.exists(dest_path):
        UI.info(f"File '{filename}' already exists in: {dest_folder}. Using the existing file.")
        return dest_path

    UI.info(f"Starting download: {filename}")
    UI.info(f"Source: {url}")
    UI.info(f"Saving directly to: {dest_path}")

    def progress_callback(block_num, block_size, total_size):
        if total_size <= 0: return
        downloaded = block_num * block_size
        pct = min(1.0, downloaded / total_size)
        mb_down = downloaded / (1024 * 1024)
        mb_tot = total_size / (1024 * 1024)
        bar_len = 30
        filled = int(bar_len * pct)
        bar = "█" * filled + "░" * (bar_len - filled)
        sys.stdout.write(f"\r [{bar}] {pct*100:5.1f}% | {mb_down:6.1f} / {mb_tot:6.1f} MB ")
        sys.stdout.flush()

    try:
        urllib.request.urlretrieve(url, dest_path, reporthook=progress_callback)
        print()
        UI.success(f"Downloaded successfully to: {dest_path}")
        return dest_path
    except Exception as e:
        print()
        if os.path.exists(dest_path):
            os.remove(dest_path)
        raise RuntimeError(f"Error while downloading {url}: {e}")


def select_and_download_dgt_volume(dest_folder: str) -> Optional[str]:
    """
    Guides the user through choosing a year and volume from data.europa.eu.
    """
    UI.section("DOWNLOADING DGT-TM PACKAGES FROM THE EUROPEAN UNION PORTAL (data.europa.eu)")
    print(UI.c(" Source page: https://data.europa.eu/data/datasets/dgt-translation-memory?locale=en", UI.CYAN))
    print(UI.c(" The file will be downloaded directly to the program folder:", UI.BOLD))
    print(UI.c(f" 📂 {dest_folder}", UI.YELLOW))
    print()

    cat = fetch_live_catalog_if_possible()
    years = sorted(cat.keys(), reverse=True)
    if not years:
        cat = DGT_OFFICIAL_CATALOG
        years = sorted(cat.keys(), reverse=True)

    popular_years = ["2025", "2024", "2023", "2022", "2020", "2019", "2018"]
    menu_items = []
    for y in popular_years:
        if y in cat:
            count = len(cat[y])
            label = f"Year {y} ({count} {'parts' if count > 1 else 'part'})"
            if y == "2025":
                label += " [NEWEST EU LEGISLATION]"
            menu_items.append((y, label))

    other_count = sum(len(cat[y]) for y in cat if y not in popular_years)
    menu_items.append(("ALL", f"Older years (2004–2017 – {other_count} parts in total)"))
    menu_items.append(("CUSTOM", "Paste a direct Download URL from the data.europa.eu site"))

    for idx, (_, label) in enumerate(menu_items, 1):
        print(f" [{UI.c(str(idx), UI.CYAN)}] {label}")
    print(f" [{UI.c('0', UI.DIM)}] Back to the main menu")

    y_choice = UI.prompt("\nChoose the year to download (or 0 to go back)", default="1")
    if y_choice.strip() in ("0", "q", "exit", "powrot", "wroc", "back", "return"):
        return None

    chosen_code = None
    try:
        y_idx = int(y_choice) - 1
        if 0 <= y_idx < len(menu_items):
            chosen_code = menu_items[y_idx][0]
    except ValueError:
        chosen_code = y_choice.strip()

    if chosen_code == "CUSTOM":
        custom_url = UI.prompt("Paste the full Download URL (starting with http:// or https://)")
        if custom_url.startswith("http"):
            return download_dgt_volume(custom_url.strip(), dest_folder)
        else:
            UI.error("Invalid URL.")
            return None

    elif chosen_code == "ALL":
        UI.section("Older DGT-TM years (2004–2017):")
        other_years = [y for y in years if y not in popular_years]
        for idx, y in enumerate(other_years, 1):
            print(f" [{UI.c(str(idx), UI.CYAN)}] Year {y} ({len(cat[y])} parts)")
        print(f" [{UI.c('0', UI.DIM)}] Back")
        o_choice = UI.prompt("Choose the year number", default="1")
        if o_choice.strip() in ("0", "q", "exit", "wroc", "back", "return"):
            return None
        try:
            o_idx = int(o_choice) - 1
            selected_year = other_years[o_idx] if 0 <= o_idx < len(other_years) else other_years[0]
        except (ValueError, IndexError):
            selected_year = other_years[0]
    else:
        selected_year = chosen_code if chosen_code in cat else "2025"

    parts = cat.get(selected_year, [])
    if not parts:
        parts = cat.get("2025", [])
        selected_year = "2025"

    UI.section(f"Available parts for year {selected_year}:")
    for idx, (fn, url, title) in enumerate(parts, 1):
        title_str = f" – {title}" if title else ""
        print(f" [{UI.c(str(idx), UI.CYAN)}] {fn}{title_str}")
    print(f" [{UI.c('0', UI.DIM)}] Back")

    p_choice = UI.prompt(f"\nChoose the part number to download (1-{len(parts)}, or 0 to go back)", default="1")
    if p_choice.strip() in ("0", "q", "exit", "wroc", "back", "return"):
        return None

    try:
        p_idx = int(p_choice) - 1
        target_fn, target_url, _ = parts[p_idx] if 0 <= p_idx < len(parts) else parts[0]
    except (ValueError, IndexError):
        target_fn, target_url, _ = parts[0]

    return download_dgt_volume(target_url, dest_folder)


def find_local_data_sources() -> List[Tuple[str, str]]:
    """
    Automatically searches the following locations for .zip files and
    folders containing .tmx files:
    1. The program folder (script_dir)
    2. The current working directory (cwd)
    3. The dgt_downloads subfolder
    4. The parent directory (..)
    5. The user's home Pobrane / Downloads folder
    """
    candidates = []
    seen_paths = set()
    seen_names = set()

    script_dir = os.path.dirname(os.path.abspath(__file__))
    cwd = os.getcwd()

    dirs_to_scan = []
    for d in [script_dir, cwd]:
        if d and d not in dirs_to_scan and os.path.exists(d):
            dirs_to_scan.append(d)

    for base in [script_dir, cwd]:
        d_sub = os.path.join(base, "dgt_downloads")
        if os.path.isdir(d_sub) and d_sub not in dirs_to_scan:
            dirs_to_scan.append(d_sub)

    parent_dir = os.path.dirname(script_dir)
    if parent_dir and parent_dir not in dirs_to_scan and os.path.exists(parent_dir):
        dirs_to_scan.append(parent_dir)

    user_home = os.path.expanduser("~")
    user_dl_dirs = []
    for dl_name in ["Downloads", "Pobrane"]:
        dl_path = os.path.join(user_home, dl_name)
        if os.path.isdir(dl_path) and dl_path not in dirs_to_scan:
            dirs_to_scan.append(dl_path)
            user_dl_dirs.append(dl_path)

    for scan_dir in dirs_to_scan:
        try:
            entries = sorted(os.listdir(scan_dir))
        except OSError:
            continue

        is_user_dl = scan_dir in user_dl_dirs

        for item in entries:
            full = os.path.join(scan_dir, item)
            if full in seen_paths or item in seen_names:
                continue

            # In the Pobrane folder only archives that look like DGT / Euramis resources are checked
            if is_user_dl and not (item.lower().startswith("vol_") or item.lower().startswith("dgt")):
                continue

            if item.lower().endswith("extractor.zip") or item.lower().startswith("eu_tmx_extractor"):
                if item.lower().endswith(".zip"):
                    continue

            if os.path.isfile(full) and item.lower().endswith(".zip"):
                try:
                    with zipfile.ZipFile(full, "r") as z_chk:
                        if not any(n.lower().endswith(".tmx") for n in z_chk.namelist()):
                            continue
                except Exception:
                    continue

                seen_paths.add(full)
                seen_names.add(item)
                size_mb = os.path.getsize(full) / (1024 * 1024)
                if scan_dir == script_dir:
                    rel_loc = " (in the program folder)"
                elif is_user_dl:
                    rel_loc = " (in your Pobrane / Downloads folder)"
                elif scan_dir == parent_dir:
                    rel_loc = " (in the parent folder)"
                else:
                    rel_loc = f" (in {os.path.basename(scan_dir)})"
                candidates.append((full, f"ZIP archive: {item} (~{size_mb:.1f} MB){rel_loc}"))

            elif os.path.isdir(full) and not item.startswith(".") and item not in ("__pycache__", "dgt_downloads"):
                tmx_count = len(glob.glob(os.path.join(full, "*.tmx")))
                if tmx_count > 0:
                    seen_paths.add(full)
                    seen_names.add(item)
                    rel_loc = " (in the program folder)" if scan_dir == script_dir else f" (in {os.path.basename(scan_dir)})"
                    candidates.append((full, f"TMX folder: {item} ({tmx_count} .tmx files){rel_loc}"))

    return candidates


# ==============================================================================
# 8. MAIN EXECUTION PROCEDURE
# ==============================================================================

def run_extraction(
    input_path: str,
    source_lang: str,
    target_lang: str,
    output_path: str,
    output_format: str = "tmx",
    deduplicate: bool = True,
    filter_identical: bool = True,
    max_translations: int = 0,
    split_size: int = 0,
    quiet: bool = False
) -> Dict:
    t_start = time.time()
    
    # 1. Locate the sources
    if not quiet:
        UI.info(f"Searching for files in: {input_path} ...")
    sources = discover_sources(input_path)
    if not sources:
        raise ValueError(f"No .tmx files or .zip archives found in: {input_path}")

    total_bytes = sum(s.size_bytes for s in sources)
    if not quiet:
        UI.success(f"Found {len(sources)} TMX files (about ~{total_bytes / (1024*1024):.1f} MB)")

    # 2. Prepare the writers with splitting and file-name sequencing
    writers: List[ChunkedWriter] = []
    base_out = os.path.splitext(output_path)[0]
    fmt_lower = output_format.lower()

    if fmt_lower in ("tmx", "all"):
        writers.append(ChunkedWriter(base_out, "tmx", source_lang, target_lang, split_size=split_size))
    if fmt_lower in ("tsv", "excel", "all"):
        writers.append(ChunkedWriter(base_out, "tsv", source_lang, target_lang, split_size=split_size))
    if fmt_lower in ("jsonl", "all"):
        writers.append(ChunkedWriter(base_out, "jsonl", source_lang, target_lang, split_size=split_size))

    if not writers:
        writers.append(ChunkedWriter(base_out, "tmx", source_lang, target_lang, split_size=split_size))

    multi_writer = MultiFormatWriter(writers)

    # 3. Prepare the extractor
    extractor = TMXExtractor(
        source_lang=source_lang,
        target_lang=target_lang,
        deduplicate=deduplicate,
        filter_identical=filter_identical,
        max_translations=max_translations
    )

    sample_preview: List[Tuple[str, str, str]] = []
    total_files = len(sources)

    if not quiet:
        split_desc = f", splitting: every {split_size:,} segments" if split_size > 0 else ", no splitting"
        UI.info(f"Starting extraction: {get_lang_display(source_lang)} ➔ {get_lang_display(target_lang)}{split_desc}")

    # 4. Extraction loop
    try:
        for idx, src_item in enumerate(sources, start=1):
            z_ref, stream = src_item.open_stream()
            try:
                for pair in extractor.parse_stream(stream):
                    multi_writer.write(pair)
                    if len(sample_preview) < 4:
                        sample_preview.append((pair.doc_id, pair.source, pair.target))

                    if max_translations > 0 and extractor.total_pairs_matched >= max_translations:
                        break
            finally:
                if stream:
                    stream.close()
                if z_ref:
                    z_ref.close()

            if not quiet:
                elapsed = time.time() - t_start
                speed = (extractor.total_pairs_matched / elapsed) if elapsed > 0 else 0
                UI.render_progress(idx, total_files, extractor.total_pairs_matched, speed)

            if max_translations > 0 and extractor.total_pairs_matched >= max_translations:
                if not quiet:
                    print()
                    UI.info(f"The requested limit of {max_translations} pairs has been reached.")
                break

    finally:
        multi_writer.close()
        if not quiet and sys.stdout.isatty():
            print()

    total_time = time.time() - t_start
    output_parts = multi_writer.get_all_parts()

    stats = {
        "files_processed": total_files,
        "total_tus_seen": extractor.total_tus_seen,
        "extracted_pairs": extractor.total_pairs_matched,
        "duplicates_removed": extractor.duplicates_removed,
        "identical_filtered": extractor.identical_filtered,
        "empty_filtered": extractor.empty_filtered,
        "deduplicated": deduplicate,
        "elapsed_seconds": total_time,
        "sample_preview": sample_preview,
        "output_parts": output_parts,
        "output_files": [p.file_path for p in output_parts]
    }

    # 5. Generate the automatic summary report
    report_path = f"{base_out}_raport.txt"
    generate_export_report(
        report_file_path=report_path,
        stats=stats,
        source_lang=source_lang,
        target_lang=target_lang,
        input_path=input_path,
        sources=sources,
        split_size=split_size,
        output_parts=output_parts
    )
    stats["report_path"] = report_path

    return stats


# ==============================================================================
# 9. INTERACTIVE WIZARD FOR NON-TECHNICAL USERS (WIZARD)
# ==============================================================================

def run_interactive_wizard():
    UI.header("EU TRANSLATION MEMORY EXTRACTOR (DGT-TM) v2.1")
    print(UI.c(" ──────────────────────────────────────────────────────────────────", UI.DIM))
    print(f" {UI.c('Author:', UI.BOLD)}       {AUTHOR} (in {ENVIRONMENT}, {YEAR})")
    print(f" {UI.c('Licence:', UI.BOLD)}   MIT License " + UI.c("(type 'L' to read it)", UI.DIM))
    print(f" {UI.c('Base tools:', UI.BOLD)}")
    print(f"   • TMXtract.jar – European Commission (DGT / JRC, 2013)")
    print(f"   • tmxtract – Rodrigo Nepomuceno (github.com/Nepomuceno/tmxtract, 2019, MIT)")
    print(UI.c(" ──────────────────────────────────────────────────────────────────", UI.DIM))
    print()
    print(UI.c(" Welcome! This program lets you easily extract ready-made", UI.WHITE))
    print(UI.c(" translation memories (sentence bases) from official EU resources.", UI.WHITE))
    print(UI.c(" The TMX files can be imported directly into Trados, memoQ,", UI.DIM))
    print(UI.c(" OmegaT or opened in Excel without any commands.", UI.DIM))

    # --- STEP 1: DATA SOURCE ---
    UI.section("STEP 1 of 5: Where are your source data?")
    script_dir = os.path.dirname(os.path.abspath(__file__))
    cwd = os.getcwd()
    out_dir = script_dir if os.access(script_dir, os.W_OK) else cwd
    local_candidates = find_local_data_sources()

    if local_candidates:
        print(UI.c(" Data files were found in your folder and nearby locations:", UI.GREEN))
    else:
        print(UI.c(" 💡 TIP: Save downloaded .zip files directly in the program folder:", UI.YELLOW))
        print(UI.c(f"    📂 {script_dir}", UI.BOLD))

    while True:
        menu_idx = 1
        options_map = {}
        for path, label in local_candidates:
            print(f" [{UI.c(str(menu_idx), UI.CYAN)}] {label}")
            options_map[str(menu_idx)] = ("local", path)
            menu_idx += 1

        print(f" [{UI.c(str(menu_idx), UI.CYAN)}] Specify your own path to a directory or a .zip / .tmx file")
        options_map[str(menu_idx)] = ("custom", None)
        menu_idx += 1

        print(f" [{UI.c(str(menu_idx), UI.CYAN)}] Download an official DGT-TM package from the internet (data.europa.eu)")
        options_map[str(menu_idx)] = ("download", None)

        print(f" [{UI.c('L', UI.MAGENTA)}] Read the full MIT licence and author information")

        def_choice = "1" if local_candidates else str(menu_idx - 1)
        choice = UI.prompt(f"\nChoose an option number (or 'L' for the licence)", default=def_choice)
        if choice.strip().upper() in ("L", "LICENCJA", "LICENSE"):
            show_license()
            UI.section("STEP 1 of 5: Where are your source data?")
            continue
        break

    selected_type, selected_val = options_map.get(choice, ("custom", None))

    input_path = ""
    if selected_type == "local":
        input_path = selected_val
    elif selected_type == "download":
        dest_folder = script_dir if os.access(script_dir, os.W_OK) else os.getcwd()
        input_path = select_and_download_dgt_volume(dest_folder)
        if not input_path:
            UI.error("No file was downloaded. Cancelled.")
            return
    else:
        while True:
            path_in = UI.prompt("Enter the full path to the file or directory")
            if os.path.exists(path_in):
                input_path = path_in
                break
            UI.error(f"The path '{path_in}' does not exist. Try again.")

    UI.success(f"Selected source: {input_path}")

    # --- STEP 2: CHOOSING THE LANGUAGE PAIR ---
    UI.section("STEP 2 of 5: In which language pair do you want to extract the memory?")
    for i, (s, t, label) in enumerate(POPULAR_PAIRS, 1):
        print(f" [{UI.c(str(i), UI.CYAN)}] {label}")
    print(f" [{UI.c(str(len(POPULAR_PAIRS) + 1), UI.CYAN)}] Enter a different language pair (e.g. 'cs sk' or 'czech slovak')")

    p_choice = UI.prompt("\nChoose the pair number", default="1")
    src_lang, trg_lang = "EN", "PL"

    try:
        idx = int(p_choice) - 1
        if 0 <= idx < len(POPULAR_PAIRS):
            src_lang, trg_lang = POPULAR_PAIRS[idx][0], POPULAR_PAIRS[idx][1]
        else:
            custom_s = UI.prompt("Enter the source language (e.g. EN, DE, polish)")
            custom_t = UI.prompt("Enter the target language (e.g. PL, FR, english)")
            src_lang = resolve_language_code(custom_s) or custom_s.upper()
            trg_lang = resolve_language_code(custom_t) or custom_t.upper()
    except ValueError:
        parts = p_choice.replace("-", " ").replace(">", " ").split()
        if len(parts) >= 2:
            src_lang = resolve_language_code(parts[0]) or parts[0].upper()
            trg_lang = resolve_language_code(parts[1]) or parts[1].upper()

    UI.success(f"Language pair: {get_lang_display(src_lang)} ➔ {get_lang_display(trg_lang)}")

    # --- STEP 3: SIZE LIMITS / SPLITTING FOR CAT TOOLS ---
    UI.section("STEP 3 of 5: RAM and CAT tool safety (Trados, memoQ)")
    print(UI.c(" Very large TMX files (over 100,000 sentences) can freeze Trados or memoQ.", UI.DIM))
    print(UI.c(" Splitting into smaller parts (part01, part02, ...) guarantees a stable import.", UI.DIM))
    print(f" [{UI.c('1', UI.CYAN)}] Split every 50,000 segments [Recommended: Trados, memoQ, OmegaT]")
    print(f" [{UI.c('2', UI.CYAN)}] Split every 100,000 segments (for more powerful computers)")
    print(f" [{UI.c('3', UI.CYAN)}] Enter a custom number of segments per file")
    print(f" [{UI.c('4', UI.CYAN)}] No splitting – save everything in one large file")

    split_choice = UI.prompt("\nChoose a splitting option", default="1")
    split_size = 50000
    if split_choice == "1":
        split_size = 50000
    elif split_choice == "2":
        split_size = 100000
    elif split_choice == "3":
        custom_limit = UI.prompt("Enter the segment limit per file (e.g. 30000)", default="50000")
        split_size = int(custom_limit) if custom_limit.isdigit() else 50000
    elif split_choice == "4":
        split_size = 0

    if split_size > 0:
        UI.success(f"Splitting active: at most {split_size:,} segments per file (sequence: _part01, _part02...)")
    else:
        UI.info("Splitting disabled: a single file will be created.")

    # --- STEP 4: OUTPUT FORMAT AND FILE NAME ---
    UI.section("STEP 4 of 5: Which output file format do you prefer?")
    print(f" [{UI.c('1', UI.CYAN)}] TMX (.tmx) – Standard translation memory (Trados, memoQ, OmegaT) [Recommended]")
    print(f" [{UI.c('2', UI.CYAN)}] Excel / TSV (.tsv) – Ready-made spreadsheet for immediate reading")
    print(f" [{UI.c('3', UI.CYAN)}] TMX + Excel/TSV (both formats at once)")
    print(f" [{UI.c('4', UI.CYAN)}] JSONL (.jsonl) – For training / fine-tuning AI models")
    print(f" [{UI.c('5', UI.CYAN)}] All formats at once (.tmx, .tsv, .jsonl)")

    f_choice = UI.prompt("\nChoose a format", default="1")
    format_map = {"1": "tmx", "2": "tsv", "3": "all", "4": "jsonl", "5": "all"}
    out_format = format_map.get(f_choice, "tmx")

    default_name = f"dgt_{src_lang.lower()}_{trg_lang.lower()}.tmx"
    out_name = UI.prompt("Base name of the output file", default=default_name)
    if os.path.isabs(out_name):
        out_path = out_name
    else:
        out_path = os.path.join(out_dir, out_name)

    # --- STEP 5: QUALITY AND FILTERING ---
    UI.section("STEP 5 of 5: Data quality options:")
    do_dedup = UI.prompt_yes_no("Remove duplicates (deduplication of identical sentences)?", default=True)
    filter_ident = UI.prompt_yes_no("Skip segments that are identical in both languages (e.g. plain numbers)?", default=True)
    limit_ans = UI.prompt("Maximum total number of sentence pairs [Enter = NO LIMIT]", default="")
    max_count = int(limit_ans) if limit_ans.isdigit() else 0

    # --- SUMMARY AND CONFIRMATION ---
    print()
    UI.header("JOB SUMMARY")
    print(f"  • Data source:       {UI.c(input_path, UI.BOLD)}")
    print(f"  • Language pair:     {UI.c(get_lang_display(src_lang), UI.GREEN)} ➔ {UI.c(get_lang_display(trg_lang), UI.GREEN)}")
    print(f"  • Output format:     {UI.c(out_format.upper(), UI.CYAN)}")
    print(f"  • Output file:       {UI.c(out_path, UI.BOLD)}")
    print(f"  • Splitting:         {UI.c(f'YES (every {split_size:,} segments)' if split_size > 0 else 'NO', UI.YELLOW)}")
    print(f"  • Deduplication:     {'YES (clean data)' if do_dedup else 'NO'}")
    print()

    if not UI.prompt_yes_no("Start the extraction?", default=True):
        print("Cancelled by the user.")
        return

    # --- START OF WORK ---
    print()
    stats = run_extraction(
        input_path=input_path,
        source_lang=src_lang,
        target_lang=trg_lang,
        output_path=out_path,
        output_format=out_format,
        deduplicate=do_dedup,
        filter_identical=filter_ident,
        max_translations=max_count,
        split_size=split_size,
        quiet=False
    )

    # --- FINAL REPORT ---
    UI.header("EXTRACTION RESULTS AND REPORT")
    pairs_cnt = stats['extracted_pairs']
    UI.success(f"Processing time:         {stats['elapsed_seconds']:.2f} s")
    UI.success(f"Files processed:         {stats['files_processed']}")
    UI.success(f"Segments scanned:        {stats['total_tus_seen']:,}")
    UI.success(f"Unique pairs extracted:  {UI.c(f' {pairs_cnt:,}', UI.BOLD + UI.GREEN)}")
    if do_dedup:
        UI.info(f"Duplicates rejected:      {stats['duplicates_removed']:,}")
    if filter_ident:
        UI.info(f"Identical rejected:       {stats['identical_filtered']:,}")

    print("\n" + UI.c("Memory files created:", UI.BOLD))
    for p in stats["output_parts"]:
        mb = p.size_bytes / (1024 * 1024)
        print(f"  📁 {UI.c(p.file_path, UI.CYAN)} ({p.segments_count:,} segments, {mb:.2f} MB)")

    print(f"\n  📄 {UI.c('Summary report:', UI.BOLD)} {UI.c(stats['report_path'], UI.YELLOW)}")

    # Preview of sample sentences
    if stats["sample_preview"]:
        UI.section("Preview of the first extracted segments:")
        for idx, (doc, s, t) in enumerate(stats["sample_preview"][:3], 1):
            doc_str = f" [Document: {doc}]" if doc else ""
            print(f"\n {UI.c(f'Example #{idx}{doc_str}:', UI.YELLOW)}")
            print(f"   {UI.c(src_lang + ':', UI.BOLD)} {s}")
            print(f"   {UI.c(trg_lang + ':', UI.GREEN)} {t}")

    print("\n" + UI.c("Done! You can now load the file into your CAT tool or Excel. 🎉", UI.BOLD + UI.GREEN))
    print()
    UI.prompt("Press Enter to exit the program", default="")


# ==============================================================================
# 10. COMMAND-LINE MODE (CLI FOR ADVANCED USERS)
# ==============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="EU TMX Extractor v2.1 – A fast tool for extracting TMX memories from EU resources (DGT-TM).",
        formatter_class=argparse.RawTextHelpFormatter,
        epilog="""Usage examples:
  1. Wizard mode (step-by-step assistant):
     python3 tmx_extractor.py

  2. Extraction with splitting every 50,000 segments (for Trados/memoQ stability):
     python3 tmx_extractor.py -i Vol_2009_4 -s EN -t PL -o mem_en_pl.tmx --split 50000

  3. Extraction directly from a ZIP archive to the Excel/TSV format:
     python3 tmx_extractor.py -i Vol_2018_1.zip -s DE -t PL -o result.tsv --format tsv

  4. Downloading an official DGT-TM package and extracting immediately:
     python3 tmx_extractor.py --download Vol_2018_1 -s EN -t PL -o dgt_en_pl.tmx
"""
    )

    parser.add_argument("-i", "--input", help="Path to a folder with .tmx files, a single .tmx file or a .zip archive")
    parser.add_argument("-s", "--source", help="Source language (e.g. EN, pl, de, polish)")
    parser.add_argument("-t", "--target", help="Target language (e.g. PL, en, fr, english)")
    parser.add_argument("-o", "--output", help="Output file name or path (e.g. result.tmx)")
    parser.add_argument(
        "--format",
        choices=["tmx", "tsv", "jsonl", "all"],
        default="tmx",
        help="Output format: tmx (CAT), tsv (Excel), jsonl (AI) or all"
    )
    parser.add_argument(
        "--split",
        type=int,
        default=0,
        help="Splitting into smaller files: maximum number of segments in one file (e.g. 50000 for CAT)"
    )
    parser.add_argument("--no-dedup", action="store_true", help="Disable removal of duplicate sentence pairs")
    parser.add_argument("--no-filter-identical", action="store_true", help="Do not skip segments that are identical in both languages")
    parser.add_argument("--max", type=int, default=0, help="Maximum total number of pairs to extract (0 = no limit)")
    parser.add_argument("--download", help="Download the given volume from the EU portal (e.g. Vol_2018_1, Vol_2018_2, etc.)")
    parser.add_argument("--wizard", "-w", action="store_true", help="Force running the interactive wizard")
    parser.add_argument("--license", "--licencja", action="store_true", help="Display the full text of the MIT licence and copyright information")
    parser.add_argument("-q", "--quiet", action="store_true", help="Quiet mode (useful in scripts/pipelines)")

    args = parser.parse_args()

    if args.license:
        print(MIT_LICENSE_TEXT)
        return

    if len(sys.argv) == 1 or args.wizard:
        try:
            run_interactive_wizard()
        except KeyboardInterrupt:
            print("\nInterrupted by the user.")
        except Exception as err:
            UI.error(f"\nAn error occurred while the program was running: {err}")
            import traceback
            traceback.print_exc()
            UI.prompt("\nPress Enter to close this window...", default="")
        return

    input_source = args.input
    if args.download:
        vol_key = args.download.strip().lower()
        script_dir = os.path.dirname(os.path.abspath(__file__))
        dest_folder = script_dir if os.access(script_dir, os.W_OK) else os.getcwd()
        matched_url = None
        flat = get_flat_catalog()
        for v_name, v_url, _ in flat:
            if vol_key in v_name.lower() or vol_key in v_url.lower():
                matched_url = v_url
                break
        if not matched_url:
            matched_url = flat[0][1]
        input_source = download_dgt_volume(matched_url, dest_folder)

    if not input_source:
        UI.error("You must provide the input path via -i / --input or use --download.")
        sys.exit(1)

    if not args.source or not args.target:
        UI.error("You must provide the source (-s) and target (-t) language, e.g. -s EN -t PL.")
        sys.exit(1)

    resolved_s = resolve_language_code(args.source) or args.source.upper()
    resolved_t = resolve_language_code(args.target) or args.target.upper()

    out_file = args.output
    if not out_file:
        out_file = f"dgt_{resolved_s.lower()}_{resolved_t.lower()}.{args.format if args.format != 'all' else 'tmx'}"

    try:
        stats = run_extraction(
            input_path=input_source,
            source_lang=resolved_s,
            target_lang=resolved_t,
            output_path=out_file,
            output_format=args.format,
            deduplicate=not args.no_dedup,
            filter_identical=not args.no_filter_identical,
            max_translations=args.max,
            split_size=args.split,
            quiet=args.quiet
        )
        if not args.quiet:
            UI.success(f"Finished! Saved {stats['extracted_pairs']:,} unique pairs.")
            UI.info(f"Export report: {stats['report_path']}")
    except Exception as err:
        UI.error(f"An error occurred during extraction: {err}")
        sys.exit(1)


if __name__ == "__main__":
    main()
