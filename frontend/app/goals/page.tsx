"use client";

import { useEffect, useState } from 'react';
import { apiRequest } from '@/lib/api';
import type { Goal } from '@/types';

export default function GoalsPage() {
  const [goals, setGoals] = useState<Goal[]>([]);
  const [form, setForm] = useState<Goal>({
    id: '',
    target_school: '',
    target_college: '',
    target_major: '',
    target_year: undefined,
    weekly_time: undefined,
    current_stage: '',
    remark: '',
  });
  const [message, setMessage] = useState('');

  useEffect(() => {
    async function load() {
      const data = await apiRequest<Goal[]>('/goals');
      setGoals(data);
    }
    load().catch(() => setMessage('无法加载目标'));
  }, []);

  async function submit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const data = await apiRequest<Goal>('/goals', {
      method: 'POST',
      body: JSON.stringify({
        target_school: form.target_school,
        target_college: form.target_college,
        target_major: form.target_major,
        target_year: form.target_year,
        weekly_time: form.weekly_time,
        current_stage: form.current_stage,
        remark: form.remark,
      }),
    });
    setGoals((current) => [...current, data]);
    setMessage('目标已创建');
  }

  return (
    <main className="p-6">
      <div className="grid gap-4 md:grid-cols-[1fr_1fr]">
        <section className="rounded border bg-white p-4">
          <h1 className="text-2xl font-bold">主线目标</h1>
          {message ? <div className="mt-3 text-green-600">{message}</div> : null}
          <form className="mt-4 grid gap-3" onSubmit={submit}>
            <input className="rounded border px-3 py-2" placeholder="目标学校" value={form.target_school || ''} onChange={(e) => setForm({ ...form, target_school: e.target.value })} />
            <input className="rounded border px-3 py-2" placeholder="目标学院" value={form.target_college || ''} onChange={(e) => setForm({ ...form, target_college: e.target.value })} />
            <input className="rounded border px-3 py-2" placeholder="目标专业" value={form.target_major || ''} onChange={(e) => setForm({ ...form, target_major: e.target.value })} />
            <input className="rounded border px-3 py-2" placeholder="目标年份" value={form.target_year ?? ''} onChange={(e) => setForm({ ...form, target_year: Number(e.target.value) })} />
            <input className="rounded border px-3 py-2" placeholder="每周投入时间" value={form.weekly_time ?? ''} onChange={(e) => setForm({ ...form, weekly_time: Number(e.target.value) })} />
            <input className="rounded border px-3 py-2" placeholder="当前阶段" value={form.current_stage || ''} onChange={(e) => setForm({ ...form, current_stage: e.target.value })} />
            <textarea className="rounded border px-3 py-2" placeholder="备注" value={form.remark || ''} onChange={(e) => setForm({ ...form, remark: e.target.value })} />
            <button className="rounded bg-slate-900 px-4 py-2 text-white">创建目标</button>
          </form>
        </section>
        <section className="rounded border bg-white p-4">
          <h2 className="text-xl font-semibold">当前目标</h2>
          {goals.length === 0 ? <div className="mt-3 text-gray-600">暂无目标，使用表单创建。</div> : goals.map((goal) => (
            <div key={goal.id} className="mt-3 rounded border p-3">
              <div>{goal.target_school || '未填写'} · {goal.target_major || '未填写'}</div>
              <div className="text-sm text-gray-600">学院：{goal.target_college || '未填写'}</div>
              <div className="text-sm text-gray-600">阶段：{goal.current_stage || '未填写'}</div>
            </div>
          ))}
        </section>
      </div>
    </main>
  );
}
