"use client";

import { useMemo, useState } from "react";

import {
  applyTemplate,
  templateRegistry,
  type TemplateCategory,
  type TemplateDefinition,
} from "@/lib/template-engine";
import type { StudioDraft } from "@/lib/cv-studio";
import { TemplateThumbnail } from "@/components/templates/TemplateThumbnail";

type PhotoFilter = "all" | "photo" | "no-photo";
type ATSFilter = "all" | "ats" | "visual";

export function TemplateEnginePanel({
  draft,
  onChange,
}: {
  draft: StudioDraft;
  onChange: (next: StudioDraft) => void;
}) {
  const [category, setCategory] = useState<TemplateCategory | "all">("all");
  const [photo, setPhoto] = useState<PhotoFilter>("all");
  const [ats, setAts] = useState<ATSFilter>("all");
  const [columns, setColumns] = useState<"all" | "one-column" | "two-column">("all");
  const [premium, setPremium] = useState<"all" | "premium" | "free">("all");
  const [search, setSearch] = useState("");

  const filtered = useMemo(() => {
    const query = search.trim().toLowerCase();

    return templateRegistry.filter((template) => {
      const categoryMatch = category === "all" || template.category === category;
      const photoMatch =
        photo === "all" ||
        (photo === "photo" ? template.photo : !template.photo);
      const atsMatch =
        ats === "all" ||
        (ats === "ats" ? template.atsFriendly : !template.atsFriendly);
      const columnsMatch = columns === "all" || template.layout === columns;
      const premiumMatch =
        premium === "all" ||
        (premium === "premium" ? template.premium : !template.premium);
      const searchMatch =
        !query ||
        template.name.toLowerCase().includes(query) ||
        template.description.toLowerCase().includes(query) ||
        template.tags.some((tag) => tag.includes(query));

      return (
        categoryMatch &&
        photoMatch &&
        atsMatch &&
        columnsMatch &&
        premiumMatch &&
        searchMatch
      );
    });
  }, [ats, category, columns, photo, premium, search]);

  function choose(template: TemplateDefinition) {
    onChange(applyTemplate(draft, template));
  }

  function reset() {
    setCategory("all");
    setPhoto("all");
    setAts("all");
    setColumns("all");
    setPremium("all");
    setSearch("");
  }

  return (
    <section className="studio-template-engine">
      <header className="studio-editor-header">
        <span>Template engine</span>
        <h2>Choose your CV template</h2>
        <p>
          Filter 50 registered templates and apply the complete design instantly.
        </p>
      </header>

      <div className="template-engine-toolbar">
        <input
          value={search}
          onChange={(event) => setSearch(event.target.value)}
          placeholder="Search templates"
        />
        <button type="button" onClick={reset}>Reset filters</button>
      </div>

      <div className="template-engine-filters">
        <Filter
          label="Category"
          value={category}
          onChange={(value) => setCategory(value as TemplateCategory | "all")}
          options={[
            ["all", "All"],
            ["ats", "ATS"],
            ["professional", "Professional"],
            ["executive", "Executive"],
            ["creative", "Creative"],
            ["photo", "Photo"],
          ]}
        />
        <Filter
          label="Headshot"
          value={photo}
          onChange={(value) => setPhoto(value as PhotoFilter)}
          options={[
            ["all", "All"],
            ["photo", "With photo"],
            ["no-photo", "Without photo"],
          ]}
        />
        <Filter
          label="Compatibility"
          value={ats}
          onChange={(value) => setAts(value as ATSFilter)}
          options={[
            ["all", "All"],
            ["ats", "ATS friendly"],
            ["visual", "Visual"],
          ]}
        />
        <Filter
          label="Columns"
          value={columns}
          onChange={(value) => setColumns(value as typeof columns)}
          options={[
            ["all", "All"],
            ["one-column", "1 column"],
            ["two-column", "2 columns"],
          ]}
        />
        <Filter
          label="Access"
          value={premium}
          onChange={(value) => setPremium(value as typeof premium)}
          options={[
            ["all", "All"],
            ["premium", "Premium"],
            ["free", "Standard"],
          ]}
        />
      </div>

      <div className="template-engine-result-heading">
        <strong>{filtered.length} templates</strong>
        <span>
          Selected:{" "}
          {templateRegistry.find((template) => template.key === draft.templateKey)
            ?.name ?? "ATS Standard"}
        </span>
      </div>

      <div className="template-engine-grid">
        {filtered.map((template) => (
          <article
            key={template.key}
            className={`engine-template-card ${
              draft.templateKey === template.key ? "selected" : ""
            }`}
          >
            <button
              type="button"
              className="engine-template-preview"
              onClick={() => choose(template)}
            >
              <div className="engine-template-badges">
                {template.premium ? <span>Premium</span> : <span>Standard</span>}
                {template.atsFriendly ? <span>ATS</span> : null}
              </div>

              <TemplateThumbnail template={template} compact />
            </button>

            <div className="engine-template-meta">
              <div>
                <h3>{template.name}</h3>
                <p>{template.description}</p>
              </div>
              <div className="engine-template-tags">
                <span>{template.category}</span>
                <span>{template.photo ? "Photo" : "No photo"}</span>
                <span>{template.layout === "one-column" ? "1 column" : "2 columns"}</span>
              </div>
              <button
                type="button"
                className={`button ${
                  draft.templateKey === template.key
                    ? "button-primary"
                    : "button-secondary"
                }`}
                onClick={() => choose(template)}
              >
                {draft.templateKey === template.key
                  ? "Selected"
                  : "Use template"}
              </button>
            </div>
          </article>
        ))}
      </div>

      {filtered.length === 0 ? (
        <div className="empty-state">
          <h3>No templates found</h3>
          <p className="muted">Change or reset your filters.</p>
          <button type="button" className="button button-primary" onClick={reset}>
            Reset filters
          </button>
        </div>
      ) : null}
    </section>
  );
}

function Filter({
  label,
  value,
  onChange,
  options,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  options: [string, string][];
}) {
  return (
    <label>
      <span>{label}</span>
      <select value={value} onChange={(event) => onChange(event.target.value)}>
        {options.map(([optionValue, optionLabel]) => (
          <option key={optionValue} value={optionValue}>
            {optionLabel}
          </option>
        ))}
      </select>
    </label>
  );
}
