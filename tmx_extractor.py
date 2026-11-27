#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
EU TMX Extractor (DGT-TM / JRC-Acquis / Euramis) - Version 2.5
=============================================================
Author: Michał Kornacki, PhD, University of Łódź
ORCID:  https://orcid.org/0000-0002-0694-004X
Environment: Antigravity (2026)
License: MIT License

This program was developed based on:
  - TMXtract.jar – official European Commission tool (DGT / JRC, 2013)
  - tmxtract – open-source tool by Rodrigo Nepomuceno (2019, MIT)
    (https://github.com/Nepomuceno/tmxtract)

A high-performance Python utility for clean, fast, and transparent extraction
of translation memories (TMX) in any selected EU language pair from official
European Union open datasets.
"""

import sys
import os
import re
import io
import math
import time
import glob
import json
import zipfile
import shutil
import argparse
from collections import Counter
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Iterator, Set, Any, Union
from xml.sax.saxutils import escape as xml_escape
import xml.etree.ElementTree as ET


# ==============================================================================
# PROJECT METADATA AND MIT LICENSE
# ==============================================================================

AUTHOR = "Michał Kornacki, PhD, University of Łódź"
ORCID = "https://orcid.org/0000-0002-0694-004X"
ENVIRONMENT = "Antigravity"
YEAR = "2026"
VERSION = "2.5"

BASE_TOOLS_INFO = (
    "• TMXtract.jar – European Commission (DGT / JRC, 2013)\n"
    "• tmxtract – Rodrigo Nepomuceno (https://github.com/Nepomuceno/tmxtract, 2019, MIT)"
)

MIT_LICENSE_TEXT = """MIT License

Copyright (c) 2026 Michał Kornacki, PhD, University of Łódź
ORCID: https://orcid.org/0000-0002-0694-004X

Developed in Antigravity (2026). This software is built upon and inspired by:
  - TMXtract.jar (Copyright (c) 2013 European Commission - DGT / JRC)
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
    """Displays the full text of the MIT License."""
    UI.header("MIT LICENSE & AUTHOR INFORMATION")
    print(UI.c(MIT_LICENSE_TEXT, UI.WHITE))
    print()
    UI.prompt("Press Enter to return to the program", default="")



# ==============================================================================
# 1. EUROPEAN UNION LANGUAGE DATABASE AND NORMALIZATION
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
    ("EN", "PL", "English -> Polish (EN -> PL) [Most popular]"),
    ("PL", "EN", "Polish -> English (PL -> EN)"),
    ("DE", "EN", "German -> English (DE -> EN)"),
    ("EN", "DE", "English -> German (EN -> DE)"),
    ("FR", "EN", "French -> English (FR -> EN)"),
    ("ES", "EN", "Spanish -> English (ES -> EN)"),
    ("DE", "PL", "German -> Polish (DE -> PL)"),
    ("PL", "DE", "Polish -> German (PL -> DE)"),
    ("FR", "PL", "French -> Polish (FR -> PL)"),
    ("ES", "PL", "Spanish -> Polish (ES -> PL)"),
    ("IT", "PL", "Italian -> Polish (IT -> PL)"),
]

DGT_OFFICIAL_CATALOG = {
    "2025": [
        ("Vol_2025.new_1.zip", "https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/DGT-TM/Resources/DGT-TM-2025/Vol_2025.new_1.zip", "New volume 2025 part 1/5"),
        ("Vol_2025.new_2.zip", "https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/DGT-TM/Resources/DGT-TM-2025/Vol_2025.new_2.zip", "New volume 2025 part 2/5"),
        ("Vol_2025.new_3.zip", "https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/DGT-TM/Resources/DGT-TM-2025/Vol_2025.new_3.zip", "New volume 2025 part 3/5"),
        ("Vol_2025.new_4.zip", "https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/DGT-TM/Resources/DGT-TM-2025/Vol_2025.new_4.zip", "New volume 2025 part 4/5"),
        ("Vol_2025.new_5.zip", "https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/DGT-TM/Resources/DGT-TM-2025/Vol_2025.new_5.zip", "New volume 2025 part 5/5"),
    ],
    "2024": [
        ("Vol_2024.new_1.zip", "https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/DGT-TM/Resources/DGT-TM-2024/Vol_2024.new_1.zip", "Volume 2024 part 1/3"),
        ("Vol_2024.new_2.zip", "https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/DGT-TM/Resources/DGT-TM-2024/Vol_2024.new_2.zip", "Volume 2024 part 2/3"),
        ("Vol_2024.new_3.zip", "https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/DGT-TM/Resources/DGT-TM-2024/Vol_2024.new_3.zip", "Volume 2024 part 3/3"),
    ],
    "2023": [
        ("Vol_2023.new_1.zip", "https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/DGT-TM/Resources/DGT-TM-2023/Vol_2023.new_1.zip", "Volume 2023 part 1/3"),
        ("Vol_2023.new_2.zip", "https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/DGT-TM/Resources/DGT-TM-2023/Vol_2023.new_2.zip", "Volume 2023 part 2/3"),
        ("Vol_2023.new_3.zip", "https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/DGT-TM/Resources/DGT-TM-2023/Vol_2023.new_3.zip", "Volume 2023 part 3/3"),
    ],
    "2022": [
        ("Vol_2022.new_1.zip", "https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/DGT-TM/Resources/DGT-TM-2022/Vol_2022.new_1.zip", "Volume 2022 part 1/3"),
        ("Vol_2022.new_2.zip", "https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/DGT-TM/Resources/DGT-TM-2022/Vol_2022.new_2.zip", "Volume 2022 part 2/3"),
        ("Vol_2022.new_3.zip", "https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/DGT-TM/Resources/DGT-TM-2022/Vol_2022.new_3.zip", "Volume 2022 part 3/3"),
    ],
    "2021": [
        ("Vol_2021.new_1.zip", "https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/DGT-TM/Resources/DGT-TM-2021/Vol_2021.new_1.zip", "Volume 2021 part 1/3"),
        ("Vol_2021.new_2.zip", "https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/DGT-TM/Resources/DGT-TM-2021/Vol_2021.new_2.zip", "Volume 2021 part 2/3"),
        ("Vol_2021.new_3.zip", "https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/DGT-TM/Resources/DGT-TM-2021/Vol_2021.new_3.zip", "Volume 2021 part 3/3"),
    ],
    "2020": [
        ("Vol_2020.new_1.zip", "https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/DGT-TM/Resources/DGT-TM-2020/Vol_2020.new_1.zip", "Volume 2020 part 1/4"),
        ("Vol_2020.new_2.zip", "https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/DGT-TM/Resources/DGT-TM-2020/Vol_2020.new_2.zip", "Volume 2020 part 2/4"),
        ("Vol_2020.new_3.zip", "https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/DGT-TM/Resources/DGT-TM-2020/Vol_2020.new_3.zip", "Volume 2020 part 3/4"),
        ("Vol_2020.new_4.zip", "https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/DGT-TM/Resources/DGT-TM-2020/Vol_2020.new_4.zip", "Volume 2020 part 4/4"),
    ],
    "2019": [
        ("Vol_2019_1.zip", "https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/DGT-TM/Resources/DGT-TM-2019/Vol_2019_1.zip", "Volume 2019 part 1/4"),
        ("Vol_2019_2.zip", "https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/DGT-TM/Resources/DGT-TM-2019/Vol_2019_2.zip", "Volume 2019 part 2/4"),
        ("Vol_2019_3.zip", "https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/DGT-TM/Resources/DGT-TM-2019/Vol_2019_3.zip", "Volume 2019 part 3/4"),
        ("Vol_2019_4.zip", "https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/DGT-TM/Resources/DGT-TM-2019/Vol_2019_4.zip", "Volume 2019 part 4/4"),
    ],
    "2018": [
        ("Vol_2018_1.zip", "https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/DGT-TM/Resources/DGT-TM-2018/Vol_2018_1.zip", "Volume 2018 part 1/4"),
        ("Vol_2018_2.zip", "https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/DGT-TM/Resources/DGT-TM-2018/Vol_2018_2.zip", "Volume 2018 part 2/4"),
        ("Vol_2018_3.zip", "https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/DGT-TM/Resources/DGT-TM-2018/Vol_2018_3.zip", "Volume 2018 part 3/4"),
        ("Vol_2018_4.zip", "https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/DGT-TM/Resources/DGT-TM-2018/Vol_2018_4.zip", "Volume 2018 part 4/4"),
    ],
    "2017": [
        ("Vol_2017_1.zip", "https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/DGT-TM/Resources/DGT-TM-2017/Vol_2017_1.zip", "Volume 2017 part 1/4"),
        ("Vol_2017_2.zip", "https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/DGT-TM/Resources/DGT-TM-2017/Vol_2017_2.zip", "Volume 2017 part 2/4"),
        ("Vol_2017_3.zip", "https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/DGT-TM/Resources/DGT-TM-2017/Vol_2017_3.zip", "Volume 2017 part 3/4"),
        ("Vol_2017_4.zip", "https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/DGT-TM/Resources/DGT-TM-2017/Vol_2017_4.zip", "Volume 2017 part 4/4"),
    ],
    "2016": [
        ("Vol_2016_1.zip", "https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/DGT-TM/Resources/DGT-TM-2016/Vol_2016_1.zip", "Volume 2016 part 1/4"),
        ("Vol_2016_2.zip", "https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/DGT-TM/Resources/DGT-TM-2016/Vol_2016_2.zip", "Volume 2016 part 2/4"),
        ("Vol_2016_3.zip", "https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/DGT-TM/Resources/DGT-TM-2016/Vol_2016_3.zip", "Volume 2016 part 3/4"),
        ("Vol_2016_4.zip", "https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/DGT-TM/Resources/DGT-TM-2016/Vol_2016_4.zip", "Volume 2016 part 4/4"),
    ],
    "2015": [
        ("Vol_2015_1.zip", "https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/DGT-TM/Resources/DGT-TM-2015/Vol_2015_1.zip", "Volume 2015 part 1/4"),
        ("Vol_2015_2.zip", "https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/DGT-TM/Resources/DGT-TM-2015/Vol_2015_2.zip", "Volume 2015 part 2/4"),
        ("Vol_2015_3.zip", "https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/DGT-TM/Resources/DGT-TM-2015/Vol_2015_3.zip", "Volume 2015 part 3/4"),
        ("Vol_2015_4.zip", "https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/DGT-TM/Resources/DGT-TM-2015/Vol_2015_4.zip", "Volume 2015 part 4/4"),
    ],
    "2014": [
        ("Vol_2014_1.zip", "https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/DGT-TM/Resources/DGT-TM-2014/Vol_2014_1.zip", "Volume 2014 part 1/4"),
        ("Vol_2014_2.zip", "https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/DGT-TM/Resources/DGT-TM-2014/Vol_2014_2.zip", "Volume 2014 part 2/4"),
        ("Vol_2014_3.zip", "https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/DGT-TM/Resources/DGT-TM-2014/Vol_2014_3.zip", "Volume 2014 part 3/4"),
        ("Vol_2014_4.zip", "https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/DGT-TM/Resources/DGT-TM-2014/Vol_2014_4.zip", "Volume 2014 part 4/4"),
    ],
    "2013": [
        ("Vol_2013_1.zip", "https://wt-public.emm4u.eu/Resources/DGT-TM-2013/Vol_2013_1.zip", "Volume 2013 part 1/4"),
        ("Vol_2013_2.zip", "https://wt-public.emm4u.eu/Resources/DGT-TM-2013/Vol_2013_2.zip", "Volume 2013 part 2/4"),
        ("Vol_2013_3.zip", "https://wt-public.emm4u.eu/Resources/DGT-TM-2013/Vol_2013_3.zip", "Volume 2013 part 3/4"),
        ("Vol_2013_4.zip", "https://wt-public.emm4u.eu/Resources/DGT-TM-2013/Vol_2013_4.zip", "Volume 2013 part 4/4"),
    ],
    "2012": [
        ("Vol_2012_1.zip", "https://wt-public.emm4u.eu/Resources/DGT-TM-2012/Vol_2012_1.zip", "Volume 2012 part 1/4"),
        ("Vol_2012_2.zip", "https://wt-public.emm4u.eu/Resources/DGT-TM-2012/Vol_2012_2.zip", "Volume 2012 part 2/4"),
        ("Vol_2012_3.zip", "https://wt-public.emm4u.eu/Resources/DGT-TM-2012/Vol_2012_3.zip", "Volume 2012 part 3/4"),
        ("Vol_2012_4.zip", "https://wt-public.emm4u.eu/Resources/DGT-TM-2012/Vol_2012_4.zip", "Volume 2012 part 4/4"),
    ],
    "2011": [
        ("Vol_2011_1.zip", "https://wt-public.emm4u.eu/Resources/DGT-TM-2011/Vol_2011_1.zip", "Volume 2011 part 1/4"),
        ("Vol_2011_2.zip", "https://wt-public.emm4u.eu/Resources/DGT-TM-2011/Vol_2011_2.zip", "Volume 2011 part 2/4"),
        ("Vol_2011_3.zip", "https://wt-public.emm4u.eu/Resources/DGT-TM-2011/Vol_2011_3.zip", "Volume 2011 part 3/4"),
        ("Vol_2011_4.zip", "https://wt-public.emm4u.eu/Resources/DGT-TM-2011/Vol_2011_4.zip", "Volume 2011 part 4/4"),
    ],
    "2010": [
        ("Vol_2010_1.zip", "https://wt-public.emm4u.eu/Resources/DGT-TM-2011/Vol_2010_1.zip", "Volume 2010 part 1/4"),
        ("Vol_2010_2.zip", "https://wt-public.emm4u.eu/Resources/DGT-TM-2011/Vol_2010_2.zip", "Volume 2010 part 2/4"),
        ("Vol_2010_3.zip", "https://wt-public.emm4u.eu/Resources/DGT-TM-2011/Vol_2010_3.zip", "Volume 2010 part 3/4"),
        ("Vol_2010_4.zip", "https://wt-public.emm4u.eu/Resources/DGT-TM-2011/Vol_2010_4.zip", "Volume 2010 part 4/4"),
    ],
    "2009": [
        ("Vol_2009_1.zip", "https://wt-public.emm4u.eu/Resources/DGT-TM-2011/Vol_2009_1.zip", "Volume 2009 part 1/4"),
        ("Vol_2009_2.zip", "https://wt-public.emm4u.eu/Resources/DGT-TM-2011/Vol_2009_2.zip", "Volume 2009 part 2/4"),
        ("Vol_2009_3.zip", "https://wt-public.emm4u.eu/Resources/DGT-TM-2011/Vol_2009_3.zip", "Volume 2009 part 3/4"),
        ("Vol_2009_4.zip", "https://wt-public.emm4u.eu/Resources/DGT-TM-2011/Vol_2009_4.zip", "Volume 2009 part 4/4"),
    ],
    "2008": [
        ("Vol_2008_1.zip", "https://wt-public.emm4u.eu/Resources/DGT-TM-2011/Vol_2008_1.zip", "Volume 2008 part 1/4"),
        ("Vol_2008_2.zip", "https://wt-public.emm4u.eu/Resources/DGT-TM-2011/Vol_2008_2.zip", "Volume 2008 part 2/4"),
        ("Vol_2008_3.zip", "https://wt-public.emm4u.eu/Resources/DGT-TM-2011/Vol_2008_3.zip", "Volume 2008 part 3/4"),
        ("Vol_2008_4.zip", "https://wt-public.emm4u.eu/Resources/DGT-TM-2011/Vol_2008_4.zip", "Volume 2008 part 4/4"),
    ],
    "2007": [
        ("Vol_2007_1.zip", "https://wt-public.emm4u.eu/Resources/DGT-TM-2011/Vol_2007_1.zip", "Volume 2007 part 1/3"),
        ("Vol_2007_2.zip", "https://wt-public.emm4u.eu/Resources/DGT-TM-2011/Vol_2007_2.zip", "Volume 2007 part 2/3"),
        ("Vol_2007_3.zip", "https://wt-public.emm4u.eu/Resources/DGT-TM-2011/Vol_2007_3.zip", "Volume 2007 part 3/3"),
    ],
    "2006": [
        ("Vol_2006_1.zip", "https://wt-public.emm4u.eu/Resources/DGT-TM-2011/Vol_2006_1.zip", "Volume 2006 part 1/5"),
        ("Vol_2006_2.zip", "https://wt-public.emm4u.eu/Resources/DGT-TM-2011/Vol_2006_2.zip", "Volume 2006 part 2/5"),
        ("Vol_2006_3.zip", "https://wt-public.emm4u.eu/Resources/DGT-TM-2011/Vol_2006_3.zip", "Volume 2006 part 3/5"),
        ("Vol_2006_4.zip", "https://wt-public.emm4u.eu/Resources/DGT-TM-2011/Vol_2006_4.zip", "Volume 2006 part 4/5"),
        ("Vol_2006_5.zip", "https://wt-public.emm4u.eu/Resources/DGT-TM-2011/Vol_2006_5.zip", "Volume 2006 part 5/5"),
    ],
    "2005": [
        ("Vol_2005_1.zip", "https://wt-public.emm4u.eu/Resources/DGT-TM-2011/Vol_2005_1.zip", "Volume 2005 part 1/3"),
        ("Vol_2005_2.zip", "https://wt-public.emm4u.eu/Resources/DGT-TM-2011/Vol_2005_2.zip", "Volume 2005 part 2/3"),
        ("Vol_2005_3.zip", "https://wt-public.emm4u.eu/Resources/DGT-TM-2011/Vol_2005_3.zip", "Volume 2005 part 3/3"),
    ],
    "2004": [
        ("Vol_2004_1.zip", "https://wt-public.emm4u.eu/Resources/DGT-TM-2011/Vol_2004_1.zip", "Volume 2004 part 1/2"),
        ("Vol_2004_2.zip", "https://wt-public.emm4u.eu/Resources/DGT-TM-2011/Vol_2004_2.zip", "Volume 2004 part 2/2"),
    ],
}


