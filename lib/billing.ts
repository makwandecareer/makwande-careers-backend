import { api } from "@/lib/client-api";

export type PlanId = "trial_14_days" | "premium_30_days";

export type BillingPlan = {
  name: string;
  amount: number;
  currency: string;
  duration_days: number;
};

export type PlansResponse = {
  plans: Record<PlanId, BillingPlan>;
};

export type InitializePaymentResponse = {
  plan: PlanId;
  reference: string;
  payment: {
    authorization_url?: string;
    access_code?: string;
    reference?: string;
  };
};

export type VerifyPaymentResponse = {
  reference: string;
  status: string | null;
  paid: boolean;
  data?: Record<string, unknown>;
};

export const DISPLAY_PLANS: Record<PlanId, BillingPlan> = {
  trial_14_days: {
    name: "14-Day Unlimited CV Trial",
    amount: 4500,
    currency: "ZAR",
    duration_days: 14,
  },
  premium_30_days: {
    name: "30-Day Premium",
    amount: 30000,
    currency: "ZAR",
    duration_days: 30,
  },
};

export function formatZar(amountInCents: number) {
  return new Intl.NumberFormat("en-ZA", {
    style: "currency",
    currency: "ZAR",
    maximumFractionDigits: 0,
  }).format(amountInCents / 100);
}

export async function initializePayment(plan: PlanId, callbackUrl: string) {
  return api<InitializePaymentResponse>("/api/billing/initialize", {
    method: "POST",
    body: JSON.stringify({ plan, callback_url: callbackUrl }),
  });
}

export async function verifyPayment(reference: string) {
  return api<VerifyPaymentResponse>(`/api/billing/verify/${encodeURIComponent(reference)}`);
}
