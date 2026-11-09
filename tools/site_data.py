"""切り出した問題（work/q_rX.json）と正解（work/ans_rX.json）から、サイトの src/data/questions.json と site.json を作る。

使い方: python tools/site_data.py
- 問題文は原文のまま。センター自身が著作権の関係で載せていない問（問題1・58〜60 など）は PDF に無いので載らない
- kind: choice（5肢択一）・tashi（多肢選択 41〜43：空欄ア〜エに 1〜20 の語）・kijutsu（記述 44〜46：40字程度）
- 解説は tools/kaisetsu/out/*.json（照合済み ok.tsv の物だけ）。無ければ「準備中」と正解だけ
"""
import glob
import hashlib
import html
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
B = 'https://gyosei-shiken.or.jp'

# 新しい順
YEARS = [
    ('r07', 7, '令和7年度', 'R7', '2025年11月9日', 2025),
    ('r06', 6, '令和6年度', 'R6', '2024年11月10日', 2024),
    ('r05', 5, '令和5年度', 'R5', '2023年11月12日', 2023),
    ('r04', 4, '令和4年度', 'R4', '2022年11月13日', 2022),
    ('r03', 3, '令和3年度', 'R3', '2021年11月14日', 2021),
    ('r02', 2, '令和2年度', 'R2', '2020年11月8日', 2020),
]

# 問番号で分ける（平成18年度からの並び。令和6年度から「一般知識等」は「基礎知識」）
CATS = [
    ('基礎法学', '📜', 'kisohogaku', '#EFEBE9', '#5D4037', [1, 2]),
    ('憲法', '🏛️', 'kenpo', '#E3F2FD', '#1565C0', [3, 4, 5, 6, 7, 41]),
    ('行政法', '🏢', 'gyoseiho', '#E8F5E9', '#2E7D32', list(range(8, 27)) + [42, 43, 44]),
    ('民法', '⚖️', 'minpo', '#FCE4EC', '#AD1457', list(range(27, 36)) + [45, 46]),
    ('商法・会社法', '💼', 'shoho', '#FFF8E1', '#8D6E00', list(range(36, 41))),
    ('基礎知識', '📰', 'kiso', '#EDE7F6', '#4527A0', list(range(47, 61))),
]
KIND_LABEL = {'choice': '5肢択一式', 'tashi': '多肢選択式', 'kijutsu': '記述式'}

LAWS = [  # (key, 名前, e-Gov の法令ID)
    ('kenpo', '日本国憲法', '321CONSTITUTION'), ('minpo', '民法', '129AC0000000089'),
    ('gyoteho', '行政手続法', '405AC0000000088'), ('fufukuho', '行政不服審査法', '426AC0000000068'),
    ('gyosoho', '行政事件訴訟法', '337AC0000000139'), ('kokubaiho', '国家賠償法', '322AC0000000125'),
    ('chijiho', '地方自治法', '322AC0000000067'), ('kaishaho', '会社法', '417AC0000000086'),
    ('shoho', '商法', '132AC0000000048'),
]
KAISETSU = os.path.join(ROOT, 'tools', 'kaisetsu')
KANA = 'アイウエオ'


def kmd5(k):
    return hashlib.md5(json.dumps({x: k.get(x) for x in ('lead', 'notice', 'points', 'hint')},
                                  ensure_ascii=False, sort_keys=True).encode('utf-8')).hexdigest()


def kaisetsu():
    ok = {}
    p = os.path.join(KAISETSU, 'ok.tsv')
    if os.path.exists(p):
        for line in open(p, encoding='utf-8').read().split('\n')[1:]:
            if line.strip():
                i, m = line.split('\t')[:2]
                ok[i] = m
    out = {}
    for f in sorted(glob.glob(os.path.join(KAISETSU, 'out', '*.json'))):
        for i, k in json.load(open(f, encoding='utf-8')).items():
            if ok.get(i) == kmd5(k):
                out[i] = k
    return out


def kaisetsu_html(k, ok):
    e = html.escape
    parts = [f'<div class="notice">⚠ {e(k["notice"])}</div>'] if k.get('notice') else []
    parts.append(f'<p>{e(k["lead"])}</p>')
    for p in k['points']:
        key = p['k']
        label = f'肢{key}' if key.isdigit() else key
        cls = ' correct' if key.isdigit() and int(key) in ok else ''
        v = '　' + e(p['v']) if p.get('v') else ''
        parts.append(f'<div class="opt{cls}"><b>{e(label)}{v}</b>　{e(p["t"])}</div>')
    return '\n'.join(parts)


