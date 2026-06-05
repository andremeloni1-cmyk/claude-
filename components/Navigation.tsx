"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { LayoutDashboard, BriefcaseBusiness, TrendingUp } from "lucide-react";

const links = [
  { href: "/", label: "Dashboard", icon: LayoutDashboard },
  { href: "/jobs", label: "Jobs", icon: BriefcaseBusiness },
  { href: "/finances", label: "Finances", icon: TrendingUp },
];

export default function Navigation() {
  const pathname = usePathname();
  return (
    <aside className="fixed inset-y-0 left-0 w-56 bg-gray-900 flex flex-col z-20">
      <div className="px-5 py-6 border-b border-gray-700">
        <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider">Business Hub</p>
        <h1 className="text-white font-bold text-lg leading-tight mt-1">Andre Meloni</h1>
      </div>
      <nav className="flex-1 px-3 py-4 space-y-1">
        {links.map(({ href, label, icon: Icon }) => {
          const active = pathname === href;
          return (
            <Link
              key={href}
              href={href}
              className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                active
                  ? "bg-indigo-600 text-white"
                  : "text-gray-400 hover:bg-gray-800 hover:text-white"
              }`}
            >
              <Icon size={18} />
              {label}
            </Link>
          );
        })}
      </nav>
    </aside>
  );
}
