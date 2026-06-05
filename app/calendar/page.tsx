"use client";
import { useEffect, useState, useCallback } from "react";
import {
  ChevronLeft,
  ChevronRight,
  Camera,
  Hammer,
  X,
  MapPin,
  DollarSign,
} from "lucide-react";
import {
  formatCurrency,
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

const MONTH_NAMES = [
  "January","February","March","April","May","June",
  "July","August","September","October","November","December",
];
const DAY_NAMES = ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"];

export default function CalendarPage() {
  const now = new Date();
  const [month, setMonth] = useState(now.getMonth());
  const [year, setYear] = useState(now.getFullYear());
  const [jobs, setJobs] = useState<Job[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedDay, setSelectedDay] = useState<number | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    const res = await fetch(`/api/jobs?month=${month}&year=${year}`);
    setJobs(await res.json());
    setLoading(false);
  }, [month, year]);

  useEffect(() => { load(); }, [load]);
  useEffect(() => { setSelectedDay(null); }, [month, year]);

  function prevMonth() {
    if (month === 0) { setMonth(11); setYear((y) => y - 1); }
    else setMonth((m) => m - 1);
  }
  function nextMonth() {
    if (month === 11) { setMonth(0); setYear((y) => y + 1); }
    else setMonth((m) => m + 1);
  }
  function goToday() {
    setMonth(now.getMonth());
    setYear(now.getFullYear());
  }

  // Build calendar grid (Monday-first)
  const firstDay = new Date(year, month, 1);
  const daysInMonth = new Date(year, month + 1, 0).getDate();
  // getDay(): 0=Sun…6=Sat → convert to Mon-first: Mon=0…Sun=6
  const startOffset = (firstDay.getDay() + 6) % 7;
  const totalCells = Math.ceil((startOffset + daysInMonth) / 7) * 7;

  // Map: day number → jobs on that day
  const jobsByDay: Record<number, Job[]> = {};
  for (const job of jobs) {
    const d = new Date(job.date).getDate();
    if (!jobsByDay[d]) jobsByDay[d] = [];
    jobsByDay[d].push(job);
  }

  const selectedJobs = selectedDay ? (jobsByDay[selectedDay] ?? []) : [];
  const isToday = (day: number) =>
    day === now.getDate() && month === now.getMonth() && year === now.getFullYear();

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Calendar</h2>
          <p className="text-gray-500 text-sm mt-0.5">{MONTH_NAMES[month]} {year}</p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={goToday}
            className="px-3 py-1.5 text-sm font-medium border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
          >
            Today
          </button>
          <button onClick={prevMonth} className="p-2 rounded-lg hover:bg-gray-200 transition-colors">
            <ChevronLeft size={18} />
          </button>
          <span className="font-semibold text-sm w-36 text-center">
            {MONTH_NAMES[month]} {year}
          </span>
          <button onClick={nextMonth} className="p-2 rounded-lg hover:bg-gray-200 transition-colors">
            <ChevronRight size={18} />
          </button>
        </div>
      </div>

      <div className="flex gap-6">
        {/* Calendar grid */}
        <div className="flex-1 bg-white rounded-2xl border border-gray-200 shadow-sm overflow-hidden">
          {/* Day name headers */}
          <div className="grid grid-cols-7 border-b border-gray-100">
            {DAY_NAMES.map((d) => (
              <div key={d} className="py-3 text-center text-xs font-semibold text-gray-400 uppercase tracking-wider">
                {d}
              </div>
            ))}
          </div>

          {/* Day cells */}
          <div className="grid grid-cols-7">
            {Array.from({ length: totalCells }, (_, i) => {
              const day = i - startOffset + 1;
              const inMonth = day >= 1 && day <= daysInMonth;
              const dayJobs = inMonth ? (jobsByDay[day] ?? []) : [];
              const selected = selectedDay === day && inMonth;
              const today = inMonth && isToday(day);

              return (
                <button
                  key={i}
                  disabled={!inMonth}
                  onClick={() => inMonth && setSelectedDay(selected ? null : day)}
                  className={`min-h-[88px] p-2 border-b border-r border-gray-100 text-left align-top transition-colors last:border-r-0 focus:outline-none ${
                    !inMonth ? "bg-gray-50/50 cursor-default" :
                    selected ? "bg-indigo-50 border-indigo-200" :
                    "hover:bg-gray-50 cursor-pointer"
                  }`}
                >
                  {inMonth && (
                    <>
                      <span className={`inline-flex items-center justify-center w-7 h-7 rounded-full text-sm font-medium mb-1 ${
                        today
                          ? "bg-indigo-600 text-white"
                          : selected
                          ? "text-indigo-700 font-bold"
                          : "text-gray-700"
                      }`}>
                        {day}
                      </span>
                      <div className="space-y-0.5">
                        {dayJobs.slice(0, 2).map((job) => (
                          <JobPill key={job.id} job={job} />
                        ))}
                        {dayJobs.length > 2 && (
                          <p className="text-xs text-gray-400 pl-1">+{dayJobs.length - 2} more</p>
                        )}
                      </div>
                    </>
                  )}
                </button>
              );
            })}
          </div>
        </div>

        {/* Day detail panel */}
        <div className="w-72 shrink-0">
          {selectedDay ? (
            <div className="bg-white rounded-2xl border border-gray-200 shadow-sm overflow-hidden">
              <div className="flex items-center justify-between px-4 py-3 border-b border-gray-100">
                <h3 className="font-semibold text-gray-800">
                  {selectedDay} {MONTH_NAMES[month]}
                </h3>
                <button onClick={() => setSelectedDay(null)} className="p-1 hover:bg-gray-100 rounded-lg">
                  <X size={15} />
                </button>
              </div>
              {selectedJobs.length === 0 ? (
                <div className="px-4 py-8 text-center text-gray-400 text-sm">No jobs this day</div>
              ) : (
                <div className="divide-y divide-gray-100">
                  {selectedJobs.map((job) => (
                    <div key={job.id} className="p-4 space-y-2">
                      <div className="flex items-start gap-2">
                        <div className={`mt-0.5 p-1.5 rounded-lg shrink-0 ${job.jobType === "wedding" ? "bg-pink-50" : "bg-amber-50"}`}>
                          {job.jobType === "wedding"
                            ? <Camera size={14} className="text-pink-500" />
                            : <Hammer size={14} className="text-amber-600" />}
                        </div>
                        <div className="min-w-0">
                          <p className="text-sm font-semibold text-gray-900 leading-tight">{job.client}</p>
                          <p className="text-xs text-gray-500 mt-0.5">{job.title}</p>
                        </div>
                      </div>
                      <div className="flex flex-wrap gap-1.5">
                        <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${JOB_STATUS_COLORS[job.status]}`}>
                          {JOB_STATUS_LABELS[job.status]}
                        </span>
                        <span className="text-xs px-2 py-0.5 rounded-full font-medium bg-gray-100 text-gray-600">
                          {JOB_TYPE_LABELS[job.jobType]}
                        </span>
                      </div>
                      {job.location && (
                        <p className="flex items-center gap-1 text-xs text-gray-500">
                          <MapPin size={11} /> {job.location}
                        </p>
                      )}
                      <div className="flex items-center gap-1 text-xs text-gray-700 font-medium">
                        <DollarSign size={11} />
                        {formatCurrency(job.value)}
                        {job.depositPaid > 0 && (
                          <span className="text-green-600 font-normal ml-1">
                            ({formatCurrency(job.depositPaid)} deposit paid)
                          </span>
                        )}
                      </div>
                      {job.notes && (
                        <p className="text-xs text-gray-400 italic">{job.notes}</p>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          ) : (
            <div className="bg-white rounded-2xl border border-gray-200 shadow-sm p-6 text-center">
              <div className="text-gray-300 mb-2">
                <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" className="mx-auto">
                  <rect x="3" y="4" width="18" height="18" rx="2" />
                  <path d="M16 2v4M8 2v4M3 10h18" />
                </svg>
              </div>
              <p className="text-sm text-gray-400">Click a day to see jobs</p>
              {!loading && jobs.length > 0 && (
                <p className="text-xs text-gray-300 mt-1">{jobs.length} job{jobs.length !== 1 ? "s" : ""} this month</p>
              )}
            </div>
          )}

          {/* Legend */}
          <div className="mt-4 bg-white rounded-2xl border border-gray-200 shadow-sm p-4">
            <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3">Legend</p>
            <div className="space-y-2">
              <div className="flex items-center gap-2 text-sm text-gray-600">
                <span className="w-3 h-3 rounded-sm bg-pink-400 shrink-0" />
                Wedding Photography
              </div>
              <div className="flex items-center gap-2 text-sm text-gray-600">
                <span className="w-3 h-3 rounded-sm bg-amber-400 shrink-0" />
                Joinery / Kitchen
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function JobPill({ job }: { job: Job }) {
  const isWedding = job.jobType === "wedding";
  return (
    <div
      className={`flex items-center gap-1 px-1.5 py-0.5 rounded text-xs font-medium truncate w-full ${
        isWedding ? "bg-pink-100 text-pink-800" : "bg-amber-100 text-amber-800"
      }`}
    >
      {isWedding ? <Camera size={10} className="shrink-0" /> : <Hammer size={10} className="shrink-0" />}
      <span className="truncate">{job.client}</span>
    </div>
  );
}
