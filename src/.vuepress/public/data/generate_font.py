import csv
import os
import shutil
import sys
import tempfile
import urllib.request
import fontTools.merge
from fontname import main as fontname
from fontTools.subset import main as pyftsubset
from fontTools.ttLib.woff2 import compress as woff2_compress
from puj import *

FONTS_DIR = '../assets/fonts'


def is_cjk_basic(c):
    return 0x4E00 <= ord(c) <= 0x9FFF or 0x3400 <= ord(c) <= 0x4DBF


TEMP_DIR = tempfile.mkdtemp()

NOTO_SANS_SC_PATH = os.path.join(FONTS_DIR, 'NotoSansSC-Regular.otf')
BASIC_SUBSET_FONT_NAME_OTF = os.path.join(TEMP_DIR, 'NotoSansSC-Regular.generated.otf')
BASIC_SUBSET_FONT_NAME_WOFF2 = os.path.join(TEMP_DIR, 'NotoSansSC-Regular.generated.woff2')

PLANGOTHIC_PATH = os.path.join(FONTS_DIR, 'Plangothic.ttc')
SUBSET_FONT_NAME = 'CJKExtSubset'
SUBSET_FONT_NAME_TTF0 = os.path.join(TEMP_DIR, '0-CJKExtSubset.generated.ttf')
SUBSET_FONT_NAME_TTF1 = os.path.join(TEMP_DIR, '1-CJKExtSubset.generated.ttf')
SUBSET_FONT_NAME_TTF = os.path.join(TEMP_DIR, 'CJKExtSubset.generated.ttf')
SUBSET_FONT_NAME_WOFF2 = os.path.join(TEMP_DIR, 'CJKExtSubset.generated.woff2')


def ensure_noto_sans_sc():
    if not os.path.exists(NOTO_SANS_SC_PATH):
        url = 'https://github.com/notofonts/noto-cjk/raw/main/Sans/SubsetOTF/SC/NotoSansSC-Regular.otf'
        urllib.request.urlretrieve(url, NOTO_SANS_SC_PATH)


def ensure_plangothic():
    if not os.path.exists(PLANGOTHIC_PATH):
        url = 'https://github.com/Fitzgerald-Porthmouth-Koenigsegg/Plangothic-Project/raw/main/Plangothic.ttc'
        urllib.request.urlretrieve(url, PLANGOTHIC_PATH)


def basic_subset():
    if os.path.exists(BASIC_SUBSET_FONT_NAME_OTF):
        os.remove(BASIC_SUBSET_FONT_NAME_OTF)
    pyftsubset([
        NOTO_SANS_SC_PATH,
        f'--unicodes=U+4E00-9FFF,U+3400-4DBF',
        f'--output-file={BASIC_SUBSET_FONT_NAME_OTF}',
    ])

    woff2_compress(BASIC_SUBSET_FONT_NAME_OTF, BASIC_SUBSET_FONT_NAME_WOFF2)

    shutil.copy(BASIC_SUBSET_FONT_NAME_WOFF2, FONTS_DIR)


def subset(chars):
    # delete old subset font
    if os.path.exists(SUBSET_FONT_NAME_TTF):
        os.remove(SUBSET_FONT_NAME_TTF)
    pyftsubset([
        PLANGOTHIC_PATH,
        f'--text={"".join(chars)}',
        f'--output-file={SUBSET_FONT_NAME_TTF0}',
        f'--font-number=0',
    ])
    pyftsubset([
        PLANGOTHIC_PATH,
        f'--text={"".join(chars)}',
        f'--output-file={SUBSET_FONT_NAME_TTF1}',
        f'--font-number=1',
    ])
    # merge two subset fonts
    merger = fontTools.merge.Merger()
    font = merger.merge([f'{SUBSET_FONT_NAME_TTF0}', f'{SUBSET_FONT_NAME_TTF1}'])
    font.save(SUBSET_FONT_NAME_TTF)
    fontname([SUBSET_FONT_NAME, SUBSET_FONT_NAME_TTF])

    if os.path.exists(SUBSET_FONT_NAME_WOFF2):
        os.remove(SUBSET_FONT_NAME_WOFF2)
    woff2_compress(SUBSET_FONT_NAME_TTF, SUBSET_FONT_NAME_WOFF2)

    shutil.copy(SUBSET_FONT_NAME_WOFF2, FONTS_DIR)


def post_process():
    # delete tmp dir
    shutil.rmtree(TEMP_DIR)


def get_chars():
    with open('entries.csv', 'r', encoding='utf-8') as f:
        lines = f.readlines()
    lines = lines[1:]
    csv_reader = csv.reader(lines, delimiter=',')
    entries = [Entry(*line) for line in csv_reader]

    # CJK B~I
    result = set()
    for entry in entries:
        if not is_cjk_basic(entry.char):
            result.add(entry.char)
        if not is_cjk_basic(entry.char_sim):
            result.add(entry.char_sim)
    return result


if __name__ == '__main__':
    chars = get_chars()
    # ensure_noto_sans_sc()
    ensure_plangothic()
    # basic_subset()
    subset(chars)
    post_process()