'use client';

import { useEffect, useState } from 'react';
import { apiRequest } from '@/lib/api';
import type { User } from '@/types';

export default function ProtectedPage({ children }: { children: (user: User) => React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadUser() {
      try {
        const data = await apiRequest<User>('/me');
        setUser(data);
      } catch {
        setUser(null);
      } finally {
        setLoading(false);
      }
    }

    loadUser();
  }, []);

  if (loading) return <div className="p-6 text-sm text-gray-600">加载中...</div>;
  if (!user) return <div className="p-6 text-sm text-gray-600">请先登录。</div>;

  return <>{children(user)}</>;
}
