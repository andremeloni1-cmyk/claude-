"use client";
import { useEffect, useState, useCallback } from "react";
import {
  Plus,
  X,
  Camera,
  Hammer,
  ChevronLeft,
  ChevronRight,
  MapPin,
  Pencil,
  Trash2,
} from "lucide-react";
import {
  formatCurrency,
  formatDate,
  JOB_STATUS_COLORS,
  JOB_STATUS_LABELS,
  JOB_TYPE_LABELS,
} from "@/lib/utils";

type Job = {
  id: string;
  title: string;
  client: string;
  jobType: string;
  date: string;
  location?: string;
  value: number;
  depositPaid: number;
  status: string;
  notes?: string;
};

const EMPTY: Omit<Job, "id"> = {
  title: "",
  client: "",
  jobType: "wedding",
  date: new Date().toISOString().slice(0, 10),
  location: "",
  value: 0,
  depositPaid: 0,
  status: "confirmed",
  notes: "",
};

const MONTH_NAMES = [
  "January","February","March","April","May","June",
  "July","August","September","October","November","December",
];

export default function JobsPage() {
  const now = new Date();
  const [month, setMonth] = useState(now.getMonth());
  const [year, setYear] = useState(now.getFullYear());
  const [jobs, setJobs] = useState<Job[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [editing, setEditing] = useState<Job | null>(null);
  const [form, setForm] = useState(EMPTY);
  const [saving, setSaving] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    const res = await fetch(`/api/jobs?month=${month}&year=${year}`);
    setJobs(await res.json());
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

  function openNew() {
    setEditing(null);
    setForm(EMPTY);
    setShowForm(true);
  }

  function openEdit(job: Job) {
    setEditing(job);
    setForm({
      title: job.title,
      client: job.client,
      jobType: job.jobType,
      date: job.date.slice(0, 10),
      location: job.location ?? "",
      value: job.value,
      depositPaid: job.depositPaid,
      status: job.status,
      notes: job.notes ?? "",
    });
    setShowForm(true);
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    if (editing) {
      await fetch(`/api/jobs/${editing.id}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(form),
      });
    } else {
      await fetch("/api/jobs", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(form),
      });
    }
    setSaving(false);
    setShowForm(false);
    load();
  }

  async function handleDelete(id: string) {
    if (!confirm("Delete this job?")) return;
    await fetch(`/api/jobs/${id}`, { method: "DELETE" });
    load();
  }

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Jobs</h2>
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
            onClick={openNew}
            className="flex items-center gap-2 bg-indigo-600 text-white px-4 py-2 rounded-xl text-sm font-medium hover:bg-indigo-700 transition-colors"
          >
            <Plus size={16} /> Add Job
          </button>
        </div>
      </div>

      {/* Jobs list */}
      {loading ? (
        <div className="text-gray-400 text-sm py-12 text-center">Loading…</div>
      ) : !jobs.length ? (
        <div className="bg-white rounded-2xl border border-gray-200 p-12 text-center shadow-sm">
          <p className="text-gray-400">No jobs for {MONTH_NAMES[month]}. Add one above.</p>
        </div>
      ) : (
        <div className="space-y-3">
          {jobs.map((job) => (
            <div key={job.id} className="bg-white rounded-2xl border border-gray-200 p-5 shadow-sm flex gap-4 items-start">
              <div className="p-2.5 rounded-xl bg-gray-100 shrink-0">
                {job.jobType === "wedding" ? (
                  <Camera size={20} className="text-pink-500" />
                ) : (
                  <Hammer size={20} className="text-amber-600" />
                )}
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-start justify-between gap-2 flex-wrap">
                  <div>
                    <h3 className="font-semibold text-gray-900">{job.client}</h3>
                    <p className="text-sm text-gray-500">{job.title}</p>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className={`text-xs px-2.5 py-0.5 rounded-full font-medium ${JOB_STATUS_COLORS[job.status]}`}>
                      {JOB_STATUS_LABELS[job.status]}
                    </span>
                    <span className="text-xs px-2.5 py-0.5 rounded-full font-medium bg-gray-100 text-gray-600">
                      {JOB_TYPE_LABELS[job.jobType]}
                    </span>
                  </div>
                </div>
                <div className="flex flex-wrap items-center gap-x-4 gap-y-1 mt-2 text-sm text-gray-500">
                  <span>{formatDate(job.date)}</span>
                  {job.location && (
                    <span className="flex items-center gap-1">
                      <MapPin size={13} /> {job.location}
                    </span>
                  )}
                  <span className="font-medium text-gray-700">{formatCurrency(job.value)}</span>
                  {job.depositPaid > 0 && (
                    <span className="text-green-600 text-xs">Deposit: {formatCurrency(job.depositPaid)}</span>
                  )}
                </div>
                {job.notes && <p className="mt-2 text-xs text-gray-400 italic">{job.notes}</p>}
              </div>
              <div className="flex gap-1 shrink-0">
                <button onClick={() => openEdit(job)} className="p-2 rounded-lg hover:bg-gray-100 text-gray-400 hover:text-gray-700 transition-colors">
                  <Pencil size={15} />
                </button>
                <button onClick={() => handleDelete(job.id)} className="p-2 rounded-lg hover:bg-red-50 text-gray-400 hover:text-red-500 transition-colors">
                  <Trash2 size={15} />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Modal */}
      {showForm && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
          <div className="bg-white rounded-2xl shadow-xl w-full max-w-lg max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between p-6 border-b">
              <h3 className="font-semibold text-lg">{editing ? "Edit Job" : "New Job"}</h3>
              <button onClick={() => setShowForm(false)} className="p-1 hover:bg-gray-100 rounded-lg">
                <X size={18} />
              </button>
            </div>
            <form onSubmit={handleSubmit} className="p-6 space-y-4">
              <Field label="Client Name">
                <input required value={form.client} onChange={(e) => setForm({ ...form, client: e.target.value })} placeholder="e.g. Smith Wedding" className={input} />
              </Field>
              <Field label="Job Title / Description">
                <input required value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} placeholder="e.g. Full day wedding photography" className={input} />
              </Field>
              <div className="grid grid-cols-2 gap-4">
                <Field label="Type">
                  <select value={form.jobType} onChange={(e) => setForm({ ...form, jobType: e.target.value })} className={input}>
                    <option value="wedding">Wedding Photography</option>
                    <option value="joinery">Joinery / Kitchen</option>
                  </select>
                </Field>
                <Field label="Status">
                  <select value={form.status} onChange={(e) => setForm({ ...form, status: e.target.value })} className={input}>
                    <option value="enquiry">Enquiry</option>
                    <option value="confirmed">Confirmed</option>
                    <option value="completed">Completed</option>
                    <option value="cancelled">Cancelled</option>
                  </select>
                </Field>
              </div>
              <Field label="Date">
                <input required type="date" value={form.date} onChange={(e) => setForm({ ...form, date: e.target.value })} className={input} />
              </Field>
              <Field label="Location">
                <input value={form.location} onChange={(e) => setForm({ ...form, location: e.target.value })} placeholder="e.g. Sydney, NSW" className={input} />
              </Field>
              <div className="grid grid-cols-2 gap-4">
                <Field label="Job Value ($)">
                  <input type="number" min="0" step="0.01" value={form.value} onChange={(e) => setForm({ ...form, value: parseFloat(e.target.value) || 0 })} className={input} />
                </Field>
                <Field label="Deposit Paid ($)">
                  <input type="number" min="0" step="0.01" value={form.depositPaid} onChange={(e) => setForm({ ...form, depositPaid: parseFloat(e.target.value) || 0 })} className={input} />
                </Field>
              </div>
              <Field label="Notes">
                <textarea value={form.notes} onChange={(e) => setForm({ ...form, notes: e.target.value })} rows={3} placeholder="Optional notes…" className={input} />
              </Field>
              <div className="flex justify-end gap-3 pt-2">
                <button type="button" onClick={() => setShowForm(false)} className="px-4 py-2 rounded-xl border text-sm font-medium hover:bg-gray-50">Cancel</button>
                <button type="submit" disabled={saving} className="px-4 py-2 rounded-xl bg-indigo-600 text-white text-sm font-medium hover:bg-indigo-700 disabled:opacity-50">
                  {saving ? "Saving…" : editing ? "Save Changes" : "Add Job"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
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

const input = "w-full border border-gray-300 rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent";
