import { NextRequest, NextResponse } from "next/server";
import { prisma } from "@/lib/db";

export async function GET(req: NextRequest) {
  const { searchParams } = new URL(req.url);
  const month = parseInt(searchParams.get("month") ?? String(new Date().getMonth()));
  const year = parseInt(searchParams.get("year") ?? String(new Date().getFullYear()));

  const start = new Date(year, month, 1);
  const end = new Date(year, month + 1, 0, 23, 59, 59);

  const [jobs, transactions, monthlyHistory] = await Promise.all([
    prisma.job.findMany({
      where: { date: { gte: start, lte: end }, status: { not: "cancelled" } },
      orderBy: { date: "asc" },
    }),
    prisma.transaction.findMany({
      where: { date: { gte: start, lte: end } },
    }),
    // last 6 months income/expense totals
    Promise.all(
      Array.from({ length: 6 }, (_, i) => {
        const d = new Date(year, month - 5 + i, 1);
        const s = new Date(d.getFullYear(), d.getMonth(), 1);
        const e = new Date(d.getFullYear(), d.getMonth() + 1, 0, 23, 59, 59);
        return prisma.transaction.groupBy({
          by: ["type"],
          where: { date: { gte: s, lte: e } },
          _sum: { amount: true },
        }).then((rows) => ({
          month: d.toLocaleDateString("en-AU", { month: "short", year: "2-digit" }),
          income: rows.find((r) => r.type === "income")?._sum.amount ?? 0,
          expenses: rows.find((r) => r.type === "expense")?._sum.amount ?? 0,
        }));
      })
    ),
  ]);

  const income = transactions
    .filter((t) => t.type === "income")
    .reduce((s, t) => s + t.amount, 0);
  const expenses = transactions
    .filter((t) => t.type === "expense")
    .reduce((s, t) => s + t.amount, 0);

  return NextResponse.json({
    jobs,
    income,
    expenses,
    profit: income - expenses,
    monthlyHistory,
  });
}
