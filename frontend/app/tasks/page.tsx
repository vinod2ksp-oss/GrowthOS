"use client";

import { useEffect, useState } from 'react';
import { apiRequest } from '@/lib/api';
import type { Evaluation, Task, TimerSession } from '@/types';

type AIFeedback = { summary: string; strengths: string[]; incomplete_parts: string[]; suggestions: string[]; followup_questions: string[] };
type Followup = { id: string; question: string; answer: string | null; evaluation: string | null };

export default function TasksPage() {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [selected, setSelected] = useState<Task | null>(null);
  const [filter, setFilter] = useState('all');
  const [timer, setTimer] = useState<TimerSession | null>(null);
  const [evidenceFile, setEvidenceFile] = useState<File | null>(null);
  const [evidenceType, setEvidenceType] = useState('result');
  const [outcomeType, setOutcomeType] = useState('learning_verified');
  const [attributeKey, setAttributeKey] = useState('mathematical_foundation');
  const [evaluation, setEvaluation] = useState<Evaluation | null>(null);
  const [aiFeedback, setAiFeedback] = useState<AIFeedback | null>(null);
  const [followups, setFollowups] = useState<Followup[]>([]);
  const [message, setMessage] = useState('');
  const [form, setForm] = useState({
    title: '',
    task_type: 'main',
    parent_task_id: '',
    status: 'pending',
    deadline: '',
    estimated_minutes: 0,
    completion_standard: '',
    evidence_requirements: '',
  });

  async function load() {
    const data = await apiRequest<Task[]>('/tasks');
    setTasks(data);
  }

  useEffect(() => {
    load().catch(() => undefined);
  }, []);

  async function submit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const data = await apiRequest<Task>('/tasks', {
      method: 'POST',
      body: JSON.stringify({
        title: form.title,
        task_type: form.task_type,
        parent_task_id: form.parent_task_id || null,
        status: form.status,
        deadline: form.deadline || null,
        estimated_minutes: form.estimated_minutes,
        completion_standard: form.completion_standard,
        evidence_requirements: form.evidence_requirements,
      }),
    });
    setTasks((current) => [data, ...current]);
  }

  async function timerAction(action: 'start' | 'pause' | 'continue' | 'end') {
    if (!selected) return;
    const path = action === 'start' ? '/timers/start' : `/timers/${timer?.id}/${action}`;
    const data = await apiRequest<TimerSession>(path, { method: 'POST', body: action === 'start' ? JSON.stringify({ task_id: selected.id }) : undefined });
    setTimer(data);
    setMessage(`计时状态：${data.end_time ? '已结束' : data.is_running ? '进行中' : '已暂停'}`);
  }

  async function uploadEvidence() {
    if (!selected || !evidenceFile) return;
    const body = new FormData();
    body.set('task_id', selected.id);
    body.set('evidence_type', evidenceType);
    body.set('description', '任务成果');
    body.set('file', evidenceFile);
    await apiRequest('/evidences', { method: 'POST', body });
    setMessage('证据已上传');
  }

  async function completeTask() {
    if (!selected) return;
    const updated = await apiRequest<Task>(`/tasks/${selected.id}`, { method: 'PATCH', body: JSON.stringify({ status: 'done' }) });
    setSelected(updated); await load(); setMessage('任务已标记完成');
  }

  async function convertOutcome() {
    if (!selected) return;
    await apiRequest(`/tasks/${selected.id}/outcome`, { method: 'POST', body: JSON.stringify({ outcome_type: outcomeType, attribute_key: attributeKey || null }) });
    setMessage('任务成果已转化为背包物品');
  }

  async function evaluate(method: 'POST' | 'GET') {
    if (!selected) return;
    const suffix = method === 'POST' ? '' : '/latest';
    setEvaluation(await apiRequest<Evaluation>(`/tasks/${selected.id}/evaluations${suffix}`, { method }));
  }

  async function requestAIFeedback() {
    if (!selected) return;
    try {
      const response = await apiRequest<{ analysis: { result_json: AIFeedback } | null }>(`/tasks/${selected.id}/ai-feedback`, { method: 'POST' });
      if (response.analysis) setAiFeedback(response.analysis.result_json);
      else setMessage('AI 当前不可用，规则评测结果不受影响。');
    } catch (reason) {
      setMessage(reason instanceof Error ? reason.message : 'AI 当前不可用');
    }
  }

  async function requestFollowups() {
    if (!selected) return;
    const response = await apiRequest<{ status: string; items: Followup[] }>(`/tasks/${selected.id}/ai-followups`, { method: 'POST' });
    setFollowups(response.items);
    if (!response.items.length) setMessage('AI 当前不可用，追问未生成。');
  }

  const filtered = tasks.filter((task) => filter === 'all' || task.status === filter || task.task_type === filter);

  return (
    <main className="p-6">
      <div className="grid gap-4 lg:grid-cols-[1fr_1fr]">
        <section className="rounded border bg-white p-4">
          <h1 className="text-2xl font-bold">任务中心</h1>
          <div className="mt-3 flex gap-2">
            <select className="rounded border px-2 py-1" value={filter} onChange={(e) => setFilter(e.target.value)}>
              <option value="all">全部</option>
              <option value="pending">待处理</option>
              <option value="done">已完成</option>
              <option value="main">主线</option>
              <option value="subtask">子任务</option>
            </select>
          </div>
          <div className="mt-4 space-y-3">
            {filtered.length === 0 ? <div className="text-gray-600">暂无任务</div> : filtered.map((task) => (
              <button key={task.id} className="block w-full rounded border p-3 text-left" onClick={() => setSelected(task)}>
                <div className="font-semibold">{task.title}</div>
                <div className="text-sm text-gray-600">{task.task_type} / {task.status}</div>
              </button>
            ))}
          </div>
        </section>

        <section className="rounded border bg-white p-4">
          <h2 className="text-xl font-semibold">创建任务</h2>
          <form className="mt-4 grid gap-3" onSubmit={submit}>
            <input className="rounded border px-3 py-2" placeholder="任务标题" value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} />
            <select className="rounded border px-2 py-2" value={form.task_type} onChange={(e) => setForm({ ...form, task_type: e.target.value as Task['task_type'] })}>
              <option value="main">主线任务</option>
              <option value="support">辅助任务</option>
              <option value="challenge">可选挑战</option>
              <option value="subtask">自定义子任务</option>
            </select>
            <select aria-label="父任务" className="rounded border px-2 py-2" value={form.parent_task_id} onChange={(e) => setForm({ ...form, parent_task_id: e.target.value })}>
              <option value="">无父任务</option>
              {tasks.filter((task) => task.task_type !== 'subtask').map((task) => <option key={task.id} value={task.id}>{task.title}</option>)}
            </select>
            <input className="rounded border px-3 py-2" type="datetime-local" value={form.deadline} onChange={(e) => setForm({ ...form, deadline: e.target.value })} />
            <input className="rounded border px-3 py-2" placeholder="预计时长（分钟）" value={form.estimated_minutes} onChange={(e) => setForm({ ...form, estimated_minutes: Number(e.target.value) })} />
            <textarea className="rounded border px-3 py-2" placeholder="完成标准" value={form.completion_standard} onChange={(e) => setForm({ ...form, completion_standard: e.target.value })} />
            <textarea className="rounded border px-3 py-2" placeholder="证据要求" value={form.evidence_requirements} onChange={(e) => setForm({ ...form, evidence_requirements: e.target.value })} />
            <button className="rounded bg-slate-900 px-4 py-2 text-white">保存任务</button>
          </form>
        </section>
      </div>

      {selected ? (
        <section className="mt-4 rounded border bg-white p-4">
          <h3 className="text-lg font-semibold">任务详情</h3>
          <div className="mt-2">标题：{selected.title}</div>
          <div className="mt-1">类型：{selected.task_type}</div>
          <div className="mt-1">状态：{selected.status}</div>
          <div className="mt-1">截止时间：{selected.deadline || '未设定'}</div>
          <div className="mt-1">预计时长：{selected.estimated_minutes ?? '未设定'}</div>
          <div className="mt-1">完成标准：{selected.completion_standard || '未填写'}</div>
          <div className="mt-1">证据要求：{selected.evidence_requirements || '未填写'}</div>
          <div className="mt-4 flex flex-wrap gap-2">
            <button type="button" className="rounded border px-3 py-2" onClick={() => timerAction('start')} disabled={Boolean(timer)}>开始计时</button>
            <button type="button" className="rounded border px-3 py-2" onClick={() => timerAction('pause')} disabled={!timer?.is_running}>暂停</button>
            <button type="button" className="rounded border px-3 py-2" onClick={() => timerAction('continue')} disabled={!timer || timer.is_running || Boolean(timer.end_time)}>恢复</button>
            <button type="button" className="rounded border px-3 py-2" onClick={() => timerAction('end')} disabled={!timer || Boolean(timer.end_time)}>结束</button>
          </div>
          <div className="mt-4 flex flex-wrap items-center gap-2">
            <select aria-label="成果证据类型" className="rounded border px-2 py-2" value={evidenceType} onChange={e=>setEvidenceType(e.target.value)}><option value="result">成果证据</option><option value="test">测试证据</option></select>
            <input type="file" accept=".png,.jpg,.jpeg,.pdf,.doc,.docx,.ppt,.pptx,.txt" onChange={(event) => setEvidenceFile(event.target.files?.[0] || null)} />
            <button type="button" className="rounded border px-3 py-2" onClick={uploadEvidence} disabled={!evidenceFile}>上传证据</button>
            <button type="button" className="rounded border px-3 py-2" onClick={() => evaluate('POST')}>提交评测</button>
            <button type="button" className="rounded border px-3 py-2" onClick={() => evaluate('GET')}>查询结果</button>
            <button type="button" className="rounded border px-3 py-2" onClick={requestAIFeedback} disabled={!evaluation}>AI 深度反馈</button>
            <button type="button" className="rounded border px-3 py-2" onClick={requestFollowups}>AI 追问</button>
            <button type="button" className="rounded border px-3 py-2" onClick={completeTask}>标记任务完成</button>
          </div>
          <div className="mt-3 flex flex-wrap gap-2"><select aria-label="成果转化类型" className="border px-2" value={outcomeType} onChange={e=>setOutcomeType(e.target.value)}><option value="learning_verified">已验证学习成果</option><option value="diagnostic_completed">诊断报告</option><option value="mistake_archive">错题档案</option><option value="project_result">项目成果</option></select><select aria-label="关联能力维度" className="border px-2" value={attributeKey} onChange={e=>setAttributeKey(e.target.value)}><option value="mathematical_foundation">数学基础</option><option value="english">英语</option><option value="professional_knowledge">专业知识</option><option value="programming_tools">编程工具</option><option value="data_analysis">数据分析</option></select><button type="button" className="border px-3 py-2" onClick={convertOutcome}>转化任务成果</button></div>
          {message ? <p className="mt-3 text-sm text-green-700">{message}</p> : null}
          {evaluation ? <p className="mt-3 text-sm">评测：{evaluation.status}，{evaluation.reason}</p> : null}
          {aiFeedback ? <div className="mt-3 border-l-4 border-slate-500 p-3 text-sm"><p>{aiFeedback.summary}</p><p>做得好的地方：{aiFeedback.strengths.join('；') || '无'}</p><p>尚未完成：{aiFeedback.incomplete_parts.join('；') || '无'}</p><p>改进建议：{aiFeedback.suggestions.join('；') || '无'}</p></div> : null}
          {followups.length ? <div className="mt-3"><h4 className="font-semibold">理解追问</h4>{followups.map((item) => <p className="text-sm" key={item.id}>{item.question}</p>)}</div> : null}
        </section>
      ) : null}
    </main>
  );
}
