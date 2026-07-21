"use client";

import Link from "next/link";
import { FormEvent, useEffect, useState } from "react";
import { api } from "@/lib/client-api";
import type { ProfileForm, User } from "@/lib/types";

const emptyProfile: ProfileForm = {
  phone: "",
  location: "",
  professional_title: "",
  professional_summary: "",
  linkedin_url: "",
  portfolio_url: "",
  website_url: "",
  visibility: "private",
};

export default function ProfilePage() {
  const [user, setUser] = useState<User | null>(null);
  const [form, setForm] = useState<ProfileForm>(emptyProfile);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);

  async function load() {
    setLoading(true);
    setError("");

    try {
      const [currentUser, profile] = await Promise.all([
        api<User>("/api/users/me"),
        api<ProfileForm | null>("/api/profile"),
      ]);

      setUser(currentUser);
      setForm(profile || emptyProfile);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Unable to load profile");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  async function submit(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    setMessage("");
    setError("");

    try {
      const saved = await api<ProfileForm>("/api/profile", {
        method: "PUT",
        body: JSON.stringify(form),
      });

      setForm(saved);
      setMessage("Professional profile saved successfully.");
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Unable to save profile");
    } finally {
      setBusy(false);
    }
  }

  if (loading) {
    return (
      <div className="loading">
        <span className="spinner" />
        Loading profile...
      </div>
    );
  }

  return (
    <>
      <header className="page-header">
        <div>
          <h1>Professional profile</h1>
          <p className="muted">
            Your profile is the single source of truth for CVs, ATS reports,
            cover letters, interview preparation, and career guidance.
          </p>
        </div>
        <button className="button button-secondary" onClick={load}>
          Refresh
        </button>
      </header>

      <section className="card" style={{ marginBottom: 18 }}>
        <div className="two-column">
          <div>
            <span className="muted">Full name</span>
            <h3>{user?.full_name}</h3>
          </div>
          <div>
            <span className="muted">Email</span>
            <h3>{user?.email}</h3>
          </div>
        </div>
      </section>

      <form className="card form" onSubmit={submit}>
        <div className="two-column">
          <div className="field">
            <label>Phone</label>
            <input
              className="input"
              value={form.phone}
              onChange={(event) => setForm({ ...form, phone: event.target.value })}
              placeholder="+27..."
            />
          </div>

          <div className="field">
            <label>Location</label>
            <input
              className="input"
              value={form.location}
              onChange={(event) => setForm({ ...form, location: event.target.value })}
              placeholder="Johannesburg, South Africa"
            />
          </div>
        </div>

        <div className="field">
          <label>Professional title</label>
          <input
            className="input"
            value={form.professional_title}
            onChange={(event) =>
              setForm({ ...form, professional_title: event.target.value })
            }
            placeholder="Chemical Engineer"
          />
        </div>

        <div className="field">
          <label>Professional summary</label>
          <textarea
            className="input"
            value={form.professional_summary}
            onChange={(event) =>
              setForm({ ...form, professional_summary: event.target.value })
            }
            placeholder="Write a concise, evidence-based professional summary."
          />
        </div>

        <div className="three-column">
          <div className="field">
            <label>LinkedIn URL</label>
            <input
              className="input"
              value={form.linkedin_url}
              onChange={(event) =>
                setForm({ ...form, linkedin_url: event.target.value })
              }
            />
          </div>

          <div className="field">
            <label>Portfolio URL</label>
            <input
              className="input"
              value={form.portfolio_url}
              onChange={(event) =>
                setForm({ ...form, portfolio_url: event.target.value })
              }
            />
          </div>

          <div className="field">
            <label>Website URL</label>
            <input
              className="input"
              value={form.website_url}
              onChange={(event) =>
                setForm({ ...form, website_url: event.target.value })
              }
            />
          </div>
        </div>

        <div className="field">
          <label>Profile visibility</label>
          <select
            className="input"
            value={form.visibility}
            onChange={(event) =>
              setForm({
                ...form,
                visibility: event.target.value as ProfileForm["visibility"],
              })
            }
          >
            <option value="private">Private</option>
            <option value="employers">Visible</option>
          </select>
        </div>

        {error && <div className="error">{error}</div>}
        {message && <div className="success">{message}</div>}

        <button className="button button-primary" disabled={busy}>
          {busy ? "Saving..." : "Save profile"}
        </button>
      </form>

      <section className="section">
        <div className="card">
          <h3>Build the rest of your career profile</h3>
          <div className="toolbar">
            <Link className="button button-secondary" href="/dashboard/education">
              Education
            </Link>
            <Link className="button button-secondary" href="/dashboard/experience">
              Experience
            </Link>
            <Link className="button button-secondary" href="/dashboard/skills">
              Skills
            </Link>
            <Link className="button button-secondary" href="/dashboard/projects">
              Projects
            </Link>
            <Link className="button button-secondary" href="/dashboard/certifications">
              Certifications
            </Link>
            <Link className="button button-secondary" href="/dashboard/languages">
              Languages
            </Link>
            <Link className="button button-secondary" href="/dashboard/references">
              References
            </Link>
          </div>
        </div>
      </section>
    </>
  );
}
