"use client";

import Image from "next/image";
import Link from "next/link";
import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/client-api";

export default function RegisterPage() {
  const router = useRouter();
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");

  async function submit(event: FormEvent) {
    event.preventDefault();
    setError("");
    try {
      await api("/api/auth/register", {
        method: "POST",
        body: JSON.stringify({ full_name: fullName, email, password }),
      });
      router.push("/login");
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Registration failed");
    }
  }

  return (
    <main className="auth-shell">
      <section className="card auth-card">
        <div style={{ textAlign: "center" }}>
          <Image src="/makwande-careers-logo.jpeg" alt="Makwande Careers" width={130} height={130} />
        </div>
        <h1>Create your account</h1>
        <form className="form" onSubmit={submit}>
          <div className="field"><label>Full name</label><input className="input" value={fullName} onChange={e => setFullName(e.target.value)} required /></div>
          <div className="field"><label>Email</label><input className="input" type="email" value={email} onChange={e => setEmail(e.target.value)} required /></div>
          <div className="field"><label>Password</label><input className="input" type="password" minLength={12} value={password} onChange={e => setPassword(e.target.value)} required /></div>
          {error && <div className="error">{error}</div>}
          <button className="button button-primary">Register</button>
        </form>
        <p className="muted">Already registered? <Link href="/login">Sign in</Link></p>
      </section>
    </main>
  );
}
