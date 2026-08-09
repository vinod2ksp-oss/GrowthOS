"use client";
import { useCallback, useEffect, useState } from "react";
import { apiRequest } from "@/lib/api";
import { useModeLabels } from "@/lib/useModeLabels";
import type { Goal } from "@/types";
type Item = {
  id: string;
  name: string;
  type: string;
  acquired_at: string;
  source: string;
  attribute_keys: string[];
  verification_status: string;
  goal_relevance: string;
  task_id?: string;
  original_material?: string;
  expired: boolean;
  description?: string;
  user_note?: string;
  hidden: boolean;
};
export default function InventoryPage() {
  const labels = useModeLabels();
  const [items, setItems] = useState<Item[]>([]);
  const [selected, setSelected] = useState<Item | null>(null);
  const [type, setType] = useState("");
  const [ability, setAbility] = useState("");
  const [relevant, setRelevant] = useState(false);
  const [goals, setGoals] = useState<Goal[]>([]);
  const [goalId, setGoalId] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const load = useCallback(async () => {
    setLoading(true);
    const q = new URLSearchParams();
    if (type) q.set("evidence_type", type);
    if (ability) q.set("attribute_key", ability);
    if (relevant) q.set("relevant_only", "true");
    if (goalId) q.set("goal_id", goalId);
    try {
      setItems(await apiRequest<Item[]>(`/inventory?${q}`));
    } catch (e) {
      setError(e instanceof Error ? e.message : "加载失败");
    } finally {
      setLoading(false);
    }
  }, [type, ability, relevant, goalId]);
  useEffect(() => { apiRequest<Goal[]>("/goals").then((data) => { setGoals(data); setGoalId(data[0]?.id || ""); }).catch(() => undefined); }, []);
  useEffect(() => {
    load();
  }, [load]);
  async function save() {
    if (!selected) return;
    await apiRequest(`/inventory/${selected.id}`, {
      method: "PATCH",
      body: JSON.stringify({
        user_note: selected.user_note || null,
        hidden_from_current_goal: selected.hidden,
      }),
    });
    await load();
  }
  return (
    <main className="mx-auto max-w-6xl p-6">
      <h1 className="text-2xl font-bold">{labels.inventory}</h1>
      <p className="text-sm text-gray-600">
        数据来源：已确认 GrowthEvidence、原始材料和任务成果，未复制事实数据。
      </p>
      <div className="mt-4 flex flex-wrap gap-2">
        <select aria-label="背包目标" className="border px-3 py-2" value={goalId} onChange={(e)=>setGoalId(e.target.value)}><option value="">未选择目标</option>{goals.map((goal)=><option key={goal.id} value={goal.id}>{goal.target_major||goal.target_school||"未命名目标"}</option>)}</select>
        <input
          className="border px-3 py-2"
          placeholder="按类型筛选"
          value={type}
          onChange={(e) => setType(e.target.value)}
        />
        <input
          className="border px-3 py-2"
          placeholder="按能力筛选"
          value={ability}
          onChange={(e) => setAbility(e.target.value)}
        />
        <label>
          <input
            type="checkbox"
            checked={relevant}
            onChange={(e) => setRelevant(e.target.checked)}
          />{" "}
          仅当前目标相关
        </label>
      </div>
      {loading ? (
        <p>加载中...</p>
      ) : error ? (
        <p className="text-red-600">{error}</p>
      ) : items.length === 0 ? (
        <p className="mt-4 text-gray-600">暂无符合条件的真实证据。</p>
      ) : (
        <div className="mt-4 grid gap-4 md:grid-cols-2">
          {items.map((item) => (
            <button
              key={item.id}
              className="border p-4 text-left"
              onClick={() => setSelected(item)}
            >
              <b>{item.name}</b>
              <p>
                {item.type} / {item.verification_status}
              </p>
              <p className="text-sm">
                关联能力：{item.attribute_keys.join("、") || "尚未关联"} /{" "}
                {item.expired ? "已过期" : "有效"}
              </p>
            </button>
          ))}
        </div>
      )}
      {selected && (
        <section className="mt-5 border p-4">
          <h2 className="font-semibold">物品详情：{selected.name}</h2>
          <p>
            来源：{selected.source} / 任务：{selected.task_id || "无"} /
            原始材料：{selected.original_material || "无"}
          </p>
          <p>对目标作用：{selected.goal_relevance}</p>
          <p>{selected.description || "无补充描述"}</p>
          <textarea
            className="mt-3 w-full border p-2"
            placeholder="用户补充说明"
            value={selected.user_note || ""}
            onChange={(e) =>
              setSelected({ ...selected, user_note: e.target.value })
            }
          />
          <label className="block">
            <input
              type="checkbox"
              checked={selected.hidden}
              onChange={(e) =>
                setSelected({ ...selected, hidden: e.target.checked })
              }
            />{" "}
            隐藏非当前目标相关物品
          </label>
          <button
            className="mt-2 border bg-slate-900 px-4 py-2 text-white"
            onClick={save}
          >
            保存显示设置
          </button>
        </section>
      )}
    </main>
  );
}
