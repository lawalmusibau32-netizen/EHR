"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select } from "@/components/ui/select";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

const APPOINTMENT_TYPES = [
  { value: "Consultation", label: "Consultation" },
  { value: "Follow-up", label: "Follow-up" },
  { value: "Procedure", label: "Procedure" },
  { value: "Telehealth", label: "Telehealth" },
  { value: "Lab Review", label: "Lab Review" },
  { value: "Referral", label: "Referral" },
];

interface PatientOption {
  patientId: number;
  mrn: string;
  firstName: string;
  lastName: string;
}

interface ClinicianOption {
  userId: number;
  displayName: string;
  role: { roleName: string };
}

interface AppointmentFormProps {
  patients: PatientOption[];
  clinicians: ClinicianOption[];
  defaultPatientId?: number;
}

export function AppointmentForm({ patients, clinicians, defaultPatientId }: AppointmentFormProps) {
  const router = useRouter();
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const patientOptions = patients.map((p) => ({
    value: String(p.patientId),
    label: `${p.lastName}, ${p.firstName} (${p.mrn})`,
  }));

  const clinicianOptions = clinicians.map((c) => ({
    value: String(c.userId),
    label: `${c.displayName} (${c.role.roleName})`,
  }));

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setError("");
    setLoading(true);

    const form = new FormData(e.currentTarget);
    const body: Record<string, FormDataEntryValue> = {};
    form.forEach((v, k) => { body[k] = v; });

    const res = await fetch("/api/appointments", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });

    const data = await res.json();

    if (!res.ok) {
      setError(data.error ?? "Failed to create appointment.");
      setLoading(false);
      return;
    }

    router.push(`/appointments/${data.appointment?.appointmentId ?? data.appointment?.appointment_id}`);
    router.refresh();
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Appointment Details</CardTitle>
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
              <Label htmlFor="clinicianUserId">Clinician (optional)</Label>
              <Select
                id="clinicianUserId"
                name="clinicianUserId"
                options={[{ value: "", label: "None" }, ...clinicianOptions]}
                placeholder="Select clinician"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="appointmentDate">Date & Time</Label>
              <Input id="appointmentDate" name="appointmentDate" type="datetime-local" required />
            </div>
            <div className="space-y-2">
              <Label htmlFor="appointmentType">Type</Label>
              <Select id="appointmentType" name="appointmentType" options={APPOINTMENT_TYPES} placeholder="Select type" required />
            </div>
            <div className="space-y-2">
              <Label htmlFor="location">Location</Label>
              <Input id="location" name="location" />
            </div>
            <div className="space-y-2">
              <Label htmlFor="reason">Reason</Label>
              <Input id="reason" name="reason" />
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="notes">Notes</Label>
            <textarea
              id="notes"
              name="notes"
              className="flex min-h-[80px] w-full rounded-md border border-input bg-transparent px-3 py-2 text-sm shadow-sm"
              maxLength={4000}
            />
          </div>

          <div className="flex gap-3 pt-2">
            <Button type="submit" disabled={loading}>
              {loading ? "Scheduling..." : "Schedule Appointment"}
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
