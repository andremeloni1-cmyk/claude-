import { NextRequest, NextResponse } from "next/server";
import { prisma } from "@/lib/db";

export async function GET(req: NextRequest) {
  const { searchParams } = new URL(req.url);
  const month = searchParams.get("month");
  const year = searchParams.get("year");

  let where = {};
  if (month && year) {
    const start = new Date(parseInt(year), parseInt(month), 1);
    const end = new Date(parseInt(year), parseInt(month) + 1, 0, 23, 59, 59);
    where = { date: { gte: start, lte: end } };
  }

  const jobs = await prisma.job.findMany({
    where,
    orderBy: { date: "asc" },
  });

  return NextResponse.json(jobs);
}

export async function POST(req: NextRequest) {
  const body = await req.json();
  const job = await prisma.job.create({
    data: {
      title: body.title,
      client: body.client,
      jobType: body.jobType,
      date: new Date(body.date),
      location: body.location || null,
      value: parseFloat(body.value) || 0,
      depositPaid: parseFloat(body.depositPaid) || 0,
      status: body.status || "confirmed",
      notes: body.notes || null,
    },
  });
  return NextResponse.json(job, { status: 201 });
}
