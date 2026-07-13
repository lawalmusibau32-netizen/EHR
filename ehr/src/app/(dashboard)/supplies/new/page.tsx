import { redirect } from "next/navigation";
import { getCurrentUser } from "@/lib/auth";
import { SupplyForm } from "@/components/supplies/supply-form";

export default async function NewSupplyPage() {
  const user = await getCurrentUser();
  if (!user || !["administrator", "receptionist"].includes(user.roleKey)) redirect("/supplies");

  return (
    <div className="max-w-2xl mx-auto">
      <SupplyForm action="Create" />
    </div>
  );
}
