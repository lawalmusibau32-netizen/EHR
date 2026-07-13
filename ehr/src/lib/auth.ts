import bcrypt from "bcryptjs";
import jwt from "jsonwebtoken";
import { cookies } from "next/headers";
import { normalizeRoleKey, type RoleKey } from "./roles";

const BCRYPT_ROUNDS = 12;
const PASSWORD_MIN_LENGTH = 6;

function getSecret(): string {
  return process.env.JWT_SECRET_KEY ?? process.env.SECRET_KEY ?? "change-this-in-production";
}

function getIssuer(): string {
  return process.env.JWT_ISSUER ?? "healthiq-ehr";
}

function getAudience(): string {
  return process.env.JWT_AUDIENCE ?? "healthiq-users";
}

export function hashPassword(password: string): string {
  return bcrypt.hashSync(password, BCRYPT_ROUNDS);
}

export function verifyPassword(password: string, hash: string): boolean {
  return bcrypt.compareSync(password, hash);
}

export function validatePassword(password: string, username?: string): string[] {
  const errors: string[] = [];
  if (password.length < PASSWORD_MIN_LENGTH) {
    errors.push(`Password must be at least ${PASSWORD_MIN_LENGTH} characters.`);
  }
  if (username && password.toLowerCase().includes(username.toLowerCase())) {
    errors.push("Password must not contain the username.");
  }
  if (!/[a-z]/.test(password)) errors.push("Password must include a lowercase letter.");
  if (!/\d/.test(password)) errors.push("Password must include a digit.");
  return errors;
}

export interface TokenPayload {
  sub: number;
  username: string;
  role: string;
  roleKey: string;
  jti: string;
  iat: number;
  exp: number;
  iss: string;
  aud: string;
}

export function createAccessToken(user: {
  userId: number;
  username: string;
  roleName: string;
  jti: string;
}): string {
  const now = Math.floor(Date.now() / 1000);
  const expiresInMinutes = parseInt(process.env.JWT_ACCESS_TOKEN_MINUTES ?? "30", 10);

  return jwt.sign(
    {
      sub: user.userId,
      username: user.username,
      role: user.roleName,
      roleKey: normalizeRoleKey(user.roleName),
      jti: user.jti,
      iat: now,
      exp: now + expiresInMinutes * 60,
      iss: getIssuer(),
      aud: getAudience(),
    } satisfies TokenPayload,
    getSecret(),
    { algorithm: "HS256" }
  );
}

export function verifyAccessToken(token: string): TokenPayload | null {
  try {
    const payload = jwt.verify(token, getSecret(), {
      algorithms: ["HS256"],
      issuer: getIssuer(),
      audience: getAudience(),
    }) as TokenPayload;
    return payload;
  } catch {
    return null;
  }
}

export const AUTH_COOKIE_NAME = process.env.AUTH_COOKIE_NAME ?? "ehr_access_token";

export async function setAuthCookie(token: string): Promise<void> {
  const cookieStore = await cookies();
  const expiresInMinutes = parseInt(process.env.JWT_ACCESS_TOKEN_MINUTES ?? "30", 10);

  cookieStore.set(AUTH_COOKIE_NAME, token, {
    httpOnly: true,
    secure: process.env.NODE_ENV === "production",
    sameSite: "lax",
    maxAge: expiresInMinutes * 60,
    path: "/",
  });
}

export async function clearAuthCookie(): Promise<void> {
  const cookieStore = await cookies();
  cookieStore.set(AUTH_COOKIE_NAME, "", { httpOnly: true, path: "/", maxAge: 0 });
}

export async function getTokenFromCookies(): Promise<string | undefined> {
  return (await cookies()).get(AUTH_COOKIE_NAME)?.value;
}

export async function getCurrentUser(): Promise<TokenPayload | null> {
  const token = await getTokenFromCookies();
  if (!token) return null;
  return verifyAccessToken(token);
}

export async function requireAuth(): Promise<TokenPayload> {
  const user = await getCurrentUser();
  if (!user) throw new Error("Authentication required.");
  return user;
}

export async function requireRole(...roles: RoleKey[]): Promise<TokenPayload> {
  const user = await requireAuth();
  if (roles.length > 0 && !roles.includes(user.roleKey as RoleKey)) {
    throw new Error("You do not have permission to access this resource.");
  }
  return user;
}

export interface SafeUser {
  userId: number;
  username: string;
  displayName: string;
  email: string | null;
  roleName: string;
  roleKey: string;
  isActive: string;
  mfaEnabled: string;
}

export function toSafeUser(user: {
  user_id: number;
  username: string;
  display_name: string;
  email: string | null;
  role_name: string;
  is_active: string;
  mfa_enabled: string;
}): SafeUser {
  return {
    userId: user.user_id,
    username: user.username,
    displayName: user.display_name,
    email: user.email,
    roleName: user.role_name,
    roleKey: normalizeRoleKey(user.role_name),
    isActive: user.is_active,
    mfaEnabled: user.mfa_enabled,
  };
}
