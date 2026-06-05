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

  const transactions = await prisma.transaction.findMany({
    where,
    include: { job: { select: { title: true, client: true } } },
    orderBy: { date: "desc" },
  });

  return NextResponse.json(transactions);
}

export async function POST(req: NextRequest) {
  const body = await req.json();
  const transaction = await prisma.transaction.create({
    data: {
      type: body.type,
      category: body.category,
      amount: parseFloat(body.amount),
      date: new Date(body.date),
      description: body.description || null,
      jobId: body.jobId || null,
    },
    include: { job: { select: { title: true, client: true } } },
  });
  return NextResponse.json(transaction, { status: 201 });
}
