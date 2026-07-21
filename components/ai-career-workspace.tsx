"use client";

import { FormEvent, useMemo, useState } from "react";
import { LoaderCircle, Sparkles } from "lucide-react";
import { AIResult } from "@/components/ai-result";
import { AITool, AI_TOOL_LABELS, runCareerAI } from "@/lib/ai-career";

const tools = Object.keys(AI_TOOL_LABELS) as AITool[];

export function AICareerWorkspace({ initialTool = "cover-letter" }: { initialTool?: AITool }) {
  const [tool, setTool] = useState<AITool>(initialTool);
  const [targetRole, setTargetRole] = useState("");
  const [companyName, setCompanyName] = useState("");
  const [jobDescription, setJobDescription] = useState("");
  const [currentSummary, setCurrentSummary] = useState("");
  const [jobTitle, setJobTitle] = useState("");
  const [currentDescription, setCurrentDescription] = useState("");
  const [timeframeMonths, setTimeframeMonths] = useState(12);
  const [tone, setTone] = useState("professional");
  const [interviewType, setInterviewType] = useState("general");
  const [result, setResult] = useState<unknown>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const description = useMemo(() => {
    const descriptions: Record<AITool, string> = {
      roadmap: "Create a practical, staged plan for reaching your target role.",
      "skills-gap": "Compare your profile with a target role and prioritise development areas.",
      "interview-prep": "Generate likely questions, answer frameworks and a preparation checklist.",
      "cover-letter": "Create a tailored and truthful cover letter using your saved career profile.",
      "improve-summary": "Rewrite your professional summary for clarity, impact and ATS alignment.",
      "improve-experience": "Strengthen a work-experience description without inventing achievements.",
      "job-match": "Measure alignment between your profile and a job description.",
    };
    return descriptions[tool];
  }, [tool]);

  function payload() {
    switch (tool) {
      case "roadmap":
        return { target_role: targetRole, timeframe_months: timeframeMonths, country: "South Africa" };
      case "skills-gap":
        return { target_role: targetRole, job_description: jobDescription };
      case "interview-prep":
        return { target_role: targetRole, company_name: companyName, job_description: jobDescription, interview_type: interviewType };
      case "cover-letter":
        return { target_role: targetRole, company_name: companyName, job_description: jobDescription, tone };
      case "improve-summary":
        return { target_role: targetRole, current_summary: currentSummary, tone };
      case "improve-experience":
        return { job_title: jobTitle, company: companyName, current_description: currentDescription, target_role: targetRole };
      case "job-match":
        return { job_description: jobDescription };
    }
  }

  async function submit(event: FormEvent) {
    event.preventDefault();
    setLoading(true);
    setError("");
    setResult(null);
    try {
      setResult(await runCareerAI(tool, payload()));
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "The AI request failed.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <>
      <header className="page-header builder-header">
        <div>
          <span className="eyebrow">Powered by OpenAI</span>
          <h1>AI Career Engine</h1>
          <p className="muted">{description}</p>
        </div>
        <div className="builder-status"><span>Model</span><strong style={{ fontSize: 18 }}>GPT-5.4 mini</strong></div>
      </header>

      <div className="tabs">
        {tools.map((item) => (
          <button key={item} type="button" className={`tab ${tool === item ? "tab-active" : ""}`} onClick={() => { setTool(item); setResult(null); setError(""); }}>
            {AI_TOOL_LABELS[item]}
          </button>
        ))}
      </div>

      <div className="two-column ai-workspace">
        <form className="card form" onSubmit={submit}>
          {tool !== "job-match" && tool !== "improve-experience" && (
            <div className="field"><label>Target role</label><input className="input" value={targetRole} onChange={(e) => setTargetRole(e.target.value)} required={tool !== "improve-summary"} placeholder="e.g. Supply Chain Coordinator" /></div>
          )}
          {tool === "improve-experience" && (
            <div className="field"><label>Job title</label><input className="input" value={jobTitle} onChange={(e) => setJobTitle(e.target.value)} required /></div>
          )}
          {(tool === "cover-letter" || tool === "interview-prep" || tool === "improve-experience") && (
            <div className="field"><label>Company name</label><input className="input" value={companyName} onChange={(e) => setCompanyName(e.target.value)} required={tool === "cover-letter"} /></div>
          )}
          {(tool === "cover-letter" || tool === "interview-prep" || tool === "skills-gap" || tool === "job-match") && (
            <div className="field"><label>Job description</label><textarea className="input" value={jobDescription} onChange={(e) => setJobDescription(e.target.value)} required={tool === "job-match"} placeholder="Paste the vacancy description here." /></div>
          )}
          {tool === "improve-summary" && (
            <div className="field"><label>Current professional summary</label><textarea className="input" value={currentSummary} onChange={(e) => setCurrentSummary(e.target.value)} placeholder="Leave blank to generate from your saved profile." /></div>
          )}
          {tool === "improve-experience" && (
            <>
              <div className="field"><label>Current description</label><textarea className="input" value={currentDescription} onChange={(e) => setCurrentDescription(e.target.value)} required /></div>
              <div className="field"><label>Target role</label><input className="input" value={targetRole} onChange={(e) => setTargetRole(e.target.value)} /></div>
            </>
          )}
          {tool === "roadmap" && (
            <div className="field"><label>Timeframe (months)</label><input className="input" type="number" min={1} max={60} value={timeframeMonths} onChange={(e) => setTimeframeMonths(Number(e.target.value))} /></div>
          )}
          {(tool === "cover-letter" || tool === "improve-summary") && (
            <div className="field"><label>Tone</label><select className="input" value={tone} onChange={(e) => setTone(e.target.value)}><option value="professional">Professional</option><option value="confident">Confident</option><option value="warm">Warm</option><option value="concise">Concise</option></select></div>
          )}
          {tool === "interview-prep" && (
            <div className="field"><label>Interview type</label><select className="input" value={interviewType} onChange={(e) => setInterviewType(e.target.value)}><option value="general">General</option><option value="behavioural">Behavioural</option><option value="technical">Technical</option><option value="panel">Panel</option></select></div>
          )}
          {error && <div className="error">{error}</div>}
          <button className="button button-primary" disabled={loading}>{loading ? <><LoaderCircle className="spin-icon" size={18} /> Generating…</> : <><Sparkles size={18} /> Generate with AI</>}</button>
        </form>

        <section className="card ai-result-card">
          <div className="ai-result-heading"><div><span className="eyebrow">Generated output</span><h2>{AI_TOOL_LABELS[tool]}</h2></div></div>
          {loading ? <div className="loading"><span className="spinner" />Creating a personalised result from your saved career profile…</div> : <AIResult result={result} />}
        </section>
      </div>
    </>
  );
}
