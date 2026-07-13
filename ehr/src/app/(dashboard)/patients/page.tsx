import Link from "next/link";
import { redirect } from "next/navigation";
import { prisma } from "@/lib/prisma";
import { getCurrentUser } from "@/lib/auth";
import { PageHeader } from "@/components/shared/page-header";
import { SearchInput } from "@/components/shared/search-input";
import { PatientsTable } from "@/components/patients/patients-table";
import { Button } from "@/components/ui/button";
import { Plus } from "lucide-react";

interface PageProps {
  searchParams: Promise<{ q?: string; include_inactive?: string }>;
}

export default async function PatientsPage({ searchParams }: PageProps) {
  const user = await getCurrentUser();
  if (!user) redirect("/login");

  const params = await searchParams;
  const search = params.q?.trim() ?? "";
  const includeInactive = params.include_inactive === "1";

  const patients = await prisma.patient.findMany({
    where: {
      ...(search
        ? {
            OR: [
              { mrn: { contains: search } },
              { firstName: { contains: search } },
              { lastName: { contains: search } },
              { email: { contains: search } },
            ],
          }
        : {}),
      ...(includeInactive ? {} : { isActive: "Y" }),
    },
    orderBy: [{ lastName: "asc" }, { firstName: "asc" }],
  });

  return (
    <div>
      <PageHeader
        title="Patients"
        description="Manage patient records"
        actions={
          ["administrator", "doctor", "receptionist"].includes(user.roleKey) && (
            <Button asChild>
              <Link href="/patients/new">
                <Plus className="h-4 w-4 mr-1" />
                Add Patient
              </Link>
            </Button>
          )
        }
      />

      <div className="flex items-center gap-3 mb-4">
        <SearchInput placeholder="Search patients..." />
      </div>

      <PatientsTable patients={patients} />
    </div>
  );
}
