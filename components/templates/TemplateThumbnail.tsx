"use client";

import type { TemplateDefinition } from "@/lib/template-engine";

export function TemplateThumbnail({
  template,
  compact = false,
}: {
  template: TemplateDefinition;
  compact?: boolean;
}) {
  const variation = Number(template.key.replace(/\D/g, "")) % 6;

  return (
    <div
      className={`visual-resume visual-resume-${variation} ${
        template.layout
      } ${template.photo ? "with-photo" : "without-photo"} ${
        compact ? "compact" : ""
      }`}
      style={
        {
          "--visual-accent": template.accent,
          "--visual-soft": template.secondaryAccent,
          fontFamily: template.fontFamily,
        } as React.CSSProperties
      }
    >
      {template.premium && (
        <div className="visual-recommended">Recommended</div>
      )}

      <header className="visual-resume-header">
        {template.photo && (
          <div className="visual-photo">
            <span className="visual-head" />
            <span className="visual-body" />
          </div>
        )}

        <div className="visual-name-block">
          <strong>LERATO MASEKO</strong>
          <small>Professional Title</small>
          <div className="visual-contact-row">
            <span />
            <span />
            <span />
          </div>
        </div>
      </header>

      <div className="visual-resume-content">
        <aside className="visual-sidebar">
          <ResumeSection title="Contact" lines={[46, 39, 43]} />
          <ResumeSection title="Skills" lines={[52, 42, 48, 36]} />
          <ResumeSection title="Education" lines={[50, 44, 38]} />
        </aside>

        <main className="visual-main">
          <ResumeSection
            title="Professional Summary"
            lines={[96, 88, 94, 83, 91]}
          />
          <ResumeSection
            title="Work History"
            lines={[76, 92, 86, 78, 89, 71]}
          />
          <ResumeSection
            title="Education"
            lines={[66, 58, 74]}
          />
        </main>
      </div>

      <div className="visual-colour-strip">
        {[template.accent, "#7f93b7", "#c3ad8b", "#7b7f83", "#a9dcd8", "#f08a7b"].map(
          (colour, index) => (
            <span
              key={`${colour}-${index}`}
              style={{ background: colour }}
            />
          ),
        )}
      </div>
    </div>
  );
}

function ResumeSection({
  title,
  lines,
}: {
  title: string;
  lines: number[];
}) {
  return (
    <section className="visual-section">
      <b>{title}</b>
      <div>
        {lines.map((width, index) => (
          <span
            key={`${title}-${index}`}
            style={{ width: `${width}%` }}
          />
        ))}
      </div>
    </section>
  );
}
