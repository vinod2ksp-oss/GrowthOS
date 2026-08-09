"use client";
import { useCallback, useEffect, useState } from "react";
import { apiRequest } from "@/lib/api";
import { useModeLabels } from "@/lib/useModeLabels";
import type { Goal } from "@/types";
type Review = {
  id: string;
  period_start: string;
  period_end: string;
  effective_study_seconds: number;
  pause_seconds: number;
  completed_task_count: number;
  effective_task_count: number;
  partial_task_count: number;
  delayed_abandoned_count: number;
  new_item_count: number;
  progress_json: {
    progress_value: number | null;
    confidence: number;
    explanation: string;
    missing_information: string[];
  };
  summary_json: {
    major_progress: string[];
    risks: string[];
    unresolved_gaps: string[];
    next_week_suggestions: string[];
    confidence_change: number;
    used_resources?: string[];
    resources_linked_to_completed_tasks?: number;
    unused_favorite_resources?: string[];
  };
};
export default function Reviews() {
  const labels = useModeLabels();
  const [goals, setGoals] = useState<Goal[]>([]);
  const [goalId, setGoalId] = useState("");
  const [items, setItems] = useState<Review[]>([]);
  const [selected, setSelected] = useState<Review | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const load = useCallback(async () => {
    try {
      const [data, g] = await Promise.all([
        apiRequest<Review[]>("/weekly-reviews"),
        apiRequest<Goal[]>("/goals"),
      ]);
      setItems(data);
      setGoals(g);
      if (g[0]) setGoalId((current) => current || g[0].id);
    } catch (e) {
      setError(e instanceof Error ? e.message : "加载失败");
    } finally {
      setLoading(false);
    }
  }, []);
  useEffect(() => {
    load();
  }, [load]);
  async function generate() {
    const now = new Date();
    const monday = new Date(now);
    monday.setDate(now.getDate() - ((now.getDay() + 6) % 7));
    const review = await apiRequest<Review>("/weekly-reviews", {
      method: "POST",
      body: JSON.stringify({
        period_start: monday.toISOString().slice(0, 10),
        goal_id: goalId || null,
      }),
    });
    setSelected(review);
    await load();
  }
  async function adjust() {
    if (!selected) return;
    await apiRequest(`/weekly-reviews/${selected.id}/adjustments`, {
      method: "POST",
    });
    setError("路径调整建议已生成，请在路径调整页面确认。");
  }
  return (
    <main className="mx-auto max-w-6xl p-6">
      <h1 className="text-2xl font-bold">{labels.review}</h1>
      <p className="text-sm text-gray-600">
        数据来源：本周期真实任务、评测、学习会话、成果证据、属性变化和目标差距。
      </p>
      <div className="mt-4">
        <select
          aria-label="结算目标"
          className="border px-3 py-2"
          value={goalId}
          onChange={(e) => setGoalId(e.target.value)}
        >
          <option value="">未指定目标</option>
          {goals.map((g) => (
            <option key={g.id} value={g.id}>
              {g.target_major || g.target_school || "未命名目标"}
            </option>
          ))}
        </select>
        <button
          className="ml-2 border bg-slate-900 px-4 py-2 text-white"
          onClick={generate}
        >
          生成本周结算
        </button>
      </div>
      {loading ? (
        <p>加载中...</p>
      ) : error ? (
        <p className="mt-3 text-green-700">{error}</p>
      ) : items.length === 0 ? (
        <p className="mt-4 text-gray-600">尚无历史周结算。</p>
      ) : (
        <section className="mt-4">
          <h2 className="font-semibold">历史周结算</h2>
          {items.map((x) => (
            <button
              key={x.id}
              className="mt-2 block w-full border p-3 text-left"
              onClick={() => setSelected(x)}
            >
              {x.period_start} 至 {x.period_end} · 有效任务{" "}
              {x.effective_task_count}
            </button>
          ))}
        </section>
      )}
      {selected && (
        <section className="mt-5 border p-4">
          <h2 className="font-semibold">结算详情</h2>
          <p>
            有效学习：{Math.round(selected.effective_study_seconds / 60)} 分钟 /
            暂停：{Math.round(selected.pause_seconds / 60)} 分钟
          </p>
          <p>
            完成 {selected.completed_task_count}，有效{" "}
            {selected.effective_task_count}，部分完成{" "}
            {selected.partial_task_count}，延期/放弃{" "}
            {selected.delayed_abandoned_count}
          </p>
          <p>
            {labels.acquired}：{selected.new_item_count}；可信度变化：
            {selected.summary_json.confidence_change.toFixed(2)}
          </p>
          <p>
            {labels.progress}：
            {selected.progress_json.progress_value === null
              ? "信息不完整"
              : `${Math.round(selected.progress_json.progress_value * 100)}%`}
            （可信度 {Math.round(selected.progress_json.confidence * 100)}%）
          </p>
          <p className="text-sm text-gray-600">
            {selected.progress_json.explanation}
          </p>
          <p>
            风险：
            {selected.summary_json.risks.join("；") || "未识别到有依据的风险"}
          </p>
          <p>
            未解决差距：
            {selected.summary_json.unresolved_gaps.join("；") || "无"}
          </p>
          <p>
            下周建议：{selected.summary_json.next_week_suggestions.join("；")}
          </p>
          <p>本周使用资源：{selected.summary_json.used_resources?.join("、") || "无记录"}</p>
          <p>关联已完成任务：{selected.summary_json.resources_linked_to_completed_tasks || 0} 项</p>
          <p>收藏但未使用：{selected.summary_json.unused_favorite_resources?.join("、") || "无"}</p>
          <button className="mt-3 border px-4 py-2" onClick={adjust}>
            生成路径调整预览
          </button>
        </section>
      )}
    </main>
  );
}
