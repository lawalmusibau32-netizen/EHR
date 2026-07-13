import { redirect } from "next/navigation";
import Link from "next/link";
import { prisma } from "@/lib/prisma";
import { getCurrentUser } from "@/lib/auth";
import { decryptValue } from "@/lib/crypto";
import { PageHeader } from "@/components/shared/page-header";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { formatDate } from "@/lib/utils";

interface PageProps {
  params: Promise<{ id: string }>;
}

export default async function PatientProfilePage({ params }: PageProps) {
  const user = await getCurrentUser();
  if (!user) redirect("/login");

  const { id } = await params;
  const patient = await prisma.patient.findUnique({
    where: { patientId: Number(id) },
  });

  if (!patient) {
    return <div>Patient not found.</div>;
  }

  const encryptedFields = ["phoneNumber", "email", "addressLine1", "addressLine2", "city", "region"] as const;
  for (const field of encryptedFields) {
    const val = (patient as Record<string, unknown>)[field];
    if (typeof val === "string" && val.startsWith("enc:v1:")) {
      (patient as Record<string, unknown>)[field] = decryptValue(val);
    }
  }

  return (
    <div>
      <PageHeader
        title={`${patient.firstName} ${patient.lastName}`}
        description={`MRN: ${patient.mrn}`}
        actions={
          <div className="flex gap-2">
            {["administrator", "doctor", "receptionist"].includes(user.roleKey) && (
              <Button variant="outline" asChild>
                <Link href={`/patients/${patient.patientId}/edit`}>Edit</Link>
              </Button>
            )}
            <Button variant="outline" asChild>
              <Link href={`/records/new?patientId=${patient.patientId}`}>New Record</Link>
            </Button>
            <Button variant="outline" asChild>
              <Link href={`/appointments/new?patientId=${patient.patientId}`}>Schedule</Link>
            </Button>
          </div>
        }
      />

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Demographics</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="grid grid-cols-2 gap-2 text-sm">
              <span className="text-muted-foreground">MRN</span>
              <span className="font-mono">{patient.mrn}</span>
              <span className="text-muted-foreground">Date of Birth</span>
              <span>{formatDate(patient.dateOfBirth)}</span>
              <span className="text-muted-foreground">Sex</span>
              <span>{patient.sex}</span>
              <span className="text-muted-foreground">Status</span>
              <span>
                <Badge variant={patient.isActive === "Y" ? "success" : "secondary"}>
                  {patient.isActive === "Y" ? "Active" : "Inactive"}
                </Badge>
              </span>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Contact</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="grid grid-cols-2 gap-2 text-sm">
              <span className="text-muted-foreground">Phone</span>
              <span>{patient.phoneNumber ?? "-"}</span>
              <span className="text-muted-foreground">Email</span>
              <span>{patient.email ?? "-"}</span>
              <span className="text-muted-foreground">Address</span>
              <span>
                {[patient.addressLine1, patient.addressLine2, patient.city, patient.region, patient.country]
                  .filter(Boolean)
                  .join(", ") || "-"}
              </span>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
