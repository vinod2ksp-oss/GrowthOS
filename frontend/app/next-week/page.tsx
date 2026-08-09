"use client";
import { useEffect, useState } from "react";
import { apiRequest } from "@/lib/api";
import { useModeLabels } from "@/lib/useModeLabels";
import type { Goal } from "@/types";
type Review = { id: string };
type Item = {
  id: string;
  title: string;
  estimated_minutes: number;
  deadline: string;
  completion_standard: string;
  evidence_requirements: string;
  generation_reason: string;
  accepted: boolean;
};
type Plan = { id: string; status: string; items: Item[] };
export default function NextWeek() {
  const labels = useModeLabels();
  const [goals, setGoals] = useState<Goal[]>([]);
  const [goalId, setGoalId] = useState("");
  const [reviewId, setReviewId] = useState("");
  const [plan, setPlan] = useState<Plan | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  useEffect(() => {
    Promise.all([
      apiRequest<Goal[]>("/goals"),
      apiRequest<Review[]>("/weekly-reviews"),
    ])
      .then(([g, r]) => {
        setGoals(g);
        setGoalId(g[0]?.id || "");
        setReviewId(r[0]?.id || "");
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);
  async function generate() {
    const q = new URLSearchParams();
    if (goalId) q.set("goal_id", goalId);
    if (reviewId) q.set("review_id", reviewId);
    setPlan(await apiRequest<Plan>(`/weekly-plans?${q}`, { method: "POST" }));
  }
  async function update(item: Item, changes: Partial<Item>) {
    if (!plan) return;
    const value = await apiRequest<Item>(
      `/weekly-plans/${plan.id}/items/${item.id}`,
      { method: "PATCH", body: JSON.stringify(changes) },
    );
    setPlan({
      ...plan,
      items: plan.items.map((x) => (x.id === item.id ? value : x)),
    });
  }
  async function delay(item: Item) {
    if (!plan) return;
    const value = await apiRequest<Item>(
      `/weekly-plans/${plan.id}/items/${item.id}/delay`,
      { method: "POST" },
    );
    setPlan({
      ...plan,
      items: plan.items.map((x) => (x.id === item.id ? value : x)),
    });
  }
  async function remove(item: Item) {
    if (!plan) return;
    await apiRequest(`/weekly-plans/${plan.id}/items/${item.id}`, { method: "DELETE" });
    setPlan({ ...plan, items: plan.items.filter((x) => x.id !== item.id) });
  }
  async function regenerate() {
    if (!plan) return;
    setPlan(await apiRequest<Plan>(`/weekly-plans/${plan.id}/regenerate`, { method: "POST" }));
  }
  async function confirm() {
    if (!plan) return;
    setPlan(
      await apiRequest<Plan>(`/weekly-plans/${plan.id}/confirm`, {
        method: "POST",
        body: JSON.stringify({
          accepted_item_ids: plan.items
            .filter((x) => x.accepted)
            .map((x) => x.id),
        }),
      }),
    );
  }
  return (
    <main className="mx-auto max-w-5xl p-6">
      <h1 className="text-2xl font-bold">{labels.nextPlan}</h1>
      <p className="text-sm text-gray-600">
        数据来源：最近周结算、目标差距、未完成任务、路径建议和已确认时间预算。
      </p>
      {loading ? (
        <p>加载中...</p>
      ) : (
        <>
          <select
            aria-label="下周目标"
            className="mt-3 border px-3 py-2"
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
            预览下一周计划
          </button>
        </>
      )}
      {error && <p className="text-red-600">{error}</p>}
      {plan && (
        <section className="mt-4">
          {plan.items.length === 0 ? (
            <p className="text-gray-600">没有不重复且符合预算的候选任务。</p>
          ) : (
            plan.items.map((x) => (
              <article key={x.id} className="mt-3 border p-4">
                <input
                  className="w-full border px-2 py-1 font-semibold"
                  value={x.title}
                  onChange={(e) =>
                    setPlan({
                      ...plan,
                      items: plan.items.map((i) =>
                        i.id === x.id ? { ...i, title: e.target.value } : i,
                      ),
                    })
                  }
                  onBlur={() => update(x, { title: x.title })}
                />
                <label>
                  预计分钟{" "}
                  <input
                    className="border px-2"
                    type="number"
                    value={x.estimated_minutes}
                    onChange={(e) =>
                      update(x, { estimated_minutes: Number(e.target.value) })
                    }
                  />
                </label>
                <p>截止：{new Date(x.deadline).toLocaleDateString()}</p>
                <p>原因：{x.generation_reason}</p>
                <label>
                  <input
                    type="checkbox"
                    checked={x.accepted}
                    onChange={(e) => update(x, { accepted: e.target.checked })}
                  />{" "}
                  接受此任务
                </label>
                <button className="ml-3 border px-2" onClick={() => delay(x)}>
                  延后一周
                </button>
                <button className="ml-3 border px-2 text-red-700" onClick={() => remove(x)}>
                  删除
                </button>
              </article>
            ))
          )}
          {plan.status === "draft" && (
            <button className="mt-4 mr-2 border px-4 py-2" onClick={regenerate}>
              重新生成一次
            </button>
          )}
          {plan.status === "draft" && (
            <button
              className="mt-4 border bg-slate-900 px-4 py-2 text-white"
              onClick={confirm}
            >
              确认下周计划
            </button>
          )}
          {plan.status === "confirmed" && (
            <p className="text-green-700">下周计划已写入任务中心。</p>
          )}
        </section>
      )}
    </main>
  );
}
