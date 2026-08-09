import type { Metadata } from 'next';
import Link from 'next/link';
import './globals.css';

export const metadata: Metadata = {
  title: 'GrowthOS 成长系统',
  description: '学习成长闭环',
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="zh-CN">
      <body>
        <header className="border-b bg-white px-6 py-3">
          <nav className="mx-auto flex max-w-6xl flex-wrap items-center gap-4 text-sm">
            <Link className="font-semibold" href="/dashboard">GrowthOS</Link>
            <Link href="/profile">档案</Link>
            <Link href="/goals">目标</Link>
            <Link href="/tasks">任务闭环</Link>
            <Link href="/materials">材料</Link>
            <Link href="/growth-evidence">证据</Link>
            <Link href="/attributes">能力</Link>
            <Link href="/goal-analysis">差距</Link>
            <Link href="/weekly-plan">七日计划</Link>
            <Link href="/inventory">背包</Link>
            <Link href="/attribute-changes">变化</Link>
            <Link href="/weekly-reviews">周结算</Link>
            <Link href="/path-adjustments">路径调整</Link>
            <Link href="/next-week">下周计划</Link>
            <Link href="/ai-settings">AI 设置</Link>
            <Link className="ml-auto" href="/login">登录</Link>
            <Link href="/register">注册</Link>
          </nav>
        </header>
        {children}
      </body>
    </html>
  );
}