def h(s):
    return html.escape(s)


def blanks_html(s):
    """空欄の記号（単独のア〜オ）を枠で囲む。カタカナ語の中の字は囲まない。"""
    return re.sub(r'(?<![ァ-ヶー・])([アイウエオ])(?![ァ-ヶー])', r'<span class="blank">\g<1></span>', html.escape(s))


def tidy(s):
    """全角空白の連なり（PDF の字下げ・行末）を1つにする。"""
    return re.sub(r'[ 　]{2,}', '　', s).strip(' 　')



def wtidy(t):
    """語群の1語: 制御文字・行の折り返しの全角空白・後ろに付いた注意書きを外す。"""
    t = re.sub(r'[\x00-\x1f]', '', t)
    t = re.split(r'[\u3000 ]*解答は、', t)[0]
    return tidy(t.replace('\u3000', ''))

def category(n):
    for name, icon, slug, bg, fg, r in CATS:
        if n in r:
            return name, icon, slug, f'background:{bg};color:{fg};border-color:{fg}'


def combo(q):
    """「空欄ア〜オに当てはまる語句の組合せ」の表: 記述ア〜オが見出しだけなら、肢を ア／イ… の組に直す。"""
    items = q['items']
    if not items:
        return None
    head = ''.join(i['key'] + i['text'] for i in items)
    if re.sub(r'[\s　]', '', head) and not re.fullmatch(r'[アイウエオ]+', re.sub(r'[\s　]', '', head)):
        return None
    labels = re.findall(r'[アイウエオ]', head)
    rows = []
    for c in q['choices']:
        fields = [f for f in re.split(r'[ 　]{2,}|　', c['text'].strip(' 　')) if f]
        if len(fields) != len(labels):
            return None
        rows.append((c['key'], list(zip(labels, fields))))
    return labels, rows


