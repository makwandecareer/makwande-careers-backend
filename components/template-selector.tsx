"use client";

import { useMemo, useState } from "react";
import {
  formalTemplates,
  type FormalTemplate,
  type TemplateColumns,
  type TemplatePhoto,
} from "@/lib/template-catalog";

export function TemplateSelector({
  value,
  onChange,
}: {
  value: string;
  onChange: (template: FormalTemplate) => void;
}) {
  const [photo, setPhoto] = useState<TemplatePhoto | "all">("all");
  const [columns, setColumns] = useState<TemplateColumns | "all">("all");
  const [search, setSearch] = useState("");

  const filtered = useMemo(() => {
    return formalTemplates.filter((template) => {
      const matchesPhoto = photo === "all" || template.photo === photo;
      const matchesColumns = columns === "all" || template.columns === columns;
      const matchesSearch =
        !search.trim() ||
        template.name.toLowerCase().includes(search.toLowerCase()) ||
        template.family.toLowerCase().includes(search.toLowerCase());

      return matchesPhoto && matchesColumns && matchesSearch;
    });
  }, [photo, columns, search]);

  return (
    <div className="template-marketplace">
      <aside className="template-filters card">
        <div className="template-filter-heading">
          <h3>Filters</h3>
          <button
            type="button"
            onClick={() => {
              setPhoto("all");
              setColumns("all");
              setSearch("");
            }}
          >
            Clear filters
          </button>
        </div>

        <div className="field">
          <label>Search templates</label>
          <input
            className="input"
            value={search}
            onChange={(event) => setSearch(event.target.value)}
            placeholder="Search formal templates"
          />
        </div>

        <fieldset>
          <legend>Headshot</legend>
          <label>
            <input
              type="radio"
              name="photo"
              checked={photo === "all"}
              onChange={() => setPhoto("all")}
            />
            All templates
          </label>
          <label>
            <input
              type="radio"
              name="photo"
              checked={photo === "with-photo"}
              onChange={() => setPhoto("with-photo")}
            />
            With photo
          </label>
          <label>
            <input
              type="radio"
              name="photo"
              checked={photo === "without-photo"}
              onChange={() => setPhoto("without-photo")}
            />
            Without photo
          </label>
        </fieldset>

        <fieldset>
          <legend>Columns</legend>
          <label>
            <input
              type="radio"
              name="columns"
              checked={columns === "all"}
              onChange={() => setColumns("all")}
            />
            All layouts
          </label>
          <label>
            <input
              type="radio"
              name="columns"
              checked={columns === 1}
              onChange={() => setColumns(1)}
            />
            1 column
          </label>
          <label>
            <input
              type="radio"
              name="columns"
              checked={columns === 2}
              onChange={() => setColumns(2)}
            />
            2 columns
          </label>
        </fieldset>

        <div className="template-count">
          <strong>{filtered.length}</strong>
          <span>formal templates</span>
        </div>
      </aside>

      <section>
        <div className="template-grid-header">
          <div>
            <h2>Choose a professional template</h2>
            <p className="muted">
              Select a formal design, then customise colour and content in the CV Studio.
            </p>
          </div>
        </div>

        <div className="formal-template-grid">
          {filtered.map((template) => (
            <article
              key={template.key}
              className={`formal-template-card ${
                value === template.key ? "selected" : ""
              }`}
            >
              <button
                type="button"
                className="formal-template-preview"
                onClick={() => onChange(template)}
                aria-label={`Choose ${template.name}`}
              >
                {template.recommended && (
                  <span className="recommended-badge">Recommended</span>
                )}

                <div
                  className={`formal-sheet columns-${template.columns} ${template.photo}`}
                  style={{ "--template-accent": template.accent } as React.CSSProperties}
                >
                  <header>
                    {template.photo === "with-photo" && <span className="photo-placeholder" />}
                    <div>
                      <strong>LERATO MASEKO</strong>
                      <small>Professional Title</small>
                    </div>
                  </header>

                  <div className="formal-lines">
                    <span className="wide" />
                    <span />
                    <span />
                    <span className="wide" />
                    <span />
                    <span />
                    <span className="wide" />
                  </div>
                </div>
              </button>

              <div className="formal-template-meta">
                <div>
                  <h3>{template.name}</h3>
                  <p>{template.description}</p>
                </div>
                <div className="template-attributes">
                  <span>{template.photo === "with-photo" ? "With photo" : "No photo"}</span>
                  <span>{template.columns} column{template.columns === 2 ? "s" : ""}</span>
                </div>
                <button
                  type="button"
                  className="button button-primary"
                  onClick={() => onChange(template)}
                >
                  {value === template.key ? "Selected" : "Use this template"}
                </button>
              </div>
            </article>
          ))}
        </div>
      </section>
    </div>
  );
}
