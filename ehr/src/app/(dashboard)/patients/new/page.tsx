import { redirect } from "next/navigation";
import { getCurrentUser } from "@/lib/auth";
import { PageHeader } from "@/components/shared/page-header";
import { PatientForm } from "@/components/patients/patient-form";

export default async function NewPatientPage() {
  const user = await getCurrentUser();
  if (!user || !["administrator", "doctor", "receptionist"].includes(user.roleKey)) {
    redirect("/patients");
  }

  return (
    <div>
      <PageHeader title="Add Patient" description="Register a new patient in the system" />
      <PatientForm action="Create" />
    </div>
  );
}
