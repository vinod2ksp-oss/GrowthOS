"use client";

import { useCallback, useEffect, useState } from "react";
import { apiRequest } from "@/lib/api";
import type { Goal } from "@/types";

type Requirement = { id: string; title: string; category: string; verification_status: string; target_min: number | null; unit: string | null };
type Gap = { requirement_id: string; gap_level: string; current_status: string; confidence: number; missing_evidence: string[]; next_step: string };
type GoalAnalysis = { id: string; result_json: { requirements: Array<{ title: string; category: string }>; time_nodes: string[]; missing_information: string[]; relationship_explanation: string } };

export default function GoalAnalysisPage() {
  const [goals, setGoals] = useState<Goal[]>([]); const [goalId, setGoalId] = useState("");
  const [requirements, setRequirements] = useState<Requirement[]>([]); const [gaps, setGaps] = useState<Gap[]>([]);
  const [form, setForm] = useState({ category: "mathematical_foundation", title: "", metric_type: "ratio", target_min: "", unit: "", source_type: "user_input", verification_status: "confirmed" });
  const [suppliedText, setSuppliedText] = useState(""); const [analysis, setAnalysis] = useState<GoalAnalysis | null>(null);
  const [loading, setLoading] = useState(true); const [aiLoading, setAiLoading] = useState(false); const [error, setError] = useState(""); const [message, setMessage] = useState("");

  useEffect(() => { apiRequest<Goal[]>("/goals").then((data) => { setGoals(data); if (data[0]) setGoalId(data[0].id); }).catch((reason) => setError(reason.message)).finally(() => setLoading(false)); }, []);
  const load = useCallback(async (id: string) => { if (!id) return; try { setRequirements(await apiRequest<Requirement[]>(`/goals/${id}/requirements`)); setGaps(await apiRequest<Gap[]>(`/goals/${id}/gaps`)); } catch (reason) { setError(reason instanceof Error ? reason.message : "加载失败"); } }, []);
  useEffect(() => { if (goalId) load(goalId); }, [goalId, load]);

  async function add() { if (!goalId || !form.title) return; await apiRequest(`/goals/${goalId}/requirements`, { method: "POST", body: JSON.stringify({ ...form, target_min: form.target_min ? Number(form.target_min) : null }) }); await load(goalId); }
  async function organize() { if (!goalId || !suppliedText.trim()) return; setAiLoading(true); try { const response = await apiRequest<{ status: string; analysis: GoalAnalysis | null }>(`/goals/${goalId}/ai-organize`, { method: "POST", body: JSON.stringify({ supplied_text: suppliedText, source_type: "user_input" }) }); setAnalysis(response.analysis); setMessage(response.analysis ? "AI 已生成待确认草稿。" : "AI 当前不可用，原有要求编辑仍可正常使用。"); } catch (reason) { setMessage(reason instanceof Error ? reason.message : "AI 当前不可用"); } finally { setAiLoading(false); } }
  async function confirmAI() { if (!analysis || !goalId) return; await apiRequest(`/ai/analyses/${analysis.id}/confirm-goal`, { method: "POST" }); setAnalysis(null); setMessage("AI 草稿已由你确认并写入目标要求"); await load(goalId); }

  return <main className="mx-auto max-w-6xl p-6"><h1 className="text-2xl font-bold">目标要求与差距分析</h1>
    {loading ? <p>加载中...</p> : goals.length === 0 ? <p className="mt-3 text-gray-600">请先在目标页面创建目标。</p> : <>
      <select aria-label="选择目标" className="mt-4 border px-3 py-2" value={goalId} onChange={(event) => setGoalId(event.target.value)}>{goals.map((goal) => <option key={goal.id} value={goal.id}>{goal.target_major || goal.target_school || "未命名目标"}</option>)}</select>
      {error && <p className="text-red-600">{error}</p>}{message && <p className="mt-2 text-sm text-green-700">{message}</p>}
      <section className="mt-5 border-b pb-5"><textarea aria-label="用户提供的目标要求文本" className="min-h-28 w-full border p-3" placeholder="粘贴你持有的招生简章或目标要求文本" value={suppliedText} onChange={(event) => setSuppliedText(event.target.value)} /><button className="mt-2 border px-4 py-2" onClick={organize} disabled={aiLoading || !suppliedText.trim()}>{aiLoading ? "AI 整理中..." : "AI 整理要求"}</button>{analysis && <div className="mt-3 border-l-4 border-slate-500 p-3"><p>{analysis.result_json.relationship_explanation}</p>{analysis.result_json.requirements.map((item, index) => <p key={`${item.title}-${index}`}>{item.category}：{item.title}</p>)}<button className="mt-2 bg-slate-900 px-4 py-2 text-white" onClick={confirmAI}>确认 AI 整理结果</button></div>}</section>
      <section className="mt-5 grid gap-2 md:grid-cols-4"><select aria-label="要求类别" className="border px-2" value={form.category} onChange={(event) => setForm({ ...form, category: event.target.value })}><option value="mathematical_foundation">数学要求</option><option value="english">英语要求</option><option value="professional_knowledge">专业课要求</option><option value="programming_tools">编程要求</option><option value="academic_research">科研或复试要求</option><option value="other">其他要求</option></select><input className="border px-3 py-2" placeholder="要求标题" value={form.title} onChange={(event) => setForm({ ...form, title: event.target.value })} /><input className="border px-3 py-2" placeholder="目标最低值（可选）" type="number" value={form.target_min} onChange={(event) => setForm({ ...form, target_min: event.target.value })} /><input className="border px-3 py-2" placeholder="单位（可选）" value={form.unit} onChange={(event) => setForm({ ...form, unit: event.target.value })} /><button className="border bg-slate-900 px-4 py-2 text-white md:col-span-4" onClick={add}>添加已确认要求</button></section>
      <section className="mt-6"><h2 className="font-semibold">要求与差距</h2>{requirements.length === 0 ? <p className="text-gray-600">尚无目标要求。</p> : requirements.map((requirement) => { const gap = gaps.find((item) => item.requirement_id === requirement.id); return <article className="mt-3 border p-4" key={requirement.id}><b>{requirement.title}</b><p className="text-sm">{requirement.category} / {requirement.verification_status}</p>{gap && <><p>差距：{gap.gap_level} / 当前：{gap.current_status}</p><p>可信度：{Math.round(gap.confidence * 100)}%</p><p className="text-sm text-gray-600">{gap.missing_evidence.join("；") || gap.next_step}</p></>}</article>; })}</section>
    </>}
  </main>;
}
