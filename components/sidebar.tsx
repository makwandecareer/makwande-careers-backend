"use client";

import Image from "next/image";
import Link from "next/link";
import { useRouter } from "next/navigation";

import {
  Award,
  BookOpen,
  BriefcaseBusiness,
  Building2,
  FileText,
  FolderKanban,
  Gauge,
  GraduationCap,
  Languages,
  LayoutTemplate,
  LogOut,
  MessageSquare,
  Palette,
  Search,
  Settings,
  ShieldCheck,
  Sparkles,
  UserRound,
  UsersRound,
  Wrench,
  Bell,
  BrainCircuit,
  BarChart3,
  ClipboardList,
  UserSearch,
  CalendarDays,
  Bot,
  CreditCard,
} from "lucide-react";

export function Sidebar() {
  const router = useRouter();

  async function logout() {
    await fetch("/api/auth/logout", {
      method: "POST",
    });

    router.push("/login");
    router.refresh();
  }

  return (
    <aside className="sidebar">
      <div className="sidebar-logo">
        <Image
          src="/makwande-careers-logo.jpeg"
          alt="Makwande Careers"
          width={44}
          height={44}
        />
        <strong>MAKWANDE CAREERS</strong>
      </div>

      {/* ===================================================== */}
      {/* OVERVIEW */}
      {/* ===================================================== */}

      <div className="side-section">Overview</div>

      <Link className="side-link" href="/dashboard">
        <Gauge size={18} />
        Dashboard
      </Link>

      <Link className="side-link" href="/dashboard/profile">
        <UserRound size={18} />
        Profile
      </Link>

      <Link className="side-link" href="/dashboard/notifications">
        <Bell size={18} />
        Notifications
      </Link>

      {/* ===================================================== */}
      {/* CAREER PROFILE */}
      {/* ===================================================== */}

      <div className="side-section">Career Profile</div>

      <Link className="side-link" href="/dashboard/education">
        <GraduationCap size={18} />
        Education
      </Link>

      <Link className="side-link" href="/dashboard/experience">
        <BriefcaseBusiness size={18} />
        Experience
      </Link>

      <Link className="side-link" href="/dashboard/skills">
        <Wrench size={18} />
        Skills
      </Link>

      <Link className="side-link" href="/dashboard/projects">
        <FolderKanban size={18} />
        Projects
      </Link>

      <Link className="side-link" href="/dashboard/certifications">
        <Award size={18} />
        Certifications
      </Link>

      <Link className="side-link" href="/dashboard/languages">
        <Languages size={18} />
        Languages
      </Link>

      <Link className="side-link" href="/dashboard/references">
        <UsersRound size={18} />
        References
      </Link>

      {/* ===================================================== */}
      {/* CV PLATFORM */}
      {/* ===================================================== */}

      <div className="side-section">CV Platform</div>

      <Link className="side-link" href="/dashboard/cvs">
        <BookOpen size={18} />
        My CVs
      </Link>

      <Link className="side-link" href="/dashboard/templates">
        <Palette size={18} />
        Templates
      </Link>

      <Link className="side-link" href="/dashboard/cv-studio">
        <LayoutTemplate size={18} />
        CV Studio
      </Link>

      <Link className="side-link" href="/dashboard/cv-builder">
        <FileText size={18} />
        AI CV Builder
      </Link>

      <Link className="side-link" href="/dashboard/ats">
        <BarChart3 size={18} />
        ATS Analysis
      </Link>

      {/* ===================================================== */}
      {/* AI */}
      {/* ===================================================== */}

      <div className="side-section">AI</div>

      <Link className="side-link" href="/dashboard/career">
        <Sparkles size={18} />
        Career Assistant
      </Link>

      <Link className="side-link" href="/dashboard/interview-ai">
        <BrainCircuit size={18} />
        Interview Coach
      </Link>

      <Link className="side-link" href="/dashboard/job-matcher">
        <Search size={18} />
        Job Matcher
      </Link>

      <Link className="side-link" href="/dashboard/cover-letter">
        <MessageSquare size={18} />
        Cover Letter AI
      </Link>

      <Link className="side-link" href="/dashboard/ai-engine">
        <Bot size={18} />
        AI Career Engine
      </Link>

      {/* ===================================================== */}
      {/* JOBS */}
      {/* ===================================================== */}

      <div className="side-section">Jobs</div>

      <Link className="side-link" href="/dashboard/jobs">
        <BriefcaseBusiness size={18} />
        Browse Jobs
      </Link>

      <Link className="side-link" href="/dashboard/saved-jobs">
        <BookOpen size={18} />
        Saved Jobs
      </Link>

      <Link className="side-link" href="/dashboard/applications">
        <ClipboardList size={18} />
        Applications
      </Link>

      <Link className="side-link" href="/dashboard/interviews">
        <CalendarDays size={18} />
        Interviews
      </Link>

      {/* ===================================================== */}
      {/* EMPLOYER */}
      {/* ===================================================== */}

      <div className="side-section">Employer</div>

      <Link className="side-link" href="/dashboard/employer">
        <Building2 size={18} />
        Employer Portal
      </Link>

      <Link className="side-link" href="/dashboard/candidates">
        <UserSearch size={18} />
        Candidate Search
      </Link>

      {/* ===================================================== */}
      {/* ACCOUNT */}
      {/* ===================================================== */}

      <div className="side-section">Account</div>

      <Link className="side-link" href="/dashboard/billing">
        <CreditCard size={18} />
        Billing & Plans
      </Link>

      <Link className="side-link" href="/dashboard/settings">
        <Settings size={18} />
        Settings
      </Link>

      <Link className="side-link" href="/dashboard/security">
        <ShieldCheck size={18} />
        Security
      </Link>

      <button
        className="side-link"
        onClick={logout}
        style={{
          width: "100%",
          border: 0,
          background: "transparent",
        }}
      >
        <LogOut size={18} />
        Sign out
      </button>
    </aside>
  );
}