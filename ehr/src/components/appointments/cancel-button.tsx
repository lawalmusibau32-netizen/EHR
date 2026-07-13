"use client";

import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";

interface CancelButtonProps {
  appointmentId: number;
}

export function CancelAppointmentButton({ appointmentId }: CancelButtonProps) {
  const router = useRouter();

  async function handleCancel() {
    if (!confirm("Are you sure you want to cancel this appointment?")) return;

    const res = await fetch(`/api/appointments/${appointmentId}`, {
      method: "DELETE",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ cancel_note: "Cancelled by user." }),
    });

    if (res.ok) {
      router.refresh();
    }
  }

  return (
    <Button variant="destructive" onClick={handleCancel}>
      Cancel Appointment
    </Button>
  );
}
