import type { GeneratedCV, ProfileBundle } from "@/lib/types";
import type { CVSectionKey, CVSettings, CVTemplateKey } from "@/lib/cv-builder";

function value(record: Record<string, unknown>, ...keys: string[]): string {
  for (const key of keys) {
    const item = record[key];
    if (item !== null && item !== undefined && item !== "") {
      return String(item);
    }
  }
  return "";
}

function period(record: Record<string, unknown>): string {
  const start = value(record, "start_date");
  const current = Boolean(record.is_current);
  const end = current ? "Present" : value(record, "end_date");
  return [start, end].filter(Boolean).join(" – ");
}

export function CVPreview({
  bundle,
  generated,
  targetRole,
  template, settings, sectionOrder, zoom,
}: {
  bundle: ProfileBundle;
  generated: GeneratedCV | null;
  targetRole: string;
  template: CVTemplateKey;
  settings: CVSettings;
  sectionOrder: CVSectionKey[];
  zoom: number;
}) {
  const profile = bundle.profile;
  const content = generated?.content || {};
  const summary =
    String(content.professional_summary || content.summary || "") ||
    profile?.professional_summary ||
    "";

  const skills =
    Array.isArray(content.skills) && content.skills.length
      ? content.skills.map(String)
      : bundle.skills.map((item) => value(item, "name", "skill")).filter(Boolean);

  const templateClass = `cv-document cv-template-${template}`;
  const padding = settings.margin === "narrow" ? "34px 38px" : settings.margin === "wide" ? "72px 78px" : "54px 58px";

  return (
    <div style={{transform:`scale(${zoom})`,transformOrigin:"top center"}}><article className={templateClass} aria-label="CV preview" style={{fontFamily:settings.font,fontSize:`${settings.fontSize}px`,lineHeight:settings.lineHeight,padding,width:settings.paperSize==="letter"?"816px":"794px",minHeight:settings.paperSize==="letter"?"1056px":"1123px",["--cv-accent" as string]:settings.accent}}>
      <header className="cv-header">
        <h1>{bundle.user.full_name}</h1>
        <p className="cv-role">
          {targetRole || profile?.professional_title || "Professional"}
        </p>
        <div className="cv-contact">
          {profile?.phone && <span>{profile.phone}</span>}
          <span>{bundle.user.email}</span>
          {profile?.location && <span>{profile.location}</span>}
          {profile?.linkedin_url && <span>{profile.linkedin_url}</span>}
          {profile?.website_url && <span>{profile.website_url}</span>}
        </div>
      </header>

      {summary && (
        <section className="cv-section">
          <h2>Professional Summary</h2>
          <p>{summary}</p>
        </section>
      )}

      {bundle.experience.length > 0 && (
        <section className="cv-section">
          <h2>Professional Experience</h2>
          <div className="cv-stack">
            {bundle.experience.map((item, index) => (
              <div className="cv-entry" key={String(item.id || index)}>
                <div className="cv-entry-heading">
                  <div>
                    <h3>{value(item, "job_title")}</h3>
                    <p>{value(item, "company")}</p>
                  </div>
                  <div className="cv-entry-meta">
                    <span>{period(item)}</span>
                    <span>{value(item, "location")}</span>
                  </div>
                </div>
                {value(item, "description") && (
                  <p>{value(item, "description")}</p>
                )}
              </div>
            ))}
          </div>
        </section>
      )}

      {bundle.education.length > 0 && (
        <section className="cv-section">
          <h2>Education</h2>
          <div className="cv-stack">
            {bundle.education.map((item, index) => (
              <div className="cv-entry" key={String(item.id || index)}>
                <div className="cv-entry-heading">
                  <div>
                    <h3>{value(item, "qualification")}</h3>
                    <p>{value(item, "institution")}</p>
                  </div>
                  <div className="cv-entry-meta">
                    <span>{period(item)}</span>
                    <span>{value(item, "field_of_study")}</span>
                  </div>
                </div>
                {value(item, "description") && (
                  <p>{value(item, "description")}</p>
                )}
              </div>
            ))}
          </div>
        </section>
      )}

      {skills.length > 0 && (
        <section className="cv-section">
          <h2>Core Skills</h2>
          <div className="cv-skill-grid">
            {skills.map((skill) => (
              <span key={skill}>{skill}</span>
            ))}
          </div>
        </section>
      )}

      {bundle.projects.length > 0 && (
        <section className="cv-section">
          <h2>Projects</h2>
          <div className="cv-stack">
            {bundle.projects.map((item, index) => (
              <div className="cv-entry" key={String(item.id || index)}>
                <div className="cv-entry-heading">
                  <div>
                    <h3>{value(item, "name", "project_name")}</h3>
                    <p>{value(item, "project_url")}</p>
                  </div>
                  <div className="cv-entry-meta">
                    <span>{period(item)}</span>
                  </div>
                </div>
                {value(item, "description") && (
                  <p>{value(item, "description")}</p>
                )}
              </div>
            ))}
          </div>
        </section>
      )}

      <div className="cv-two-column">
        {bundle.certifications.length > 0 && (
          <section className="cv-section">
            <h2>Certifications</h2>
            <ul>
              {bundle.certifications.map((item, index) => (
                <li key={String(item.id || index)}>
                  <strong>{value(item, "name")}</strong>
                  {value(item, "issuer") && ` — ${value(item, "issuer")}`}
                </li>
              ))}
            </ul>
          </section>
        )}

        {bundle.languages.length > 0 && (
          <section className="cv-section">
            <h2>Languages</h2>
            <ul>
              {bundle.languages.map((item, index) => (
                <li key={String(item.id || index)}>
                  <strong>{value(item, "name")}</strong>
                  {value(item, "proficiency") &&
                    ` — ${value(item, "proficiency")}`}
                </li>
              ))}
            </ul>
          </section>
        )}
      </div>

      {bundle.references.length > 0 && (
        <section className="cv-section">
          <h2>References</h2>
          <div className="cv-reference-grid">
            {bundle.references.map((item, index) => (
              <div key={String(item.id || index)}>
                <strong>{value(item, "full_name")}</strong>
                <p>
                  {[value(item, "relationship"), value(item, "company")]
                    .filter(Boolean)
                    .join(", ")}
                </p>
                <p>
                  {[value(item, "email"), value(item, "phone")]
                    .filter(Boolean)
                    .join(" · ")}
                </p>
              </div>
            ))}
          </div>
        </section>
      )}
    </article></div>
  );
}
