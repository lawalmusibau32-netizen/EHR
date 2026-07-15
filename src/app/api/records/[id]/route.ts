import { NextResponse } from "next/server";
import { prisma } from "@/lib/prisma";
import { AUTH_COOKIE_NAME, verifyAccessToken } from "@/lib/auth";

function getUser(request: Request) {
  const token = request.cookies.get(AUTH_COOKIE_NAME)?.value;
  if (!token) return null;
  return verifyAccessToken(token);
}

export async function GET(request: Request, { params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const user = getUser(request);
  if (!user || !["administrator", "doctor", "nurse"].includes(user.roleKey)) {
    return NextResponse.json({ error: "Unauthorized." }, { status: 401 });
  }

  const record = await prisma.medicalRecord.findUnique({
    where: { recordId: Number(id) },
    include: {
      patient: true,
      patientRecord: { select: { displayName: true } },
      diagnoses: { where: { isActive: "Y" }, orderBy: [{ isPrimary: "desc" }, { diagnosedAt: "desc" }] },
      prescriptions: { where: { isActive: "Y" }, orderBy: { prescribedAt: "desc" } },
      treatments: { where: { isActive: "Y" }, orderBy: { treatmentDate: "desc" } },
    },
  });

  if (!record) {
    return NextResponse.json({ error: "Record not found." }, { status: 404 });
  }

  return NextResponse.json({
    record: {
      ...record,
      createdByName: record.patientRecord.displayName,
      patientRecord: undefined,
    },
    diagnoses: record.diagnoses,
    prescriptions: record.prescriptions,
    treatments: record.treatments,
  });
}
