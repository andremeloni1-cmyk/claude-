export function formatCurrency(amount: number) {
  return new Intl.NumberFormat("en-AU", {
    style: "currency",
    currency: "AUD",
  }).format(amount);
}

export function formatDate(date: Date | string) {
  return new Date(date).toLocaleDateString("en-AU", {
    weekday: "short",
    day: "numeric",
    month: "short",
    year: "numeric",
  });
}

export function formatShortDate(date: Date | string) {
  return new Date(date).toLocaleDateString("en-AU", {
    day: "numeric",
    month: "short",
  });
}

export function getMonthRange(year: number, month: number) {
  const start = new Date(year, month, 1);
  const end = new Date(year, month + 1, 0, 23, 59, 59, 999);
  return { start, end };
}

export const JOB_TYPE_LABELS: Record<string, string> = {
  wedding: "Wedding",
  joinery: "Joinery / Kitchen",
};

export const JOB_STATUS_LABELS: Record<string, string> = {
  enquiry: "Enquiry",
  confirmed: "Confirmed",
  completed: "Completed",
  cancelled: "Cancelled",
};

export const JOB_STATUS_COLORS: Record<string, string> = {
  enquiry: "bg-yellow-100 text-yellow-800",
  confirmed: "bg-blue-100 text-blue-800",
  completed: "bg-green-100 text-green-800",
  cancelled: "bg-red-100 text-red-800",
};

export const EXPENSE_CATEGORIES = [
  "Equipment",
  "Travel",
  "Materials",
  "Subcontractors",
  "Marketing",
  "Insurance",
  "Software / Subscriptions",
  "Office",
  "Vehicle",
  "Other",
];

export const INCOME_CATEGORIES = [
  "Wedding Photography",
  "Joinery / Kitchen",
  "Deposit",
  "Final Payment",
  "Other",
];
