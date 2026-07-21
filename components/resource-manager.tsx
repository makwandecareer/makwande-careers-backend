"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";
import { api } from "@/lib/client-api";

type Field = {
  key: string;
  label: string;
  type?: "text" | "date" | "number" | "textarea" | "checkbox";
  required?: boolean;
};

function displayValue(value: unknown): string {
  if (value === null || value === undefined || value === "") return "—";
  if (typeof value === "boolean") return value ? "Yes" : "No";
  return String(value);
}

export function ResourceManager({
  title,
  description,
  endpoint,
  fields,
}: {
  title: string;
  description: string;
  endpoint: string;
  fields: Field[];
}) {
  const initial = useMemo(
    () =>
      Object.fromEntries(
        fields.map((field) => [
          field.key,
          field.type === "checkbox" ? false : "",
        ]),
      ),
    [fields],
  );

  const [form, setForm] = useState<Record<string, unknown>>(initial);
  const [items, setItems] = useState<Record<string, unknown>[]>([]);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  async function load() {
    setLoading(true);
    setError("");

    try {
      setItems(await api<Record<string, unknown>[]>(endpoint));
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Unable to load records");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, [endpoint]);

  function startEdit(item: Record<string, unknown>) {
    const values = Object.fromEntries(
      fields.map((field) => [field.key, item[field.key] ?? (field.type === "checkbox" ? false : "")]),
    );

    setEditingId(String(item.id));
    setForm(values);
    setMessage("");
    setError("");
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  function cancelEdit() {
    setEditingId(null);
    setForm(initial);
    setMessage("");
    setError("");
  }

  async function submit(event: FormEvent) {
    event.preventDefault();
    setSaving(true);
    setError("");
    setMessage("");

    try {
      const payload: Record<string, unknown> = { ...form };

      for (const field of fields) {
        const value = payload[field.key];

        if (field.type === "number" && value !== "") {
          payload[field.key] = Number(value);
        }

        if (value === "") {
          payload[field.key] = null;
        }
      }

      const path = editingId ? `${endpoint}/${editingId}` : endpoint;
      const method = editingId ? "PUT" : "POST";

      await api(path, {
        method,
        body: JSON.stringify(payload),
      });

      setEditingId(null);
      setForm(initial);
      setMessage(
        editingId
          ? `${title} record updated successfully.`
          : `${title} record saved successfully.`,
      );
      await load();
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Unable to save record");
    } finally {
      setSaving(false);
    }
  }

  async function remove(id: string) {
    const confirmed = window.confirm(
      `Delete this ${title.toLowerCase()} record permanently?`,
    );

    if (!confirmed) return;

    try {
      await api(`${endpoint}/${id}`, { method: "DELETE" });
      setMessage(`${title} record deleted successfully.`);
      await load();
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Unable to delete record");
    }
  }

  return (
    <>
      <header className="page-header">
        <div>
          <h1>{title}</h1>
          <p className="muted">{description}</p>
        </div>
        <button className="button button-secondary" onClick={load}>
          Refresh records
        </button>
      </header>

      <div className="two-column">
        <form className="card form" onSubmit={submit}>
          <h3>{editingId ? `Edit ${title}` : `Add ${title}`}</h3>

          {fields.map((field) => (
            <div className="field" key={field.key}>
              <label>{field.label}</label>

              {field.type === "textarea" ? (
                <textarea
                  className="input"
                  value={String(form[field.key] ?? "")}
                  onChange={(event) =>
                    setForm({ ...form, [field.key]: event.target.value })
                  }
                  required={field.required}
                />
              ) : field.type === "checkbox" ? (
                <label className="toolbar">
                  <input
                    type="checkbox"
                    checked={Boolean(form[field.key])}
                    onChange={(event) =>
                      setForm({ ...form, [field.key]: event.target.checked })
                    }
                  />
                  Yes
                </label>
              ) : (
                <input
                  className="input"
                  type={field.type || "text"}
                  value={String(form[field.key] ?? "")}
                  onChange={(event) =>
                    setForm({ ...form, [field.key]: event.target.value })
                  }
                  required={field.required}
                />
              )}
            </div>
          ))}

          {error && <div className="error">{error}</div>}
          {message && <div className="success">{message}</div>}

          <div className="toolbar">
            <button className="button button-primary" disabled={saving}>
              {saving
                ? "Saving..."
                : editingId
                  ? `Update ${title.toLowerCase()}`
                  : `Save ${title.toLowerCase()}`}
            </button>

            {editingId && (
              <button
                type="button"
                className="button button-secondary"
                onClick={cancelEdit}
              >
                Cancel
              </button>
            )}
          </div>
        </form>

        <section className="card">
          <div className="page-header">
            <div>
              <h3>Saved records</h3>
              <p className="muted">{items.length} record(s) found</p>
            </div>
          </div>

          {loading && (
            <div className="loading">
              <span className="spinner" />
              Loading records...
            </div>
          )}

          {!loading && items.length === 0 && (
            <p className="muted">No records saved yet.</p>
          )}

          <div className="list">
            {items.map((item, index) => (
              <article className="list-item" key={String(item.id || index)}>
                <div style={{ width: "100%" }}>
                  {fields.map((field) => (
                    <div className="report-row" key={field.key}>
                      <span>{field.label}</span>
                      <strong>{displayValue(item[field.key])}</strong>
                    </div>
                  ))}

                  <div className="toolbar" style={{ marginTop: 12 }}>
                    <button
                      className="button button-secondary"
                      onClick={() => startEdit(item)}
                    >
                      Edit
                    </button>
                    <button
                      className="button button-ghost"
                      onClick={() => remove(String(item.id))}
                    >
                      Delete
                    </button>
                  </div>
                </div>
              </article>
            ))}
          </div>
        </section>
      </div>
    </>
  );
}
