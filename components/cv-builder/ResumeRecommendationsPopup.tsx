"use client";

import { useEffect, useMemo, useState } from "react";

export type ResumeRecommendation = {
  code: string;
  title: string;
  message: string;
  action: string;
  severity: "low" | "medium" | "high" | string;
};

type Props = {
  recommendations: ResumeRecommendation[];
  profileScore?: number | null;
  onOpenProfile?: () => void;
};

export function ResumeRecommendationsPopup({
  recommendations,
  profileScore,
  onOpenProfile,
}: Props) {
  const [open, setOpen] = useState(false);
  const [dismissed, setDismissed] = useState(false);

  const important = useMemo(
    () =>
      recommendations
        .filter((item) => item.severity === "high")
        .slice(0, 6),
    [recommendations],
  );

  useEffect(() => {
    if (!dismissed && recommendations.length > 0) {
      setOpen(true);
    }
  }, [dismissed, recommendations]);

  if (!open || recommendations.length === 0) {
    return null;
  }

  const visible = important.length
    ? important
    : recommendations.slice(0, 6);

  return (
    <div
      className="resume-recommendations-backdrop"
      role="presentation"
      onMouseDown={() => setOpen(false)}
    >
      <section
        className="resume-recommendations-modal"
        role="dialog"
        aria-modal="true"
        aria-labelledby="resume-recommendations-title"
        onMouseDown={(event) => event.stopPropagation()}
      >
        <header className="resume-recommendations-header">
          <div>
            <span className="eyebrow">AI Resume Quality Review</span>
            <h2 id="resume-recommendations-title">
              Improve this resume before recruitment use
            </h2>
            <p>
              {typeof profileScore === "number"
                ? `Profile readiness: ${profileScore}%. `
                : ""}
              Review these recommendations and add only verified candidate
              information.
            </p>
          </div>

          <button
            type="button"
            aria-label="Close recommendations"
            onClick={() => setOpen(false)}
          >
            ×
          </button>
        </header>

        <div className="resume-recommendations-list">
          {visible.map((item) => (
            <article
              className={`resume-recommendation severity-${item.severity}`}
              key={item.code}
            >
              <div>
                <strong>{item.title}</strong>
                <p>{item.message}</p>
                <small>{item.action}</small>
              </div>
            </article>
          ))}
        </div>

        {recommendations.length > visible.length ? (
          <p className="resume-recommendations-more">
            {recommendations.length - visible.length} additional
            recommendation(s) are available in the resume quality panel.
          </p>
        ) : null}

        <footer className="resume-recommendations-actions">
          <button
            type="button"
            className="secondary"
            onClick={() => {
              setDismissed(true);
              setOpen(false);
            }}
          >
            Dismiss for now
          </button>

          {onOpenProfile ? (
            <button
              type="button"
              className="primary"
              onClick={() => {
                setOpen(false);
                onOpenProfile();
              }}
            >
              Update candidate profile
            </button>
          ) : null}
        </footer>
      </section>
    </div>
  );
}
