"use client";

import { useState } from "react";
import { CheckCircle2, CreditCard, LoaderCircle, ShieldCheck } from "lucide-react";
import { DISPLAY_PLANS, formatZar, initializePayment, PlanId } from "@/lib/billing";

const benefits: Record<PlanId, string[]> = {
  trial_14_days: [
    "Unlimited CV creation for 14 days",
    "AI CV Builder and CV Studio access",
    "ATS optimisation tools",
    "OpenAI career tools",
  ],
  premium_30_days: [
    "Unlimited CV creation for 30 days",
    "Full AI Career Engine access",
    "Cover letters and interview preparation",
    "Job matching and skills-gap analysis",
    "Priority access to premium tools",
  ],
};

export default function BillingPage() {
  const [loadingPlan, setLoadingPlan] = useState<PlanId | null>(null);
  const [error, setError] = useState("");

  async function checkout(plan: PlanId) {
    setLoadingPlan(plan);
    setError("");
    try {
      const callbackUrl = `${window.location.origin}/payment/callback`;
      const response = await initializePayment(plan, callbackUrl);
      const authorizationUrl = response.payment.authorization_url;
      if (!authorizationUrl) throw new Error("Paystack did not return a checkout URL.");
      window.location.assign(authorizationUrl);
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Could not start checkout.");
      setLoadingPlan(null);
    }
  }

  return (
    <>
      <header className="page-header builder-header">
        <div>
          <span className="eyebrow">Secure payments by Paystack</span>
          <h1>Choose your access plan</h1>
          <p className="muted">Build unlimited CVs and use Makwande Careers AI tools during your selected access period.</p>
        </div>
        <div className="builder-status"><span>Currency</span><strong>ZAR</strong></div>
      </header>

      {error && <div className="error" style={{ marginBottom: 18 }}>{error}</div>}

      <div className="billing-grid">
        {(Object.entries(DISPLAY_PLANS) as [PlanId, (typeof DISPLAY_PLANS)[PlanId]][]).map(([id, plan]) => (
          <article className={`card pricing-card ${id === "premium_30_days" ? "pricing-featured" : ""}`} key={id}>
            {id === "premium_30_days" && <div className="pricing-badge">Best value</div>}
            <div>
              <span className="eyebrow">{plan.duration_days}-day access</span>
              <h2>{plan.name}</h2>
              <div className="price-line"><strong>{formatZar(plan.amount)}</strong><span>once-off</span></div>
            </div>
            <div className="pricing-benefits">
              {benefits[id].map((benefit) => <div key={benefit}><CheckCircle2 size={18} /> <span>{benefit}</span></div>)}
            </div>
            <button className="button button-primary button-wide" disabled={loadingPlan !== null} onClick={() => checkout(id)}>
              {loadingPlan === id ? <><LoaderCircle className="spin-icon" size={18} />Opening Paystack…</> : <><CreditCard size={18} />Choose {plan.duration_days}-day plan</>}
            </button>
          </article>
        ))}
      </div>

      <section className="card payment-trust">
        <ShieldCheck size={28} />
        <div><strong>Secure checkout</strong><p className="muted">Payment details are handled by Paystack. Makwande Careers does not store your card information.</p></div>
      </section>
    </>
  );
}
