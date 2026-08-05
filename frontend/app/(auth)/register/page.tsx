"use client";

import { useRouter } from 'next/navigation';
import { useState } from 'react';
import { apiRequest } from '@/lib/api';

export default function RegisterPage() {
  const router = useRouter();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  async function onSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError('');
    setSuccess('');
    try {
      await apiRequest<{ id: string; email: string; is_active: boolean }>('/register', {
        method: 'POST',
        body: JSON.stringify({ email, password }),
      });
      setSuccess('注册成功，正在跳转登录页…');
      setTimeout(() => router.push('/login'), 700);
    } catch (err) {
      setError(err instanceof Error ? err.message : '注册失败');
    }
  }

  return (
    <main className="flex min-h-screen items-center justify-center p-6">
      <div className="w-full max-w-md rounded border bg-white p-6">
        <h1 className="text-2xl font-bold">注册 GrowthOS</h1>
        <form className="mt-4 space-y-3" onSubmit={onSubmit}>
          <input className="w-full rounded border px-3 py-2" placeholder="邮箱" value={email} onChange={(e) => setEmail(e.target.value)} />
          <input className="w-full rounded border px-3 py-2" placeholder="密码" type="password" value={password} onChange={(e) => setPassword(e.target.value)} />
          {error ? <div className="text-sm text-red-600">{error}</div> : null}
          {success ? <div className="text-sm text-green-600">{success}</div> : null}
          <button className="w-full rounded bg-slate-900 px-4 py-2 text-white">注册</button>
        </form>
      </div>
    </main>
  );
}
