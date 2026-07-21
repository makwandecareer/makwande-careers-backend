"use client";

import Image from "next/image";
import Link from "next/link";
import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError("");

    const response = await fetch("/api/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    });

    if (!response.ok) {
      setError(await response.text());
      setBusy(false);
      return;
    }

    router.push("/dashboard");
    router.refresh();
  }

  return (
    <main className="auth-shell">
      <section className="card auth-card">
        <div style={{ textAlign: "center" }}>
          <Image src="/makwande-careers-logo.jpeg" alt="Makwande Careers" width={130} height={130} />
        </div>
        <h1>Welcome back</h1>
        <p className="muted">Sign in to continue to your career dashboard.</p>
        <form className="form" onSubmit={submit}>
          <div className="field"><label>Email</label><input className="input" type="email" value={email} onChange={e => setEmail(e.target.value)} required /></div>
          <div className="field"><label>Password</label><input className="input" type="password" value={password} onChange={e => setPassword(e.target.value)} required /></div>
          {error && <div className="error">{error}</div>}
          <button className="button button-primary" disabled={busy}>{busy ? "Signing in..." : "Sign in"}</button>
        </form>
        <p className="muted">New here? <Link href="/register">Create an account</Link></p>
      </section>
    </main>
  );
}
