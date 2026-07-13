import { NextResponse } from "next/server";
import { AUTH_COOKIE_NAME, verifyAccessToken } from "@/lib/auth";
import { prisma } from "@/lib/prisma";

export async function GET(request: Request) {
  const token = request.cookies.get(AUTH_COOKIE_NAME)?.value;
  if (!token) {
    return NextResponse.json({ error: "Not authenticated." }, { status: 401 });
  }

  const payload = verifyAccessToken(token);
  if (!payload) {
    return NextResponse.json({ error: "Invalid token." }, { status: 401 });
  }

  const user = await prisma.user.findUnique({
    where: { userId: payload.sub },
    include: { role: true },
  });

  if (!user || user.isActive !== "Y") {
    return NextResponse.json({ error: "User not found." }, { status: 404 });
  }

  return NextResponse.json({
    user: {
      userId: user.userId,
      username: user.username,
      displayName: user.displayName,
      email: user.email,
      roleName: user.role.roleName,
    },
  });
}