def fetch_live_catalog_if_possible():
    """
    Attempts to fetch the most up-to-date volume list from data.europa.eu API.
    Falls back immediately to the built-in DGT_OFFICIAL_CATALOG if offline.
    """
    try:
        import urllib.request, json, re
        url = "https://data.europa.eu/api/hub/search/datasets/dgt-translation-memory"
        req = urllib.request.Request(url, headers={"User-Agent": f"EU-TMX-Extractor/{VERSION}"})
        with urllib.request.urlopen(req, timeout=1.5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        dists = data.get("result", {}).get("distributions", [])
        cat = {}
        for d in dists:
            t_title = d.get("title", {}).get("en") or d.get("title", {}).get("pl") or ""
            for u in d.get("download_url", []):
                fn = u.split("/")[-1]
                m = re.search(r"Vol_(\d{4})", fn)
                y = m.group(1) if m else "Other"
                cat.setdefault(y, []).append((fn, u, t_title))
        if cat:
            for y in cat:
                cat[y].sort(key=lambda x: x[0])
            return cat
    except Exception:
        pass
    return DGT_OFFICIAL_CATALOG


def get_flat_catalog():
    """Returns a flat list of all official volumes (filename, url, description)."""
    res = []
    for y in sorted(DGT_OFFICIAL_CATALOG.keys(), reverse=True):
        res.extend(DGT_OFFICIAL_CATALOG[y])
    return res


def resolve_language_code(text: str) -> Optional[str]:
    """Matches user input to a 2-letter ISO code (e.g. 'PL', 'EN'). Accepts English and Polish names."""
    if not text:
        return None
    raw = text.strip()
    upper = raw.upper()
    two_letter = upper.split("-")[0]
    if two_letter in EU_LANGUAGES:
        return two_letter
    clean = raw.lower()
    for code, info in EU_LANGUAGES.items():
        if clean == info["en"].lower() or clean in info["en"].lower():
            return code
        if clean == info["pl"].lower() or clean in info["pl"].lower():
            return code
    if len(upper) == 2 and upper.isalpha():
        return upper
    return None


def get_lang_display(code: str) -> str:
    """Returns human-readable language string, e.g. 'PL (Polish)'."""
    upper = code.upper()
    if upper in EU_LANGUAGES:
        return f"{upper} ({EU_LANGUAGES[upper]['en']})"
    return upper


# ==============================================================================
# 2. CROSS-PLATFORM CONSOLE AND UI (WINDOWS / MACOS / LINUX)
# ==============================================================================

def init_console() -> bool:
    """
    Initializes console environment:
    1. Enforces UTF-8 encoding on sys.stdout, sys.stderr, sys.stdin (errors='replace').
    2. On Windows (cmd.exe / PowerShell), enables native ANSI VT processing via Win32 API.
    Returns True if ANSI color escapes are supported, False otherwise.
    """
    for stream in (sys.stdout, sys.stderr, sys.stdin):
        if hasattr(stream, "reconfigure"):
            try:
                stream.reconfigure(encoding="utf-8", errors="replace")
            except Exception:
                pass

    if os.environ.get("NO_COLOR"):
        return False

    if not sys.stdout.isatty():
        return False

    if sys.platform == "win32":
        try:
            import ctypes
            from ctypes import wintypes
            kernel32 = ctypes.windll.kernel32

            # STD_OUTPUT_HANDLE = -11
            h_out = kernel32.GetStdHandle(-11)
            if not h_out or h_out == wintypes.HANDLE(-1).value:
                return False

            mode = wintypes.DWORD()
            if not kernel32.GetConsoleMode(h_out, ctypes.byref(mode)):
                return False

            # ENABLE_VIRTUAL_TERMINAL_PROCESSING = 0x0004
            ENABLE_VT = 0x0004
            new_mode = mode.value | ENABLE_VT
            if kernel32.SetConsoleMode(h_out, new_mode):
                try:
                    h_err = kernel32.GetStdHandle(-12)
                    if h_err and h_err != wintypes.HANDLE(-1).value:
                        err_mode = wintypes.DWORD()
                        if kernel32.GetConsoleMode(h_err, ctypes.byref(err_mode)):
                            kernel32.SetConsoleMode(h_err, err_mode.value | ENABLE_VT)
                except Exception:
                    pass
                return True
            return False
        except Exception:
            return False

    term = os.environ.get("TERM", "")
    if term == "dumb":
        return False
    return True


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

    _ansi_re = re.compile(r'\033\[[0-9;]*[a-zA-Z]')
    _has_color: bool = init_console()

    @classmethod
    def strip_ansi(cls, text: str) -> str:
        """Strips all ANSI escape sequences from text."""
        return cls._ansi_re.sub('', str(text))

    @classmethod
    def c(cls, text: str, color: str) -> str:
        """Returns colored text if terminal supports it, clean plain text otherwise."""
        if cls._has_color:
            return f"{color}{text}{cls.RESET}"
        return cls.strip_ansi(text)

    @classmethod
    def clear_screen(cls):
        """
        Clears the terminal screen smoothly to present each wizard step from the top.
        Only executed when running in an interactive terminal (isatty).
        """
        if not sys.stdout.isatty():
            return
        try:
            if sys.platform == "win32":
                os.system("cls")
            else:
                sys.stdout.write("\033[2J\033[H")
                sys.stdout.flush()
        except Exception:
            pass

    @classmethod
    def scroll_to_bottom(cls):
        """
        Ensures that the terminal viewport window is scrolled down to the active cursor
        line before prompts, preventing prompts from being hidden off-screen or below
        the viewport fold in Windows CMD/conhost or long console buffers.
        """
        if not sys.stdout.isatty():
            return
        if sys.platform == "win32":
            try:
                import ctypes
                from ctypes import wintypes
                kernel32 = ctypes.windll.kernel32
                h_out = kernel32.GetStdHandle(-11)
                if h_out and h_out != wintypes.HANDLE(-1).value:
                    class COORD(ctypes.Structure):
                        _fields_ = [("X", ctypes.c_short), ("Y", ctypes.c_short)]
                    class SMALL_RECT(ctypes.Structure):
                        _fields_ = [("Left", ctypes.c_short), ("Top", ctypes.c_short),
                                    ("Right", ctypes.c_short), ("Bottom", ctypes.c_short)]
                    class CONSOLE_SCREEN_BUFFER_INFO(ctypes.Structure):
                        _fields_ = [("dwSize", COORD),
                                    ("dwCursorPosition", COORD),
                                    ("wAttributes", ctypes.c_ushort),
                                    ("srWindow", SMALL_RECT),
                                    ("dwMaximumWindowSize", COORD)]
                    csbi = CONSOLE_SCREEN_BUFFER_INFO()
                    if kernel32.GetConsoleScreenBufferInfo(h_out, ctypes.byref(csbi)):
                        cursor_y = csbi.dwCursorPosition.Y
                        win_height = csbi.srWindow.Bottom - csbi.srWindow.Top
                        if cursor_y >= csbi.srWindow.Bottom:
                            new_bottom = min(csbi.dwSize.Y - 1, cursor_y + 1)
                            new_top = max(0, new_bottom - win_height)
                            rect = SMALL_RECT(csbi.srWindow.Left, new_top, csbi.srWindow.Right, new_bottom)
                            kernel32.SetConsoleWindowInfo(h_out, True, ctypes.byref(rect))
            except Exception:
                pass
        else:
            try:
                sys.stdout.flush()
            except Exception:
                pass

    @classmethod
    def header(cls, title: str):
        """Displays a main header with universal, cross-platform separators."""
        width = 72
        line = "=" * width
        print()
        print(cls.c(line, cls.CYAN))
        print(cls.c(f"  {title.strip()}", cls.BOLD + cls.CYAN))
        print(cls.c(line, cls.CYAN))
        print()

    @classmethod
    def section(cls, title: str):
        """Displays a section title with a clean separator."""
        print(cls.c(f"\n--- {title.strip()} ---", cls.BOLD + cls.YELLOW))

    @classmethod
    def step_banner(cls, step_num: int, total_steps: int, title: str, breadcrumbs: Optional[List[str]] = None):
        """
        Clears the screen and displays a prominent top header with breadcrumbs.
        Guarantees each step starts at line 0 of the terminal without clutter
        and without forcing the user to scroll through previous steps.
        """
        cls.clear_screen()
        width = 72
        line = "=" * width
        print(cls.c(line, cls.CYAN))
        print(cls.c(f"  EU TRANSLATION MEMORY EXTRACTOR (DGT-TM) v{VERSION}", cls.BOLD + cls.CYAN))
        if breadcrumbs:
            bc_str = " | ".join(breadcrumbs)
            print(cls.c(f"  Active setup: {bc_str}", cls.DIM))
        print(cls.c(line, cls.CYAN))
        step_title = f"STEP {step_num} OF {total_steps}: {title.upper()}"
        cls.section(step_title)

    @classmethod
    def success(cls, msg: str):
        tag = cls.c("[OK]", cls.GREEN + cls.BOLD)
        print(f" {tag} {msg}")

    @classmethod
    def info(cls, msg: str):
        tag = cls.c("[INFO]", cls.CYAN + cls.BOLD)
        print(f" {tag} {msg}")

    @classmethod
    def warning(cls, msg: str):
        tag = cls.c("[WARNING]", cls.YELLOW + cls.BOLD)
        print(f" {tag} {msg}")

    @classmethod
    def error(cls, msg: str):
        tag = cls.c("[ERROR]", cls.RED + cls.BOLD)
        print(f" {tag} {msg}")

    @classmethod
    def prompt(cls, text: str, default: Optional[str] = None) -> str:
        """Prompts the user for input, ensuring console viewport is scrolled to cursor line."""
        cls.scroll_to_bottom()
        tag = cls.c("[?]", cls.MAGENTA + cls.BOLD)
        prompt_str = f" {tag} {cls.c(text, cls.BOLD)}"
        if default is not None:
            prompt_str += f" {cls.c(f'[{default}]', cls.DIM)}: "
        else:
            prompt_str += ": "
        try:
            res = input(prompt_str).strip()
            return res if res else (default if default is not None else "")
        except (KeyboardInterrupt, EOFError):
            print("\nAborted by user.")
            sys.exit(0)

    @classmethod
    def prompt_yes_no(cls, text: str, default: bool = True) -> bool:
        """Prompts for yes/no. Accepts English (y/yes) and Polish (t/tak) inputs."""
        choice_str = "[Y/n]" if default else "[y/N]"
        ans = cls.prompt(f"{text} {choice_str}", default="y" if default else "n").lower()
        return ans in ("y", "yes", "t", "tak", "1", "true")

    @classmethod
    def render_progress(cls, current: int, total: int, pairs_count: int, speed: float = 0.0):
        if not sys.stdout.isatty():
            return
        width = 25
        pct = (current / total) if total > 0 else 1.0
        filled = int(width * pct)
        bar = "=" * filled + "-" * (width - filled)
        pct_str = f"{int(pct * 100):3d}%"
        speed_str = f" ({speed:,.0f} pairs/s)" if speed > 0 else ""
        pairs_fmt = f"{pairs_count:,}"
        sys.stdout.write(
            f"\r [{cls.c(bar, cls.CYAN)}] {pct_str} | File {current}/{total} | Extracted: {cls.c(pairs_fmt, cls.GREEN)} pairs{speed_str} "
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
    """Scans a file or directory for .tmx and .zip files."""
    p = Path(path).resolve()
    if not p.exists():
        raise FileNotFoundError(f"Specified path does not exist: {path}")

    items: List[SourceItem] = []

    if p.is_file():
        if p.suffix.lower() == ".zip":
            _scan_zip(str(p), items)
        elif p.suffix.lower() == ".tmx":
            item = SourceItem(p.name, str(p), is_zip=False)
            item.size_bytes = p.stat().st_size
            items.append(item)
    elif p.is_dir():
        for root, _, files in os.walk(str(p)):
            for f in sorted(files):
                full_path = os.path.join(root, f)
                ext = os.path.splitext(f)[1].lower()
                if ext == ".tmx":
                    item = SourceItem(f, full_path, is_zip=False)
                    item.size_bytes = os.path.getsize(full_path)
                    items.append(item)
                elif ext == ".zip":
                    _scan_zip(full_path, items)

    return items


def _scan_zip(zip_path: str, out_items: List[SourceItem]):
    try:
        with zipfile.ZipFile(zip_path, "r") as zf:
            for info in zf.infolist():
                if info.filename.lower().endswith(".tmx") and not info.is_dir():
                    disp = f"{os.path.basename(zip_path)} -> {os.path.basename(info.filename)}"
                    item = SourceItem(disp, zip_path, is_zip=True, zip_entry_name=info.filename)
                    item.size_bytes = info.file_size
                    out_items.append(item)
    except zipfile.BadZipFile:
        UI.warning(f"Corrupted or invalid ZIP archive (skipped): {zip_path}")


# ==============================================================================
# 4. PARSING AND EXTRACTION ENGINE
# ==============================================================================

class TranslationPair:
    __slots__ = ("source", "target", "doc_id", "src_lang", "trg_lang", "pivot_en")

    def __init__(
        self,
        source: str,
        target: str,
        doc_id: str = "",
        src_lang: str = "",
        trg_lang: str = "",
        pivot_en: str = ""
    ):
        self.source = source
        self.target = target
        self.doc_id = doc_id
        self.src_lang = src_lang
        self.trg_lang = trg_lang
        self.pivot_en = pivot_en


DOMAIN_CATEGORIES: Tuple[str, ...] = (
    "legal",
    "finance",
    "trade",
    "it_telecom",
    "engineering",
    "energy_env",
    "medical",
    "chemicals",
    "agri_food",
    "general",
)

SPECIALIZED_CATEGORIES: Tuple[str, ...] = (
    "legal",
    "finance",
    "trade",
    "it_telecom",
    "engineering",
    "energy_env",
    "medical",
    "chemicals",
    "agri_food",
)

DOMAIN_LABELS: Dict[str, str] = {
    "legal": "Law, Judiciary, EU Legislation & Treaties",
    "finance": "Finance, Banking (CRR/ECB), Accounting (IFRS) & Tax",
    "trade": "International Trade, Customs, Procurement, Competition & Business",
    "it_telecom": "IT, Software, Cybersecurity (NIS2), AI & Telecommunications",
    "engineering": "Engineering, Automotive, Transport, Aviation & Machinery",
    "energy_env": "Energy, Climate, Emissions (EU ETS), Waste & Environment",
    "medical": "Medicine, Pharmaceuticals, Medical Devices & Veterinary",
    "chemicals": "Chemicals, REACH/CLP, Safety Data Sheets (SDS) & Biocides",
    "agri_food": "Agriculture, Food Safety (EFSA), Animal Feed & Fisheries",
    "general": "General, Administrative & Unclassified",
}

# Convenient CLI / input shorthand aliases mapped to canonical category codes
CATEGORY_ALIASES: Dict[str, str] = {
    "business": "trade",
    "customs": "trade",
    "environment": "energy_env",
    "energy": "energy_env",
    "climate": "energy_env",
    "it": "it_telecom",
    "telecom": "it_telecom",
    "cyber": "it_telecom",
    "tech": "engineering",
    "transport": "engineering",
    "automotive": "engineering",
    "pharma": "medical",
    "health": "medical",
    "chem": "chemicals",
    "reach": "chemicals",
    "food": "agri_food",
    "agri": "agri_food",
    "agriculture": "agri_food",
}


def parse_categories_arg(raw: Optional[str]) -> Optional[Set[str]]:
    """Parses a comma-separated list of categories (supporting aliases) into a validated set, or None for all."""
    if not raw or not raw.strip():
        return None
    tokens = [t.strip().lower() for t in re.split(r"[,;\s]+", raw.strip()) if t.strip()]
    if not tokens or "all" in tokens:
        return None
    valid: Set[str] = set()
    for t in tokens:
        mapped = CATEGORY_ALIASES.get(t, t)
        if mapped in DOMAIN_CATEGORIES:
            valid.add(mapped)
    return valid if valid else None


class OfflineTfidfBayesClassifier:
    """
    Stage A2: Pure-Python statistical TF-IDF + Bigram centroid classifier (stdlib only).
    Tokenizes into hyphen-preserving unigrams and bigrams, computes L2-normalized
    TF-IDF cosine similarity against curated EU domain prototypes across all 9 specialized
    verticals, and returns statistical confidence boosts (+0, +1, or +2).
    """

    _DOMAIN_PROTOTYPES: Dict[str, Dict[str, float]] = {
        "legal": {
            "regulation": 2.4, "directive": 2.4, "decision": 1.6, "treaty": 2.6,
            "jurisdiction": 2.8, "infringement": 2.8, "tribunal": 2.6, "court": 2.0,
            "legislation": 2.4, "legislative": 2.2, "statutory": 2.6, "liability": 2.1,
            "obligation": 1.8, "compliance": 1.9, "enforceable": 2.5, "sanction": 2.2,
            "penalty": 2.0, "penalties": 2.0, "repeal": 2.5, "member_states": 1.8,
            "official_journal": 2.3, "legal_basis": 2.6, "competent_authority": 2.2,
            "equal_treatment": 2.7, "entry_into_force": 2.4, "pursuant_to": 2.1,
            "court_of_justice": 2.9, "restrictive_measures": 2.7, "fundamental_rights": 2.6,
            "rozporządzenie": 2.4, "dyrektywa": 2.4, "trybunał": 2.6, "ustawa": 2.4,
            "postępowanie": 1.9, "dziennik_urzędowy": 2.3,
        },
        "finance": {
            "financial": 2.1, "finance": 2.1, "banking": 2.6, "bank": 2.0, "central_bank": 2.9,
            "credit_institution": 2.9, "credit_institutions": 2.9, "credit": 2.0, "loan": 2.2,
            "interest_rate": 2.7, "sovereign_debt": 2.9, "recapitalisation": 2.9,
            "liquidity_coverage": 3.0, "leverage_ratio": 2.9, "prudential": 2.7,
            "balance_sheet": 2.9, "comprehensive_income": 3.0, "fair_value": 2.9,
            "impairment_loss": 3.0, "amortisation": 2.7, "depreciation": 2.7,
            "financial_assets": 3.0, "non-current_assets": 2.9, "equity": 2.5,
            "receivables": 2.6, "accounting": 2.6, "audit": 2.3, "ifrs": 3.0,
            "tax": 2.3, "taxation": 2.5, "vat": 2.8, "excise": 2.6, "fiscal": 2.5,
            "insolvency": 2.8, "bankruptcy": 2.8, "dividend": 2.7, "shareholder": 2.6,
            "issuing_shares": 2.9, "stock_exchange": 2.8, "sprawozdanie_finansowe": 3.0,
            "aktywa_finansowe": 3.0, "podatek": 2.4, "księgowość": 2.5, "upadłość": 2.8,
        },
        "trade": {
            "state_aid": 3.0, "undertaking": 2.5, "undertakings": 2.5, "anti-dumping": 3.1,
            "countervailing": 3.0, "customs_duty": 2.9, "customs_tariff": 2.9, "tariff": 2.6,
            "combined_nomenclature": 3.0, "rules_of_origin": 2.9, "free_trade": 2.8,
            "export_levy": 2.9, "public_procurement": 3.0, "procurement": 2.5,
            "contracting_authority": 2.8, "tender": 2.4, "antitrust": 2.9, "merger": 2.7,
            "competition": 2.3, "competitiveness": 2.2, "internal_market": 2.4,
            "enterprise": 2.2, "enterprises": 2.2, "sme": 2.6, "subsidy": 2.5, "subsidies": 2.5,
            "exporting_producers": 2.9, "importers": 2.5, "exporters": 2.5,
            "pomoc_państwa": 3.0, "zamówienia_publiczne": 3.0, "antydumpingowe": 3.0,
            "przedsiębiorstwo": 2.4, "konkurencja": 2.3, "taryfa_celna": 2.9,
        },
        "it_telecom": {
            "cybersecurity": 3.1, "encryption": 2.9, "cryptography": 2.9, "algorithm": 2.7,
            "artificial_intelligence": 3.1, "machine_learning": 3.0, "cloud_computing": 2.9,
            "software": 2.6, "hardware": 2.4, "database": 2.4, "server": 2.4,
            "telecommunications": 2.9, "broadband": 2.8, "bandwidth": 2.7, "wireless": 2.5,
            "radio_spectrum": 2.9, "radio_frequency": 2.8, "interoperability": 2.7,
            "information_systems": 2.8, "personal_data": 2.9, "data_protection": 2.9,
            "anonymisation": 2.8, "electronic_identification": 2.9, "trust_services": 2.8,
            "digital_services": 2.8, "online_platform": 2.8, "source_code": 2.8,
            "cyberbezpieczeństwo": 3.1, "oprogramowanie": 2.6, "telekomunikacja": 2.9,
            "dane_osobowe": 2.9, "sztuczna_inteligencja": 3.1,
        },
        "engineering": {
            "engine": 2.5, "engines": 2.5, "diesel": 2.5, "vehicle": 2.4, "vehicles": 2.4,
            "motor_vehicles": 2.8, "automotive": 2.6, "homologation": 2.9, "type-approval": 2.9,
            "after-treatment": 3.0, "exhaust_after-treatment": 3.1, "compression-ignition": 3.0,
            "positive-ignition": 3.0, "turbocharger": 2.8, "opacimeter": 2.9, "particulate_traps": 2.8,
            "headlamp": 2.7, "braking": 2.6, "aircraft": 2.5, "airworthiness": 3.0,
            "airspace": 2.7, "ertms": 3.0, "rolling_stock": 2.9, "railway": 2.4,
            "semiconductor": 2.9, "microprocessor": 2.8, "electrical_circuits": 2.9,
            "voltage": 2.6, "ultrasonic": 2.7, "transducers": 2.8, "machinery": 2.3,
            "apparatus": 2.2, "welding": 2.7, "construction_products": 2.7,
            "silnik": 2.5, "pojazd": 2.4, "homologacja": 2.9, "oczyszczania_spalin": 3.0,
        },
        "energy_env": {
            "emission": 2.4, "emissions": 2.4, "pollutant": 2.8, "pollutants": 2.8,
            "pollution": 2.7, "greenhouse_gas": 3.1, "co2": 2.9, "carbon_dioxide": 2.9,
            "emissions_trading": 3.0, "eu_ets": 3.0, "climate_change": 2.9, "decarbonisation": 2.9,
            "renewable_energy": 3.0, "photovoltaic": 2.9, "wind_turbines": 2.9,
            "biofuels": 2.8, "biogas": 2.8, "biomass": 2.7, "fossil_fuels": 2.8,
            "energy_efficiency": 2.9, "electricity": 2.2, "biodiversity": 3.0, "ecosystem": 2.8,
            "deforestation": 2.9, "natura_2000": 3.0, "recycling": 2.6, "hazardous_waste": 3.0,
            "municipal_waste": 2.9, "wastewater": 2.9, "waste_treatment": 2.9, "water_treatment": 2.8,
            "landfill": 2.8, "water_quality": 2.7, "air_quality": 2.7, "sustainability": 2.4,
            "środowisko": 2.4, "zanieczyszczenia": 2.7, "energia_odnawialna": 3.0, "odpady": 2.3,
        },
        "medical": {
            "pharmaceutical": 2.9, "medicinal": 2.8, "medicinal_product": 3.1, "medicinal_products": 3.1,
            "clinical_trial": 3.0, "clinical_trials": 3.0, "clinical_audits": 2.9,
            "pharmacovigilance": 3.1, "medical_devices": 3.0, "in_vitro": 2.8,
            "patient": 2.5, "patients": 2.5, "disease": 2.5, "diseases": 2.5,
            "therapeutic": 2.7, "therapy": 2.4, "vaccine": 2.9, "vaccination": 2.9,
            "immunisation": 2.8, "antibiotic": 2.9, "antimicrobial": 2.9, "pathogen": 2.9,
            "epidemiology": 2.9, "epidemiological": 2.9, "veterinary": 2.7, "zoonotic": 2.9,
            "hospital": 2.4, "surgical": 2.6, "dosage": 2.6, "pathology": 2.8, "histopathology": 2.9,
            "medical_treatment": 3.0, "clinical_treatment": 3.0, "public_health": 2.5,
            "farmaceutyczny": 2.9, "produkt_leczniczy": 3.1, "pacjent": 2.5, "szczepionka": 2.9,
        },
        "chemicals": {
            "biocidal": 3.0, "biocides": 3.0, "active_substance": 2.9, "active_substances": 2.9,
            "pesticides": 2.9, "pesticide_residues": 3.0, "herbicides": 2.9, "fungicides": 2.9,
            "plant_protection": 2.8, "safety_data": 2.9, "reach": 2.7, "echa": 2.9,
            "toxicology": 2.9, "toxicological": 2.9, "ecotoxicological": 3.0,
            "carcinogenic": 2.9, "mutagenic": 2.9, "reprotoxic": 3.0, "cytotoxic": 2.9,
            "endocrine_disrupting": 3.0, "dioxins": 2.9, "furans": 2.9, "pcbs": 2.8,
            "hazardous_substances": 2.9, "chemical_substances": 2.8, "polymers": 2.6,
            "fertilisers": 2.6, "detergents": 2.6, "cosmetic_products": 2.6,
            "titanium_dioxide": 2.8, "hydrofluorocarbons": 2.8, "substancja_czynna": 2.9,
            "produkty_biobójcze": 3.0, "toksykologia": 2.9, "pestycydów": 2.9,
        },
        "agri_food": {
            "agricultural": 2.6, "agriculture": 2.6, "common_agricultural": 3.0,
            "food_safety": 2.9, "efsa": 3.0, "novel_food": 3.0, "foodstuffs": 2.9,
            "food_additives": 3.0, "feed_additives": 3.0, "feedingstuffs": 2.9,
            "animal_nutrition": 2.9, "animal_feed": 2.9, "phytosanitary": 3.0,
            "plant_health": 2.9, "organic_production": 2.9, "geographical_indications": 2.9,
            "fishing_opportunities": 3.0, "fish_stocks": 3.0, "allowable_catches": 3.0,
            "fisheries": 2.7, "aquaculture": 2.9, "livestock": 2.7, "animal_welfare": 2.8,
            "bovine": 2.7, "porcine": 2.7, "poultry": 2.7, "cereals": 2.6, "wheat": 2.5,
            "rapeseed": 2.6, "mineral_waters": 2.7, "rybołówstwo": 2.7, "rolnictwo": 2.6,
            "bezpieczeństwo_żywności": 2.9, "pasze": 2.8, "żywność": 2.4,
        },
    }

    _TOKEN_RE = re.compile(r"[a-zA-Z0-9ąęćłńóśźżĄĘĆŁŃÓŚŹŻ]+(?:-[a-zA-Z0-9ąęćłńóśźżĄĘĆŁŃÓŚŹŻ]+)*")
    _STOPWORDS: Set[str] = {
        "the", "and", "for", "with", "that", "this", "from", "are", "was", "were",
        "have", "has", "had", "not", "but", "all", "any", "can", "may", "must",
        "shall", "such", "into", "upon", "under", "over", "after", "before",
        "oraz", "dla", "przez", "przy", "jest", "nie", "tak", "lub", "albo", "jak",
    }

    def __init__(self):
        self._norms: Dict[str, float] = {}
        for cat, weights in self._DOMAIN_PROTOTYPES.items():
            self._norms[cat] = math.sqrt(sum(v * v for v in weights.values())) or 1.0

    def _extract_features(self, text: str) -> Counter:
        raw_tokens = [t.lower() for t in self._TOKEN_RE.findall(text)]
        tokens = [t for t in raw_tokens if len(t) >= 2 and t not in self._STOPWORDS]
        feats: Counter = Counter(tokens)
        for i in range(len(tokens) - 1):
            feats[f"{tokens[i]}_{tokens[i + 1]}"] += 1
        return feats

    def score_boosts(self, text: str) -> Dict[str, int]:
        """Returns statistical boost (+0, +1, or +2) per specialized domain."""
        boosts: Dict[str, int] = {cat: 0 for cat in SPECIALIZED_CATEGORIES}
        if not text:
            return boosts
        feats = self._extract_features(text)
        if len(feats) < 4:
            return boosts

        doc_norm = math.sqrt(sum(c * c for c in feats.values())) or 1.0
        for cat, proto in self._DOMAIN_PROTOTYPES.items():
            dot = 0.0
            for term, tf in feats.items():
                w = proto.get(term)
                if w:
                    dot += tf * w
            if dot > 0.0:
                cos_sim = dot / (doc_norm * self._norms[cat])
                if cos_sim >= 0.24:
                    boosts[cat] = 2
                elif cos_sim >= 0.13:
                    boosts[cat] = 1
        return boosts


class DomainClassifier:
    """
    Two-stage offline multi-label classifier for EU DGT-TM segments across 10 market-aligned categories:
    legal, finance, trade, it_telecom, engineering, energy_env, medical, chemicals, agri_food, and general.
    Combines:
      - Stage A1: Unicode & hyphen-safe tiered regex/collocation rules, per-language
        distinct-concept scoring (preventing EN+PL translation double-counting), and
        cross-domain disambiguation.
      - Stage A2: Pure-Python TF-IDF / bigram statistical classifier (OfflineTfidfBayesClassifier).
      - Dominant-only document-title context prior.
    """

    _B_START = r"(?<![^\W_]|-)(?:"
    _B_END = r")(?![^\W_]|-)"

    _RAW_RULES: Dict[str, List[Tuple[int, str]]] = {
        "legal": [
            (3, r"regulations?|directives?|treat(?:y|ies)|jurisdictions?|infringements?|plaintiffs?|defendants?|tribunals?|court of justice|statutes?|statutory|legislations?|legislative|constitutional|prosecutions?|litigations?|indictments?|arbitrations?|subpoenas?|annulments?|enacting|pursuant to|whereas|recitals?|corrigend(?:um|a)|equal treatment|natural and legal persons?|delegated acts?|implementing acts?|restrictive measures|fundamental rights|rule of law|rozporządzeni[a-ząćęłńóśźż]*|dyrektyw[a-ząćęłńóśźż]*|trybunał[a-ząćęłńóśźż]*|orzeczeni[a-ząćęłńóśźż]*|jurysdykcj[a-ząćęłńóśźż]*|ustaw[a-ząćęłńóśźż]*|kodeks[a-ząćęłńóśźż]*|prawodawstw[a-ząćęłńóśźż]*|naruszeni[a-ząćęłńóśźż]*|sądow[a-ząćęłńóśźż]*|sprostowani[a-ząćęłńóśźż]*|środk[a-ząćęłńóśźż]* ograniczając[a-ząćęłńóśźż]*|praworządnoś[ćci][a-ząćęłńóśźż]*"),
            (2, r"article\s+\d+|paragraph\s+\d+|subparagraph|annex\s+[ivx\d]+|official journal|competent authorit(?:y|ies)|member states?|legal basis|binding|enforceable|compliance|obligations?|(?<!financial\s)liabilit(?:y|ies)|sanctions?|penalt(?:y|ies)|prohibitions?|amendments?|repeal(?:ed|ing)?|entry into force|decisions?|herein|thereof|artykuł[a-ząćęłńóśźż]*\s+\d+|art\.\s*\d+|ustęp[a-ząćęłńóśźż]*\s+\d+|załącznik[a-ząćęłńóśźż]*|dziennik[a-ząćęłńóśźż]* urzędow[a-ząćęłńóśźż]*|państw[a-ząćęłńóśźż]* członkowsk[a-ząćęłńóśźż]*|odpowiedzialnoś[ćci][a-ząćęłńóśźż]*|sankcj[a-ząćęłńóśźż]*|zakaz[a-ząćęłńóśźż]*|uchyleni[a-ząćęłńóśźż]*|wejście w życie"),
            (1, r"law|legal|courts?|contracts?|agreements?|clauses?|provisions?|rules?|decrees?|authorit(?:y|ies)|prawo|prawn[a-ząćęłńóśźż]*|sąd(?:u|y|ów|zie|om)?|umow[a-ząćęłńóśźż]*|przepis[a-ząćęłńóśźż]*|postanowieni[a-ząćęłńóśźż]*|organ(?:u|y|ów|om)?"),
        ],
        "finance": [
            (3, r"balance sheets?|profit or loss|comprehensive income|fair value|impairment loss|amortisation|depreciation|trade receivables|non-current assets?|current assets?|financial assets?|financial liabilit(?:y|ies)|cash flows?|financial statements?|ifrs|ias\s+\d+|capital adequacy|liquidity coverage|net stable funding|leverage ratio|prudential supervision|credit institutions?|central banks?|recapitalisation|sovereign debt|issuing shares|shareholders?|dividends?|stock exchange|value added tax|vat|excise dut(?:y|ies)|excise|corporate tax|income tax|tax treatment|insolvenc(?:y|ies)|bankruptc(?:y|ies)|bilans[a-ząćęłńóśźż]*|rachun[a-ząćęłńóśźż]* zysków i strat|całkowit[a-ząćęłńóśźż]* dochod[a-ząćęłńóśźż]*|wartoś[ćci] godziw[a-ząćęłńóśźż]*|odpis[a-ząćęłńóśźż]* aktualizując[a-ząćęłńóśźż]*|amortyzacj[a-ząćęłńóśźż]*|aktyw[a-ząćęłńóśźż]* finansow[a-ząćęłńóśźż]*|aktyw[a-ząćęłńóśźż]* trwał[a-ząćęłńóśźż]*|zobowiązani[a-ząćęłńóśźż]* finansow[a-ząćęłńóśźż]*|przepływ[a-ząćęłńóśźż]* pieniężn[a-ząćęłńóśźż]*|sprawozdani[a-ząćęłńóśźż]* finansow[a-ząćęłńóśźż]*|instytucj[a-ząćęłńóśźż]* kredytow[a-ząćęłńóśźż]*|nadzór ostrożnościowy|bank[a-ząćęłńóśźż]* centraln[a-ząćęłńóśźż]*|dokapitalizowani[a-ząćęłńóśźż]*|dług[a-ząćęłńóśźż]* publiczn[a-ząćęłńóśźż]*|papier[a-ząćęłńóśźż]* wartościow[a-ząćęłńóśźż]*|obligacj[a-ząćęłńóśźż]*|emisj[a-ząćęłńóśźż]* akcji|akcjonariusz[a-ząćęłńóśźż]*|dywidend[a-ząćęłńóśźż]*|giełd[a-ząćęłńóśźż]*|podat(?:ek|ku|ki|ków|kow[a-ząćęłńóśźż]*)|akcyz[a-ząćęłńóśźż]*|upadłoś[ćci][a-ząćęłńóśźż]*|niewypłacalnoś[ćci][a-ząćęłńóśźż]*"),
            (2, r"financial|finance|banking|banks?|credits?|loans?|interest rates?|investments?|investors?|insurance|reinsurance|pensions?|taxation|fiscal|audits?|auditors?|accounting|equity|receivables|revenues?|profits?|securities|bonds?|appropriations?|finansow[a-ząćęłńóśźż]*|bankow[a-ząćęłńóśźż]*|kredyt[a-ząćęłńóśźż]*|pożyczk[a-ząćęłńóśźż]*|stop[a-ząćęłńóśźż]* procentow[a-ząćęłńóśźż]*|inwestycj[a-ząćęłńóśźż]*|ubezpieczeni[a-ząćęłńóśźż]*|emerytaln[a-ząćęłńóśźż]*|opodatkowani[a-ząćęłńóśźż]*|fiskaln[a-ząćęłńóśźż]*|audyt[a-ząćęłńóśźż]*|biegł[a-ząćęłńóśźż]* rewident[a-ząćęłńóśźż]*|księgowoś[ćci][a-ząćęłńóśźż]*|rachunkowoś[ćci][a-ząćęłńóśźż]*|kapitał[a-ząćęłńóśźż]* własn[a-ząćęłńóśźż]*|należności[a-ząćęłńóśźż]*|przychod[a-ząćęłńóśźż]*|zysk(?:u|i|ów|om|iem|ami|ach)?"),
            (1, r"funds?|budgets?|capital|assets?|payments?|shares|currenc(?:y|ies)|exchange rates?|fundusz[a-ząćęłńóśźż]*|budżet[a-ząćęłńóśźż]*|kapitał[a-ząćęłńóśźż]*|aktyw(?:a|ów|ach)|płatnoś[ćci][a-ząćęłńóśźż]*|walut[a-ząćęłńóśźż]*|kurs[a-ząćęłńóśźż]* wymiany"),
        ],
        "trade": [
            (3, r"state aid|anti-dumping|countervailing|customs dut(?:y|ies)|customs tariffs?|combined nomenclature|tariff quotas?|rules of origin|preferential origin|preferential treatment|free trade agreements?|export lev(?:y|ies)|safeguard investigations?|public procurement|contracting authorit(?:y|ies)|tenderers?|antitrust|cartels?|mergers?|acquisitions?|undertaking(?!\s+services)|undertakings|microenterprises?|smes?|exporting producers?|pomoc[a-ząćęłńóśźż]* państwa|antydumping[a-ząćęłńóśźż]*|cło|cła|ceł|celn[a-ząćęłńóśźż]*|taryf[a-ząćęłńóśźż]* celn[a-ząćęłńóśźż]*|nomenklatur[a-ząćęłńóśźż]* scalon[a-ząćęłńóśźż]*|kontyngent[a-ząćęłńóśźż]* taryfow[a-ząćęłńóśźż]*|reguł[a-ząćęłńóśźż]* pochodzenia|umow[a-ząćęłńóśźż]* o wolnym handlu|zamówieni[a-ząćęłńóśźż]* publiczn[a-ząćęłńóśźż]*|instytucj[a-ząćęłńóśźż]* zamawiając[a-ząćęłńóśźż]*|oferent[a-ząćęłńóśźż]*|kartel[a-ząćęłńóśźż]*|fuzj[a-ząćęłńóśźż]*|przedsiębiorstw[a-ząćęłńóśźż]*|mśp"),
            (2, r"markets?|internal market|single market|trade|commercial|enterprises?|compan(?:y|ies)|corporate|competition|competitiveness|exports?|exporting|exporters?|imports?|importing|importers?|customs|tariffs?|subsid(?:y|ies)|procurement|tenders?|concessions?|consumers?|turnover|supply chains?|rynek|rynku|rynkow[a-ząćęłńóśźż]*|rynki|rynków|handel|handlu|handlem|handlow[a-ząćęłńóśźż]*|spół(?:ka|ki|ek|ce|kę)|konkurencj[a-ząćęłńóśźż]*|konkurencyjnoś[ćci][a-ząćęłńóśźż]*|eksport[a-ząćęłńóśźż]*|wywóz|wywozu|wywozow[a-ząćęłńóśźż]*|import[a-ząćęłńóśźż]*|przywóz|przywozu|przywozow[a-ząćęłńóśźż]*|taryf[a-ząćęłńóśźż]*|dotacj[a-ząćęłńóśźż]*|subwencj[a-ząćęłńóśźż]*|subsydi[a-ząćęłńóśźż]*|przetarg[a-ząćęłńóśźż]*|koncesj[a-ząćęłńóśźż]*|konsument[a-ząćęłńóśźż]*|łańcuch[a-ząćęłńóśźż]* dostaw"),
            (1, r"business|economic|economy|prices?|costs?|fees?|quotas?|suppliers?|manufacturers?|producers?|biznes[a-ząćęłńóśźż]*|gospodar[a-ząćęłńóśźż]*|cen[ay]|koszt[a-ząćęłńóśźż]*|opłat[a-ząćęłńóśźż]*|kontyngent[a-ząćęłńóśźż]*|dostawc[a-ząćęłńóśźż]*|producent[a-ząćęłńóśźż]*"),
        ],
        "it_telecom": [
            (3, r"cybersecurity|cryptography|encryption|algorithms?|artificial intelligence|machine learning|neural networks?|cloud computing|telecommunications?|telecommunication|broadband|bandwidth|radio spectrum|radio frequency|interoperability|information systems?|network and information|personal data|data protection|pseudonymisation|anonymisation|electronic identification|trust services?|digital services?|online platforms?|search engines?|source code|open source|malware|ransomware|cyberbezpieczeństw[a-ząćęłńóśźż]*|kryptografi[a-ząćęłńóśźż]*|szyfrowani[a-ząćęłńóśźż]*|algorytm[a-ząćęłńóśźż]*|sztuczn[a-ząćęłńóśźż]* inteligencj[a-ząćęłńóśźż]*|uczeni[a-ząćęłńóśźż]* maszynow[a-ząćęłńóśźż]*|chmur[a-ząćęłńóśźż]* obliczeniow[a-ząćęłńóśźż]*|telekomunikac[a-ząćęłńóśźż]*|szerokopasmow[a-ząćęłńóśźż]*|częstotliwoś[ćci] radiow[a-ząćęłńóśźż]*|widm[a-ząćęłńóśźż]* radiow[a-ząćęłńóśźż]*|interoperacyjnoś[ćci][a-ząćęłńóśźż]*|system[a-ząćęłńóśźż]* informatyczn[a-ząćęłńóśźż]*|dan[a-ząćęłńóśźż]* osobow[a-ząćęłńóśźż]*|ochron[a-ząćęłńóśźż]* danych|anonimizacj[a-ząćęłńóśźż]*|identyfikacj[a-ząćęłńóśźż]* elektroniczn[a-ząćęłńóśźż]*|usług[a-ząćęłńóśźż]* zaufania|usług[a-ząćęłńóśźż]* cyfrow[a-ząćęłńóśźż]*|platform[a-ząćęłńóśźż]* internetow[a-ząćęłńóśźż]*|kod[a-ząćęłńóśźż]* źródłow[a-ząćęłńóśźż]*"),
            (2, r"software|hardware|databases?|servers?|internet|wireless|bluetooth|satellite communication|digital|electronic\s+(?:means|communications?|registr(?:y|ies)|signatures?|data)|it networks?|information technology|authentication|vulnerabilit(?:y|ies)|interfaces?|metadata|oprogramowani[a-ząćęłńóśźż]*|baz[ay] danych|baz danych|serwer[a-ząćęłńóśźż]*|bezprzewodow[a-ząćęłńóśźż]*|cyfrow[a-ząćęłńóśźż]*|informatyczn[a-ząćęłńóśźż]*|uwierzytelniani[a-ząćęłńóśźż]*|podatności[a-ząćęłńóśźż]*|interfejs[a-ząćęłńóśźż]*|metadan[a-ząćęłńóśźż]*"),
            (1, r"networks?|platforms?|portals?|online|data processing|electronic|sieci[a-ząćęłńóśźż]*|przetwarzani[a-ząćęłńóśźż]* danych|elektroniczn[a-ząćęłńóśźż]*"),
        ],
        "engineering": [
            (3, r"after-treatment|after treatment|exhaust after-treatment|exhaust after treatment|oczyszczani[aeu] spalin|oczyszczaniem spalin|compression-ignition|positive-ignition|type-approval|homologation|opacimeters?|turbochargers?|particulate traps?|denox|on-board diagnostic|adaptive front-lighting|motor vehicles?|rolling stock|ertms|airworthiness|air traffic|airspace|aerodromes?|unmanned aircraft|semiconductors?|microprocessors?|electrical circuits?|construction products?|ultrasonic transducers?|soldering|brazing|welding|zapłon[a-ząćęłńóśźż]* samoczynn[a-ząćęłńóśźż]*|zapłon[a-ząćęłńóśźż]* wymuszon[a-ząćęłńóśźż]*|homologacj[a-ząćęłńóśźż]*|filtr[a-ząćęłńóśźż]* cząstek stałych|pojazd[a-ząćęłńóśźż]* silnikow[a-ząćęłńóśźż]*|tabor[a-ząćęłńóśźż]* kolejow[a-ząćęłńóśźż]*|zdatnoś[ćci] do lotu|ruch[a-ząćęłńóśźż]* lotnicz[a-ząćęłńóśźż]*|przestrzeni[a-ząćęłńóśźż]* powietrzn[a-ząćęłńóśźż]*|lotnisk[a-ząćęłńóśźż]*|półprzewodnik[a-ząćęłńóśźż]*|obwod[a-ząćęłńóśźż]* elektryczn[a-ząćęłńóśźż]*|wyrob[a-ząćęłńóśźż]* budowlan[a-ząćęłńóśźż]*|spawani[a-ząćęłńóśźż]*|lutowani[a-ząćęłńóśźż]*|zgrzewani[a-ząćęłńóśźż]*"),
            (2, r"engines?|diesel|vehicles?|automotive|aircraft|avionics|diagnostic systems?|railway|maritime transport|brakes?|braking|headlamps?|tyres?|tires?|chassis|axles?|steering|voltage|electric|electrical|sensors?|apparatus|machinery|turbines?|boilers?|pumps?|valves?|compressors?|calibration|metrology|heat treatment|technical specifications?|silnik[a-ząćęłńóśźż]*|pojazd[a-ząćęłńóśźż]*|samochod[a-ząćęłńóśźż]*|statk[a-ząćęłńóśźż]* powietrzn[a-ząćęłńóśźż]*|kolejow[a-ząćęłńóśźż]*|hamulc[a-ząćęłńóśźż]*|hamowani[a-ząćęłńóśźż]*|reflektor[a-ząćęłńóśźż]*|opon[a-ząćęłńóśźż]*|podwozi[a-ząćęłńóśźż]*|napięci[a-ząćęłńóśźż]*|elektryczn[a-ząćęłńóśźż]*|czujnik[a-ząćęłńóśźż]*|maszyn[a-ząćęłńóśźż]*|turbin[a-ząćęłńóśźż]*|pomp[ay]?|zawor[a-ząćęłńóśźż]*|sprężark[a-ząćęłńóśźż]*|kalibracj[a-ząćęłńóśźż]*|obróbk[a-ząćęłńóśźż]* ciepln[a-ząćęłńóśźż]*|specyfikacj[a-ząćęłńóśźż]* techniczn[a-ząćęłńóśźż]*"),
            (1, r"devices?|equipment|machines?|appliances?|parameters?|signals?|measurements?|specifications?|mechanical|technical(?!\s+assistance)(?!\s+and\s+administrative)|exhaust|urządzeni[a-ząćęłńóśźż]*|wyposażeni[a-ząćęłńóśźż]*|sprzęt[u]?|parametr[a-ząćęłńóśźż]*|sygnał[a-ząćęłńóśźż]*|pomiar[a-ząćęłńóśźż]*|mechaniczn[a-ząćęłńóśźż]*|spalin[a-ząćęłńóśźż]*"),
        ],
        "energy_env": [
            (3, r"greenhouse gas(?:es)?|co2(?!\s*,\s*and\s*incubation)|co2eq|carbon dioxide|emissions trading|eu ets|climate change|decarbonisation|energy efficiency|renewable energy|renewable gas|photovoltaic|wind turbines?|offshore wind|biofuels?|biogas|biomass|fossil fuels?|repowereu|power grids?|electricity grids?|biodiversity|ecosystems?|deforestation|natura 2000|hazardous waste|municipal waste|waste incineration|waste treatment|water treatment|sewage treatment|wastewater|landfills?|effluents?|environmental impact|cieplarnian[a-ząćęłńóśźż]*|dwutlen(?:ek|ku) węgla|handl[a-ząćęłńóśźż]* przydziałami emisji|zmian[a-ząćęłńóśźż]* klimatu|dekarbonizacj[a-ząćęłńóśźż]*|efektywnoś[ćci] energetyczn[a-ząćęłńóśźż]*|energi[a-ząćęłńóśźż]* odnawialn[a-ząćęłńóśźż]*|odnawialn[a-ząćęłńóśźż]* źródł[a-ząćęłńóśźż]* energii|fotowoltaiczn[a-ząćęłńóśźż]*|fotowoltaik[a-ząćęłńóśźż]*|turbin[a-ząćęłńóśźż]* wiatrow[a-ząćęłńóśźż]*|biopaliw[a-ząćęłńóśźż]*|biogaz[a-ząćęłńóśźż]*|biomas[a-ząćęłńóśźż]*|paliw[a-ząćęłńóśźż]* kopaln[a-ząćęłńóśźż]*|sieci[a-ząćęłńóśźż]* elektroenergetyczn[a-ząćęłńóśźż]*|bioróżnorodnoś[ćci][a-ząćęłńóśźż]*|różnorodnoś[ćci] biologiczn[a-ząćęłńóśźż]*|ekosystem[a-ząćęłńóśźż]*|wylesiani[a-ząćęłńóśźż]*|odpad[a-ząćęłńóśźż]* niebezpieczn[a-ząćęłńóśźż]*|odpad[a-ząćęłńóśźż]* komunaln[a-ząćęłńóśźż]*|spalani[a-ząćęłńóśźż]* odpadów|oczyszczani[a-ząćęłńóśźż]* ścieków|ściek[a-ząćęłńóśźż]*|składowisk[a-ząćęłńóśźż]*|ochron[a-ząćęłńóśźż]* środowiska"),
            (2, r"environment|environmental|emissions?|pollutants?|pollution|climate|waste|recycling|circular economy|water quality|groundwater|surface water|forestry|wildlife|habitats?|endangered species|ecology|ecological|sustainability|sustainable|air quality|energy consumption|electricity|natural gas|nuclear energy|środowisk[a-ząćęłńóśźż]*|emisj[a-ząćęłńóśźż]*(?!\s+akcji)(?!\s+obligacji)(?!\s+papierów)|zanieczyszczeni[a-ząćęłńóśźż]*|klimat[a-ząćęłńóśźż]*|odpad[a-ząćęłńóśźż]*|recykling[a-ząćęłńóśźż]*|gospodark[a-ząćęłńóśźż]* o obiegu zamkniętym|jakoś[ćci] wody|wody podziemne|wody powierzchniowe|leśnictw[a-ząćęłńóśźż]*|siedlisk[a-ząćęłńóśźż]*|ekolog[a-ząćęłńóśźż]*|zrównoważon[a-ząćęłńóśźż]*|jakoś[ćci] powietrza|zużyci[a-ząćęłńóśźż]* energii|energi[a-ząćęłńóśźż]* elektryczn[a-ząćęłńóśźż]*|gaz[a-ząćęłńóśźż]* ziemn[a-ząćęłńóśźż]*|energi[a-ząćęłńóśźż]* jądrow[a-ząćęłńóśźż]*"),
            (1, r"energy|fuels?|exhaust|nature|natural(?!\s+and\s+legal\s+persons?)(?!\s+persons?)(?!\s+gas)|conservation|rivers?|marine|forests?|soil|ozone|energi[a-ząćęłńóśźż]*|paliw[a-ząćęłńóśźż]*|spalin[a-ząćęłńóśźż]*|przyrod[a-ząćęłńóśźż]*|rzek[ai]|morsk[a-ząćęłńóśźż]*|las(?:u|y|ów|om|ach)?|gleb[ay]|ozon[a-ząćęłńóśźż]*"),
        ],
        "medical": [
            (3, r"pharmaceuticals?|medicinal products?|european medicines agency|clinical trials?|clinical investigations?|clinical audits?|pharmacovigilance|medical devices?|in vitro diagnostic|medical diagnos(?:is|tic)|clinical diagnos(?:is|tic)|organo-therapeutic|therapeutic|histopathology|pathology|epidemiolog(?:y|ical)|vaccines?|vaccinations?|immunisation|antibiotics?|antimicrobials?|pathogens?|communicable diseases?|foot and mouth disease|zoonotic|zoonoses|veterinary medicinal|veterinary surgeon|veterinary services?|veterinary profession|medical treatment|clinical treatment|hospital treatment|cancer treatment|outpatient treatment|eu4health|healthcare personnel|farmaceutyczn[a-ząćęłńóśźż]*|produkt[a-ząćęłńóśźż]* lecznicz[a-ząćęłńóśźż]*|europejsk[a-ząćęłńóśźż]* agencj[a-ząćęłńóśźż]* leków|badani[a-ząćęłńóśźż]* kliniczn[a-ząćęłńóśźż]*|audyt[a-ząćęłńóśźż]* kliniczn[a-ząćęłńóśźż]*|wyrob[a-ząćęłńóśźż]* medyczn[a-ząćęłńóśźż]*|diagnostyk[a-ząćęłńóśźż]* in vitro|terapeutyczn[a-ząćęłńóśźż]*|histopatologi[a-ząćęłńóśźż]*|patologi[a-ząćęłńóśźż]*|epidemiolog[a-ząćęłńóśźż]*|szczepion[a-ząćęłńóśźż]*|szczepieni[a-ząćęłńóśźż]*|antybiotyk[a-ząćęłńóśźż]*|przeciwdrobnoustrojow[a-ząćęłńóśźż]*|patogen[a-ząćęłńóśźż]*|chorob[a-ząćęłńóśźż]* zakaźn[a-ząćęłńóśźż]*|pryszczyc[a-ząćęłńóśźż]*|weterynaryjn[a-ząćęłńóśźż]*|lekarz[a-ząćęłńóśźż]* weterynarii|leczeni[a-ząćęłńóśźż]* szpitaln[a-ząćęłńóśźż]*|leczeni[a-ząćęłńóśźż]* kliniczn[a-ząćęłńóśźż]*|leczeni[a-ząćęłńóśźż]* medyczn[a-ząćęłńóśźż]*|onkologiczn[a-ząćęłńóśźż]*|personel[a-ząćęłńóśźż]* medyczn[a-ząćęłńóśźż]*"),
            (2, r"medical|medicine|medicines|healthcare|public health|mental health|human health|animal health|patients?|diseases?|illness(?:es)?|disorders?|therap(?:y|ies)|hospitals?|clinics?|surgical|dosages?|posology|adverse reactions?|contraindications?|veterinary|medyczn[a-ząćęłńóśźż]*|medycyn[a-ząćęłńóśźż]*|ochron[a-ząćęłńóśźż]* zdrowia|opiek[a-ząćęłńóśźż]* zdrowotn[a-ząćęłńóśźż]*|zdrowi[aeu] publiczn[a-ząćęłńóśźż]*|zdrowi[aeu] psychiczn[a-ząćęłńóśźż]*|zdrowi[aeu] ludzki[a-ząćęłńóśźż]*|zdrowi[aeu] zwierząt|pacjent[a-ząćęłńóśźż]*|chorob[a-ząćęłńóśźż]*|chorób|zaburzeni[a-ząćęłńóśźż]*|terapi[a-ząćęłńóśźż]*|szpital[a-ząćęłńóśźż]*|chirurg[a-ząćęłńóśźż]*|dawk[a-ząćęłńóśźż]*|dawkowani[a-ząćęłńóśźż]*|działani[a-ząćęłńóśźż]* niepożądan[a-ząćęłńóśźż]*|przeciwwskazani[a-ząćęłńóśźż]*"),
            (1, r"blood|tissues?|clinical|diagnosis|doctors?|physicians?|nurses?|veterinarians?|lesions?|krew|krwi|tkank[a-ząćęłńóśźż]*|kliniczn[a-ząćęłńóśźż]*|diagnoz[a-ząćęłńóśźż]*|lekarz[a-ząćęłńóśźż]*|pielęgniar[a-ząćęłńóśźż]*|weterynarz[a-ząćęłńóśźż]*"),
        ],
        "chemicals": [
            (3, r"reach regulation|european chemicals agency|echa|safety data sheets?|biocidal products?|biocides?|active substances?|plant protection products?|pesticides?|herbicides?|fungicides?|insecticides?|maximum residue levels?|mrls?|pesticide residues?|endocrine disrupt(?:or|ing)|carcinogenic|mutagenic|reprotoxic|cytotoxic|ecotoxicolog(?:y|ical)|toxicolog(?:y|ical)|skin irritation|eye irritation|eye exposure|dioxins?|furans?|pcbs|polyalcohols?|diols?|titanium dioxide|hydrofluorocarbons?|kart[a-ząćęłńóśźż]* charakterystyk[a-ząćęłńóśźż]*|produkt[a-ząćęłńóśźż]* biobójcz[a-ząćęłńóśźż]*|biocyd[a-ząćęłńóśźż]*|substancj[a-ząćęłńóśźż]* czynn[a-ząćęłńóśźż]*|środk[a-ząćęłńóśźż]* ochrony roślin|pestycyd[a-ząćęłńóśźż]*|herbicyd[a-ząćęłńóśźż]*|fungicyd[a-ząćęłńóśźż]*|insektycyd[a-ząćęłńóśźż]*|najwyższ[a-ząćęłńóśźż]* dopuszczaln[a-ząćęłńóśźż]* poziom[a-ząćęłńóśźż]* pozostałości|pozostałości[a-ząćęłńóśźż]* pestycydów|zaburzając[a-ząćęłńóśźż]* funkcjonowanie układu hormonalnego|rakotwórcz[a-ząćęłńóśźż]*|mutagenn[a-ząćęłńóśźż]*|działając[a-ząćęłńóśźż]* szkodliwie na rozrodczość|cytotoksyczn[a-ząćęłńóśźż]*|ekotoksykologi[a-ząćęłńóśźż]*|toksykologi[a-ząćęłńóśźż]*|toksykologiczn[a-ząćęłńóśźż]*|dioksyn[a-ząćęłńóśźż]*|ditlen(?:ek|ku) tytanu|wodorofluorowęglowodor[a-ząćęłńóśźż]*"),
            (2, r"chemical substances?|chemicals|hazardous substances?|hazardous mixtures?|polymers?|solvents?|fertilisers?|fertilizers?|cosmetic products?|cosmetics?|detergents?|toxicity|acute toxicity|corrosive|flammable|oxidising|exposure limits?|substancj[a-ząćęłńóśźż]* chemiczn[a-ząćęłńóśźż]*|chemikali[a-ząćęłńóśźż]*|substancj[a-ząćęłńóśźż]* niebezpieczn[a-ząćęłńóśźż]*|mieszanin[a-ząćęłńóśźż]* niebezpieczn[a-ząćęłńóśźż]*|polimer[a-ząćęłńóśźż]*|rozpuszczalnik[a-ząćęłńóśźż]*|nawoz[a-ząćęłńóśźż]*|nawozy|produkt[a-ząćęłńóśźż]* kosmetyczn[a-ząćęłńóśźż]*|kosmetyk[a-ząćęłńóśźż]*|detergent[a-ząćęłńóśźż]*|toksycznoś[ćci][a-ząćęłńóśźż]*|łatwopaln[a-ząćęłńóśźż]*|żrąc[a-ząćęłńóśźż]*"),
            (1, r"substances?|chemical|mixtures?|compounds?|residues?|concentrations?|substancj[a-ząćęłńóśźż]*|chemiczn[a-ząćęłńóśźż]*|mieszanin[a-ząćęłńóśźż]*|pozostałości[a-ząćęłńóśźż]*|stężeni[a-ząćęłńóśźż]*"),
        ],
        "agri_food": [
            (3, r"common agricultural policy|common fisheries policy|food safety|european food safety authority|efsa|novel foods?|foodstuffs?|food additives?|feed additives?|feedingstuffs?|animal feed|compound feed|animal nutrition|food and feed|phytosanitary|plant health|organic production|organic farming|geographical indications?|protected designation of origin|fishing opportunities|fish stocks?|total allowable catches?|by-catches?|aquaculture|livestock|wspóln[a-ząćęłńóśźż]* polityk[a-ząćęłńóśźż]* roln[a-ząćęłńóśźż]*|wspóln[a-ząćęłńóśźż]* polityk[a-ząćęłńóśźż]* rybołówstwa|bezpieczeństw[a-ząćęłńóśźż]* żywności|now[a-ząćęłńóśźż]* żywnoś[ćci][a-ząćęłńóśźż]*|środk[a-ząćęłńóśźż]* spożywcz[a-ząćęłńóśźż]*|dodatk[a-ząćęłńóśźż]* do żywności|dodatk[a-ząćęłńóśźż]* paszow[a-ząćęłńóśźż]*|pasz(?:a|y|ę|ą|om|ach|ami|e|owe|owych)|żywieni[a-ząćęłńóśźż]* zwierząt|żywnoś[ćci] i pasz|fitosanitarn[a-ząćęłńóśźż]*|zdrowi[aeu] roślin|produkcj[a-ząćęłńóśźż]* ekologiczn[a-ząćęłńóśźż]*|rolnictw[a-ząćęłńóśźż]* ekologiczn[a-ząćęłńóśźż]*|oznaczeni[a-ząćęłńóśźż]* geograficzn[a-ząćęłńóśźż]*|chronion[a-ząćęłńóśźż]* nazw[a-ząćęłńóśźż]* pochodzenia|uprawnieni[a-ząćęłńóśźż]* do połowów|stad[a-ząćęłńóśźż]* ryb|całkowit[a-ząćęłńóśźż]* dopuszczaln[a-ząćęłńóśźż]* połow[a-ząćęłńóśźż]*|przyłow[a-ząćęłńóśźż]*|akwakultur[a-ząćęłńóśźż]*|zwierz[a-ząćęłńóśźż]* gospodarsk[a-ząćęłńóśźż]*"),
            (2, r"agricultural|agriculture|farmers?|crops?|cereals?|wheat|barley|maize|rapeseed|dairy|bovine|porcine|ovine|caprine|poultry|mineral waters?|aerated waters?|fisheries|fishing vessels?|slaughter(?:house)?|animal welfare|seed certification|rolnictw[a-ząćęłńóśźż]*|rolnik[a-ząćęłńóśźż]*|gospodarstw[a-ząćęłńóśźż]* roln[a-ząćęłńóśźż]*|upraw[a-ząćęłńóśźż]*|zbóż|zboża|pszenic[a-ząćęłńóśźż]*|jęczmieni[a-ząćęłńóśźż]*|kukurydz[a-ząćęłńóśźż]*|rzepak[a-ząćęłńóśźż]*|mleczarsk[a-ząćęłńóśźż]*|bydł[ao]|trzod[a-ząćęłńóśźż]* chlewn[a-ząćęłńóśźż]*|drobi[u]?|wod[ay] mineraln[a-ząćęłńóśźż]*|wod[ay] gazowan[a-ząćęłńóśźż]*|rybołówstw[a-ząćęłńóśźż]*|połow(?:u|y|ów|om|ach)|statk[a-ząćęłńóśźż]* ryback[a-ząćęłńóśźż]*|uboj[u]?|rzeźni[a-ząćęłńóśźż]*|dobrostan[a-ząćęłńóśźż]* zwierząt|materiał[a-ząćęłńóśźż]* siewn[a-ząćęłńóśźż]*"),
            (1, r"food|feed|plants?|animals?|fish|species|harvest(?:ed)?|beverages?|sugar|wine|meat|milk|żywnoś[ćci][a-ząćęłńóśźż]*|roślin[a-ząćęłńóśźż]*|zwierząt|zwierzęta|ryb[ay]?|gatun(?:ek|ki|ków|kom|kach)|zbiorów|zbiory|napoj[a-ząćęłńóśźż]*|cukier|cukru|mięs[ao]"),
        ],
    }

    _COMPILED_RULES: Dict[str, List[Tuple[int, re.Pattern]]] = {}

    def __init__(self, use_doc_context: bool = True, threshold: int = 3):
        self.use_doc_context = use_doc_context
        self.threshold = threshold
        self.doc_profiles: Dict[str, Dict[str, Any]] = {}
        self.stat_classifier = OfflineTfidfBayesClassifier()
        if not DomainClassifier._COMPILED_RULES:
            DomainClassifier._COMPILED_RULES = {
                cat: [
                    (w, re.compile(f"{DomainClassifier._B_START}{pat}{DomainClassifier._B_END}", re.IGNORECASE))
                    for w, pat in rules
                ]
                for cat, rules in DomainClassifier._RAW_RULES.items()
            }

    def _score_single_lang(self, text: str) -> Tuple[Dict[str, int], Dict[str, bool]]:
        scores: Dict[str, int] = {cat: 0 for cat in SPECIALIZED_CATEGORIES}
        has_tier3: Dict[str, bool] = {cat: False for cat in SPECIALIZED_CATEGORIES}
        if not text:
            return scores, has_tier3

        stat_boosts = self.stat_classifier.score_boosts(text)
        for cat, rules in self._COMPILED_RULES.items():
            cat_score = 0
            for weight, regex in rules:
                distinct_hits = len({m.lower() for m in regex.findall(text)})
                if distinct_hits:
                    if weight >= 3:
                        has_tier3[cat] = True
                    cat_score += weight * min(distinct_hits, 2)
            scores[cat] = cat_score + stat_boosts.get(cat, 0)
        return scores, has_tier3

    def _score_pair(self, source_text: str, target_text: str, pivot_en_text: str = "") -> Tuple[Dict[str, int], Dict[str, bool]]:
        """
        Scores source, target, and optional pivot_en independently and takes the per-category
        maximum, avoiding EN+PL double-counting of the exact same translated concept.
        """
        scores: Dict[str, int] = {cat: 0 for cat in SPECIALIZED_CATEGORIES}
        has_tier3: Dict[str, bool] = {cat: False for cat in SPECIALIZED_CATEGORIES}

        for txt in (source_text, target_text, pivot_en_text):
            if not txt:
                continue
            s_map, t3_map = self._score_single_lang(txt)
            for cat in SPECIALIZED_CATEGORIES:
                if s_map[cat] > scores[cat]:
                    scores[cat] = s_map[cat]
                if t3_map[cat]:
                    has_tier3[cat] = True

        # Cross-domain suppression: if strong engineering/energy_env/chemicals hit occurs
        # and medical has no Tier-3 hit, suppress weak medical noise.
        if (scores["engineering"] >= 3 or scores["energy_env"] >= 3 or scores["chemicals"] >= 3) and not has_tier3["medical"]:
            if scores["medical"] < 4:
                scores["medical"] = 0

        return scores, has_tier3

    def _update_and_get_prior(self, doc_key: str, raw_scores: Dict[str, int]) -> Dict[str, int]:
        if not self.use_doc_context or not doc_key:
            return {cat: 0 for cat in SPECIALIZED_CATEGORIES}

        profile = self.doc_profiles.get(doc_key)
        if profile is None:
            profile = {"count": 0, "totals": {cat: 0 for cat in SPECIALIZED_CATEGORIES}}
            self.doc_profiles[doc_key] = profile

        if profile["count"] < 6:
            profile["count"] += 1
            for cat, val in raw_scores.items():
                profile["totals"][cat] += val

        # Dominant-only soft prior: +1 boost ONLY if domain is strongly established
        # AND represents at least 50% of the document's top domain score.
        priors: Dict[str, int] = {cat: 0 for cat in SPECIALIZED_CATEGORIES}
        totals = profile["totals"]
        max_total = max(totals.values()) if totals else 0
        if max_total >= 5:
            for cat in SPECIALIZED_CATEGORIES:
                if totals[cat] >= 5 and totals[cat] >= 0.5 * max_total:
                    priors[cat] = 1
        return priors

    def classify_multi(
        self,
        source_text: str,
        target_text: str,
        pivot_en_text: str = "",
        doc_key: str = ""
    ) -> List[str]:
        """
        Classifies a segment into one or more matching categories (multi-label).
        Falls back to ['general'] if no specialized domain meets the threshold.
        """
        raw_scores, _ = self._score_pair(source_text, target_text, pivot_en_text)
        priors = self._update_and_get_prior(doc_key, raw_scores)

        matched: List[str] = []
        for cat in SPECIALIZED_CATEGORIES:
            raw = raw_scores[cat]
            effective = raw + (priors[cat] if raw >= 2 else 0)
            if effective >= self.threshold:
                matched.append(cat)

        return matched if matched else ["general"]


class TMXExtractor:
    def __init__(
        self,
        source_lang: str,
        target_lang: str,
        deduplicate: bool = True,
        filter_identical: bool = True,
        min_length: int = 1,
        max_length: int = 0,
        max_translations: int = 0,
        capture_pivot_en: bool = False
    ):
        self.src_code = source_lang.upper()
        self.trg_code = target_lang.upper()
        self.deduplicate = deduplicate
        self.filter_identical = filter_identical
        self.min_length = min_length
        self.max_length = max_length
        self.max_translations = max_translations
        self.capture_pivot_en = capture_pivot_en and self.src_code != "EN" and self.trg_code != "EN"

        self.total_tus_seen = 0
        self.total_pairs_matched = 0
        self.duplicates_removed = 0
        self.identical_filtered = 0
        self.empty_filtered = 0
        self.pivot_en_found = 0
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
                    pivot_en_seg = None
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

                        elif self.capture_pivot_en and pivot_en_seg is None and self.matches_lang(lang, "EN"):
                            seg_elem = tuv.find("seg")
                            if seg_elem is not None:
                                pivot_en_seg = "".join(seg_elem.itertext()).strip()

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
                                if pivot_en_seg:
                                    self.pivot_en_found += 1
                                yield TranslationPair(
                                    source=src_seg,
                                    target=trg_seg,
                                    doc_id=doc_id,
                                    src_lang=src_full_lang or self.src_code,
                                    trg_lang=trg_full_lang or self.trg_code,
                                    pivot_en=pivot_en_seg or ""
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
            tuv_re = re.compile(r"<tuv\b[^>]*\b(?:xml:)?lang=[\"\x27]([^\"]+)[\"\x27][^>]*>\s*<seg>(.*?)</seg>", re.DOTALL)
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
                pivot_en_seg = None
                for l_key, s_val in tuvs.items():
                    if src_seg is None and self.matches_lang(l_key, self.src_code):
                        src_seg = s_val
                    elif trg_seg is None and self.matches_lang(l_key, self.trg_code):
                        trg_seg = s_val
                    elif self.capture_pivot_en and pivot_en_seg is None and self.matches_lang(l_key, "EN"):
                        pivot_en_seg = s_val

                if src_seg and trg_seg:
                    pair_key = (src_seg, trg_seg)
                    if self.deduplicate and pair_key in self.seen_hashes:
                        self.duplicates_removed += 1
                    else:
                        if self.deduplicate:
                            self.seen_hashes.add(pair_key)
                        self.total_pairs_matched += 1
                        if pivot_en_seg:
                            self.pivot_en_found += 1
                        yield TranslationPair(
                            source=src_seg,
                            target=trg_seg,
                            doc_id=doc_id,
                            pivot_en=pivot_en_seg or ""
                        )
        except Exception:
            pass


# ==============================================================================
# 5. WRITERS WITH RAM PROTECTION AND FILE CHUNKING
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
    Handles streaming output with optional segment chunking (_part01, _part02...)
    for CAT memory protection (Trados, memoQ, OmegaT).
    If no chunking is needed (only 1 part created), retains clean filename without suffix.
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

        if self.ext == "tmx":
            part_str = f"Part {self.current_part_num}. " if self.split_size > 0 else ""
            part_note = (
                f"{part_str}Exported from official European Union legislation resources (DGT-TM). "
                f"Prepared by: {AUTHOR} (in {ENVIRONMENT}, {YEAR}). License: MIT. "
                "Based on: TMXtract.jar (European Commission - DGT/JRC, 2013) and tmxtract (Rodrigo Nepomuceno, 2019, MIT)."
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


def _create_multi_writer(
    base_out: str,
    fmt_lower: str,
    source_lang: str,
    target_lang: str,
    split_size: int = 0
) -> MultiFormatWriter:
    """Factory helper creating a MultiFormatWriter for a given base path and format."""
    writers: List[ChunkedWriter] = []
    if fmt_lower in ("tmx", "all"):
        writers.append(ChunkedWriter(base_out, "tmx", source_lang, target_lang, split_size=split_size))
    if fmt_lower in ("tsv", "excel", "all"):
        writers.append(ChunkedWriter(base_out, "tsv", source_lang, target_lang, split_size=split_size))
    if fmt_lower in ("jsonl", "all"):
        writers.append(ChunkedWriter(base_out, "jsonl", source_lang, target_lang, split_size=split_size))
    if not writers:
        writers.append(ChunkedWriter(base_out, "tmx", source_lang, target_lang, split_size=split_size))
    return MultiFormatWriter(writers)


class CategoryRouterWriter:
    """
    Lazily creates and routes segments to per-category MultiFormatWriter instances
    (e.g., base_legal.tmx, base_business.tmx, ...), preventing empty files for
    categories that have 0 matching segments.
    """
    def __init__(
        self,
        base_out: str,
        fmt_lower: str,
        source_lang: str,
        target_lang: str,
        split_size: int = 0
    ):
        self.base_out = base_out
        self.fmt_lower = fmt_lower
        self.source_lang = source_lang
        self.target_lang = target_lang
        self.split_size = split_size
        self.writers_by_cat: Dict[str, MultiFormatWriter] = {}

    def write_for_category(self, category: str, pair: TranslationPair):
        mw = self.writers_by_cat.get(category)
        if mw is None:
            cat_base = f"{self.base_out}_{category}"
            mw = _create_multi_writer(cat_base, self.fmt_lower, self.source_lang, self.target_lang, self.split_size)
            self.writers_by_cat[category] = mw
        mw.write(pair)

    def close(self):
        for mw in self.writers_by_cat.values():
            mw.close()

    def get_all_parts(self) -> List[PartFileInfo]:
        parts: List[PartFileInfo] = []
        for cat in DOMAIN_CATEGORIES:
            mw = self.writers_by_cat.get(cat)
            if mw is not None:
                parts.extend(mw.get_all_parts())
        return parts


# ==============================================================================
# 6. EXPORT SUMMARY REPORT
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
    """Generates a comprehensive English summary text report for an extraction run."""
    now_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    total_in_mb = sum(s.size_bytes for s in sources) / (1024 * 1024)
    total_tus = stats["total_tus_seen"]
    unique_pairs = stats["extracted_pairs"]
    dup_removed = stats["duplicates_removed"]
    dup_pct = (dup_removed / (unique_pairs + dup_removed) * 100) if (unique_pairs + dup_removed) > 0 else 0.0

    lines = [
        "═" * 80,
        "          EU TRANSLATION MEMORY (DGT-TM) EXPORT REPORT",
        "═" * 80,
        "",
        "1. GENERAL EXPORT METADATA:",
        f"   • Generation timestamp:          {now_str}",
        f"   • Tool:                          EU TMX Extractor v{VERSION}",
        f"   • Author:                        {AUTHOR} (in {ENVIRONMENT}, {YEAR})",
        f"   • ORCID:                         {ORCID}",
        f"   • License:                       MIT License (see LICENSE file or run with --license)",
        f"   • Base Tools:                    TMXtract.jar (European Commission - DGT / JRC, 2013)",
        f"                                    and tmxtract (Rodrigo Nepomuceno, 2019, MIT)",
        f"   • Language Pair:                 {get_lang_display(source_lang)} -> {get_lang_display(target_lang)}",
        f"   • Source Code (ISO / DGT):       {source_lang.upper()} (in TMX: {source_lang.lower()})",
        f"   • Target Code (ISO / DGT):       {target_lang.upper()} (in TMX: {target_lang.lower()})",
        f"   • Operation Elapsed Time:        {stats['elapsed_seconds']:.2f} s",
        "",
        "2. SOURCE ASSETS:",
        f"   • Input Path:                    {input_path}",
        f"   • Processed Files:               {len(sources)} file(s) (.tmx / .zip)",
        f"   • Total Input Data Size:         {total_in_mb:.2f} MB",
        f"   • Total TU Units Scanned:        {total_tus:,}",
        "",
        "3. QUALITY & FILTERING STATISTICS:",
        f"   • Extracted Unique Pairs:        {unique_pairs:,}",
        f"   • Removed Duplicates:            {dup_removed:,} ({dup_pct:.1f}%)",
        f"   • Filtered Identical Segments:   {stats['identical_filtered']:,}",
        f"   • Filtered Empty Segments:       {stats['empty_filtered']:,}",
        f"   • Deduplication:                 {'ENABLED (clean unique translation memory)' if stats.get('deduplicated', True) else 'DISABLED'}",
    ]

    if stats.get("domain_mode"):
        inc_cats = stats.get("include_categories")
        inc_str = ", ".join(sorted(inc_cats)) if inc_cats else "all"
        lines.extend([
            f"   • Domain Classification Mode:    {stats['domain_mode']} (multi-label, filter: {inc_str})",
            f"   • Filtered Out by Domain:        {stats.get('filtered_by_category', 0):,}",
        ])
        cat_counts = stats.get("category_counts", {})
        if cat_counts:
            breakdown = ", ".join(f"{cat}: {cat_counts.get(cat, 0):,}" for cat in DOMAIN_CATEGORIES if cat_counts.get(cat, 0) > 0)
            lines.append(f"   • Domain Category Breakdown:     {breakdown}")
        if stats.get("domain_lang_warning"):
            lines.append(f"   • Domain Language Limitation:    {stats['domain_lang_warning']}")

    lines.extend([
        "",
        "4. GENERATED OUTPUT FILES:",
        f"   • Chunking (RAM Protection):     {'YES (max ' + str(split_size) + ' segments per file)' if split_size > 0 else 'NO (single file)'}",
        f"   • Total Output Files Created:    {len(output_parts)}",
    ])

    for idx, p in enumerate(output_parts, 1):
        mb = p.size_bytes / (1024 * 1024)
        lines.append(f"     [{idx}] {os.path.basename(p.file_path)} (format: {p.format_name.upper()}, segments: {p.segments_count:,}, size: {mb:.2f} MB)")
        lines.append(f"         Path: {p.file_path}")

    if stats.get("sample_preview"):
        lines.extend([
            "",
            "5. SAMPLE EXTRACTED TRANSLATION UNITS (PREVIEW):"
        ])
        for s_idx, (doc, s_text, t_text) in enumerate(stats["sample_preview"], 1):
            doc_info = f" [CELEX Document: {doc}]" if doc else ""
            lines.append(f"   --- Sample #{s_idx}{doc_info} ---")
            lines.append(f"   [{source_lang.upper()}]: {s_text}")
            lines.append(f"   [{target_lang.upper()}]: {t_text}")

    lines.extend([
        "",
        "═" * 80,
        " Generated TMX files are 100% compliant with the TMX 1.4 standard.",
        " You can import them directly into SDL Trados Studio, memoQ, OmegaT,",
        " Wordfast, CafeTran, or spreadsheet software (for TSV files).",
        "═" * 80
    ])

    report_text = "\n".join(lines)
    with open(report_file_path, "w", encoding="utf-8") as rf:
        rf.write(report_text)


# ==============================================================================
# 7. DGT-TM REPOSITORY DOWNLOAD AND DISK SUMMARY
# ==============================================================================

def get_disk_space_info(folder_path: str) -> Dict[str, Any]:
    """Retrieves disk space parameters for the partition containing folder_path."""
    try:
        usage = shutil.disk_usage(folder_path)
        return {
            "total_bytes": usage.total,
            "used_bytes": usage.used,
            "free_bytes": usage.free,
            "total_gb": usage.total / (1024 ** 3),
            "free_gb": usage.free / (1024 ** 3),
            "free_mb": usage.free / (1024 ** 2),
        }
    except Exception:
        return {
            "total_bytes": 100 * (1024 ** 3),
            "used_bytes": 50 * (1024 ** 3),
            "free_bytes": 50 * (1024 ** 3),
            "total_gb": 100.0,
            "free_gb": 50.0,
            "free_mb": 50000.0,
        }


def estimate_dgt_volume_size(filename: str) -> int:
    """Estimates download size in bytes based on filename pattern."""
    fn = filename.lower()
    if "2025" in fn or "2024" in fn:
        return 320 * 1024 * 1024
    if "2023" in fn or "2022" in fn:
        return 220 * 1024 * 1024
    if "2021" in fn or "2020" in fn:
        return 160 * 1024 * 1024
    if "2019" in fn or "2018" in fn or "2017" in fn or "2016" in fn:
        return 110 * 1024 * 1024
    if "2015" in fn or "2014" in fn or "2013" in fn or "2012" in fn:
        return 65 * 1024 * 1024
    if "2011" in fn:
        return 25 * 1024 * 1024
    if "2010" in fn:
        return 20 * 1024 * 1024
    return 15 * 1024 * 1024


def get_repository_disk_summary(dest_folder: str, volumes: List[Tuple[str, str, str]]) -> Dict[str, Any]:
    """
    Checks destination folder status:
    - Existing valid ZIP archives
    - Files remaining to download
    - Estimated required disk space
    - Available free space on partition
    """
    os.makedirs(dest_folder, exist_ok=True)
    disk_info = get_disk_space_info(dest_folder)

    existing = []
    to_download = []
    existing_bytes = 0
    missing_bytes_est = 0

    for item in volumes:
        fn = item[0]
        url = item[1]
        title = item[2] if len(item) > 2 else ""
        dest_file = os.path.join(dest_folder, fn)
        is_valid = False
        if os.path.isfile(dest_file) and os.path.getsize(dest_file) > 50:
            try:
                with zipfile.ZipFile(dest_file, "r") as zf:
                    _ = zf.namelist()
                is_valid = True
            except Exception:
                is_valid = False

        if is_valid:
            existing.append(dest_file)
            existing_bytes += os.path.getsize(dest_file)
        else:
            to_download.append((fn, url, title))
            missing_bytes_est += estimate_dgt_volume_size(fn)

    buffer_bytes = min(1024 * 1024 * 1024, max(100 * 1024 * 1024, int(missing_bytes_est * 0.2)))
    has_enough_space = disk_info["free_bytes"] > (missing_bytes_est + buffer_bytes)
    is_critical_space = disk_info["free_bytes"] < missing_bytes_est

    return {
        "dest_folder": os.path.abspath(dest_folder),
        "total_volumes": len(volumes),
        "existing_count": len(existing),
        "existing_paths": existing,
        "existing_bytes": existing_bytes,
        "existing_gb": existing_bytes / (1024 ** 3),
        "to_download_count": len(to_download),
        "to_download_volumes": to_download,
        "to_download_bytes_est": missing_bytes_est,
        "to_download_gb_est": missing_bytes_est / (1024 ** 3),
        "disk_free_gb": disk_info["free_gb"],
        "disk_total_gb": disk_info["total_gb"],
        "has_enough_space": has_enough_space,
        "is_critical_space": is_critical_space
    }


def display_disk_space_summary(summary: Dict[str, Any], title: str = "DGT-TM REPOSITORY AND DISK SPACE SUMMARY") -> None:
    """Displays a clean, informative disk summary banner."""
    UI.section(title)
    print(f" {UI.c('* Destination folder:', UI.BOLD)}         {summary['dest_folder']}")
    print(f" {UI.c('* Total repository volumes:', UI.BOLD)}    {summary['total_volumes']} ZIP files")
    if summary['existing_count'] > 0:
        print(f" {UI.c('* Already downloaded locally:', UI.BOLD)}  {summary['existing_count']} files " + UI.c(f"({summary['existing_gb']:.2f} GB - will be skipped)", UI.GREEN))
    print(f" {UI.c('* New files to download:', UI.BOLD)}        {summary['to_download_count']} ZIP files")
    est_gb_str = f"~{summary['to_download_gb_est']:.2f} GB"
    print(f" {UI.c('* Estimated download size:', UI.BOLD)}     {UI.c(est_gb_str, UI.YELLOW)} (compressed ZIP archives)")

    free_str = f"{summary['disk_free_gb']:.1f} GB free (on drive with {summary['disk_total_gb']:.1f} GB)"
    if summary['has_enough_space']:
        status_tag = UI.c("[OK] Sufficient free space available", UI.GREEN)
    elif summary['is_critical_space']:
        status_tag = UI.c("[CRITICALLY LOW DISK SPACE! Risk of disk full]", UI.RED)
    else:
        status_tag = UI.c("[WARNING - LIMITED DISK SPACE]", UI.YELLOW)

    print(f" {UI.c('* Available disk space:', UI.BOLD)}       {free_str}")
    print(f" {UI.c('* Disk space status:', UI.BOLD)}           {status_tag}")
    print(UI.c("-" * 72, UI.DIM))


def download_dgt_volume(url: str, dest_folder: str, show_summary: bool = True, target_filename: Optional[str] = None) -> str:
    """Downloads a single DGT-TM ZIP archive with real-time speed and progress reporting."""
    import urllib.request
    filename = target_filename or url.split("/")[-1]
    dest_path = os.path.join(dest_folder, filename)
    os.makedirs(dest_folder, exist_ok=True)

    if os.path.exists(dest_path) and os.path.getsize(dest_path) > 50:
        try:
            with zipfile.ZipFile(dest_path, "r") as z_test:
                _ = z_test.namelist()
            UI.info(f"File '{filename}' already exists and is verified in: {dest_folder}. Using existing file.")
            return dest_path
        except zipfile.BadZipFile:
            UI.warning(f"File '{filename}' exists but is corrupted. Re-downloading...")
            try:
                os.remove(dest_path)
            except OSError:
                pass

    if show_summary:
        disk_info = get_disk_space_info(dest_folder)
        est_mb = estimate_dgt_volume_size(filename) / (1024 * 1024)
        print(f" {UI.c('Estimated size:', UI.BOLD)} ~{est_mb:.1f} MB | {UI.c('Available disk space:', UI.BOLD)} {disk_info['free_gb']:.1f} GB")

    UI.info(f"Starting download: {filename}")
    UI.info(f"Source: {url}")
    UI.info(f"Saving directly to: {dest_path}")

    start_time = time.time()

    def progress_callback(block_num, block_size, total_size):
        if total_size <= 0: return
        downloaded = block_num * block_size
        pct = min(1.0, downloaded / total_size)
        mb_down = downloaded / (1024 * 1024)
        mb_tot = total_size / (1024 * 1024)
        elapsed = time.time() - start_time
        speed_mb = (downloaded / (1024 * 1024)) / elapsed if elapsed > 0.5 else 0.0
        bar_len = 25
        filled = int(bar_len * pct)
        bar = "=" * filled + "-" * (bar_len - filled)
        sys.stdout.write(f"\r [{bar}] {pct*100:5.1f}% | {mb_down:6.1f} / {mb_tot:6.1f} MB | {speed_mb:4.1f} MB/s ")
        sys.stdout.flush()

    try:
        opener = urllib.request.build_opener()
        opener.addheaders = [("User-Agent", f"EU-TMX-Extractor/{VERSION}")]
        urllib.request.install_opener(opener)
        urllib.request.urlretrieve(url, dest_path, reporthook=progress_callback)
        print()
        if os.path.exists(dest_path) and os.path.getsize(dest_path) > 50:
            with zipfile.ZipFile(dest_path, "r") as z_verify:
                _ = z_verify.namelist()
            UI.success(f"Successfully downloaded to: {dest_path}")
            return dest_path
        else:
            raise RuntimeError("Downloaded file is incomplete or corrupted.")
    except Exception as e:
        print()
        if os.path.exists(dest_path):
            try:
                os.remove(dest_path)
            except OSError:
                pass
        raise RuntimeError(f"Error downloading {url}: {e}")


def download_dgt_repository_batch(
    dest_folder: str,
    volumes: Optional[List[Tuple[str, str, str]]] = None,
    prompt_confirmation: bool = True,
    interactive_post_action: bool = True
) -> Optional[Tuple[str, Any]]:
    """
    Downloads the entire DGT-TM repository (or a given slice) file by file.
    Displays a clear disk space summary before starting.
    Concludes with a prompt asking whether to proceed directly to TMX extraction or exit.
    """
    if volumes is None:
        cat = fetch_live_catalog_if_possible() or DGT_OFFICIAL_CATALOG
        volumes = []
        for y in sorted(cat.keys(), reverse=True):
            volumes.extend(cat[y])

    summary = get_repository_disk_summary(dest_folder, volumes)
    display_disk_space_summary(summary)

    if summary["to_download_count"] == 0:
        UI.success("All selected ZIP files already exist in your destination folder and are valid!")
    else:
        if summary["is_critical_space"]:
            UI.warning(f"Very low free disk space ({summary['disk_free_gb']:.1f} GB) compared to estimated download ({summary['to_download_gb_est']:.1f} GB)!")
            if prompt_confirmation:
                proceed = UI.prompt("Do you still want to proceed at your own risk? [y/N]", default="n")
                if proceed.strip().lower() not in ("y", "yes", "t", "tak"):
                    UI.info("Download operation was cancelled.")
                    return None
        elif prompt_confirmation:
            proceed = UI.prompt(f"\nDo you want to start downloading now ({summary['to_download_count']} new ZIP files)? [Y/n]", default="y")
            if proceed.strip().lower() not in ("y", "yes", "t", "tak"):
                UI.info("Download operation was cancelled.")
                return None

    all_valid_zips = list(summary["existing_paths"])
    downloaded_count = 0
    skipped_count = summary["existing_count"]
    errors = []
    total_count = summary["total_volumes"]

    to_dl = summary["to_download_volumes"]
    start_all_time = time.time()

    for idx, (fn, url, title) in enumerate(to_dl, 1):
        curr_idx = skipped_count + idx
        dest_file = os.path.join(dest_folder, fn)
        title_str = f" ({title})" if title else ""
        print(f"\n[{curr_idx}/{total_count}] Downloading archive: {UI.c(fn, UI.BOLD)}{title_str}")
        try:
            download_dgt_volume(url, dest_folder, show_summary=False, target_filename=fn)
            if os.path.isfile(dest_file) and os.path.getsize(dest_file) > 50:
                all_valid_zips.append(dest_file)
                downloaded_count += 1
            else:
                raise RuntimeError("Downloaded archive does not exist or is corrupted.")
        except Exception as err:
            UI.error(f"Failed to download {fn}: {err}")
            errors.append((fn, url, str(err)))
            if prompt_confirmation:
                try:
                    action = UI.prompt("What would you like to do? [1] Skip and continue, [2] Stop downloading", default="1")
                    if action.strip() == "2":
                        UI.warning("Download interrupted by user.")
                        break
                except (EOFError, SystemExit):
                    break

    elapsed_tot = time.time() - start_all_time
    UI.section("REPOSITORY DOWNLOAD COMPLETED")
    print(f" {UI.c('* Total repository volumes:', UI.BOLD)}    {len(all_valid_zips)} / {total_count} ZIP files ready")
    print(f" {UI.c('* Downloaded in this session:', UI.BOLD)}  {downloaded_count} new files")
    print(f" {UI.c('* Previously existing:', UI.BOLD)}         {skipped_count} files (skipped)")
    if errors:
        print(f" {UI.c('* Download errors:', UI.BOLD)}             " + UI.c(f"{len(errors)} files", UI.RED))
        for e_fn, _, e_msg in errors:
            print(f"   - {e_fn}: {e_msg}")
    else:
        print(f" {UI.c('* Download errors:', UI.BOLD)}             " + UI.c("0 (all files downloaded successfully)", UI.GREEN))
    print(f" {UI.c('* Elapsed time:', UI.BOLD)}                {elapsed_tot:.1f} s")
    print(f" {UI.c('* Files saved to folder:', UI.BOLD)}       {dest_folder}")
    print(UI.c("-" * 72, UI.DIM))

    if not all_valid_zips:
        UI.error("No ZIP archives were downloaded. Cannot proceed to extraction.")
        return None

    all_valid_zips = sorted(list(set(all_valid_zips)))

    if interactive_post_action:
        print()
        UI.section("WHAT WOULD YOU LIKE TO DO NEXT?")
        print(f" [{UI.c('1', UI.GREEN)}] Proceed directly to TMX extraction (Batch mode across all {len(all_valid_zips)} files) [Recommended]")
        print(f" [{UI.c('2', UI.YELLOW)}] Finish and exit here (ZIP files remain safely stored on disk)")
        print()
        choice = UI.prompt("Select option (1 or 2)", default="1").strip()
        if choice == "2":
            print()
            UI.success("All ZIP files have been safely saved to folder:")
            print(f" 📂 {UI.c(dest_folder, UI.BOLD)}")
            UI.info("You can run the program anytime to extract TMX translation memories.")
            UI.info("Thank you for using EU TMX Extractor!")
            return ("exit", None)
        else:
            return ("batch", all_valid_zips)

    return ("batch", all_valid_zips)


def get_default_tmx_dir() -> str:
    """
    Returns the default TMX storage/download folder:
    - If running inside '--- APP ---' (or sibling '../TMX' exists), returns '<parent>/TMX'.
    - Otherwise returns '<script_dir>/TMX' (if writable) or '<cwd>/TMX'.
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(script_dir)
    if os.path.basename(script_dir) == "--- APP ---" or os.path.isdir(os.path.join(parent_dir, "TMX")):
        return os.path.join(parent_dir, "TMX")
    base = script_dir if os.access(script_dir, os.W_OK) else os.getcwd()
    return os.path.join(base, "TMX")


def select_and_download_dgt_volume(dest_folder: Optional[str] = None) -> Optional[Union[str, Tuple[str, Any]]]:
    """Interactive menu for downloading official DGT-TM packages from data.europa.eu."""
    if not dest_folder:
        dest_folder = get_default_tmx_dir()

    UI.section("DOWNLOAD OFFICIAL EU DGT-TM PACKAGES (data.europa.eu)")
    print(UI.c(" Official dataset: https://data.europa.eu/data/datasets/dgt-translation-memory?locale=en", UI.CYAN))
    chosen_dest = UI.prompt("Destination folder for downloaded DGT-TM ZIP files", default=dest_folder)
    if chosen_dest.strip():
        dest_folder = os.path.abspath(os.path.expanduser(chosen_dest.strip()))
    os.makedirs(dest_folder, exist_ok=True)
    print(UI.c(f" Active download folder: {dest_folder}", UI.YELLOW))
    print()

    cat = fetch_live_catalog_if_possible()
    years = sorted(cat.keys(), reverse=True)
    if not years:
        cat = DGT_OFFICIAL_CATALOG
        years = sorted(cat.keys(), reverse=True)

    flat_all = []
    for y in years:
        flat_all.extend(cat[y])

    print(f" [{UI.c('W', UI.GREEN)}] DOWNLOAD ENTIRE REPOSITORY AT ONCE (all {len(flat_all)} ZIP files, 2004–2025, file by file) [RECOMMENDED]")
    print(UI.c("-" * 72, UI.DIM))

    popular_years = ["2025", "2024", "2023", "2022", "2020", "2019", "2018"]
    menu_items = []
    for y in popular_years:
        if y in cat:
            count = len(cat[y])
            label = f"Year {y} ({count} {'parts' if count > 1 else 'part'})"
            if y == "2025":
                label += " [LATEST EU LEGISLATION]"
            menu_items.append((y, label))

    other_count = sum(len(cat[y]) for y in cat if y not in popular_years)
    menu_items.append(("ALL", f"Older years (2004–2017 – total {other_count} parts)"))
    menu_items.append(("CUSTOM", "Paste a direct Download URL from data.europa.eu"))

    for idx, (_, label) in enumerate(menu_items, 1):
        print(f" [{UI.c(str(idx), UI.CYAN)}] {label}")
    print(f" [{UI.c('0', UI.DIM)}] Back to main menu")

    y_choice = UI.prompt("\nSelect option (or 'W' to download entire repository, 0 to return)", default="W")
    if y_choice.strip() in ("0", "q", "exit", "back", "wroc"):
        return None

    if y_choice.strip().upper() in ("W", "ALL", "REPO", "EVERYTHING", "WSZYSTKO", "CALE"):
        return download_dgt_repository_batch(dest_folder, flat_all)

    chosen_code = None
    try:
        y_idx = int(y_choice) - 1
        if 0 <= y_idx < len(menu_items):
            chosen_code = menu_items[y_idx][0]
    except ValueError:
        chosen_code = y_choice.strip()

    if chosen_code == "CUSTOM":
        custom_url = UI.prompt("Paste direct Download URL (starting with http:// or https://)")
        if custom_url.startswith("http"):
            return download_dgt_volume(custom_url.strip(), dest_folder, show_summary=True)
        else:
            UI.error("Invalid URL format.")
            return None

    elif chosen_code == "ALL":
        UI.section("Older DGT-TM years (2004–2017):")
        other_years = [y for y in years if y not in popular_years]
        for idx, y in enumerate(other_years, 1):
            print(f" [{UI.c(str(idx), UI.CYAN)}] Year {y} ({len(cat[y])} parts)")
        print(f" [{UI.c('0', UI.DIM)}] Back")
        o_choice = UI.prompt("Select year number", default="1")
        if o_choice.strip() in ("0", "q", "exit", "back", "wroc"):
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
    if len(parts) > 1:
        print(f" [{UI.c('W', UI.GREEN)}] Download ALL parts of year {selected_year} ({len(parts)} ZIP files, file by file)")
    for idx, (fn, url, title) in enumerate(parts, 1):
        title_str = f" – {title}" if title else ""
        print(f" [{UI.c(str(idx), UI.CYAN)}] {fn}{title_str}")
    print(f" [{UI.c('0', UI.DIM)}] Back")

    p_choice = UI.prompt(f"\nSelect part number to download (or 'W' for all parts, 0 to return)", default="W" if len(parts) > 1 else "1")
    if p_choice.strip() in ("0", "q", "exit", "back", "wroc"):
        return None

    if p_choice.strip().upper() in ("W", "ALL", "WSZYSTKO"):
        return download_dgt_repository_batch(dest_folder, parts)

    try:
        p_idx = int(p_choice) - 1
        target_fn, target_url, _ = parts[p_idx] if 0 <= p_idx < len(parts) else parts[0]
    except (ValueError, IndexError):
        target_fn, target_url, _ = parts[0]

    return download_dgt_volume(target_url, dest_folder, show_summary=True)


def find_local_data_sources() -> List[Tuple[str, str]]:
    """Automatically scans local directories for .zip and .tmx files."""
    candidates = []
    seen_paths = set()
    seen_names = set()

    script_dir = os.path.dirname(os.path.abspath(__file__))
    cwd = os.getcwd()
    default_tmx_dir = get_default_tmx_dir()

    dirs_to_scan = []
    for d in [default_tmx_dir, os.path.join(script_dir, "TMX"), os.path.join(cwd, "TMX"), script_dir, cwd]:
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
                    rel_loc = " (in program folder)"
                elif is_user_dl:
                    rel_loc = " (in your Downloads folder)"
                elif scan_dir == parent_dir:
                    rel_loc = " (in parent folder)"
                else:
                    rel_loc = f" (in {os.path.basename(scan_dir)})"
                candidates.append((full, f"ZIP Archive: {item} (~{size_mb:.1f} MB){rel_loc}"))

            elif os.path.isdir(full) and not item.startswith(".") and item not in ("__pycache__", "dgt_downloads"):
                tmx_count = len(glob.glob(os.path.join(full, "*.tmx")))
                if tmx_count > 0:
                    seen_paths.add(full)
                    seen_names.add(item)
                    rel_loc = " (in program folder)" if scan_dir == script_dir else f" (in {os.path.basename(scan_dir)})"
                    candidates.append((full, f"TMX Directory: {item} ({tmx_count} .tmx files){rel_loc}"))

    return candidates


# ==============================================================================
# 8. EXTRACTION EXECUTION ENGINE
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
    quiet: bool = False,
    include_categories: Optional[Set[str]] = None,
    split_by_category: bool = False
) -> Dict:
    """Executes extraction from input_path to output_path with optional domain filtering/splitting."""
    t_start = time.time()

    if not quiet:
        UI.info(f"Scanning files in: {input_path} ...")
    sources = discover_sources(input_path)
    if not sources:
        raise ValueError(f"No .tmx or .zip files found in: {input_path}")

    total_bytes = sum(s.size_bytes for s in sources)
    if not quiet:
        UI.success(f"Found {len(sources)} TMX files (total ~{total_bytes / (1024*1024):.1f} MB)")

    base_out = os.path.splitext(output_path)[0]
    fmt_lower = output_format.lower()

    domain_active = bool(split_by_category or include_categories is not None)
    classifier = DomainClassifier(use_doc_context=True) if domain_active else None
    category_counts: Dict[str, int] = {cat: 0 for cat in DOMAIN_CATEGORIES}
    filtered_by_category = 0
    written_pairs = 0

    if split_by_category:
        active_writer: Union[CategoryRouterWriter, MultiFormatWriter] = CategoryRouterWriter(
            base_out, fmt_lower, source_lang, target_lang, split_size=split_size
        )
    else:
        active_writer = _create_multi_writer(
            base_out, fmt_lower, source_lang, target_lang, split_size=split_size
        )

    extractor = TMXExtractor(
        source_lang=source_lang,
        target_lang=target_lang,
        deduplicate=deduplicate,
        filter_identical=filter_identical,
        max_translations=max_translations,
        capture_pivot_en=domain_active
    )

    sample_preview: List[Tuple[str, str, str]] = []
    total_files = len(sources)
    needs_en_pivot = (
        domain_active
        and source_lang.upper() not in ("EN", "PL")
        and target_lang.upper() not in ("EN", "PL")
    )

    if not quiet:
        split_desc = f", splitting: every {split_size:,} segments" if split_size > 0 else ", single file (no splitting)"
        dom_desc = ""
        if domain_active:
            dom_mode = "split-by-category" if split_by_category else "filtered"
            inc_lbl = ",".join(sorted(include_categories)) if include_categories else "all"
            dom_desc = f", domains: {dom_mode} ({inc_lbl})"
        UI.info(f"Starting extraction: {get_lang_display(source_lang)} -> {get_lang_display(target_lang)}{split_desc}{dom_desc}")
        if needs_en_pivot:
            UI.info(
                f"Language note: Domain dictionaries use EN/PL. For {source_lang.upper()} -> {target_lang.upper()}, "
                "classification relies on embedded English (<tuv lang='EN'>) variants inside multilingual DGT-TM units."
            )

    try:
        for idx, src_item in enumerate(sources, start=1):
            z_ref, stream = src_item.open_stream()
            doc_key_fallback = src_item.display_name
            try:
                for pair in extractor.parse_stream(stream):
                    if classifier is not None:
                        matched_cats = classifier.classify_multi(
                            pair.source,
                            pair.target,
                            pivot_en_text=pair.pivot_en,
                            doc_key=pair.doc_id or doc_key_fallback
                        )
                        if include_categories is not None:
                            matched_cats = [c for c in matched_cats if c in include_categories]
                        if not matched_cats:
                            filtered_by_category += 1
                            continue

                        for c in matched_cats:
                            category_counts[c] = category_counts.get(c, 0) + 1

                        if isinstance(active_writer, CategoryRouterWriter):
                            for c in matched_cats:
                                active_writer.write_for_category(c, pair)
                        else:
                            active_writer.write(pair)
                        written_pairs += 1
                    else:
                        active_writer.write(pair)
                        written_pairs += 1

                    if len(sample_preview) < 4:
                        sample_preview.append((pair.doc_id, pair.source, pair.target))

                    if max_translations > 0 and written_pairs >= max_translations:
                        break
            finally:
                if stream:
                    stream.close()
                if z_ref:
                    z_ref.close()

            if not quiet:
                elapsed = time.time() - t_start
                speed = (written_pairs / elapsed) if elapsed > 0 else 0
                UI.render_progress(idx, total_files, written_pairs, speed)

            if max_translations > 0 and written_pairs >= max_translations:
                if not quiet:
                    print()
                    UI.info(f"Target limit of {max_translations} pairs reached.")
                break

    finally:
        active_writer.close()
        if not quiet and sys.stdout.isatty():
            print()

    total_time = time.time() - t_start
    output_parts = active_writer.get_all_parts()

    domain_mode_label = ""
    if split_by_category and include_categories is not None:
        domain_mode_label = "filter + split"
    elif split_by_category:
        domain_mode_label = "split by category"
    elif include_categories is not None:
        domain_mode_label = "filter only"

    domain_lang_warning = ""
    if needs_en_pivot and (written_pairs + filtered_by_category) > 0 and extractor.pivot_en_found == 0:
        domain_lang_warning = (
            f"No English (EN) pivot segments were found in the input TMX for {source_lang.upper()} -> {target_lang.upper()}. "
            "Domain categorization uses EN/PL dictionaries and therefore cannot classify standalone bilingual TMX files lacking EN or PL."
        )
        if not quiet:
            UI.warning(domain_lang_warning)

    stats = {
        "files_processed": total_files,
        "total_tus_seen": extractor.total_tus_seen,
        "extracted_pairs": written_pairs,
        "duplicates_removed": extractor.duplicates_removed,
        "identical_filtered": extractor.identical_filtered,
        "empty_filtered": extractor.empty_filtered,
        "deduplicated": deduplicate,
        "elapsed_seconds": total_time,
        "sample_preview": sample_preview,
        "output_parts": output_parts,
        "output_files": [p.file_path for p in output_parts],
        "domain_mode": domain_mode_label,
        "include_categories": sorted(include_categories) if include_categories else None,
        "category_counts": category_counts if domain_active else {},
        "filtered_by_category": filtered_by_category,
        "pivot_en_found": extractor.pivot_en_found,
        "domain_lang_warning": domain_lang_warning,
    }

    report_path_en = f"{base_out}_report.txt"
    report_path_pl = f"{base_out}_raport.txt"
    generate_export_report(
        report_file_path=report_path_en,
        stats=stats,
        source_lang=source_lang,
        target_lang=target_lang,
        input_path=input_path,
        sources=sources,
        split_size=split_size,
        output_parts=output_parts
    )
    try:
        shutil.copyfile(report_path_en, report_path_pl)
    except Exception:
        pass

    stats["report_path"] = report_path_en
    return stats


def generate_master_batch_report(
    report_file_path: str,
    zip_paths: List[str],
    results: List[Tuple[str, Dict]],
    errors: List[Tuple[str, str]],
    source_lang: str,
    target_lang: str,
    output_dir: str,
    total_elapsed: float
):
    """Generates master summary report for batch extraction across multiple ZIP archives."""
    now_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    total_pairs = sum(st["extracted_pairs"] for _, st in results)
    total_tus = sum(st["total_tus_seen"] for _, st in results)
    total_dups = sum(st["duplicates_removed"] for _, st in results)
    all_parts = []
    for _, st in results:
        all_parts.extend(st.get("output_parts", []))

    lines = [
        "=" * 80,
        "          BATCH EXTRACTION MASTER REPORT (DGT-TM BATCH)",
        "=" * 80,
        "",
        "1. GENERAL BATCH METADATA:",
        f"   * Generation timestamp:           {now_str}",
        f"   * Program version:                EU TMX Extractor v{VERSION}",
        f"   * Author:                         {AUTHOR} (in {ENVIRONMENT}, {YEAR})",
        f"   * ORCID:                          {ORCID}",
        f"   * Language pair:                  {get_lang_display(source_lang)} -> {get_lang_display(target_lang)}",
        f"   * Total ZIP archives in batch:    {len(zip_paths)}",
        f"   * Successfully processed:         {len(results)}",
        f"   * Errors / skipped:               {len(errors)}",
        f"   * Total elapsed time:             {total_elapsed:.2f} s",
        f"   * Total unique pairs extracted:   {total_pairs:,} sentence pairs",
        f"   * Total TU units scanned:         {total_tus:,} TU",
        f"   * Total duplicates removed:       {total_dups:,}",
        f"   * Output directory:               {output_dir}",
        "",
        "2. DETAILED BREAKDOWN OF PROCESSED ZIP ARCHIVES:",
    ]

    for idx, (z_path, st) in enumerate(results, 1):
        z_name = os.path.basename(z_path)
        z_mb = os.path.getsize(z_path) / (1024 * 1024) if os.path.exists(z_path) else 0.0
        lines.append(f"   [{idx}] {z_name} (~{z_mb:.1f} MB):")
        lines.append(f"       - Extracted: {st['extracted_pairs']:,} pairs in {st['elapsed_seconds']:.2f} s")
        lines.append(f"       - Created files ({len(st['output_parts'])}):")
        for p in st["output_parts"]:
            p_mb = p.size_bytes / (1024 * 1024)
            lines.append(f"         * {os.path.basename(p.file_path)} ({p.segments_count:,} segments, {p_mb:.2f} MB)")
        if st.get("report_path"):
            lines.append(f"       - Detailed report: {st['report_path']}")

    if errors:
        lines.extend([
            "",
            "3. ERRORS ENCOUNTERED DURING PROCESSING:"
        ])
        for idx, (z_path, err_msg) in enumerate(errors, 1):
            lines.append(f"   [{idx}] {os.path.basename(z_path)}: {err_msg}")

    lines.extend([
        "",
        "=" * 80,
        " All generated TMX files are 100% compliant with the TMX 1.4 standard.",
        " You can import them directly into SDL Trados Studio, memoQ, OmegaT.",
        "=" * 80
    ])

    report_text = "\n".join(lines)
    with open(report_file_path, "w", encoding="utf-8") as rf:
        rf.write(report_text)


def run_batch_extraction(
    zip_paths: List[str],
    source_lang: str,
    target_lang: str,
    output_dir: str,
    output_format: str = "tmx",
    deduplicate: bool = True,
    filter_identical: bool = True,
    max_translations: int = 0,
    split_size: int = 0,
    quiet: bool = False,
    include_categories: Optional[Set[str]] = None,
    split_by_category: bool = False
) -> Dict:
    """Extracts TMX from all provided ZIP archives one by one (batch mode)."""
    t_batch_start = time.time()
    os.makedirs(output_dir, exist_ok=True)
    sorted_zips = sorted(zip_paths, key=lambda p: os.path.basename(p).lower())

    results: List[Tuple[str, Dict]] = []
    errors: List[Tuple[str, str]] = []
    all_output_parts: List[PartFileInfo] = []

    if not quiet:
        UI.header(f"STARTING BATCH EXTRACTION ({len(sorted_zips)} ZIP ARCHIVES)")
        UI.info(f"Language pair: {get_lang_display(source_lang)} -> {get_lang_display(target_lang)}")
        UI.info(f"Output directory: {output_dir}")
        if split_size > 0:
            UI.info(f"CAT splitting: every {split_size:,} segments per file")
        if split_by_category or include_categories is not None:
            inc_lbl = ", ".join(sorted(include_categories)) if include_categories else "all"
            UI.info(f"Domain routing: {'split by category' if split_by_category else 'filter only'} ({inc_lbl})")
        print()

    for idx, z_path in enumerate(sorted_zips, 1):
        z_name = os.path.basename(z_path)
        z_base = os.path.splitext(z_name)[0]
        out_base_name = f"{z_base}_{source_lang.lower()}_{target_lang.lower()}"
        out_file_path = os.path.join(output_dir, f"{out_base_name}.{output_format if output_format != 'all' else 'tmx'}")

        if not quiet:
            UI.section(f"[{idx}/{len(sorted_zips)}] Processing Archive: {z_name}")

        try:
            stats = run_extraction(
                input_path=z_path,
                source_lang=source_lang,
                target_lang=target_lang,
                output_path=out_file_path,
                output_format=output_format,
                deduplicate=deduplicate,
                filter_identical=filter_identical,
                max_translations=max_translations,
                split_size=split_size,
                quiet=quiet,
                include_categories=include_categories,
                split_by_category=split_by_category
            )
            results.append((z_path, stats))
            all_output_parts.extend(stats.get("output_parts", []))
            if not quiet:
                UI.success(f"Finished {z_name}: extracted {stats['extracted_pairs']:,} unique pairs.")
        except Exception as e:
            errors.append((z_path, str(e)))
            if not quiet:
                UI.error(f"Error processing {z_name}: {e}")

    total_batch_time = time.time() - t_batch_start
    master_report_en = os.path.join(
        output_dir, f"batch_summary_report_{source_lang.lower()}_{target_lang.lower()}.txt"
    )
    master_report_pl = os.path.join(
        output_dir, f"raport_zbiorczy_batch_{source_lang.lower()}_{target_lang.lower()}.txt"
    )

    generate_master_batch_report(
        report_file_path=master_report_en,
        zip_paths=sorted_zips,
        results=results,
        errors=errors,
        source_lang=source_lang,
        target_lang=target_lang,
        output_dir=output_dir,
        total_elapsed=total_batch_time
    )
    try:
        shutil.copyfile(master_report_en, master_report_pl)
    except Exception:
        pass

    total_extracted = sum(st["extracted_pairs"] for _, st in results)

    if not quiet:
        UI.header("BATCH EXTRACTION COMPLETED (SUMMARY)")
        UI.success(f"Processed {len(results)}/{len(sorted_zips)} ZIP archives successfully.")
        if errors:
            UI.warning(f"Archives with errors: {len(errors)}")
        UI.success(f"Total unique pairs extracted: {total_extracted:,}")
        UI.info(f"Total elapsed time: {total_batch_time:.2f} s")
        UI.info(f"Master batch report saved to: {master_report_en}")
        print("\n" + UI.c("Created Translation Memory files:", UI.BOLD))
        for p in all_output_parts:
            mb = p.size_bytes / (1024 * 1024)
            print(f"  * {os.path.basename(p.file_path)} ({p.segments_count:,} segments, {mb:.2f} MB)")
        print()

    return {
        "total_zips": len(sorted_zips),
        "successful_zips": len(results),
        "failed_zips": len(errors),
        "total_pairs": total_extracted,
        "total_elapsed": total_batch_time,
        "results": results,
        "errors": errors,
        "master_report_path": master_report_en,
        "all_output_parts": all_output_parts
    }


# ==============================================================================
# 9. USER-FRIENDLY INTERACTIVE WIZARD
# ==============================================================================

def _prompt_domain_options_wizard(src_lang: str = "EN", trg_lang: str = "PL") -> Tuple[Optional[Set[str]], bool, str]:
    """Prompts for optional domain filtering/splitting in Step 5 of the wizard."""
    cats_inline = ", ".join(DOMAIN_CATEGORIES)
    pair_has_en_or_pl = src_lang.upper() in ("EN", "PL") or trg_lang.upper() in ("EN", "PL")
    print()
    print(UI.c(" Domain categorization (10 market-aligned categories):", UI.BOLD))
    print(UI.c(f"   Categories: {cats_inline}", UI.DIM))
    print(UI.c("   [NOTE] Domain filtering is automated (machine-based) and is not 100% accurate.", UI.YELLOW))
    print(UI.c("          If a segment matches two or more categories, it is placed in all matching files.", UI.DIM))
    print(UI.c("   [LANG] Classification dictionaries are built for English and Polish (EN / PL).", UI.CYAN))
    print(UI.c("          For other pairs (e.g. FR -> DE), categorization works ONLY on official multilingual", UI.DIM))
    print(UI.c("          DGT-TM packages containing an English (<tuv lang='EN'>) variant – it will NOT work", UI.DIM))
    print(UI.c("          on standalone bilingual TMX files lacking EN or PL.", UI.DIM))
    if not pair_has_en_or_pl:
        print(UI.c(
            f"   [!] Active pair ({src_lang.upper()} -> {trg_lang.upper()}) does not include EN or PL: "
            "ensure your input is a multilingual DGT-TM archive with EN segments!",
            UI.YELLOW + UI.BOLD
        ))
    print(f" [{UI.c('1', UI.CYAN)}] No domain splitting – keep all segments together [Default]")
    print(f" [{UI.c('2', UI.CYAN)}] Split output into separate files by domain (_legal, _finance, _trade, _it_telecom, _engineering, _energy_env, _medical, _chemicals, _agri_food, _general)")
    print(f" [{UI.c('3', UI.CYAN)}] Filter only selected domain categories")

    d_choice = UI.prompt("Select domain option", default="1").strip()
    if d_choice == "2":
        return None, True, "Split into separate files by category (10 domains, multi-label)"
    elif d_choice == "3":
        print(UI.c(" Available categories:", UI.BOLD))
        for c_code in DOMAIN_CATEGORIES:
            print(f"   * {UI.c(f'{c_code:<12}', UI.CYAN)} - {DOMAIN_LABELS.get(c_code, '')}")
        raw_cats = UI.prompt("Enter categories separated by commas (e.g. legal, finance, medical)", default="legal")
        inc_cats = parse_categories_arg(raw_cats) or {"legal"}
        split_ans = UI.prompt_yes_no("Split selected categories into separate files (instead of one combined file)?", default=True)
        cats_str = ", ".join(sorted(inc_cats))
        mode_lbl = f"Filter ({cats_str}) + split by category" if split_ans else f"Filter ({cats_str}) into single output"
        return inc_cats, split_ans, mode_lbl

    return None, False, "All segments together (no domain splitting)"


def run_interactive_wizard():
    """Runs the 5-step guided wizard for non-technical users with auto-scrolling."""
    UI.clear_screen()
    UI.header(f"EU TRANSLATION MEMORY EXTRACTOR (DGT-TM) v{VERSION}")
    print(UI.c(" ------------------------------------------------------------------", UI.DIM))
    print(f" {UI.c('Author:', UI.BOLD)}       {AUTHOR} (in {ENVIRONMENT}, {YEAR})")
    print(f" {UI.c('ORCID:', UI.BOLD)}        {ORCID}")
    print(f" {UI.c('License:', UI.BOLD)}      MIT License " + UI.c("(enter 'L' to read full license)", UI.DIM))
    print(f" {UI.c('Base tools:', UI.BOLD)}")
    print(f"   * TMXtract.jar - European Commission (DGT / JRC, 2013)")
    print(f"   * tmxtract - Rodrigo Nepomuceno (github.com/Nepomuceno/tmxtract, 2019, MIT)")
    print(UI.c(" ------------------------------------------------------------------", UI.DIM))
    print()
    print(UI.c(" Welcome! This program allows you to easily extract ready-to-use", UI.WHITE))
    print(UI.c(" translation memories (sentence databases) from official EU resources.", UI.WHITE))
    print(UI.c(" You can import TMX files directly into SDL Trados, memoQ, OmegaT,", UI.DIM))
    print(UI.c(" or open them in Microsoft Excel without writing any commands.", UI.DIM))

    # --- STEP 1: DATA SOURCE ---
    UI.section("STEP 1 OF 5: Where is your source data located?")
    script_dir = os.path.dirname(os.path.abspath(__file__))
    cwd = os.getcwd()
    out_dir = script_dir if os.access(script_dir, os.W_OK) else cwd
    local_candidates = find_local_data_sources()

    if local_candidates:
        print(UI.c(" Detected data files in your folder and surroundings:", UI.GREEN))
    else:
        print(UI.c(" [TIP] Save downloaded .zip files directly into the TMX folder:", UI.YELLOW))
        print(UI.c(f"    FOLDER: {get_default_tmx_dir()}", UI.BOLD))

    while True:
        menu_idx = 1
        options_map = {}

        all_detected_zips = [p for p, _ in local_candidates if p.lower().endswith(".zip")]
        if len(all_detected_zips) >= 2:
            print(f" [{UI.c('W', UI.GREEN)}] Process ALL above ZIP archives one by one (batch mode: {len(all_detected_zips)} files) [RECOMMENDED]")
            options_map["W"] = ("batch", all_detected_zips)
            options_map["w"] = ("batch", all_detected_zips)

        for path, label in local_candidates:
            print(f" [{UI.c(str(menu_idx), UI.CYAN)}] {label}")
            options_map[str(menu_idx)] = ("local", path)
            menu_idx += 1

        print(f" [{UI.c(str(menu_idx), UI.CYAN)}] Specify a custom directory or file path (.zip / .tmx)")
        options_map[str(menu_idx)] = ("custom", None)
        menu_idx += 1

        print(f" [{UI.c(str(menu_idx), UI.CYAN)}] Download official DGT-TM packages from the Internet (data.europa.eu)")
        options_map[str(menu_idx)] = ("download", None)

        print(f" [{UI.c('L', UI.MAGENTA)}] Read full MIT License and author information")

        def_choice = "1" if local_candidates else str(menu_idx - 1)
        choice = UI.prompt(f"\nSelect option number (or 'L' for license)", default=def_choice)
        if choice.strip().upper() in ("L", "LICENSE", "LICENCJA"):
            show_license()
            UI.step_banner(1, 5, "Where is your source data located?")
            continue
        break

    selected_type, selected_val = options_map.get(choice, ("custom", None))

    input_path = ""
    if selected_type == "local":
        input_path = selected_val
    elif selected_type == "download":
        dest_folder = get_default_tmx_dir()
        dl_res = select_and_download_dgt_volume(dest_folder)
        if not dl_res:
            UI.info("Download cancelled or returning to menu.")
            return
        if isinstance(dl_res, tuple):
            mode, val = dl_res
            if mode == "batch":
                selected_type = "batch"
                selected_val = val
                input_path = f"Batch mode from downloaded repository ({len(val)} ZIP files)"
            elif mode == "exit":
                return
            else:
                input_path = val
                selected_type = "local"
                selected_val = val
        else:
            input_path = dl_res
            selected_type = "local"
            selected_val = dl_res
    elif selected_type == "batch":
        input_path = f"Batch mode ({len(selected_val)} ZIP files)"
    else:
        while True:
            path_in = UI.prompt("Enter full path to file or directory")
            if not os.path.exists(path_in):
                UI.error(f"Path '{path_in}' does not exist. Please try again.")
                continue

            if os.path.isdir(path_in):
                dir_zips = [
                    os.path.join(path_in, f) for f in sorted(os.listdir(path_in))
                    if f.lower().endswith(".zip") and not f.lower().endswith("extractor.zip")
                ]
                if len(dir_zips) >= 2:
                    UI.info(f"Target folder contains {len(dir_zips)} ZIP archives.")
                    print(f" [{UI.c('1', UI.CYAN)}] Process all {len(dir_zips)} ZIP archives one by one (batch mode) [Recommended]")
                    print(f" [{UI.c('2', UI.CYAN)}] Select a specific single archive from this directory")
                    print(f" [{UI.c('3', UI.CYAN)}] Scan this directory as a plain folder with .tmx files")
                    c_mode = UI.prompt("Select option", default="1")
                    if c_mode == "1":
                        selected_type = "batch"
                        selected_val = dir_zips
                        input_path = f"Batch mode ({len(dir_zips)} ZIP files)"
                        break
                    elif c_mode == "2":
                        for z_i, z_p in enumerate(dir_zips, 1):
                            print(f" [{UI.c(str(z_i), UI.CYAN)}] {os.path.basename(z_p)}")
                        pick = UI.prompt("Select file number", default="1")
                        try:
                            p_i = int(pick) - 1
                            input_path = dir_zips[p_i] if 0 <= p_i < len(dir_zips) else dir_zips[0]
                        except (ValueError, IndexError):
                            input_path = dir_zips[0]
                        selected_type = "local"
                        selected_val = input_path
                        break
                    else:
                        input_path = path_in
                        selected_type = "local"
                        selected_val = path_in
                        break
                else:
                    input_path = path_in
                    selected_type = "local"
                    selected_val = path_in
                    break
            else:
                input_path = path_in
                selected_type = "local"
                selected_val = path_in
                break

    display_source = os.path.basename(input_path) if os.path.isfile(input_path) else input_path

    # --- STEP 2: LANGUAGE PAIR ---
    UI.step_banner(2, 5, "Which language pair do you want to extract?", [f"Source: {display_source}"])
    for i, (s, t, label) in enumerate(POPULAR_PAIRS, 1):
        print(f" [{UI.c(str(i), UI.CYAN)}] {label}")
    print(f" [{UI.c(str(len(POPULAR_PAIRS) + 1), UI.CYAN)}] Enter a custom language pair (e.g. 'de en' or 'german english')")

    p_choice = UI.prompt("\nSelect language pair number", default="1")
    src_lang, trg_lang = "EN", "PL"

    try:
        idx = int(p_choice) - 1
        if 0 <= idx < len(POPULAR_PAIRS):
            src_lang, trg_lang = POPULAR_PAIRS[idx][0], POPULAR_PAIRS[idx][1]
        else:
            custom_s = UI.prompt("Enter source language (e.g. EN, DE, English, German)")
            custom_t = UI.prompt("Enter target language (e.g. PL, FR, Polish, French)")
            src_lang = resolve_language_code(custom_s) or custom_s.upper()
            trg_lang = resolve_language_code(custom_t) or custom_t.upper()
    except ValueError:
        parts = p_choice.replace("-", " ").replace(">", " ").split()
        if len(parts) >= 2:
            src_lang = resolve_language_code(parts[0]) or parts[0].upper()
            trg_lang = resolve_language_code(parts[1]) or parts[1].upper()

    pair_display = f"{get_lang_display(src_lang)} -> {get_lang_display(trg_lang)}"

    # --- STEP 3: CAT RAM PROTECTION & SEGMENT SPLITTING ---
    UI.step_banner(3, 5, "CAT RAM Protection & Segment Splitting (Trados, memoQ, OmegaT)", [f"Source: {display_source}", f"Pair: {src_lang}->{trg_lang}"])
    print(UI.c(" Very large TMX files (>100k segments) can crash or freeze Trados or memoQ.", UI.DIM))
    print(UI.c(" Splitting into smaller parts (_part01, _part02...) ensures fast, stable imports.", UI.DIM))
    print(f" [{UI.c('1', UI.CYAN)}] Split every 50,000 segments [Recommended: Trados, memoQ, OmegaT]")
    print(f" [{UI.c('2', UI.CYAN)}] Split every 100,000 segments (for higher-end PCs)")
    print(f" [{UI.c('3', UI.CYAN)}] Enter custom segment limit per file")
    print(f" [{UI.c('4', UI.CYAN)}] No splitting – save everything into a single large file")

    split_choice = UI.prompt("\nSelect splitting option", default="1")
    split_size = 50000
    if split_choice == "1":
        split_size = 50000
    elif split_choice == "2":
        split_size = 100000
    elif split_choice == "3":
        custom_limit = UI.prompt("Enter segment limit per file (e.g. 30000)", default="50000")
        split_size = int(custom_limit) if custom_limit.isdigit() else 50000
    elif split_choice == "4":
        split_size = 0

    split_desc = f"{split_size:,} segments/file" if split_size > 0 else "Single file (no split)"

    # --- STEP 4: OUTPUT FORMAT AND DIRECTORY (BATCH VS SINGLE) ---
    if selected_type == "batch":
        UI.step_banner(4, 5, "Output Format and Destination Directory (Batch Mode)", [f"Source: {display_source}", f"Pair: {src_lang}->{trg_lang}", f"Splitting: {split_desc}"])
        print(f" [{UI.c('1', UI.CYAN)}] TMX (.tmx) – Standard Translation Memory (Trados, memoQ, OmegaT) [Recommended]")
        print(f" [{UI.c('2', UI.CYAN)}] Excel / TSV (.tsv) – Spreadsheet for immediate reading")
        print(f" [{UI.c('3', UI.CYAN)}] TMX + Excel/TSV (Both formats simultaneously)")
        print(f" [{UI.c('4', UI.CYAN)}] JSONL (.jsonl) – For AI fine-tuning / LLM datasets")
        print(f" [{UI.c('5', UI.CYAN)}] All formats (.tmx, .tsv, .jsonl)")

        f_choice = UI.prompt("\nSelect format", default="1")
        format_map = {"1": "tmx", "2": "tsv", "3": "all", "4": "jsonl", "5": "all"}
        out_format = format_map.get(f_choice, "tmx")

        print(UI.c("\nIn batch mode, each ZIP archive produces its own translation memory file:", UI.DIM))
        print(UI.c("e.g. Vol_2025.new_1.zip -> Vol_2025.new_1_en_pl.tmx (and text report)", UI.DIM))
        out_folder = UI.prompt("Destination folder for output files", default=out_dir)
        os.makedirs(out_folder, exist_ok=True)

        UI.step_banner(5, 5, "Data Quality and Filtering Options for Batch", [f"Source: {display_source}", f"Pair: {src_lang}->{trg_lang}", f"Format: {out_format.upper()}"])
        do_dedup = UI.prompt_yes_no("Remove duplicates (deduplicate identical translation pairs in each file)?", default=True)
        filter_ident = UI.prompt_yes_no("Filter out identical segments (e.g. exact same numbers/codes in both languages)?", default=True)
        limit_ans = UI.prompt("Maximum translation pairs per archive [Enter = NO LIMIT]", default="")
        max_count = int(limit_ans) if limit_ans.isdigit() else 0
        inc_cats, split_by_cat, dom_summary = _prompt_domain_options_wizard(src_lang, trg_lang)

        print()
        UI.header("BATCH EXTRACTION JOB SUMMARY")
        print(f"  * Total ZIP archives:  {UI.c(str(len(selected_val)), UI.BOLD)} files")
        for z_i, z_p in enumerate(selected_val[:5], 1):
            print(f"    [{z_i}] {os.path.basename(z_p)}")
        if len(selected_val) > 5:
            print(f"    ... and {len(selected_val) - 5} more")
        print(f"  * Language pair:       {UI.c(get_lang_display(src_lang), UI.GREEN)} -> {UI.c(get_lang_display(trg_lang), UI.GREEN)}")
        print(f"  * Output format:       {UI.c(out_format.upper(), UI.CYAN)}")
        print(f"  * Destination folder:  {UI.c(out_folder, UI.BOLD)}")
        print(f"  * Chunking for CAT:    {UI.c(f'YES (every {split_size:,} segments)' if split_size > 0 else 'NO (single file)', UI.YELLOW)}")
        print(f"  * Deduplication:       {'YES (clean unique memory)' if do_dedup else 'NO'}")
        print(f"  * Domain routing:      {dom_summary}")
        print()

        if not UI.prompt_yes_no("Do you want to start batch extraction across all archives now?", default=True):
            print("Cancelled by user.")
            return

        UI.clear_screen()
        run_batch_extraction(
            zip_paths=selected_val,
            source_lang=src_lang,
            target_lang=trg_lang,
            output_dir=out_folder,
            output_format=out_format,
            deduplicate=do_dedup,
            filter_identical=filter_ident,
            max_translations=max_count,
            split_size=split_size,
            quiet=False,
            include_categories=inc_cats,
            split_by_category=split_by_cat
        )
        UI.prompt("Press Enter to exit the program", default="")
        return

    # --- STEP 4: OUTPUT FORMAT AND FILE NAME (SINGLE FILE) ---
    UI.step_banner(4, 5, "Desired Output Format and File Naming", [f"Source: {display_source}", f"Pair: {src_lang}->{trg_lang}", f"Splitting: {split_desc}"])
    print(f" [{UI.c('1', UI.CYAN)}] TMX (.tmx) – Standard Translation Memory (Trados, memoQ, OmegaT) [Recommended]")
    print(f" [{UI.c('2', UI.CYAN)}] Excel / TSV (.tsv) – Spreadsheet for immediate reading")
    print(f" [{UI.c('3', UI.CYAN)}] TMX + Excel/TSV (Both formats simultaneously)")
    print(f" [{UI.c('4', UI.CYAN)}] JSONL (.jsonl) – For AI fine-tuning / LLM datasets")
    print(f" [{UI.c('5', UI.CYAN)}] All formats (.tmx, .tsv, .jsonl)")

    f_choice = UI.prompt("\nSelect format", default="1")
    format_map = {"1": "tmx", "2": "tsv", "3": "all", "4": "jsonl", "5": "all"}
    out_format = format_map.get(f_choice, "tmx")

    default_name = f"dgt_{src_lang.lower()}_{trg_lang.lower()}.tmx"
    out_name = UI.prompt("Base output filename", default=default_name)
    if os.path.isabs(out_name):
        out_path = out_name
    else:
        out_path = os.path.join(out_dir, out_name)

    # --- STEP 5: DATA QUALITY AND FILTERING ---
    UI.step_banner(5, 5, "Data Quality and Filtering Options", [f"Source: {display_source}", f"Pair: {src_lang}->{trg_lang}", f"Format: {out_format.upper()}"])
    do_dedup = UI.prompt_yes_no("Remove duplicates (deduplicate identical translation pairs)?", default=True)
    filter_ident = UI.prompt_yes_no("Filter out identical segments (e.g. same numbers or codes in both languages)?", default=True)
    limit_ans = UI.prompt("Maximum total sentence pairs [Enter = NO LIMIT]", default="")
    max_count = int(limit_ans) if limit_ans.isdigit() else 0
    inc_cats, split_by_cat, dom_summary = _prompt_domain_options_wizard(src_lang, trg_lang)

    print()
    UI.header("EXTRACTION JOB SUMMARY")
    print(f"  * Source data:       {UI.c(input_path, UI.BOLD)}")
    print(f"  * Language pair:     {UI.c(get_lang_display(src_lang), UI.GREEN)} -> {UI.c(get_lang_display(trg_lang), UI.GREEN)}")
    print(f"  * Output format:     {UI.c(out_format.upper(), UI.CYAN)}")
    print(f"  * Output file:       {UI.c(out_path, UI.BOLD)}")
    print(f"  * Chunking for CAT:  {UI.c(f'YES (every {split_size:,} segments)' if split_size > 0 else 'NO (single file)', UI.YELLOW)}")
    print(f"  * Deduplication:     {'YES (clean unique memory)' if do_dedup else 'NO'}")
    print(f"  * Domain routing:    {dom_summary}")
    print()

    if not UI.prompt_yes_no("Do you want to start extraction now?", default=True):
        print("Cancelled by user.")
        return

    UI.clear_screen()
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
        quiet=False,
        include_categories=inc_cats,
        split_by_category=split_by_cat
    )

    UI.header("EXTRACTION RESULTS & SUMMARY REPORT")
    pairs_cnt = stats['extracted_pairs']
    UI.success(f"Elapsed time:             {stats['elapsed_seconds']:.2f} seconds")
    UI.success(f"Files processed:          {stats['files_processed']}")
    UI.success(f"Segments scanned:         {stats['total_tus_seen']:,}")
    UI.success(f"Unique pairs extracted:  {UI.c(f' {pairs_cnt:,}', UI.BOLD + UI.GREEN)}")
    if do_dedup:
        UI.info(f"Duplicates removed:       {stats['duplicates_removed']:,}")
    if filter_ident:
        UI.info(f"Identical filtered:       {stats['identical_filtered']:,}")
    if stats.get("category_counts"):
        cat_str = ", ".join(f"{c}: {n:,}" for c, n in stats["category_counts"].items() if n > 0)
        if cat_str:
            UI.info(f"Domain breakdown:         {cat_str}")
        if stats.get("filtered_by_category"):
            UI.info(f"Filtered out by domain:   {stats['filtered_by_category']:,}")

    print("\n" + UI.c("Created Translation Memory files:", UI.BOLD))
    for p in stats["output_parts"]:
        mb = p.size_bytes / (1024 * 1024)
        print(f"  * {UI.c(p.file_path, UI.CYAN)} ({p.segments_count:,} segments, {mb:.2f} MB)")

    print(f"\n  [REPORT] {UI.c('Summary text report:', UI.BOLD)} {UI.c(stats['report_path'], UI.YELLOW)}")

    if stats.get("sample_preview"):
        UI.section("Sample preview of first extracted segments:")
        for idx, (doc, s, t) in enumerate(stats["sample_preview"][:3], 1):
            doc_str = f" [Document CELEX: {doc}]" if doc else ""
            print(f"\n {UI.c(f'Sample #{idx}{doc_str}:', UI.YELLOW)}")
            print(f"   {UI.c(src_lang + ':', UI.BOLD)} {s}")
            print(f"   {UI.c(trg_lang + ':', UI.GREEN)} {t}")

    print("\n" + UI.c("Done! You can now import your memory file into your CAT tool or Excel.", UI.BOLD + UI.GREEN))
    print()
    UI.prompt("Press Enter to exit the program", default="")


# ==============================================================================
# 10. COMMAND-LINE INTERFACE (CLI FOR ADVANCED USERS)
# ==============================================================================

def main():
    parser = argparse.ArgumentParser(
        description=f"EU TMX Extractor v{VERSION} - High-performance extractor for EU translation memories (DGT-TM).",
        formatter_class=argparse.RawTextHelpFormatter,
        epilog="""Usage examples:
  1. Interactive Wizard mode (step-by-step assistant for beginners):
     python3 tmx_extractor.py

  2. Extract with 50,000 segment chunking (for Trados/memoQ RAM stability):
     python3 tmx_extractor.py -i Vol_2009_4.zip -s EN -t PL -o memory_en_pl.tmx --split 50000

  3. Split output into 10 specialized translation domains (multi-label):
     python3 tmx_extractor.py -i Vol_2025.new_1.zip -s EN -t PL -o eu_mem.tmx --split-by-category

  4. Extract all ZIP archives in a folder one by one (batch mode):
     python3 tmx_extractor.py -i ./TMX --batch -s EN -t PL --output-dir ./results

  5. Download entire DGT-TM repository (all 87 volumes, 2004-2025, file by file):
     python3 tmx_extractor.py --download-repo --dest-dir ./TMX

  6. View MIT License:
     python3 tmx_extractor.py --license
"""
    )
    parser.add_argument("-i", "--input", help="Path to input .tmx file, .zip archive, or directory")
    parser.add_argument("-s", "--source-lang", default="EN", help="Source language code (e.g. EN, DE, FR, PL) [default: EN]")
    parser.add_argument("-t", "--target-lang", default="PL", help="Target language code (e.g. PL, EN, DE, ES) [default: PL]")
    parser.add_argument("-o", "--output", default="", help="Output base filename (.tmx, .tsv, .jsonl)")
    parser.add_argument("-f", "--format", choices=["tmx", "tsv", "jsonl", "all"], default="tmx", help="Output format [default: tmx]")
    parser.add_argument("--batch", action="store_true", help="Batch process all ZIP archives found in --input directory")
    parser.add_argument("--output-dir", default="", help="Output directory for batch processing")
    parser.add_argument("--split", type=int, default=0, help="Split output into files of N segments each (e.g. 50000) [0 = no split]")
    parser.add_argument(
        "--categories",
        default="",
        help=(
            "Filter domain categories (comma-separated: legal,finance,trade,it_telecom,engineering,"
            "energy_env,medical,chemicals,agri_food,general). Uses EN/PL dictionaries; pairs like FR-DE "
            "require multilingual DGT-TM input containing an EN <tuv>."
        )
    )
    parser.add_argument(
        "--split-by-category",
        action="store_true",
        help=(
            "Split output into separate files per domain category (_legal, _finance, _trade, etc.). "
            "Uses EN/PL dictionaries; pairs like FR-DE require multilingual DGT-TM input containing an EN <tuv>."
        )
    )
    parser.add_argument("--no-dedup", action="store_true", help="Disable duplicate removal (keep all repeated sentences)")
    parser.add_argument("--no-filter-identical", action="store_true", help="Keep segments identical in source and target")
    parser.add_argument("-m", "--max-count", type=int, default=0, help="Maximum number of translation pairs to extract [0 = unlimited]")
    parser.add_argument("-q", "--quiet", action="store_true", help="Quiet mode (suppress progress bar and banner)")
    parser.add_argument("--download-volume", help="Download a specific volume URL or filename")
    parser.add_argument("--download-repo", action="store_true", help="Download entire official DGT-TM repository (2004-2025) file by file")
    parser.add_argument("--dest-dir", default=get_default_tmx_dir(), help="Destination directory for downloads [default: TMX folder]")
    parser.add_argument("--license", action="store_true", help="Display full MIT license and author information")

    args = parser.parse_args()

    if args.license:
        print(MIT_LICENSE_TEXT)
        return

    if args.download_repo:
        download_dgt_repository_batch(dest_folder=args.dest_dir, prompt_confirmation=not args.quiet, interactive_post_action=False)
        return

    if args.download_volume:
        download_dgt_volume(args.download_volume, dest_folder=args.dest_dir, show_summary=not args.quiet)
        return

    if not args.input:
        run_interactive_wizard()
        return

    src = resolve_language_code(args.source_lang) or args.source_lang.upper()
    trg = resolve_language_code(args.target_lang) or args.target_lang.upper()
    inc_cats = parse_categories_arg(args.categories)

    if args.batch:
        if os.path.isfile(args.input) and args.input.lower().endswith(".zip"):
            zip_files = [args.input]
        elif os.path.isdir(args.input):
            zip_files = [
                os.path.join(args.input, f) for f in sorted(os.listdir(args.input))
                if f.lower().endswith(".zip") and not f.lower().endswith("extractor.zip")
            ]
        else:
            UI.error(f"Batch input path must be a directory or ZIP file: {args.input}")
            sys.exit(1)

        if not zip_files:
            UI.error(f"No ZIP archives found in: {args.input}")
            sys.exit(1)

        target_out_dir = args.output_dir or (args.input if os.path.isdir(args.input) else os.path.dirname(args.input))
        run_batch_extraction(
            zip_paths=zip_files,
            source_lang=src,
            target_lang=trg,
            output_dir=target_out_dir,
            output_format=args.format,
            deduplicate=not args.no_dedup,
            filter_identical=not args.no_filter_identical,
            max_translations=args.max_count,
            split_size=args.split,
            quiet=args.quiet,
            include_categories=inc_cats,
            split_by_category=args.split_by_category
        )
        return

    out_file = args.output
    if not out_file:
        base_name = f"dgt_{src.lower()}_{trg.lower()}.{args.format if args.format != 'all' else 'tmx'}"
        out_file = os.path.join(os.getcwd(), base_name)

    run_extraction(
        input_path=args.input,
        source_lang=src,
        target_lang=trg,
        output_path=out_file,
        output_format=args.format,
        deduplicate=not args.no_dedup,
        filter_identical=not args.no_filter_identical,
        max_translations=args.max_count,
        split_size=args.split,
        quiet=args.quiet,
        include_categories=inc_cats,
        split_by_category=args.split_by_category
    )


if __name__ == "__main__":
    main()
