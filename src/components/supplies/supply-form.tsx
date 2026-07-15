"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { Select } from "@/components/ui/select";

const CATEGORIES = ["Medication", "Consumable", "Equipment", "Vaccine", "IV Fluid", "Lab Reagent", "Other"];

interface SupplyFormProps {
  supply?: {
    supplyId: number;
    name: string;
    category: string;
    quantity: number;
    unit: string;
    reorderLevel: number;
    unitCost?: number | null;
    expiryDate?: string | null;
    batchNumber?: string | null;
    manufacturer?: string | null;
    notes?: string | null;
  };
  action: "Create" | "Edit";
}

export function SupplyForm({ supply, action }: SupplyFormProps) {
  const router = useRouter();
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setError("");
    setSubmitting(true);

    const form = new FormData(e.currentTarget);
    const body = Object.fromEntries(form.entries());

    body.quantity = Number(body.quantity);
    body.reorderLevel = Number(body.reorderLevel);
    body.unitCost = body.unitCost ? Number(body.unitCost) : null;
    body.expiryDate = body.expiryDate || "";
    body.batchNumber = body.batchNumber || "";
    body.manufacturer = body.manufacturer || "";
    body.notes = body.notes || "";

    try {
      const res = await fetch(
        supply ? `/api/supplies/${supply.supplyId}` : "/api/supplies",
        {
          method: supply ? "PUT" : "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(body),
        }
      );

      if (!res.ok) {
        const data = await res.json();
        setError(data.error || "Something went wrong.");
        setSubmitting(false);
        return;
      }

      router.push("/supplies");

    } catch {
      setError("Network error. Please try again.");
      setSubmitting(false);
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>{action} Supply</CardTitle>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-6">
          {error && (
            <div className="text-sm text-red-500 bg-red-500/10 px-3 py-2 rounded-md">{error}</div>
          )}

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2 md:col-span-2">
              <Label htmlFor="name">Name *</Label>
              <Input id="name" name="name" defaultValue={supply?.name ?? ""} required />
            </div>

            <div className="space-y-2">
              <Label htmlFor="category">Category *</Label>
              <Select
                name="category"
                options={CATEGORIES.map(c => ({ value: c, label: c }))}
                defaultValue={supply?.category ?? "Medication"}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="unit">Unit *</Label>
              <Input id="unit" name="unit" placeholder="e.g. tabs, bottles, ml" defaultValue={supply?.unit ?? ""} required />
            </div>

            <div className="space-y-2">
              <Label htmlFor="quantity">Current Stock *</Label>
              <Input id="quantity" name="quantity" type="number" min="0" defaultValue={supply?.quantity ?? 0} required />
            </div>

            <div className="space-y-2">
              <Label htmlFor="reorderLevel">Reorder Level</Label>
              <Input id="reorderLevel" name="reorderLevel" type="number" min="0" defaultValue={supply?.reorderLevel ?? 10} />
            </div>

            <div className="space-y-2">
              <Label htmlFor="unitCost">Unit Cost (GHS)</Label>
              <Input id="unitCost" name="unitCost" type="number" min="0" step="0.01" defaultValue={supply?.unitCost ?? ""} />
            </div>

            <div className="space-y-2">
              <Label htmlFor="expiryDate">Expiry Date</Label>
              <Input id="expiryDate" name="expiryDate" type="date" defaultValue={supply?.expiryDate ? supply.expiryDate.split("T")[0] : ""} />
            </div>

            <div className="space-y-2">
              <Label htmlFor="batchNumber">Batch/Lot Number</Label>
              <Input id="batchNumber" name="batchNumber" defaultValue={supply?.batchNumber ?? ""} />
            </div>

            <div className="space-y-2">
              <Label htmlFor="manufacturer">Manufacturer</Label>
              <Input id="manufacturer" name="manufacturer" defaultValue={supply?.manufacturer ?? ""} />
            </div>

            <div className="space-y-2 md:col-span-2">
              <Label htmlFor="notes">Notes</Label>
              <textarea
                id="notes"
                name="notes"
                rows={3}
                className="flex w-full rounded-md border border-input bg-transparent px-3 py-2 text-sm shadow-sm placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring resize-y"
                defaultValue={supply?.notes ?? ""}
              />
            </div>
          </div>

          <div className="flex gap-3 justify-end">
            <Button type="button" variant="outline" onClick={() => router.back()}>Cancel</Button>
            <Button type="submit" disabled={submitting}>
              {submitting ? "Saving..." : action === "Create" ? "Add Supply" : "Update Supply"}
            </Button>
          </div>
        </form>
      </CardContent>
    </Card>
  );
}
