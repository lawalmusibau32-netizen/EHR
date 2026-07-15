import { Sidebar } from "./sidebar";
import { Topbar } from "./topbar";
import { getCurrentUser } from "@/lib/auth";

interface AppShellProps {
  children: React.ReactNode;
}

export async function AppShell({ children }: AppShellProps) {
  const user = await getCurrentUser();

  if (!user) {
    return <>{children}</>;
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
