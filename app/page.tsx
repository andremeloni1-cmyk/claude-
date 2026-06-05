"use client";
import { useEffect, useState, useCallback } from "react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";
import {
  TrendingUp,
  TrendingDown,
  DollarSign,
  CalendarDays,
  Camera,
  Hammer,
  ChevronLeft,
  ChevronRight,
} from "lucide-react";
import { formatCurrency, formatDate, JOB_STATUS_COLORS, JOB_STATUS_LABELS } from "@/lib/utils";

type Job = {
  id: string;
  title: string;
  client: string;
  jobType: string;
  date: string;
  location?: string;
  value: number;
  status: string;
};

type MonthPoint = { month: string; income: number; expenses: number };

type DashboardData = {
  jobs: Job[];
  income: number;
  expenses: number;
  profit: number;
  monthlyHistory: MonthPoint[];
};

const MONTH_NAMES = [
  "January","February","March","April","May","June",
  "July","August","September","October","November","December",
];

export default function DashboardPage() {
  const now = new Date();
  const [month, setMonth] = useState(now.getMonth());
  const [year, setYear] = useState(now.getFullYear());
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    setLoading(true);
    const res = await fetch(`/api/dashboard?month=${month}&year=${year}`);
    const json = await res.json();
    setData(json);
    setLoading(false);
  }, [month, year]);

  useEffect(() => { load(); }, [load]);

  function prevMonth() {
    if (month === 0) { setMonth(11); setYear((y) => y - 1); }
    else setMonth((m) => m - 1);
  }
  function nextMonth() {
    if (month === 11) { setMonth(0); setYear((y) => y + 1); }
    else setMonth((m) => m + 1);
  }

  return (
    <div className="max-w-6xl mx-auto space-y-8">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Dashboard</h2>
          <p className="text-gray-500 text-sm mt-0.5">Overview for {MONTH_NAMES[month]} {year}</p>
        </div>
        <div className="flex items-center gap-2">
          <button onClick={prevMonth} className="p-2 rounded-lg hover:bg-gray-200 transition-colors">
            <ChevronLeft size={18} />
          </button>
          <span className="font-medium text-sm w-32 text-center">
            {MONTH_NAMES[month]} {year}
          </span>
          <button onClick={nextMonth} className="p-2 rounded-lg hover:bg-gray-200 transition-colors">
            <ChevronRight size={18} />
          </button>
        </div>
      </div>

      <div className="grid grid-cols-3 gap-5">
        <StatCard
          label="Income"
          value={loading ? "—" : formatCurrency(data?.income ?? 0)}
          icon={<TrendingUp size={20} className="text-green-600" />}
          color="bg-green-50 border-green-200"
        />
        <StatCard
          label="Expenses"
          value={loading ? "—" : formatCurrency(data?.expenses ?? 0)}
          icon={<TrendingDown size={20} className="text-red-500" />}
          color="bg-red-50 border-red-200"
        />
        <StatCard
          label="Net Profit"
          value={loading ? "—" : formatCurrency(data?.profit ?? 0)}
          icon={<DollarSign size={20} className="text-indigo-600" />}
          color={(data?.profit ?? 0) >= 0 ? "bg-indigo-50 border-indigo-200" : "bg-orange-50 border-orange-200"}
        />
      </div>

      <div className="grid grid-cols-2 gap-6">
        <div className="bg-white rounded-2xl border border-gray-200 p-6 shadow-sm">
          <h3 className="font-semibold text-gray-800 mb-4">6-Month Overview</h3>
          {loading ? (
            <div className="h-52 flex items-center justify-center text-gray-400 text-sm">Loading…</div>
          ) : (
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={data?.monthlyHistory ?? []} margin={{ top: 0, right: 8, left: -10, bottom: 0 }}>
                <XAxis dataKey="month" tick={{ fontSize: 12 }} />
                <YAxis tick={{ fontSize: 11 }} tickFormatter={(v) => `$${(v / 1000).toFixed(0)}k`} />
                <Tooltip formatter={(v) => formatCurrency(Number(v))} />
                <Legend />
                <Bar dataKey="income" name="Income" fill="#6366f1" radius={[4, 4, 0, 0]} />
                <Bar dataKey="expenses" name="Expenses" fill="#f87171" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>

        <div className="bg-white rounded-2xl border border-gray-200 p-6 shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-semibold text-gray-800">Jobs This Month</h3>
            <span className="text-xs font-medium bg-indigo-100 text-indigo-700 px-2 py-0.5 rounded-full">
              {data?.jobs.length ?? 0} booked
            </span>
          </div>
          {loading ? (
            <div className="text-gray-400 text-sm">Loading…</div>
          ) : !data?.jobs.length ? (
            <div className="flex flex-col items-center justify-center py-8 text-center">
              <CalendarDays size={32} className="text-gray-300 mb-2" />
              <p className="text-gray-400 text-sm">No jobs this month</p>
            </div>
          ) : (
            <ul className="space-y-3 overflow-y-auto max-h-52">
              {data.jobs.map((job) => (
                <li key={job.id} className="flex items-start gap-3">
                  <div className="mt-0.5 p-1.5 rounded-lg bg-gray-100">
                    {job.jobType === "wedding" ? (
                      <Camera size={14} className="text-pink-500" />
                    ) : (
                      <Hammer size={14} className="text-amber-600" />
                    )}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium truncate">{job.client}</p>
                    <p className="text-xs text-gray-500 truncate">{job.title}</p>
                    <p className="text-xs text-gray-400">{formatDate(job.date)}</p>
                  </div>
                  <span className={`text-xs px-2 py-0.5 rounded-full font-medium shrink-0 ${JOB_STATUS_COLORS[job.status]}`}>
                    {JOB_STATUS_LABELS[job.status]}
                  </span>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>
    </div>
  );
}

function StatCard({
  label,
  value,
  icon,
  color,
}: {
  label: string;
  value: string;
  icon: React.ReactNode;
  color: string;
}) {
  return (
    <div className={`rounded-2xl border p-5 shadow-sm ${color}`}>
      <div className="flex items-center justify-between mb-3">
        <span className="text-sm font-medium text-gray-600">{label}</span>
        {icon}
      </div>
      <p className="text-2xl font-bold text-gray-900">{value}</p>
    </div>
  );
}
