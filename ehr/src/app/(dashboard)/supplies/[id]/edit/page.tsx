import { redirect, notFound } from "next/navigation";
import { prisma } from "@/lib/prisma";
import { getCurrentUser } from "@/lib/auth";
import { SupplyForm } from "@/components/supplies/supply-form";

interface PageProps {
  params: Promise<{ id: string }>;
}

export default async function EditSupplyPage({ params }: PageProps) {
  const user = await getCurrentUser();
  if (!user || !["administrator", "receptionist"].includes(user.roleKey)) redirect("/supplies");

  const { id } = await params;
  const supply = await prisma.inventorySupply.findUnique({ where: { supplyId: Number(id) } });
  if (!supply || supply.isActive !== "Y") notFound();

  return (
    <div className="max-w-2xl mx-auto">
      <SupplyForm
        action="Edit"
        supply={{
          supplyId: supply.supplyId,
          name: supply.name,
          category: supply.category,
          quantity: supply.quantity,
          unit: supply.unit,
          reorderLevel: supply.reorderLevel,
          unitCost: supply.unitCost ? Number(supply.unitCost) : null,
          expiryDate: supply.expiryDate?.toISOString() ?? null,
          batchNumber: supply.batchNumber,
          manufacturer: supply.manufacturer,
          notes: supply.notes,
        }}
      />
    </div>
  );
}
