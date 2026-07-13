import Link from "next/link";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { formatDate } from "@/lib/utils";

const typeColors: Record<string, "default" | "success" | "warning" | "info" | "secondary"> = {
  Encounter: "info",
  Diagnosis: "warning",
  Medication: "success",
  "Lab Result": "secondary",
  Imaging: "default",
  Procedure: "destructive",
  Note: "default",
};

interface RecordRow {
  recordId: number;
  title: string;
  recordType: string;
  recordStatus: string;
  encounterDate: Date;
  patient: { patientId: number; mrn: string; firstName: string; lastName: string };
  createdByName: string;
  diagnosisCount: number;
  prescriptionCount: number;
  treatmentCount: number;
}

interface RecordsTableProps {
  records: RecordRow[];
}

export function RecordsTable({ records }: RecordsTableProps) {
  return (
    <div className="rounded-md border">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Date</TableHead>
            <TableHead>Patient</TableHead>
            <TableHead>Title</TableHead>
            <TableHead>Type</TableHead>
            <TableHead>Dx / Rx / Tx</TableHead>
            <TableHead>Status</TableHead>
            <TableHead className="text-right">Actions</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {records.length === 0 && (
            <TableRow>
              <TableCell colSpan={7} className="text-center text-muted-foreground py-8">
                No records found.
              </TableCell>
            </TableRow>
          )}
          {records.map((r) => (
            <TableRow key={r.recordId}>
              <TableCell>{formatDate(r.encounterDate)}</TableCell>
              <TableCell>
                <Link href={`/patients/${r.patient.patientId}`} className="font-medium hover:underline">
                  {r.patient.lastName}, {r.patient.firstName}
                </Link>
                <div className="text-xs text-muted-foreground font-mono">{r.patient.mrn}</div>
              </TableCell>
              <TableCell className="max-w-[200px] truncate">{r.title}</TableCell>
              <TableCell>
                <Badge variant={typeColors[r.recordType] ?? "default"}>{r.recordType}</Badge>
              </TableCell>
              <TableCell className="text-xs text-muted-foreground">
                {r.diagnosisCount}d / {r.prescriptionCount}p / {r.treatmentCount}t
              </TableCell>
              <TableCell>{r.recordStatus}</TableCell>
              <TableCell className="text-right">
                <Button variant="ghost" size="sm" asChild>
                  <Link href={`/records/${r.recordId}`}>View</Link>
                </Button>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}
