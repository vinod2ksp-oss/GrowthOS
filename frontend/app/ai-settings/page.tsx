"use client";

import { useEffect, useState } from "react";
import { apiRequest } from "@/lib/api";

type AISettings = {
  enabled: boolean;
  model: string | null;
  allow_material_analysis: boolean;
  description: string;
  privacy_notice: string;
};

export default function AISettingsPage() {
  const [settings, setSettings] = useState<AISettings | null>(null);
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    apiRequest<AISettings>("/ai/settings").then(setSettings).catch((reason) => setError(reason.message));
  }, []);

  async function updateConsent(allowed: boolean) {
    if (!settings) return;
    const previous = settings.allow_material_analysis;
    setSettings({ ...settings, allow_material_analysis: allowed });
    setSaving(true);
    try {
      await apiRequest("/ai/settings", { method: "PATCH", body: JSON.stringify({ allow_material_analysis: allowed }) });
    } catch (reason) {
      setSettings({ ...settings, allow_material_analysis: previous });
      setError(reason instanceof Error ? reason.message : "设置保存失败");
    } finally {
      setSaving(false);
    }
  }

  return <main className="mx-auto max-w-3xl p-6">
    <h1 className="text-2xl font-bold">AI 功能状态</h1>
    {error ? <p className="mt-4 text-red-600">{error}</p> : null}
    {!settings ? <p className="mt-4">加载中...</p> : <section className="mt-5 border p-5">
      <p>当前状态：{settings.enabled ? "可用" : "未配置，规则功能正常运行"}</p>
      <p>当前模型：{settings.model || "未配置"}</p>
      <p className="mt-3 text-sm text-gray-600">{settings.description}</p>
      <p className="mt-2 text-sm text-gray-600">{settings.privacy_notice}</p>
      <label className="mt-5 flex items-center gap-2"><input type="checkbox" checked={settings.allow_material_analysis} disabled={saving} onChange={(event) => updateConsent(event.target.checked)} />允许将我主动选择的材料提取文本发送给已配置的 AI 服务</label>
    </section>}
  </main>;
}
