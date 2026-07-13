"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select } from "@/components/ui/select";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

const RECORD_TYPES = [
  { value: "Encounter", label: "Encounter" },
  { value: "Diagnosis", label: "Diagnosis" },
  { value: "Medication", label: "Medication" },
  { value: "Lab Result", label: "Lab Result" },
  { value: "Imaging", label: "Imaging" },
  { value: "Procedure", label: "Procedure" },
  { value: "Note", label: "Note" },
];

interface PatientOption {
  patientId: number;
  mrn: string;
  firstName: string;
  lastName: string;
}

interface RecordFormProps {
  patients: PatientOption[];
  defaultPatientId?: number;
}

export function RecordForm({ patients, defaultPatientId }: RecordFormProps) {
  const router = useRouter();
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const patientOptions = patients.map((p) => ({
    value: String(p.patientId),
    label: `${p.lastName}, ${p.firstName} (${p.mrn})`,
  }));

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setError("");
    setLoading(true);

    const form = new FormData(e.currentTarget);
    const body: Record<string, FormDataEntryValue> = {};
    form.forEach((v, k) => { body[k] = v; });

    const res = await fetch("/api/records", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });

    const data = await res.json();

    if (!res.ok) {
      setError(data.error ?? "Failed to create record.");
      setLoading(false);
      return;
    }

    router.push(`/records/${data.record?.recordId}`);
    router.refresh();
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Record Details</CardTitle>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-4">
          {error && <div className="rounded-md bg-destructive/10 p-3 text-sm text-destructive">{error}</div>}

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="patientId">Patient</Label>
              <Select
                id="patientId"
                name="patientId"
                options={patientOptions}
                placeholder="Select patient"
                defaultValue={defaultPatientId ? String(defaultPatientId) : ""}
                required
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="recordType">Record Type</Label>
              <Select id="recordType" name="recordType" options={RECORD_TYPES} placeholder="Select type" required />
            </div>
            <div className="space-y-2">
              <Label htmlFor="title">Title</Label>
              <Input id="title" name="title" required maxLength={150} />
            </div>
            <div className="space-y-2">
              <Label htmlFor="encounterDate">Encounter Date</Label>
              <Input id="encounterDate" name="encounterDate" type="datetime-local" />
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="clinicalNote">Clinical Note</Label>
            <textarea
              id="clinicalNote"
              name="clinicalNote"
              className="flex min-h-[200px] w-full rounded-md border border-input bg-transparent px-3 py-2 text-sm shadow-sm"
              required
              maxLength={10000}
            />
          </div>

          <div className="flex gap-3 pt-2">
            <Button type="submit" disabled={loading}>
              {loading ? "Creating..." : "Create Record"}
            </Button>
            <Button type="button" variant="outline" onClick={() => router.back()}>
              Cancel
            </Button>
          </div>
        </form>
      </CardContent>
    </Card>
  );
}
