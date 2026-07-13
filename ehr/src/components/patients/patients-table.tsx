import Link from "next/link";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { formatDate } from "@/lib/utils";
import type { Patient } from "@/generated/prisma/client";

interface PatientsTableProps {
  patients: Patient[];
}

export function PatientsTable({ patients }: PatientsTableProps) {
  return (
    <div className="rounded-md border">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>MRN</TableHead>
            <TableHead>Name</TableHead>
            <TableHead>DOB</TableHead>
            <TableHead>Sex</TableHead>
            <TableHead>Status</TableHead>
            <TableHead className="text-right">Actions</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {patients.length === 0 && (
            <TableRow>
              <TableCell colSpan={6} className="text-center text-muted-foreground py-8">
                No patients found.
              </TableCell>
            </TableRow>
          )}
          {patients.map((patient) => (
            <TableRow key={patient.patientId}>
              <TableCell className="font-mono text-xs">{patient.mrn}</TableCell>
              <TableCell>
                <Link href={`/patients/${patient.patientId}`} className="font-medium hover:underline">
                  {patient.lastName}, {patient.firstName}
                </Link>
              </TableCell>
              <TableCell>{formatDate(patient.dateOfBirth)}</TableCell>
              <TableCell>{patient.sex}</TableCell>
              <TableCell>
                <Badge variant={patient.isActive === "Y" ? "success" : "secondary"}>
                  {patient.isActive === "Y" ? "Active" : "Inactive"}
                </Badge>
              </TableCell>
              <TableCell className="text-right">
                <Button variant="ghost" size="sm" asChild>
                  <Link href={`/patients/${patient.patientId}`}>View</Link>
                </Button>
                <Button variant="ghost" size="sm" asChild>
                  <Link href={`/patients/${patient.patientId}/edit`}>Edit</Link>
                </Button>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}
