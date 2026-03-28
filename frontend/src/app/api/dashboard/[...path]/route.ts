import { NextRequest, NextResponse } from "next/server";

const BACKEND_ORIGIN = process.env.BACKEND_ORIGIN ?? "http://127.0.0.1:8000";

export async function GET(
  request: NextRequest,
  context: { params: Promise<{ path: string[] }> },
) {
  const { path } = await context.params;
  const query = request.nextUrl.searchParams.toString();
  const suffix = query ? `?${query}` : "";
  const url = `${BACKEND_ORIGIN}/api/dashboard/${path.join("/")}${suffix}`;

  try {
    const response = await fetch(url, {
      cache: "no-store",
      headers: {
        Accept: "application/json",
      },
    });
    const contentType = response.headers.get("content-type") ?? "application/json";
    const text = await response.text();
    return new NextResponse(text, {
      status: response.status,
      headers: {
        "content-type": contentType,
      },
    });
  } catch {
    return NextResponse.json(
      {
        code: 500,
        message: "backend unavailable",
        data: null,
      },
      { status: 500 },
    );
  }
}
