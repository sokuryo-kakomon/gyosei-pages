import questionsJson from '../data/questions.json';
import hoshiJson from '../data/questions_hoshi.json';
import siteJson from '../data/site.json';
import guidesJson from '../data/guides.json';
import pagesJson from '../data/pages.json';
import type { Question, Site, Guides, StaticPage, QuestionIndex, Exam, Year, Category } from './types';

// サーバー側（ビルド時）専用。React の island からは import しない
// （questions.json は 700KB あり、クライアントへ丸ごと送りたくない）。

export const SITE_NAME = '行政書士 過去問ドリル';

export const site = siteJson as Site;
export const guides = guidesJson as Guides;
export const pages = pagesJson as Record<'about' | 'privacy', StaticPage>;

// 行政書士は /r07/q1/。hoshi は測量士サイトから写した名残で、空のまま（questions_hoshi.json は []）
export const shiQuestions = (questionsJson as Question[]).map((q) => tidy({ ...q, exam: 'shi' as const }));

// 表示用に整える（元データはそのまま）。
//  - 多肢選択の語群は 1〜20 の番号順（原文の PDF が2段組のため、奇数・偶数の順に入っている年がある）
//  - 記述の問題文から答案用紙の注意書きを外し、参照条文を条・項・号ごとに改行する
function tidy<T extends Question>(q: T): T {
  if (q.words?.length) q = { ...q, words: [...q.words].sort((a, b) => Number(a.key) - Number(b.key)) };
  if (q.kind === 'kijutsu') q = { ...q, statementHtml: kijutsuHtml(q.statementHtml) };
  return q;
}
export function kijutsuHtml(h: string) {
  let s = h.replace(/解答は、必ず答案用紙[^。]*。/g, '');
  const i = s.indexOf('（参照条文）');
  if (i < 0) return s;
  let head = s.slice(0, i), ref = s.slice(i + '（参照条文）'.length);
  const nao = ref.match(/なお、字数には、句読点も含む。$/);
  if (nao) { ref = ref.slice(0, nao.index); head += nao[0]; }
  ref = ref
    .replace(/(?<=[。）略])(?=[^。<]{0,30}?(?:第\s*\d+条|\d+条|[a-zａ-ｚ] ?条)(?:第\d+項)?(?:の\d+)?　)/g, '<br>')
    .replace(/(?<=[。）])(?=\d+　)/g, '<br>')
    .replace(/(?<=[^　>\s])(?=[②-⑩])/g, '<br>')
    .replace(/(?<=[^　\s条>])(?=[一二三四五六七八九十]　)/g, '<br>');
  return `${head}<br><br><b>（参照条文）</b><br>${ref}`;
}
export const hoshiQuestions = (hoshiJson as Question[]).map((q) => ({ ...q, exam: 'hoshi' as const }));
export const questions: Question[] = [...shiQuestions, ...hoshiQuestions];

export interface ExamInfo {
  id: Exam; name: string; full: string; base: string; part: string; years: Year[]; questions: Question[];
}
export const EXAMS: Record<Exam, ExamInfo> = {
  shi: { id: 'shi', name: '行政書士', full: '行政書士試験', base: '', part: '', years: site.years, questions: shiQuestions },
  hoshi: { id: 'hoshi', name: '測量士補', full: '測量士補試験', base: '/hoshi', part: '択一式', years: site.hoshiYears, questions: hoshiQuestions },
};
// 載せている年度の幅（例 long「平成30年度〜令和8年度」・short「平成30〜令和8年」）と年数
export function yearSpan(exam: Exam = 'shi') {
  const ys = EXAMS[exam].years.filter((y) => EXAMS[exam].questions.some((q) => q.year === y.id));
  const [newest, oldest] = [ys[0], ys[ys.length - 1]];
  const bare = (l: string) => l.replace(/（.*）/, '');
  return { long: `${bare(oldest.label)}〜${bare(newest.label)}`, short: `${bare(oldest.label).replace('年度', '')}〜${bare(newest.label).replace('度', '')}`, n: ys.length };
}
export const SITE_TAGLINE = `行政書士試験の過去問 ${yearSpan('shi').n}年分の演習`;
export const examOfPath = (path: string): Exam => (path.startsWith('/hoshi') ? 'hoshi' : 'shi');

// 測量士の名前のまま使っている所が多いので、years / categories は測量士のもの
export const years = site.years;
export const categories = site.categories;
export const byId = new Map(questions.map((q) => [q.id, q]));

export const ofYear = (y: string, exam: Exam = 'shi') => EXAMS[exam].questions.filter((q) => q.year === y);
export const ofCategory = (slug: string, exam: Exam = 'shi') => EXAMS[exam].questions.filter((q) => q.categorySlug === slug);
export const yearById = (y: string, exam: Exam = 'shi') => EXAMS[exam].years.find((x) => x.id === y)!;
export const categoryBySlug = (s: string) => categories.find((c) => c.slug === s);
// 分野ごとの問題数（試験ごと）。site.json の count は測量士のもの
export const categoriesOf = (exam: Exam): Category[] =>
  categories.map((c) => ({ ...c, count: EXAMS[exam].questions.filter((q) => q.categorySlug === c.slug).length }));

export function toIndex(q: Question): QuestionIndex {
  return {
    id: q.id, exam: q.exam ?? 'shi', year: q.year, num: q.num, category: q.category, categorySlug: q.categorySlug,
    excerpt: q.statementText.slice(0, 64), url: q.url,
  };
}

export function pageTitle(t: string) { return `${t}｜${SITE_NAME}`; }
