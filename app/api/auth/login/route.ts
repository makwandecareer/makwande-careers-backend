import { NextRequest, NextResponse } from "next/server";

const BACKEND = process.env.BACKEND_API_URL!;

export async function POST(request: NextRequest) {
  const payload = await request.json();
  const response = await fetch(`${BACKEND}/api/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
    cache: "no-store",
  });
  const data = await response.json();

  if (!response.ok) return NextResponse.json(data, { status: response.status });

  const result = NextResponse.json({ authenticated: true });
  result.cookies.set("makwande_access_token", data.access_token, {
    httpOnly: true,
    secure: process.env.NODE_ENV === "production",
    sameSite: "lax",
    path: "/",
    maxAge: 60 * 60 * 24 * 30,
  });
  return result;
}
