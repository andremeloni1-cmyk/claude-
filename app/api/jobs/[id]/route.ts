import { NextRequest, NextResponse } from "next/server";
import { prisma } from "@/lib/db";

export async function PUT(req: NextRequest, { params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const body = await req.json();
  const job = await prisma.job.update({
    where: { id },
    data: {
      title: body.title,
      client: body.client,
      jobType: body.jobType,
      date: new Date(body.date),
      location: body.location || null,
      value: parseFloat(body.value) || 0,
      depositPaid: parseFloat(body.depositPaid) || 0,
      status: body.status,
      notes: body.notes || null,
    },
  });
  return NextResponse.json(job);
}

export async function DELETE(_req: NextRequest, { params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  await prisma.job.delete({ where: { id } });
  return NextResponse.json({ success: true });
}
