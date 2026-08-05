"use client";

import { useRouter } from 'next/navigation';
import { useState } from 'react';
import { apiRequest, setStoredToken } from '@/lib/api';

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');

  async function onSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError('');
    try {
      const data = await apiRequest<{ access_token: string; token_type: string }>('/login', {
        method: 'POST',
        body: JSON.stringify({ email, password }),
      });
      setStoredToken(data.access_token);
      router.push('/profile');
    } catch (err) {
      setError(err instanceof Error ? err.message : '登录失败');
    }
  }

  return (
    <main className="flex min-h-screen items-center justify-center p-6">
      <div className="w-full max-w-md rounded border bg-white p-6">
        <h1 className="text-2xl font-bold">登录 GrowthOS</h1>
        <form className="mt-4 space-y-3" onSubmit={onSubmit}>
          <input className="w-full rounded border px-3 py-2" placeholder="邮箱" value={email} onChange={(e) => setEmail(e.target.value)} />
          <input className="w-full rounded border px-3 py-2" placeholder="密码" type="password" value={password} onChange={(e) => setPassword(e.target.value)} />
          {error ? <div className="text-sm text-red-600">{error}</div> : null}
          <button className="w-full rounded bg-slate-900 px-4 py-2 text-white">登录</button>
        </form>
      </div>
    </main>
  );
}
