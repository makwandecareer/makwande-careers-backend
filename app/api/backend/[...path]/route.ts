import { cookies } from "next/headers";
import { NextRequest, NextResponse } from "next/server";

function getBackendTarget(path: string[], search: string) {
  const configuredBackend = process.env.BACKEND_API_URL?.trim().replace(/\/$/, "");

  if (!configuredBackend) {
    throw new Error("BACKEND_API_URL is not configured.");
  }

  let backendPath = path.join("/").replace(/^\/+/, "");

  if (configuredBackend.endsWith("/api") && backendPath.startsWith("api/")) {
    backendPath = backendPath.slice(4);
  }

  return `${configuredBackend}/${backendPath}${search}`;
}

async function proxy(
  request: NextRequest,
  context: { params: Promise<{ path: string[] }> },
) {
  const { path } = await context.params;
  const token = (await cookies()).get("makwande_access_token")?.value;
  let target: string;
  try {
    target = getBackendTarget(path, request.nextUrl.search);
  } catch (error) {
    return NextResponse.json(
      { detail: error instanceof Error ? error.message : "Backend configuration is invalid." },
      { status: 500 },
    );
  }

  const headers = new Headers();
  const contentType = request.headers.get("content-type");
  if (contentType) headers.set("Content-Type", contentType);
  if (token) headers.set("Authorization", `Bearer ${token}`);

  const body =
    request.method === "GET" || request.method === "HEAD"
      ? undefined
      : await request.arrayBuffer();

  let backendResponse: Response;
  try {
    backendResponse = await fetch(target, {
      method: request.method,
      headers,
      body,
      cache: "no-store",
    });
  } catch {
    return NextResponse.json(
      { detail: "The frontend could not connect to the backend API." },
      { status: 502 },
    );
  }

  const responseHeaders = new Headers();
  for (const key of ["content-type", "content-disposition"]) {
    const value = backendResponse.headers.get(key);
    if (value) responseHeaders.set(key, value);
  }

  return new NextResponse(backendResponse.body, {
    status: backendResponse.status,
    headers: responseHeaders,
  });
}

export const GET = proxy;
export const POST = proxy;
export const PUT = proxy;
export const PATCH = proxy;
export const DELETE = proxy;
