import { persistentAtom } from '@nanostores/persistent';

// 学習記録（localStorage）。記録の形は測量士サイトと同じ。キーは行政書士用に分けてある。
//
// 将来ユーザー認証を入れてクラウド同期する場合は、この store を唯一の書き口として
// onProgressChange() で変更を拾い、ログイン中なら送信する形にする。
// コンポーネント側は store しか見ないので、同期先が増えても触らずに済む。

export interface Rec {
  answered: boolean;
  correct: boolean;       // 直近の解答が正解か
  userAnswer: number;
  correctAnswer: number;
  ngCount: number;        // 通算で間違えた回数
  okStreak: number;       // 連続正解数（間違えると 0 に戻る）
  attempts: number;
  at?: number;            // 直近の解答時刻（新サイトから追加。旧記録には無い）
}
export type Progress = Record<string, Rec>;

const codec = {
  encode: JSON.stringify,
  decode: (s: string) => { try { return JSON.parse(s); } catch { return undefined; } },
};

export const $progress = persistentAtom<Progress>('gyosei_q_v1', {}, codec);
export const $bookmarks = persistentAtom<string[]>('gyosei_bm_v1', [], codec);
// 解いた日（YYYY-MM-DD）の記録。Rec.at は問題ごとに最後の1回しか残らないので、連続日数はこちらで数える
export const $days = persistentAtom<string[]>('gyosei_days_v1', [], codec);

const dayKey = (d: Date) => `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;

// accepted: 複数正解・正解なし（全員正解）の問で正解と扱う番号すべて
export function recordAnswer(qid: string, userAnswer: number, correctAnswer: number, accepted?: number[]): Rec {
  const prev = $progress.get()[qid];
  const ok = accepted ? accepted.includes(userAnswer) : userAnswer === correctAnswer;
  const rec: Rec = {
    answered: true,
    correct: ok,
    userAnswer,
    correctAnswer,
    ngCount: (prev?.ngCount || 0) + (ok ? 0 : 1),
    okStreak: ok ? (prev?.okStreak || 0) + 1 : 0,
    attempts: (prev?.attempts || 0) + 1,
    at: Date.now(),
  };
  $progress.set({ ...$progress.get(), [qid]: rec });
  const today = dayKey(new Date());
  const days = $days.get();
  if (!days.includes(today)) $days.set([...days, today].slice(-400));
  return rec;
}

export function resetProgress() {
  $progress.set({});
  $bookmarks.set([]);
  $days.set([]);
}

export function toggleBookmark(qid: string) {
  const b = $bookmarks.get();
  $bookmarks.set(b.includes(qid) ? b.filter((x) => x !== qid) : [...b, qid]);
}

// 記録の answered は true と 1 の両方で入っている（前の作り・書き出しの読み込みなど）。読む所はどこも「真なら答えた」で読む
export const isAnswered = (r?: { answered?: unknown } | null) => !!r?.answered;
// 記述式の前回の自己採点：2＝要点は書けた・1＝一部・0＝書けなかった。数が無い古い記録は正誤から（正解なら 2、ほかは 0）
export function selfMarkOf(r?: Rec | null): 0 | 1 | 2 | null {
  if (!isAnswered(r)) return null;
  const v = Number(r!.userAnswer);
  if (v === 0 || v === 1 || v === 2) return v;
  return r!.correct ? 2 : 0;
}

// 要復習 = 一度でも間違えていて、まだ 2 回連続で正解できていない
export const isWeak = (r?: Rec) => !!r && r.ngCount > 0 && r.okStreak < 2;

// 間違えた問題だけ（模擬試験・弱点まとめで同じ数え方）= 直近で不正解 または 要復習
export const needsReview = (r?: Rec) => (isAnswered(r) && !r!.correct) || isWeak(r);

export function summarize(ids: string[], prog: Progress) {
  let answered = 0, correct = 0, weak = 0;
  for (const id of ids) {
    const r = prog[id];
    if (isAnswered(r)) { answered++; if (r!.correct) correct++; }
    if (isWeak(r)) weak++;
  }
  return {
    total: ids.length, answered, correct, wrong: answered - correct, weak,
    rate: answered ? Math.round((correct / answered) * 100) : 0,
    coverage: ids.length ? Math.round((answered / ids.length) * 100) : 0,
  };
}

export function onProgressChange(fn: (p: Progress) => void) {
  return $progress.listen(fn);
}

// 何日続けて解いているか。今日まだ解いていなければ昨日までの連続を数える（今日解けば続く）
export function streak(days: string[], prog: Progress, now = new Date()) {
  const set = new Set(days);
  for (const r of Object.values(prog)) if (r?.at) set.add(dayKey(new Date(r.at)));
  const d = new Date(now);
  const today = set.has(dayKey(d));
  if (!today) d.setDate(d.getDate() - 1);
  let n = 0;
  while (set.has(dayKey(d))) { n++; d.setDate(d.getDate() - 1); }
  return { n, today };
}
