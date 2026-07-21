import { NextResponse } from "next/server";

export async function POST() {
  const response = NextResponse.json({ authenticated: false });
  response.cookies.set("makwande_access_token", "", {
    httpOnly: true,
    path: "/",
    expires: new Date(0),
  });
  return response;
}
