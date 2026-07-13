import { redirect } from "next/navigation";
import { prisma } from "@/lib/prisma";
import { getCurrentUser } from "@/lib/auth";
import UsersList from "./users-list";

export default async function UsersPage() {
  const user = await getCurrentUser();
  if (!user || user.roleKey !== "administrator") redirect("/dashboard");

  const users = await prisma.user.findMany({
    include: { role: true },
    orderBy: { createdAt: "desc" },
  });

  const roles = await prisma.role.findMany({ orderBy: { roleName: "asc" } });

  return <UsersList users={JSON.parse(JSON.stringify(users))} roles={JSON.parse(JSON.stringify(roles))} />;
}
