import { useEffect, useState } from 'react';
import { useStore } from '@nanostores/react';
import type { Question } from '../../lib/types';
import { $aiCode, AI_ENDPOINT, postJson } from '../../store/ai';

// 記述式（問44〜46）の AI 採点。有料プランだけ（利用コードを中継サーバーに送り、向こうで回数を数える）。
// 回数は「AI に質問」と共通（1日15回・月90回）。採点は目安で、センターは採点基準を公表していない。
type Item = { point: string; max: number; got: number; reason: string };
type Result = { score: number; items: Item[]; comment: string; betterAnswer: string; chars: number };

export default function KijutsuGrade({ q, answer }: { q: Question; answer: string }) {
  const code = useStore($aiCode);
  const [busy, setBusy] = useState(false);
  const [res, setRes] = useState<Result | null>(null);
  const [err, setErr] = useState('');
  const [upsell, setUpsell] = useState(false);
  useEffect(() => { setRes(null); setErr(''); setUpsell(false); }, [q.id]);
  if (!AI_ENDPOINT) return null;

  const run = async () => {
    setErr(''); setRes(null); setUpsell(false);
    if (!code) { setUpsell(true); return; }
    setBusy(true);
    try {
      const { ok, data } = await postJson<Result & { plan?: string }>('/grade', { qid: q.id, answer: answer.trim(), code });
      if (ok) setRes(data);
      else { setErr(data.error || '採点できませんでした。'); if (data.plan === 'none' || data.plan === 'stopped') setUpsell(true); }
    } catch {
      setErr('通信に失敗しました。電波の良い所でもう一度お試しください。');
    } finally { setBusy(false); }
  };

  const mark = (x: Item) => (x.got >= x.max ? '○' : x.got > 0 ? '△' : '×');
  return (
    <>
      <button type="button" className="btn btn-ghost btn-sm" disabled={busy || !answer.trim()} onClick={run}
        title={answer.trim() ? '' : '答えを書くと押せます'}>
        {busy ? '🤖 採点しています…' : '🤖 AI で採点（有料プラン）'}
      </button>
      {(upsell || err || res) && (
        <div className="basis-full mt-2">
          {err && <p className="text-sm text-[#a33] mb-2">{err}</p>}
          {upsell && (
            <div className="card p-4 text-sm">
              <p className="mb-2">AI の採点は<b>有料プラン（月額980円）</b>の機能です。最上位の AI が、正解例と解説から採点の要素を分けて、要素ごとに点を付けます（AI に質問と合わせて1日15回まで）。</p>
              <a href="/ai/" className="btn btn-primary btn-sm no-underline">有料プランを見る</a>
              <span className="text-xs text-ink-faint ml-2">利用コードをお持ちの方も、このページから入れられます。</span>
            </div>
          )}
          {res && (
            <div className="card p-4 text-sm">
              <div className="flex flex-wrap items-baseline gap-3 mb-2">
                <span className="serif text-3xl text-moss-deep">{res.score}<span className="text-base text-ink-soft"> / 20点</span></span>
                <span className={res.chars > 45 ? 'text-shu font-bold' : 'text-ink-soft'}>{res.chars}字</span>
              </div>
              <ul className="divide-y divide-line mb-3">
                {res.items.map((x, i) => (
                  <li key={i} className="py-1.5 flex gap-2">
                    <b className={'w-5 shrink-0 ' + (mark(x) === '○' ? 'text-moss-deep' : 'text-shu')}>{mark(x)}</b>
                    <div className="min-w-0">
                      <div><b>{x.point}</b><span className="text-ink-soft ml-2">{x.got}/{x.max}点</span></div>
                      <div className="text-ink-soft">{x.reason}</div>
                    </div>
                  </li>
                ))}
              </ul>
              <p className="mb-2">{res.comment}</p>
              <div className="keybox"><b>書き直し例</b><br />{res.betterAnswer}</div>
              <p className="text-[.7rem] text-ink-faint mt-2">AI の採点は目安です。センターは記述式の採点基準を公表していません。</p>
            </div>
          )}
        </div>
      )}
    </>
  );
}
