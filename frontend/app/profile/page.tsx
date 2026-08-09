"use client";

import { useEffect, useState } from 'react';
import { apiRequest } from '@/lib/api';
import type { Profile } from '@/types';

const emptyProfile: Profile = {
  id: '',
  nickname: '',
  learning_stage: '',
  grade_level: '',
  school: '',
  major: '',
  auxiliary_direction: '',
  weekly_study_hours: 0,
  display_mode: '',
  resource_budget: undefined,
};

export default function ProfilePage() {
  const [form, setForm] = useState<Profile>(emptyProfile);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');

  useEffect(() => {
    async function load() {
      try {
        const data = await apiRequest<Profile | null>('/profile');
        setForm(data || emptyProfile);
      } catch (err) {
        setError(err instanceof Error ? err.message : '加载失败');
      }
    }
    load();
  }, []);

  async function submit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    try {
      await apiRequest<Profile>('/profile', {
        method: 'PUT',
        body: JSON.stringify({
          nickname: form.nickname,
          learning_stage: form.learning_stage,
          grade_level: form.grade_level,
          school: form.school,
          major: form.major,
          auxiliary_direction: form.auxiliary_direction,
          weekly_study_hours: form.weekly_study_hours,
          display_mode: form.display_mode,
          resource_budget: form.resource_budget,
        }),
      });
      setMessage('档案已保存');
    } catch (err) {
      setError(err instanceof Error ? err.message : '保存失败');
    }
  }

  return (
    <main className="p-6">
      <div className="rounded border bg-white p-6">
        <h1 className="text-2xl font-bold">用户档案</h1>
        {message ? <div className="mt-3 text-green-600">{message}</div> : null}
        {error ? <div className="mt-3 text-red-600">{error}</div> : null}
        <form className="mt-4 grid gap-3 md:grid-cols-2" onSubmit={submit}>
          <input className="rounded border px-3 py-2" placeholder="昵称" value={form.nickname || ''} onChange={(e) => setForm({ ...form, nickname: e.target.value })} />
          <input className="rounded border px-3 py-2" placeholder="学段" value={form.learning_stage || ''} onChange={(e) => setForm({ ...form, learning_stage: e.target.value })} />
          <input className="rounded border px-3 py-2" placeholder="年级" value={form.grade_level || ''} onChange={(e) => setForm({ ...form, grade_level: e.target.value })} />
          <input className="rounded border px-3 py-2" placeholder="学校" value={form.school || ''} onChange={(e) => setForm({ ...form, school: e.target.value })} />
          <input className="rounded border px-3 py-2" placeholder="主修专业" value={form.major || ''} onChange={(e) => setForm({ ...form, major: e.target.value })} />
          <input className="rounded border px-3 py-2" placeholder="辅助方向" value={form.auxiliary_direction || ''} onChange={(e) => setForm({ ...form, auxiliary_direction: e.target.value })} />
          <input className="rounded border px-3 py-2" placeholder="每周可学习时间" value={form.weekly_study_hours ?? ''} onChange={(e) => setForm({ ...form, weekly_study_hours: Number(e.target.value) })} />
          <input className="rounded border px-3 py-2" placeholder="显示模式" value={form.display_mode || ''} onChange={(e) => setForm({ ...form, display_mode: e.target.value })} />
          <input className="rounded border px-3 py-2" type="number" min="0" placeholder="学习资源预算" value={form.resource_budget ?? ''} onChange={(e) => setForm({ ...form, resource_budget: e.target.value ? Number(e.target.value) : null })} />
          <button className="rounded bg-slate-900 px-4 py-2 text-white md:col-span-2">保存档案</button>
        </form>
      </div>
    </main>
  );
}
