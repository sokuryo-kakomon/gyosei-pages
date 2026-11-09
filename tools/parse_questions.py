"""センターの問題 PDF（rX_mondai.pdf）から問題を切り出す。
使い方: python tools/parse_questions.py genpon/r6_mondai.pdf work/q_r6.json
出力: [{num, kind, stem, items:[{key,text}], choices:[{key,text}], words:[{key,text}], raw}]
kind: choice（5肢択一）・tashi（多肢選択 41〜43）・kijutsu（記述 44〜46）"""
import json
import re
import sys
import unicodedata

import fitz

KANA = 'アイウエオカキク'


def raw_lines(p):
    """get_text() と同じ行の並びで、ルビ（小さい字 7pt 未満）だけ落とす。"""
    lines = []
    for b in p.get_text('dict')['blocks']:
        for l in b.get('lines', []):
            t = ''.join(s['text'] for s in l['spans'] if s['size'] >= 7)
            if t or not any(s['text'].strip() for s in l['spans']):
                lines.append(t)
    return lines


def page_text(p):
    lines = raw_lines(p)
    out = []
    first = True
    for ln in lines:
        s = ln.rstrip()
        # ページ番号（ページの頭の数字だけの行）・下書用のマス目の数字（10・15…）・節の見出しは捨てる。
        # 1〜5 だけの行は肢の番号のことがあるので残す
        if re.fullmatch(r'\s*\d{1,2}\s*', s):
            if first or int(s) > 5:
                first = False
                continue
        if s.strip():
            first = False
        if re.match(r'^(法\s*令\s*等|基礎知識|一般知識等?)\s*［', s) or re.match(r'^問題\d+～問題\d+は', s):
            continue
        if s.startswith('［問題') or s in ('(', ')', '（下書用）'):
            continue
        out.append(s)
    return out


def join_lines(lines):
    """折り返しを戻す。肢・記述の頭（「1 　」「ア」だけの行）は区切りとして残す。"""
    out = []
    for s in lines:
        t = s.strip()
        if not t:
            continue
        head = re.match(r'^([1-5])\s*　', t) or re.fullmatch(r'[1-5]', t) or re.fullmatch(r'[アイウエオ]', t) \
            or re.match(r'^[アイウエオ]\s*　', t)
        if re.fullmatch(r'[1-5アイウエオ]', t):
            out.append(t + '　')   # 番号だけの行: 次の行がその肢の本文
        elif head or not out:
            out.append(t)
        elif out[-1].endswith('　') and re.fullmatch(r'[1-5アイウエオ]　', out[-1]):
            out[-1] += t
        else:
            out[-1] += t
    return out


def split_marked(lines, pat):
    """先頭が pat の行から始まる塊に分ける。"""
    blocks, cur = [], None
    for t in lines:
        m = re.match(pat, t)
        if m:
            cur = {'key': m.group(1), 'text': t[m.end():].strip()}
            blocks.append(cur)
        elif cur is not None:
            cur['text'] += t
        else:
            blocks.append({'key': None, 'text': t})
    return blocks


def parse(path):
    doc = fitz.open(path)
    lines = []
    for i, p in enumerate(doc):
        if i == 0:
            continue  # 表紙（注意事項）。記入例の「問題1・問題2」を拾わない
        lines += page_text(p)
    text = '\n'.join(lines)
    # 表紙（注意事項）を落とす: 本文の最初の「問題N　」の手前まで
    parts = re.split(r'\n(?=問題\s*(\d{1,2})(?:\s*[　 ]|\n|$))', '\n' + text)
    qs = []
    for k in range(1, len(parts) - 1, 2):
        num = int(parts[k])
        body = parts[k + 1]
        body = re.sub(r'^問題\s*\d{1,2}\s*', '', body)
        raw = body.strip()
        kind = 'tashi' if 41 <= num <= 43 else 'kijutsu' if 44 <= num <= 46 else 'choice'
        q = {'num': num, 'kind': kind, 'raw': raw, 'stem': '', 'items': [], 'choices': [], 'words': []}
        ls = join_lines(raw.split('\n'))
        if kind == 'kijutsu':
            q['stem'] = ''.join(l for l in ls if not re.fullmatch(r'[\d\s]+', l))
        elif kind == 'tashi':
            # 選択肢 1〜20 は末尾の「1 　語」の並び（1行に複数あることがある）
            joined = '\n'.join(raw.split('\n'))
            m = re.search(r'\n1\s*　', joined)
            stem_part, word_part = (joined[:m.start()], joined[m.start():]) if m else (joined, '')
            q['stem'] = ''.join(stem_part.split('\n'))
            toks = re.split(r'(?:(?<=^)|(?<=[\s　]))(\d{1,2})\s*　', word_part.replace('\n', '　'))
            words = []
            for i in range(1, len(toks) - 1, 2):
                words.append({'key': toks[i], 'text': toks[i + 1].strip('　 ').strip()})
            q['words'] = words
        else:
            blocks = split_marked(ls, r'^([1-5])(?:\s*　|$)')
            stem = []
            choices = []
            for b in blocks:
                if b['key'] is None:
                    stem.append(b['text'])
                else:
                    choices.append(b)
            # 記述ア〜オ（組合せの問）は stem の中にある
            stem_lines = join_lines('\n'.join(stem).split('\n'))
            sb = split_marked(stem_lines, r'^([アイウエオ])(?:\s*　|$)')
            q['stem'] = ''.join(b['text'] for b in sb if b['key'] is None)
            q['items'] = [b for b in sb if b['key'] is not None]
            q['choices'] = choices
        qs.append(q)
    return qs


if __name__ == '__main__':
    qs = parse(sys.argv[1])
    json.dump(qs, open(sys.argv[2], 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(sys.argv[1], len(qs), [q['num'] for q in qs][:3], '...')
