import { redirect } from "next/navigation";
import { getCurrentUser } from "@/lib/auth";
import { Sidebar } from "@/components/layout/sidebar";
import { Topbar } from "@/components/layout/topbar";

export default async function DashboardLayout({ children }: { children: React.ReactNode }) {
  const user = await getCurrentUser();

  if (!user) {
    redirect("/login");
  }

  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar roleKey={user.roleKey} />
      <div className="flex-1 flex flex-col overflow-hidden">
        <Topbar userName={user.username} roleName={user.role} />
        <main className="flex-1 overflow-y-auto p-6 scrollbar-thin">{children}</main>
      </div>
    </div>
  );
}
