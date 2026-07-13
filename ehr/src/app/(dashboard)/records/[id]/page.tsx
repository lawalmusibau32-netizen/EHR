import { redirect } from "next/navigation";
import Link from "next/link";
import { prisma } from "@/lib/prisma";
import { getCurrentUser } from "@/lib/auth";
import { PageHeader } from "@/components/shared/page-header";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { formatDateTime } from "@/lib/utils";

interface PageProps {
  params: Promise<{ id: string }>;
}

export default async function RecordDetailPage({ params }: PageProps) {
  const user = await getCurrentUser();
  if (!user || !["administrator", "doctor", "nurse"].includes(user.roleKey)) {
    redirect("/records");
  }

  const { id } = await params;

  const record = await prisma.medicalRecord.findUnique({
    where: { recordId: Number(id) },
    include: {
      patient: { select: { displayName: true } },
      patientRecord: { select: { patientId: true, mrn: true, firstName: true, lastName: true } },
      diagnoses: { where: { isActive: "Y" }, orderBy: [{ isPrimary: "desc" }, { diagnosedAt: "desc" }] },
      prescriptions: { where: { isActive: "Y" }, orderBy: { prescribedAt: "desc" } },
      treatments: { where: { isActive: "Y" }, orderBy: { treatmentDate: "desc" } },
    },
  });

  if (!record) {
    return <div>Record not found.</div>;
  }

  return (
    <div>
      <PageHeader
        title={record.title}
        description={`${record.recordType} • ${formatDateTime(record.encounterDate)}`}
        actions={
          <Button variant="outline" asChild>
            <Link href="/records">Back to Records</Link>
          </Button>
        }
      />

      <div className="grid grid-cols-1 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Record Info</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="grid grid-cols-2 gap-2 text-sm">
              <span className="text-muted-foreground">Patient</span>
              <span>
                <Link href={`/patients/${record.patientRecord.patientId}`} className="hover:underline font-medium">
                  {record.patientRecord.firstName} {record.patientRecord.lastName}
                </Link>
                <span className="text-xs text-muted-foreground ml-1 font-mono">({record.patientRecord.mrn})</span>
              </span>
              <span className="text-muted-foreground">Type</span>
              <span><Badge variant="info">{record.recordType}</Badge></span>
              <span className="text-muted-foreground">Status</span>
              <span>{record.recordStatus}</span>
              <span className="text-muted-foreground">Created By</span>
              <span>{record.patient.displayName}</span>
              <span className="text-muted-foreground">Encounter Date</span>
              <span>{formatDateTime(record.encounterDate)}</span>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Clinical Note</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm whitespace-pre-wrap">{record.clinicalNote}</p>
          </CardContent>
        </Card>

        {record.diagnoses.length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle>Diagnoses ({record.diagnoses.length})</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {record.diagnoses.map((d) => (
                  <div key={d.diagnosisId} className="text-sm">
                    <div className="flex items-center gap-2">
                      <span className="font-medium">{d.diagnosisName}</span>
                      {d.isPrimary === "Y" && <Badge variant="warning">Primary</Badge>}
                      <Badge variant={d.diagnosisStatus === "ACTIVE" ? "success" : "secondary"}>{d.diagnosisStatus}</Badge>
                    </div>
                    {d.icd10Code && <div className="text-xs text-muted-foreground mt-0.5">ICD-10: {d.icd10Code}</div>}
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}

        {record.prescriptions.length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle>Prescriptions ({record.prescriptions.length})</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {record.prescriptions.map((p) => (
                  <div key={p.prescriptionId} className="text-sm">
                    <div className="font-medium">{p.medicationName}</div>
                    <div className="text-xs text-muted-foreground mt-0.5">
                      {[p.dosage, p.frequency, p.route].filter(Boolean).join(" • ") || "-"}
                      {p.durationDays ? ` • ${p.durationDays} days` : ""}
                    </div>
                    {p.instructions && <div className="text-xs mt-0.5">{p.instructions}</div>}
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}

        {record.treatments.length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle>Treatments ({record.treatments.length})</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {record.treatments.map((t) => (
                  <div key={t.treatmentId} className="text-sm">
                    <div className="font-medium">{t.treatmentName}</div>
                    {t.treatmentDescription && <div className="text-xs text-muted-foreground mt-0.5">{t.treatmentDescription}</div>}
                    <div className="flex gap-2 text-xs text-muted-foreground mt-0.5">
                      {t.outcome && <span>Outcome: {t.outcome}</span>}
                      {t.treatmentDate && <span>{formatDateTime(t.treatmentDate)}</span>}
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}
