"use client";

import { useEffect, useState } from "react";
import { apiRequest } from "@/lib/api";
import type { Goal } from "@/types";

type Attribute = { attribute_key: string; current_status: string; range_min: number | null; range_max: number | null; confidence: number; evidence_count: number; explanation: string; gap_status: string; target_range: { min: number | null; max: number | null; unit: string | null } | null };
type Explanation = { explanation: string; low_confidence_reasons: string[]; needed_evidence: string[]; priority_improvement: string };

export default function AttributesPage() {
  const [items, setItems] = useState<Attribute[]>([]); const [goals, setGoals] = useState<Goal[]>([]); const [goalId, setGoalId] = useState("");
  const [goalsLoaded, setGoalsLoaded] = useState(false); const [loading, setLoading] = useState(true); const [error, setError] = useState("");
  const [explanations, setExplanations] = useState<Record<string, Explanation>>({}); const [aiMessage, setAiMessage] = useState("");
  useEffect(() => { apiRequest<Goal[]>("/goals").then((data) => { setGoals(data); setGoalId(data[0]?.id || ""); }).catch((reason) => setError(reason.message)).finally(() => setGoalsLoaded(true)); }, []);
  useEffect(() => { if (!goalsLoaded) return; setLoading(true); apiRequest<Attribute[]>(`/growth-attributes${goalId ? `?goal_id=${goalId}` : ""}`).then(setItems).catch((reason) => setError(reason.message)).finally(() => setLoading(false)); }, [goalId, goalsLoaded]);
  async function explain(key: string) { try { const response = await apiRequest<{ analysis: { result_json: Explanation } | null }>(`/growth-attributes/${key}/ai-explain`, { method: "POST" }); if (response.analysis) setExplanations((current) => ({ ...current, [key]: response.analysis!.result_json })); else setAiMessage("AI 当前不可用，规则诊断结果不受影响。"); } catch (reason) { setAiMessage(reason instanceof Error ? reason.message : "AI 当前不可用"); } }
  return <main className="mx-auto max-w-6xl p-6"><h1 className="text-2xl font-bold">能力面板</h1>{goals.length > 0 && <select aria-label="能力目标" className="mt-4 border px-3 py-2" value={goalId} onChange={(event) => setGoalId(event.target.value)}>{goals.map((goal) => <option key={goal.id} value={goal.id}>{goal.target_major || goal.target_school || "未命名目标"}</option>)}</select>}{aiMessage && <p className="mt-2 text-sm text-gray-600">{aiMessage}</p>}{loading ? <p>加载中...</p> : error ? <p className="text-red-600">{error}</p> : <div className="mt-4 grid gap-3 md:grid-cols-2">{items.map((item) => <article key={item.attribute_key} className="border p-4"><h2 className="font-semibold">{item.attribute_key}</h2><p>状态：{item.current_status}</p><p>评估区间：{item.range_min === null ? "证据不足" : `${(item.range_min * 100).toFixed(1)}% - ${((item.range_max || item.range_min) * 100).toFixed(1)}%`}</p><p>目标区间：{item.target_range?.min === null || !item.target_range ? "未确认" : `${item.target_range.min} - ${item.target_range.max ?? "未设上限"} ${item.target_range.unit || ""}`}</p><p>差距状态：{item.gap_status}</p><p>可信度：{Math.round(item.confidence * 100)}% / 证据 {item.evidence_count} 条</p><p className="mt-2 text-sm text-gray-600">{item.explanation}</p><button className="mt-3 border px-3 py-2" onClick={() => explain(item.attribute_key)}>AI 解读</button>{explanations[item.attribute_key] && <div className="mt-3 border-l-4 border-slate-500 pl-3 text-sm"><p>{explanations[item.attribute_key].explanation}</p><p>优先建议：{explanations[item.attribute_key].priority_improvement}</p><p>仍需证据：{explanations[item.attribute_key].needed_evidence.join("；") || "无"}</p></div>}</article>)}</div>}</main>;
}
