"use client";
import { useEffect, useState, useCallback } from "react";
import {
  PieChart,
  Pie,
  Cell,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";
import {
  Plus,
  X,
  TrendingUp,
  TrendingDown,
  DollarSign,
  ChevronLeft,
  ChevronRight,
  Trash2,
} from "lucide-react";
import {
  formatCurrency,
  formatShortDate,
  EXPENSE_CATEGORIES,
  INCOME_CATEGORIES,
} from "@/lib/utils";

type Transaction = {
  id: string;
  type: "income" | "expense";
  category: string;
  amount: number;
  date: string;
  description?: string;
  job?: { title: string; client: string } | null;
};

const EMPTY_TX = {
  type: "income" as "income" | "expense",
  category: INCOME_CATEGORIES[0],
  amount: 0,
  date: new Date().toISOString().slice(0, 10),
  description: "",
  jobId: "",
};

const MONTH_NAMES = [
  "January","February","March","April","May","June",
  "July","August","September","October","November","December",
];

const EXPENSE_COLORS = [
  "#6366f1","#f87171","#fb923c","#facc15","#4ade80","#34d399","#60a5fa","#a78bfa","#f472b6","#94a3b8",
];

export default function FinancesPage() {
  const now = new Date();
  const [month, setMonth] = useState(now.getMonth());
  const [year, setYear] = useState(now.getFullYear());
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState(EMPTY_TX);
  const [saving, setSaving] = useState(false);
  const [tab, setTab] = useState<"all" | "income" | "expense">("all");

  const load = useCallback(async () => {
    setLoading(true);
    const res = await fetch(`/api/transactions?month=${month}&year=${year}`);
    setTransactions(await res.json());
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

  const income = transactions.filter((t) => t.type === "income").reduce((s, t) => s + t.amount, 0);
  const expenses = transactions.filter((t) => t.type === "expense").reduce((s, t) => s + t.amount, 0);
  const profit = income - expenses;

  // expense breakdown by category
  const expenseByCategory = Object.entries(
    transactions
      .filter((t) => t.type === "expense")
      .reduce((acc, t) => {
        acc[t.category] = (acc[t.category] ?? 0) + t.amount;
        return acc;
      }, {} as Record<string, number>)
  ).map(([name, value]) => ({ name, value }));

  const filtered = transactions.filter((t) => tab === "all" || t.type === tab);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    await fetch("/api/transactions", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(form),
    });
    setSaving(false);
    setShowForm(false);
    load();
  }

  async function handleDelete(id: string) {
    if (!confirm("Delete this transaction?")) return;
    await fetch(`/api/transactions/${id}`, { method: "DELETE" });
    load();
  }

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Finances</h2>
          <p className="text-gray-500 text-sm mt-0.5">{MONTH_NAMES[month]} {year}</p>
        </div>
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1">
            <button onClick={prevMonth} className="p-2 rounded-lg hover:bg-gray-200 transition-colors">
              <ChevronLeft size={18} />
            </button>
            <span className="font-medium text-sm w-32 text-center">{MONTH_NAMES[month]} {year}</span>
            <button onClick={nextMonth} className="p-2 rounded-lg hover:bg-gray-200 transition-colors">
              <ChevronRight size={18} />
            </button>
          </div>
          <button
            onClick={() => { setForm(EMPTY_TX); setShowForm(true); }}
            className="flex items-center gap-2 bg-indigo-600 text-white px-4 py-2 rounded-xl text-sm font-medium hover:bg-indigo-700 transition-colors"
          >
            <Plus size={16} /> Add Entry
          </button>
        </div>
      </div>

      {/* Summary cards */}
      <div className="grid grid-cols-3 gap-5">
        <SummaryCard label="Income" value={formatCurrency(income)} icon={<TrendingUp size={18} className="text-green-600" />} color="bg-green-50 border-green-200" />
        <SummaryCard label="Expenses" value={formatCurrency(expenses)} icon={<TrendingDown size={18} className="text-red-500" />} color="bg-red-50 border-red-200" />
        <SummaryCard label="Net Profit" value={formatCurrency(profit)} icon={<DollarSign size={18} className="text-indigo-600" />} color={profit >= 0 ? "bg-indigo-50 border-indigo-200" : "bg-orange-50 border-orange-200"} />
      </div>

      <div className="grid grid-cols-3 gap-6">
        {/* Expense breakdown */}
        <div className="bg-white rounded-2xl border border-gray-200 p-5 shadow-sm">
          <h3 className="font-semibold text-gray-800 mb-3">Expense Breakdown</h3>
          {expenseByCategory.length === 0 ? (
            <div className="flex items-center justify-center h-40 text-gray-300 text-sm">No expenses</div>
          ) : (
            <ResponsiveContainer width="100%" height={200}>
              <PieChart>
                <Pie
                  data={expenseByCategory}
                  cx="50%"
                  cy="50%"
                  innerRadius={45}
                  outerRadius={75}
                  paddingAngle={3}
                  dataKey="value"
                >
                  {expenseByCategory.map((_, i) => (
                    <Cell key={i} fill={EXPENSE_COLORS[i % EXPENSE_COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip formatter={(v) => formatCurrency(Number(v))} />
                <Legend iconSize={10} wrapperStyle={{ fontSize: 11 }} />
              </PieChart>
            </ResponsiveContainer>
          )}
        </div>

        {/* Transaction list */}
        <div className="col-span-2 bg-white rounded-2xl border border-gray-200 shadow-sm overflow-hidden">
          <div className="flex items-center gap-1 p-4 border-b">
            {(["all", "income", "expense"] as const).map((t) => (
              <button
                key={t}
                onClick={() => setTab(t)}
                className={`px-3 py-1.5 rounded-lg text-sm font-medium capitalize transition-colors ${
                  tab === t ? "bg-indigo-600 text-white" : "text-gray-500 hover:bg-gray-100"
                }`}
              >
                {t}
              </button>
            ))}
          </div>
          {loading ? (
            <div className="p-8 text-center text-gray-400 text-sm">Loading…</div>
          ) : !filtered.length ? (
            <div className="p-8 text-center text-gray-400 text-sm">No transactions</div>
          ) : (
            <div className="overflow-y-auto max-h-[420px]">
              {filtered.map((tx) => (
                <div key={tx.id} className="flex items-center gap-3 px-4 py-3 border-b last:border-0 hover:bg-gray-50">
                  <div className={`w-2 h-8 rounded-full shrink-0 ${tx.type === "income" ? "bg-green-400" : "bg-red-400"}`} />
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium truncate">{tx.description || tx.category}</p>
                    <p className="text-xs text-gray-400">
                      {tx.category} · {formatShortDate(tx.date)}
                      {tx.job && ` · ${tx.job.client}`}
                    </p>
                  </div>
                  <p className={`text-sm font-semibold shrink-0 ${tx.type === "income" ? "text-green-600" : "text-red-500"}`}>
                    {tx.type === "income" ? "+" : "-"}{formatCurrency(tx.amount)}
                  </p>
                  <button onClick={() => handleDelete(tx.id)} className="p-1.5 rounded-lg hover:bg-red-50 text-gray-300 hover:text-red-500 transition-colors">
                    <Trash2 size={14} />
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Add transaction modal */}
      {showForm && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
          <div className="bg-white rounded-2xl shadow-xl w-full max-w-md">
            <div className="flex items-center justify-between p-6 border-b">
              <h3 className="font-semibold text-lg">Add Transaction</h3>
              <button onClick={() => setShowForm(false)} className="p-1 hover:bg-gray-100 rounded-lg">
                <X size={18} />
              </button>
            </div>
            <form onSubmit={handleSubmit} className="p-6 space-y-4">
              <Field label="Type">
                <div className="flex gap-2">
                  {(["income", "expense"] as const).map((t) => (
                    <button
                      key={t}
                      type="button"
                      onClick={() => setForm({ ...form, type: t, category: t === "income" ? INCOME_CATEGORIES[0] : EXPENSE_CATEGORIES[0] })}
                      className={`flex-1 py-2 rounded-xl text-sm font-medium border capitalize transition-colors ${
                        form.type === t
                          ? t === "income" ? "bg-green-500 text-white border-green-500" : "bg-red-500 text-white border-red-500"
                          : "border-gray-200 text-gray-600 hover:bg-gray-50"
                      }`}
                    >
                      {t}
                    </button>
                  ))}
                </div>
              </Field>
              <Field label="Category">
                <select
                  value={form.category}
                  onChange={(e) => setForm({ ...form, category: e.target.value })}
                  className={inputCls}
                >
                  {(form.type === "income" ? INCOME_CATEGORIES : EXPENSE_CATEGORIES).map((c) => (
                    <option key={c}>{c}</option>
                  ))}
                </select>
              </Field>
              <Field label="Amount ($)">
                <input
                  required
                  type="number"
                  min="0.01"
                  step="0.01"
                  value={form.amount || ""}
                  onChange={(e) => setForm({ ...form, amount: parseFloat(e.target.value) || 0 })}
                  className={inputCls}
                />
              </Field>
              <Field label="Date">
                <input
                  required
                  type="date"
                  value={form.date}
                  onChange={(e) => setForm({ ...form, date: e.target.value })}
                  className={inputCls}
                />
              </Field>
              <Field label="Description (optional)">
                <input
                  value={form.description}
                  onChange={(e) => setForm({ ...form, description: e.target.value })}
                  placeholder="e.g. Camera battery replacement"
                  className={inputCls}
                />
              </Field>
              <div className="flex justify-end gap-3 pt-2">
                <button type="button" onClick={() => setShowForm(false)} className="px-4 py-2 rounded-xl border text-sm font-medium hover:bg-gray-50">Cancel</button>
                <button type="submit" disabled={saving} className="px-4 py-2 rounded-xl bg-indigo-600 text-white text-sm font-medium hover:bg-indigo-700 disabled:opacity-50">
                  {saving ? "Saving…" : "Add"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

function SummaryCard({ label, value, icon, color }: { label: string; value: string; icon: React.ReactNode; color: string }) {
  return (
    <div className={`rounded-2xl border p-5 shadow-sm ${color}`}>
      <div className="flex items-center justify-between mb-2">
        <span className="text-sm font-medium text-gray-600">{label}</span>
        {icon}
      </div>
      <p className="text-2xl font-bold text-gray-900">{value}</p>
    </div>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div>
      <label className="block text-sm font-medium text-gray-700 mb-1">{label}</label>
      {children}
    </div>
  );
}

const inputCls = "w-full border border-gray-300 rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent";
