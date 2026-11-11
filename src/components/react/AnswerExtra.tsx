import { useEffect, useState } from 'react';
import type { Question } from '../../lib/types';
import { recordAnswer, type Rec } from '../../store/progress';
import KijutsuGrade from './KijutsuGrade';

// 多肢選択（問41〜43）: 空欄ア〜エそれぞれに語群 1〜20 から選び、まとめて答え合わせ。
// 1空欄2点・4つ全部合って「正解」と記録する（成績表の正答率は全部合った問の割合）。
export function TashiAnswer({ q, onDone }: { q: Question; onDone: (ok: boolean, rec: Rec) => void }) {
  const keys = Object.keys(q.blanks ?? {});
  const [sel, setSel] = useState<Record<string, number>>({});
  const [checked, setChecked] = useState(false);
  useEffect(() => { setSel({}); setChecked(false); }, [q.id]);
  const words = q.words ?? [];
  const wordOf = (n: number) => words.find((w) => Number(w.key) === n)?.text ?? '';
  const right = keys.filter((k) => sel[k] === q.blanks![k]).length;
  const check = () => {
    setChecked(true);
    const all = right === keys.length;
    const rec = recordAnswer(q.id, right, keys.length, [keys.length]);
    onDone(all, rec);
  };
  return (
    <div>
      <div className="qhtml mb-3">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-x-3 gap-y-1 text-[.93rem] bg-paper rounded-dojo px-3 py-2">
          {words.map((w) => <div key={w.key}><b className="mr-1">{w.key}</b>{w.text}</div>)}
        </div>
      </div>
      <div className="space-y-2">
        {keys.map((k) => {
          const ok = checked && sel[k] === q.blanks![k];
          const ng = checked && !ok;
          return (
            <label key={k} className={'flex flex-wrap items-center gap-2 px-3 py-2 rounded-dojo border ' +
              (ok ? 'border-moss bg-moss-pale' : ng ? 'border-shu bg-shu-pale' : 'border-line bg-card')}>
              <span className="blank">{k}</span>
              <select className="border border-line rounded-dojo px-2 py-1 bg-white text-sm min-w-[12rem]" disabled={checked}
                value={sel[k] ?? ''} onChange={(e) => setSel({ ...sel, [k]: Number(e.target.value) })}>
                <option value="">選ぶ</option>
                {words.map((w) => <option key={w.key} value={w.key}>{w.key}　{w.text}</option>)}
              </select>
              {checked && <span className="text-sm font-bold">{ok ? '○' : `× 正解は ${q.blanks![k]} ${wordOf(q.blanks![k])}`}</span>}
            </label>
          );
        })}
      </div>
      {!checked ? (
        <button type="button" className="btn btn-primary mt-3" disabled={keys.some((k) => !sel[k])} onClick={check}>答え合わせ</button>
      ) : (
        <div className={'mt-3 px-4 py-3 rounded-dojo font-bold flex flex-wrap items-center gap-3 ' + (right === keys.length ? 'bg-moss-pale text-moss-deep' : 'bg-shu-pale text-shu')}>
          <span>{right === keys.length ? '全問正解！' : `${keys.length}つ中 ${right}つ正解`}（{right * 2}点／{keys.length * 2}点）</span>
          <button type="button" className="btn btn-ghost btn-sm" onClick={() => { setSel({}); setChecked(false); }}>もう一度</button>
        </div>
      )}
    </div>
  );
}

// 記述（問44〜46）: 40字程度で書き、センターの正解例と見比べて自分で採点する。
// AI の採点は有料プランの機能（KijutsuGrade）。
export function KijutsuAnswer({ q, onDone, onReveal }: { q: Question; onDone: (ok: boolean, rec: Rec) => void; onReveal: () => void }) {
  const [text, setText] = useState('');
  const [shown, setShown] = useState(false);
  const [graded, setGraded] = useState<number | null>(null);
  useEffect(() => { setText(''); setShown(false); setGraded(null); }, [q.id]);
  const len = [...text.replace(/\s/g, '')].length;
  const grade = (v: number) => {
    setGraded(v);
    // 自己採点: 2＝書けた（正解と記録）・1＝一部・0＝書けなかった
    const rec = recordAnswer(q.id, v, 2, [2]);
    onDone(v === 2, rec);
  };
  return (
    <div>
      <textarea className="w-full border border-line rounded-dojo px-3 py-2 bg-white text-[1rem] leading-relaxed" rows={3} maxLength={120}
        placeholder="40字程度で書く（句読点も1字）" value={text} onChange={(e) => setText(e.target.value)} />
      <div className="flex flex-wrap items-center gap-3 mt-1 text-sm">
        <span className={len > 45 ? 'text-shu font-bold' : 'text-ink-soft'}>{len}字</span>
        {!shown && (
          <button type="button" className="btn btn-primary btn-sm" onClick={() => { setShown(true); onReveal(); }}>正解例と見比べる</button>
        )}
        <KijutsuGrade q={q} answer={text} />
      </div>
      {shown && (
        <div className="mt-3">
          <div className="qhtml"><div className="keybox text-[.95rem]"><b>センター公表の正解例</b><br />{(q.modelAnswer ?? '').split(/(?=正解例\d)/).map((s, i) => <div key={i}>{s}</div>)}</div></div>
          {graded === null ? (
            <div className="flex flex-wrap items-center gap-2 mt-2 text-sm">
              <span className="font-bold">自分で採点：</span>
              <button type="button" className="btn btn-ghost btn-sm" onClick={() => grade(2)}>◎ 要点は書けた</button>
              <button type="button" className="btn btn-ghost btn-sm" onClick={() => grade(1)}>△ 一部書けた</button>
              <button type="button" className="btn btn-ghost btn-sm" onClick={() => grade(0)}>× 書けなかった</button>
            </div>
          ) : (
            <div className={'mt-2 px-4 py-2 rounded-dojo font-bold ' + (graded === 2 ? 'bg-moss-pale text-moss-deep' : 'bg-shu-pale text-shu')}>
              {graded === 2 ? '◎ 書けた' : graded === 1 ? '△ 一部書けた（要復習に入れておくと良いです）' : '× 書けなかった（要復習に入れておくと良いです）'}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
