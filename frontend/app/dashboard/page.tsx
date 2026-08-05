"use client";

import { useEffect, useState } from 'react';
import { apiRequest, clearStoredToken } from '@/lib/api';
import { useRouter } from 'next/navigation';

export default function DashboardPage() {
  const router = useRouter();
  const [user, setUser] = useState<{ id: string; email: string } | null>(null);
  const [error, setError] = useState('');

  useEffect(() => {
    async function load() {
      try {
        const data = await apiRequest<{ id: string; email: string }>('/me');
        setUser(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : '加载失败');
      }
    }
    load();
  }, []);

  async function logout() {
    clearStoredToken();
    router.replace('/login');
  }

  return (
    <main className="p-6">
      <div className="rounded border bg-white p-4">
        <h1 className="text-2xl font-bold">宿主面板</h1>
        {error ? <div className="mt-3 text-red-600">{error}</div> : null}
        {user ? <div className="mt-3">当前用户：{user.email}</div> : null}
        <button className="mt-4 rounded bg-slate-900 px-4 py-2 text-white" onClick={logout}>退出登录</button>
      </div>
    </main>
  );
}
