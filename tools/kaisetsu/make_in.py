"""解説の書き手に渡す入力（tools/kaisetsu/in/<年>_NN-NN.json）を作る。
使い方: python tools/kaisetsu/make_in.py <年 r07 など> [1組の問数 既定 10]
"""
import json
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
y = sys.argv[1]
size = int(sys.argv[2]) if len(sys.argv) > 2 else 10
qs = [q for q in json.load(open(os.path.join(ROOT, 'src/data/questions.json'), encoding='utf-8')) if q['year'] == y]
qs.sort(key=lambda q: q['num'])
for i in range(0, len(qs), size):
    part = qs[i:i + size]
    out = []
    for q in part:
        d = {'id': f"{y}-{q['num']}", 'year': q['yearLabel'], 'num': q['num'], 'category': q['category'], 'kind': q['kind'],
             'stem': q['statementText'],
             'items': [[it['key'], it['text']] for it in q['items']],
             'choices': [[c['key'], c['text']] for c in q['choices']]}
        if q['kind'] == 'choice':
            d['answer'] = q['ok']
        elif q['kind'] == 'tashi':
            d['words'] = [[w['key'], w['text']] for w in q['words']]
            d['answer'] = q['blanks']
        else:
            d['model_answer'] = q['modelAnswer']
        out.append(d)
    name = f"{y}_{part[0]['num']:02d}-{part[-1]['num']:02d}.json"
    json.dump(out, open(os.path.join(ROOT, 'tools/kaisetsu/in', name), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(name, len(out))
