"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Suspense, useEffect, useState } from "react";
import { CheckCircle2, LoaderCircle, XCircle } from "lucide-react";
import { verifyPayment, VerifyPaymentResponse } from "@/lib/billing";

function CallbackContent() {
  const params = useSearchParams();
  const reference = params.get("reference") || params.get("trxref") || "";
  const [result, setResult] = useState<VerifyPaymentResponse | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!reference) {
      setError("No payment reference was returned by Paystack.");
      return;
    }
    verifyPayment(reference).then(setResult).catch((requestError) => {
      setError(requestError instanceof Error ? requestError.message : "Payment verification failed.");
    });
  }, [reference]);

  const pending = !result && !error;
  const success = result?.paid === true;

  return (
    <main className="auth-shell payment-callback-shell">
      <section className="card payment-callback-card">
        {pending && <><LoaderCircle className="spin-icon callback-icon" /><h1>Verifying payment</h1><p className="muted">Please wait while we confirm your Paystack transaction.</p></>}
        {success && <><CheckCircle2 className="callback-icon success-icon" /><h1>Payment successful</h1><p className="muted">Your payment has been confirmed. Your Makwande Careers access is ready.</p><div className="success">Reference: {result.reference}</div><Link className="button button-primary button-wide" href="/dashboard">Continue to dashboard</Link></>}
        {!pending && !success && <><XCircle className="callback-icon error-icon" /><h1>Payment not completed</h1><p className="muted">{error || `Paystack returned the status: ${result?.status || "unknown"}.`}</p><Link className="button button-primary button-wide" href="/dashboard/billing">Return to billing</Link></>}
      </section>
    </main>
  );
}

export default function PaymentCallbackPage() {
  return <Suspense fallback={<main className="auth-shell"><div className="loading"><span className="spinner" />Loading payment result…</div></main>}><CallbackContent /></Suspense>;
}
