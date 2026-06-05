import { PrismaClient } from "@prisma/client";
import { PrismaBetterSqlite3 } from "@prisma/adapter-better-sqlite3";
import path from "path";

const dbPath = path.join(process.cwd(), "dev.db");
const adapter = new PrismaBetterSqlite3({ url: dbPath });
// eslint-disable-next-line @typescript-eslint/no-explicit-any
const prisma = new PrismaClient({ adapter } as any);

async function main() {
  const now = new Date();
  const y = now.getFullYear();
  const m = now.getMonth();

  await prisma.job.createMany({
    data: [
      {
        title: "Full Day Wedding Photography",
        client: "James & Sarah Thompson",
        jobType: "wedding",
        date: new Date(y, m, 8),
        location: "Centennial Park, Sydney",
        value: 4200,
        depositPaid: 1000,
        status: "confirmed",
      },
      {
        title: "Kitchen Installation",
        client: "Mike Robertson",
        jobType: "joinery",
        date: new Date(y, m, 15),
        location: "Mosman, NSW",
        value: 8500,
        depositPaid: 2000,
        status: "confirmed",
      },
      {
        title: "Engagement Shoot",
        client: "Priya & Daniel Patel",
        jobType: "wedding",
        date: new Date(y, m, 22),
        location: "Manly Beach",
        value: 950,
        depositPaid: 950,
        status: "completed",
      },
      {
        title: "Custom Wardrobe Build",
        client: "Jessica Chen",
        jobType: "joinery",
        date: new Date(y, m, 28),
        location: "Randwick, NSW",
        value: 3200,
        depositPaid: 800,
        status: "confirmed",
      },
    ],
  });

  await prisma.transaction.createMany({
    data: [
      { type: "income", category: "Wedding Photography", amount: 1000, date: new Date(y, m, 2), description: "Thompson wedding deposit" },
      { type: "income", category: "Joinery / Kitchen", amount: 2000, date: new Date(y, m, 5), description: "Robertson kitchen deposit" },
      { type: "income", category: "Final Payment", amount: 950, date: new Date(y, m, 22), description: "Patel engagement shoot" },
      { type: "expense", category: "Equipment", amount: 320, date: new Date(y, m, 3), description: "Extra camera batteries & cards" },
      { type: "expense", category: "Materials", amount: 1240, date: new Date(y, m, 10), description: "Kitchen cabinet hardware" },
      { type: "expense", category: "Travel", amount: 85, date: new Date(y, m, 14), description: "Fuel & parking" },
      { type: "expense", category: "Software / Subscriptions", amount: 49, date: new Date(y, m, 1), description: "Lightroom subscription" },
    ],
  });

  console.log("Seed data created.");
}

main().finally(() => prisma.$disconnect());
