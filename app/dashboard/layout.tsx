import { Sidebar } from "@/components/sidebar";

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  return <div className="app-shell"><Sidebar /><main className="app-content">{children}</main></div>;
}
