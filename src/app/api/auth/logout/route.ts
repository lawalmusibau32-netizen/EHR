import { NextResponse } from "next/server";
import { prisma } from "@/lib/prisma";
import { AUTH_COOKIE_NAME, verifyAccessToken } from "@/lib/auth";

export async function POST(request: Request) {
  try {
    const token = request.cookies.get(AUTH_COOKIE_NAME)?.value;
    if (token) {
      const payload = verifyAccessToken(token);
      if (payload) {
        await prisma.authSession.updateMany({
          where: { jti: payload.jti },
          data: { revokedAt: new Date() },
        });

        await prisma.auditLog.create({
          data: {
            userId: payload.sub,
            actionType: "LOGOUT",
            entityName: "auth_sessions",
            entityId: "browser",
            details: "Logout completed.",
            ipAddress: request.headers.get("x-forwarded-for") ?? "unknown",
          },
        });
      }
    }

    const response = NextResponse.json({ message: "Logged out." });
    response.cookies.set(AUTH_COOKIE_NAME, "", { httpOnly: true, path: "/", maxAge: 0 });
    return response;
  } catch {
    return NextResponse.json({ error: "An error occurred." }, { status: 500 });
  }
}
