"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { apiRequest } from "@/lib/api";

type Resource = { id: string; name: string; description: string | null; product_type: string; provider_name: string | null; external_url: string | null; is_free: boolean; price: number | null; currency: string; copyright_status: string; applicable_stages: string[]; related_attributes: string[]; related_task_tags: string[]; is_sponsored: boolean; sponsorship_label: string | null };

export default function ResourceDetailPage() {
  const params = useParams<{ id: string }>(); const [item, setItem] = useState<Resource | null>(null); const [error, setError] = useState(""); const [confirming, setConfirming] = useState(false);
  useEffect(() => { apiRequest<Resource>(`/resources/${params.id}`).then(setItem).catch((reason) => setError(reason.message)); }, [params.id]);
  async function external() { if (!item?.external_url) return; const response = await apiRequest<{ external_url: string }>(`/resources/${item.id}/interactions`, { method: "POST", body: JSON.stringify({ interaction_type: "external_clicked" }) }); window.open(response.external_url, "_blank", "noopener,noreferrer"); setConfirming(false); }
  return <main className="mx-auto max-w-3xl p-6"><h1 className="text-2xl font-bold">资源详情</h1>{error ? <p className="text-red-600">{error}</p> : !item ? <p>加载中...</p> : <article className="mt-5 border p-5"><div className="flex justify-between"><h2 className="text-xl font-semibold">{item.name}</h2><span>{item.is_sponsored ? item.sponsorship_label || "推广" : "自然资源"}</span></div><p className="mt-2">{item.description || "未提供描述"}</p><p>提供方：{item.provider_name || "未提供"}</p><p>类型：{item.product_type}</p><p>价格：{item.is_free ? "免费" : `${item.price ?? "未提供"} ${item.currency}`}</p><p>版权状态：{item.copyright_status}</p><p>关联能力：{item.related_attributes.join("、") || "无"}</p><p>任务标签：{item.related_task_tags.join("、") || "无"}</p>{item.external_url && <button className="mt-4 border px-4 py-2" onClick={() => setConfirming(true)}>前往外部资源</button>}{confirming && <div className="mt-3 border-l-4 border-amber-500 p-3"><p>即将前往第三方页面。GrowthOS 不会将此次跳转视为已购买。</p><button className="mt-2 bg-slate-900 px-4 py-2 text-white" onClick={external}>确认前往</button><button className="ml-2 border px-4 py-2" onClick={() => setConfirming(false)}>取消</button></div>}</article>}</main>;
}