def main():
    kai = kaisetsu()
    qs = []
    for y, yn, label, short, date, ad in YEARS:
        parsed = json.load(open(os.path.join(ROOT, 'work', f'q_r{yn}.json'), encoding='utf-8'))
        ans = json.load(open(os.path.join(ROOT, 'work', f'ans_r{yn}.json'), encoding='utf-8'))
        pdf = f'{B}/pdf/r{yn}_mondai.pdf'
        for r in parsed:
            n = r['num']
            kind = r['kind']
            cname, icon, slug, style = category(n)
            stem = tidy(r['stem'])
            item_list, choice_list, tables, choice_style = [], [], [], 'sentence'
            extra = {}
            if kind == 'choice':
                a = ans['choice'][str(n)]
                ok = [1, 2, 3, 4, 5] if a == '全員正解' else [int(a)]
                cb = combo(r)
                if cb:
                    labels, rows = cb
                    choice_list = [{'key': k, 'html': '　'.join(f'<span class="ck">{l}</span>{h(f)}' for l, f in fl),
                                    'text': '　'.join(f'{l}：{f}' for l, f in fl), 'value': int(k)} for k, fl in rows]
                    choice_style = 'sentence'
                else:
                    item_list = [{'key': i['key'], 'html': h(tidy(i['text'])), 'text': tidy(i['text'])} for i in r['items']]
                    choice_list = [{'key': c['key'], 'html': h(tidy(c['text'])), 'text': tidy(c['text']), 'value': int(c['key'])}
                                   for c in r['choices']]
                    if max(len(c['text']) for c in choice_list) <= 12:
                        choice_style = 'combo'
                if len(ok) == 5:
                    ans_html = '<p>正解は<b>なし</b>（受験者全員を正解として取り扱い）です。</p>'
                else:
                    ans_html = f'<p>正解は <b>{ok[0]}</b> です。</p>'
            elif kind == 'tashi':
                t = ans['tashi'][str(n)]
                blanks = {t[i]: int(t[i + 1]) for i in range(0, len(t) - 1, 2)}
                words = [{'key': w['key'], 'text': wtidy(w['text'])} for w in r['words']]
                assert len(words) == 20, (y, n, len(words))
                wmap = {int(w['key']): w['text'] for w in words}
                extra = {'blanks': blanks, 'words': words}
                ok = [0]
                ans_html = '<p>正解は ' + '・'.join(f'{k}＝<b>{v} {h(wmap[v])}</b>' for k, v in blanks.items()) + ' です。</p>'
                choice_style = 'none'
            else:
                model = ans['kijutsu'][str(n)]
                extra = {'modelAnswer': model}
                ok = [0]
                ans_html = '<p>センターが公表した<b>正解例</b>：</p><p class="model">' + \
                    h(model).replace('正解例', '<br>正解例').lstrip('<br>') + '</p>'
                choice_style = 'none'
            k = kai.get(f'{y}-{n}')
            src_note = '<p class="text-ink-soft">正解は一般財団法人 行政書士試験研究センターの公表によります。</p>'
            if k:
                expl = kaisetsu_html(k, ok) + '\n<div class="conc">' + re.sub(r'<[^>]+>', '', ans_html) + '</div>'
            else:
                expl = ans_html + src_note + '<p class="text-ink-soft">この問題の解説は準備中です。</p>'
            yl = label.replace('年度', '年')
            q = {
                'id': f'{y}-q{n}', 'year': y, 'yearNum': ad, 'yearLabel': label, 'num': n,
                'kind': kind, 'kindLabel': KIND_LABEL[kind],
                'answer': ok[0], 'ok': ok,
                'category': cname, 'categoryIcon': icon, 'categorySlug': slug, 'categoryStyle': style,
                'title': f'行政書士 {label} 問{n}〔{cname}・{KIND_LABEL[kind]}〕',
                'description': f'行政書士試験 {yl} 問{n}（{cname}・{KIND_LABEL[kind]}）の過去問。' + stem[:80] + ('…' if len(stem) > 80 else ''),
                'statementHtml': blanks_html(stem) if '空欄' in stem else h(stem),
                'statementText': stem,
                'items': item_list,
                'choices': choice_list,
                'choiceStyle': choice_style,
                'tablesHtml': tables,
                'figure': None,
                'explanationHtml': expl,
                'explanationText': re.sub(r'<[^>]+>', '', expl),
                'hint': k.get('hint', '') if k else '',
                'url': f'/{y}/q{n}/',
                'prev': None, 'next': None,
                'source': pdf,
                **extra,
            }
            qs.append(q)
    for a, b in zip(qs, qs[1:]):
        if a['year'] == b['year']:
            a['next'], b['prev'] = b['id'], a['id']
    bad = [q['id'] for q in qs if q['kind'] == 'choice' and len(q['choices']) != 5]
    assert not bad, bad

    with open(os.path.join(ROOT, 'src', 'data', 'questions.json'), 'w', encoding='utf-8') as f:
        json.dump(qs, f, ensure_ascii=False, indent=0)
    with open(os.path.join(ROOT, 'src', 'data', 'questions_hoshi.json'), 'w', encoding='utf-8') as f:
        f.write('[]\n')

    sp = os.path.join(ROOT, 'src', 'data', 'site.json')
    site = json.load(open(sp, encoding='utf-8'))
    site.update({
        'name': '行政書士 過去問ドリル',
        'legacyName': '行政書士 過去問ドリル',
        'url': 'https://gyosei-kakomon-drill.com',
        'amazonTag': '',
        'years': [{'id': y, 'num': ad, 'label': label, 'short': short, 'examDate': date, 'ad': ad,
                   'pdf': {'questions': f'{B}/pdf/r{yn}_mondai.pdf', 'answers': f'{B}/doc/exam/r{yn}ans.html'},
                   'count': sum(1 for q in qs if q['year'] == y)} for y, yn, label, short, date, ad in YEARS],
        'hoshiYears': [],
        'categories': [{'name': n, 'icon': i, 'slug': s, 'bg': bg, 'fg': fg, 'count': sum(1 for q in qs if q['categorySlug'] == s)}
                       for n, i, s, bg, fg, _ in CATS],
        'lawRefs': {
            'laws': [{'key': k, 'name': n, 'url': f'https://laws.e-gov.go.jp/law/{i}'} for k, n, i in LAWS],
            'summaries': {}, 'junsokuPages': {},
            'defaults': {'minpo': 'minpo', 'kenpo': 'kenpo', 'shoho': 'kaishaho'},
        },
        'source': {'name': '一般財団法人 行政書士試験研究センター「過去の試験問題」',
                   'url': f'{B}/doc/exam/index.html'},
    })
    with open(sp, 'w', encoding='utf-8') as f:
        json.dump(site, f, ensure_ascii=False, indent=1)
        f.write('\n')
    print(f'{len(qs)} 問・解説あり {len(kai)}', {c['name']: c['count'] for c in site['categories']},
          {kd: sum(1 for q in qs if q['kind'] == kd) for kd in KIND_LABEL})


if __name__ == '__main__':
    main()
