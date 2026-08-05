'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';

export default function AuthGate({ children }: { children: React.ReactNode }) {
  const router = useRouter();

  useEffect(() => {
    const token = window.localStorage.getItem('growthos_token');
    if (!token) {
      router.replace('/login');
    }
  }, [router]);

  return <>{children}</>;
}
