"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { api } from "@/lib/client-api";
import type { GeneratedCV } from "@/lib/types";

export default function CVsPage() {
  const [items, setItems] = useState<GeneratedCV[]>([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  async function load() {
    setLoading(true);
    setError("");
    try {
      setItems(await api<GeneratedCV[]>("/api/cvs"));
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Unable to load CVs");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void load();
  }, []);

  return (
    <>
      <header className="page-header">
        <div>
          <span className="eyebrow">Document library</span>
          <h1>My CVs</h1>
          <p className="muted">
            Manage the professional CV versions generated from your career profile.
          </p>
        </div>
        <Link className="button button-primary" href="/dashboard/cv-builder">
          Create a new CV
        </Link>
      </header>

      {error && <div className="error">{error}</div>}

      <section className="card">
        {loading && (
          <div className="loading">
            <span className="spinner" />
            Loading CVs...
          </div>
        )}

        {!loading && items.length === 0 && (
          <div className="empty-state">
            <h3>No CVs saved yet</h3>
            <p className="muted">
              Build your first globally competitive CV using your saved career profile.
            </p>
            <Link className="button button-primary" href="/dashboard/cv-builder">
              Build my first CV
            </Link>
          </div>
        )}

        <div className="cv-library-grid">
          {items.map((item, index) => (
            <article className="cv-library-card" key={String(item.id || index)}>
              <div className="cv-library-preview">
                <span className="cv-library-brand" />
                <span />
                <span />
                <span className="short" />
                <span />
                <span className="short" />
              </div>
              <div>
                <h3>{item.title || "Untitled CV"}</h3>
                <p className="muted">
                  {item.target_role || "No target role"}
                </p>
                <div className="toolbar">
                  <span className="tag">
                    {item.template_key || "ATS Standard"}
                  </span>
                  <Link
                    className="button button-secondary"
                    href="/dashboard/cv-builder"
                  >
                    Open builder
                  </Link>
                </div>
              </div>
            </article>
          ))}
        </div>
      </section>
    </>
  );
}
