import Link from "next/link";
import { redirect } from "next/navigation";
import { prisma } from "@/lib/prisma";
import { getCurrentUser } from "@/lib/auth";
import { PageHeader } from "@/components/shared/page-header";
import { Button } from "@/components/ui/button";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Plus, Package } from "lucide-react";

export default async function SuppliesPage() {
  const user = await getCurrentUser();
  if (!user) redirect("/login");

  const supplies = await prisma.inventorySupply.findMany({
    where: { isActive: "Y" },
    orderBy: [{ name: "asc" }],
  });

  const canWrite = ["administrator", "receptionist"].includes(user.roleKey);

  return (
    <div>
      <PageHeader
        title="Inventory"
        description="Track health supplies, medications, and equipment"
        actions={
          canWrite && (
            <Button asChild>
              <Link href="/supplies/new">
                <Plus className="h-4 w-4 mr-1" />
                Add Supply
              </Link>
            </Button>
          )
        }
      />

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <div className="rounded-lg border bg-card p-4">
          <div className="text-xs text-muted-foreground mb-1">Total Items</div>
          <div className="text-2xl font-bold text-foreground">{supplies.length}</div>
        </div>
        <div className="rounded-lg border bg-card p-4">
          <div className="text-xs text-muted-foreground mb-1">Medications</div>
          <div className="text-2xl font-bold text-primary">{supplies.filter(s => s.category === "Medication").length}</div>
        </div>
        <div className="rounded-lg border bg-card p-4">
          <div className="text-xs text-muted-foreground mb-1">Low Stock</div>
          <div className="text-2xl font-bold text-amber-500">{supplies.filter(s => s.quantity <= s.reorderLevel).length}</div>
        </div>
        <div className="rounded-lg border bg-card p-4">
          <div className="text-xs text-muted-foreground mb-1">Categories</div>
          <div className="text-2xl font-bold text-emerald-500">{new Set(supplies.map(s => s.category)).size}</div>
        </div>
      </div>

      <div className="rounded-md border">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Name</TableHead>
              <TableHead>Category</TableHead>
              <TableHead>Stock</TableHead>
              <TableHead>Unit</TableHead>
              <TableHead>Reorder Level</TableHead>
              <TableHead>Expiry</TableHead>
              <TableHead className="text-right">Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {supplies.length === 0 && (
              <TableRow>
                <TableCell colSpan={7} className="text-center text-muted-foreground py-12">
                  <Package className="h-8 w-8 mx-auto mb-2 opacity-30" />
                  No supplies yet. Add your first item.
                </TableCell>
              </TableRow>
            )}
            {supplies.map((supply) => {
              const isLow = supply.quantity <= supply.reorderLevel;
              const isExpired = supply.expiryDate && new Date(supply.expiryDate) < new Date();
              return (
                <TableRow key={supply.supplyId}>
                  <TableCell className="font-medium">{supply.name}</TableCell>
                  <TableCell><Badge variant="outline">{supply.category}</Badge></TableCell>
                  <TableCell>
                    <span className={isLow ? "text-amber-500 font-semibold" : ""}>
                      {supply.quantity}
                      {isLow && " ⚠"}
                    </span>
                  </TableCell>
                  <TableCell className="text-muted-foreground">{supply.unit}</TableCell>
                  <TableCell className="text-xs text-muted-foreground">{supply.reorderLevel}</TableCell>
                  <TableCell>
                    {supply.expiryDate ? (
                      <span className={isExpired ? "text-red-500 text-xs" : "text-xs"}>
                        {new Date(supply.expiryDate).toLocaleDateString("en-GB")}
                        {isExpired && " (expired)"}
                      </span>
                    ) : (
                      <span className="text-muted-foreground/50 text-xs">—</span>
                    )}
                  </TableCell>
                  <TableCell className="text-right">
                    {canWrite && (
                      <Button variant="ghost" size="sm" asChild>
                        <Link href={`/supplies/${supply.supplyId}/edit`}>Edit</Link>
                      </Button>
                    )}
                  </TableCell>
                </TableRow>
              );
            })}
          </TableBody>
        </Table>
      </div>
    </div>
  );
}
