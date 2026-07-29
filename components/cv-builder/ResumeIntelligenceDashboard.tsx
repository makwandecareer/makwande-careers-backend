"use client";

export type ResumeIntelligence = {
  ats_score: number;
  profile_readiness: number;
  recruiter_readiness: number;
  formatting_score: number;
  keyword_match: number;
  matched_keywords: string[];
  missing_keywords: string[];
  responsibility_bullet_count: number;
  achievement_count: number;
  measurable_achievement_count: number;
  warnings: string[];
  disclaimer: string;
};

type Props = {
  intelligence?: ResumeIntelligence | null;
};

function ScoreCard({ label, value }: { label: string; value: number }) {
  const safeValue = Math.max(0, Math.min(100, Number(value) || 0));
  return (
    <article className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
      <p className="text-sm font-medium text-slate-600">{label}</p>
      <p className="mt-2 text-3xl font-bold text-slate-950">{safeValue}%</p>
      <div className="mt-3 h-2 overflow-hidden rounded-full bg-slate-100">
        <div className="h-full rounded-full bg-slate-900" style={{ width: `${safeValue}%` }} />
      </div>
    </article>
  );
}

export function ResumeIntelligenceDashboard({ intelligence }: Props) {
  if (!intelligence) return null;

  return (
    <section className="space-y-5 rounded-3xl border border-slate-200 bg-slate-50 p-5">
      <div>
        <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">
          Makwande Careers AI
        </p>
        <h2 className="mt-1 text-xl font-bold text-slate-950">Resume Intelligence</h2>
      </div>

      <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-5">
        <ScoreCard label="ATS Match" value={intelligence.ats_score} />
        <ScoreCard label="Profile Readiness" value={intelligence.profile_readiness} />
        <ScoreCard label="Recruiter Readiness" value={intelligence.recruiter_readiness} />
        <ScoreCard label="Formatting" value={intelligence.formatting_score} />
        <ScoreCard label="Keyword Match" value={intelligence.keyword_match} />
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <article className="rounded-2xl border border-slate-200 bg-white p-4">
          <h3 className="font-semibold text-slate-950">Professional structure</h3>
          <dl className="mt-3 grid grid-cols-3 gap-3 text-center">
            <div className="rounded-xl bg-slate-50 p-3">
              <dt className="text-xs text-slate-500">Responsibility bullets</dt>
              <dd className="mt-1 text-xl font-bold">{intelligence.responsibility_bullet_count}</dd>
            </div>
            <div className="rounded-xl bg-slate-50 p-3">
              <dt className="text-xs text-slate-500">Achievements</dt>
              <dd className="mt-1 text-xl font-bold">{intelligence.achievement_count}</dd>
            </div>
            <div className="rounded-xl bg-slate-50 p-3">
              <dt className="text-xs text-slate-500">Measured KPIs</dt>
              <dd className="mt-1 text-xl font-bold">{intelligence.measurable_achievement_count}</dd>
            </div>
          </dl>
        </article>

        <article className="rounded-2xl border border-slate-200 bg-white p-4">
          <h3 className="font-semibold text-slate-950">Priority recommendations</h3>
          {intelligence.warnings.length ? (
            <ul className="mt-3 space-y-2">
              {intelligence.warnings.map((warning) => (
                <li key={warning} className="rounded-xl bg-amber-50 px-3 py-2 text-sm text-amber-950">
                  {warning}
                </li>
              ))}
            </ul>
          ) : (
            <p className="mt-3 text-sm text-emerald-700">No critical structural issues were detected.</p>
          )}
        </article>
      </div>

      {!!intelligence.missing_keywords.length && (
        <article className="rounded-2xl border border-slate-200 bg-white p-4">
          <h3 className="font-semibold text-slate-950">Missing job-description keywords</h3>
          <div className="mt-3 flex flex-wrap gap-2">
            {intelligence.missing_keywords.map((keyword) => (
              <span key={keyword} className="rounded-full bg-slate-100 px-3 py-1 text-xs text-slate-700">
                {keyword}
              </span>
            ))}
          </div>
        </article>
      )}

      <p className="text-xs leading-5 text-slate-500">{intelligence.disclaimer}</p>
    </section>
  );
}
