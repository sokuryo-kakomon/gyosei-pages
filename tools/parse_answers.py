"""センターの正解ページ rXans.html から、択一の正解・多肢選択の ア〜エ・記述の正解例を読む。
使い方: python tools/parse_answers.py genpon/r6ans.html  → JSON を標準出力へ"""
import html
import json
import re
import sys
import unicodedata


def norm(s):
    return unicodedata.normalize('NFKC', html.unescape(re.sub(r'<[^>]+>', '', s))).strip()


def parse(path):
    s = open(path, encoding='utf-8', errors='replace').read()
    sel_start = s.find('id="selective"')
    desc_start = s.find('id="descriptive"')
    sel = s[sel_start:desc_start if desc_start > 0 else None]
    desc = s[desc_start:] if desc_start > 0 else ''

    out = {'choice': {}, 'tashi': {}, 'kijutsu': {}}
    for row in re.findall(r'<tr[^>]*>(.*?)</tr>', sel, flags=re.S):
        cells = [norm(c) for c in re.findall(r'<t[dh][^>]*>(.*?)</t[dh]>', row, flags=re.S)]
        i = 0
        while i < len(cells):
            m = re.fullmatch(r'問題\s*(\d+)', cells[i].replace(' ', ''))
            if not m:
                i += 1
                continue
            n = int(m.group(1))
            rest = []
            j = i + 1
            while j < len(cells) and not re.fullmatch(r'問題\s*\d+', cells[j].replace(' ', '')):
                rest.append(cells[j])
                j += 1
            rest = [r for r in rest if r]
            if 41 <= n <= 43:
                out['tashi'][n] = rest
            else:
                out['choice'][n] = rest[0] if rest else ''
            i = j

    # 記述: 問題44〜46 の見出しの後に、1字ずつの表と（◯◯字）
    parts = re.split(r'問題\s*(4[4-6])', norm(re.sub(r'</t[dh]>', '|', desc)).replace('|', ''))
    for k in range(1, len(parts) - 1, 2):
        n = int(parts[k])
        body = re.sub(r'\s+', '', parts[k + 1])
        body = re.split(r'総務大臣指定|一般財団法人', body)[0]
        out['kijutsu'][n] = body
    return out


if __name__ == '__main__':
    print(json.dumps(parse(sys.argv[1]), ensure_ascii=False, indent=1))
