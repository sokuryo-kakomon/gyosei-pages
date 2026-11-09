"""宅建サイトから写した画面の文言を行政書士に直す（1回だけ使う）。"""
import os
import re

R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def edit(path, pairs):
    p = os.path.join(R, path)
    s = open(p, encoding='utf-8').read()
    for a, b in pairs:
        if a not in s:
            raise SystemExit(f'{path}: 見つからない: {a[:40]}')
        s = s.replace(a, b)
    open(p, 'w', encoding='utf-8', newline='').write(s)


edit('src/components/Header.astro', [('>宅建</span>', '>行政書士</span>')])
edit('src/components/QuestionPage.astro', [
    ('問題文は RETIO 公表の原文のまま', '問題文は行政書士試験研究センター公表の原文のまま'),
    ('`宅建 ${q.yearLabel.replace(/年度/, \'年\')} 問${q.num}（${q.category}）｜${SITE_NAME}`',
     '`行政書士 ${q.yearLabel.replace(/年度/, \'年\')} 問${q.num}（${q.category}・${q.kindLabel}）｜${SITE_NAME}`'),
    ('出典：一般財団法人 不動産適正取引推進機構 公表の{q.yearLabel}宅地建物取引士資格試験の試験問題',
     '出典：一般財団法人 行政書士試験研究センター 公表の{q.yearLabel}行政書士試験の試験問題（同センターの許諾を得て掲載）'),
])
edit('src/components/react/PracticeApp.tsx', [("shi: '宅建'", "shi: '行政書士'"), ('（宅建だけ）', '（行政書士だけ）')])
edit('src/components/TopHome.astro', [
    ("'takken_days_v1'", "'gyosei_days_v1'"),
    ("localStorage.getItem('takken_q_v1') || '{}'))) if", "localStorage.getItem('gyosei_q_v1') || '{}'))) if"),
    ("const prog = JSON.parse(localStorage.getItem('takken_q_v1')", "const prog = JSON.parse(localStorage.getItem('gyosei_q_v1')"),
])
edit('src/components/YearPage.astro', [('`宅建 ${y.label} 過去問', '`行政書士 ${y.label} 過去問')])
edit('src/lib/data.ts', [
    ("'宅建 過去問ドリル'", "'行政書士 過去問ドリル'"),
    ('// 宅建は /r07/q1/。', '// 行政書士は /r07/q1/。'),
    ("name: '宅建', full: '宅地建物取引士資格試験'", "name: '行政書士', full: '行政書士試験'"),
    ('`宅建試験の過去問 ${yearSpan(\'shi\').n}回分の演習`', '`行政書士試験の過去問 ${yearSpan(\'shi\').n}年分の演習`'),
])
edit('src/pages/about.astro', [('「宅建 過去問ドリル」', '「行政書士 過去問ドリル」')])
edit('src/pages/practice/index.astro', [('`宅建試験の過去問', '`行政書士試験の過去問')])
edit('public/robots.txt', [('takken-kakomon-drill.com', 'gyosei-kakomon-drill.com')])
edit('astro.config.mjs', [("'https://takken-kakomon-drill.com'", "'https://gyosei-kakomon-drill.com'")])

# lawref.ts: 法令名の表を行政書士の科目に
p = os.path.join(R, 'src/lib/lawref.ts')
s = open(p, encoding='utf-8').read()
s = re.sub(r"const NAMES: \[string, string\]\[\] = \[.*?\];", """const NAMES: [string, string][] = [
  ['行政手続法', 'gyoteho'], ['行政不服審査法', 'fufukuho'], ['行政事件訴訟法', 'gyosoho'], ['行訴法', 'gyosoho'],
  ['国家賠償法', 'kokubaiho'], ['地方自治法', 'chijiho'], ['会社法', 'kaishaho'], ['商法', 'shoho'],
  ['日本国憲法', 'kenpo'], ['憲法', 'kenpo'], ['民法', 'minpo'],
];""", s, flags=re.S)
s = s.replace('// 直前に出てきた法令名（民法／借地借家法／宅建業法 …）を文脈として持ち回る。',
              '// 直前に出てきた法令名（民法／行政手続法／会社法 …）を文脈として持ち回る。')
s = s.replace('// 法令名がまだ出ていなければ、分野ごとの既定（権利関係→民法・宅建業法→宅建業法）を使い、それも無ければリンクにしない。',
              '// 法令名がまだ出ていなければ、分野ごとの既定（民法→民法・憲法→憲法・商法→会社法）を使い、それも無ければリンクにしない。')
s = s.replace('// 長い名前を先に（「宅地建物取引業法施行規則」などは法律ではないので、名前の後ろに「施行」が続くときは外す）',
              '// 長い名前を先に（「地方自治法施行令」などは法律ではないので、名前の後ろに「施行」が続くときは外す）')
open(p, 'w', encoding='utf-8', newline='').write(s)

open(os.path.join(R, 'public/CNAME'), 'w').write('gyosei-kakomon-drill.com\n')
print('ok')
