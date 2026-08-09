"use client";

import { useEffect, useState } from "react";
import { apiRequest } from "@/lib/api";

type Material = { id: string; original_filename: string; parse_status: string; confirmation_status: string; parsed_content?: { extracted_text?: string | null } };
type Course = { course_name: string; course_category: string; score: string; full_score: string; credit: string; semester: string; is_core: boolean };
type Experience = { experience_type: string; name: string; organization: string; start_date: string; end_date: string; description: string; outcome: string; associated_skills: string[] };
type AIAnalysis = { id: string; result_json: { courses: Array<Partial<Course> & { score?: number; full_score?: number; credit?: number }>; experiences: Array<Partial<Experience>>; missing_information: string[] } };

const emptyCourse: Course = { course_name: "", course_category: "mathematical_foundation", score: "", full_score: "", credit: "", semester: "", is_core: false };
const emptyExperience: Experience = { experience_type: "project", name: "", organization: "", start_date: "", end_date: "", description: "", outcome: "", associated_skills: [] };

export default function MaterialsPage() {
  const [items, setItems] = useState<Material[]>([]);
  const [selected, setSelected] = useState<Material | null>(null);
  const [file, setFile] = useState<File | null>(null);
  const [type, setType] = useState("transcript");
  const [entryMode, setEntryMode] = useState<"course" | "experience">("course");
  const [course, setCourse] = useState<Course>(emptyCourse);
  const [experience, setExperience] = useState<Experience>(emptyExperience);
  const [analysis, setAnalysis] = useState<AIAnalysis | null>(null);
  const [loading, setLoading] = useState(true);
  const [aiLoading, setAiLoading] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  async function load() {
    setLoading(true);
    try { setItems(await apiRequest<Material[]>("/materials")); }
    catch (reason) { setError(reason instanceof Error ? reason.message : "加载失败"); }
    finally { setLoading(false); }
  }
  useEffect(() => { load(); }, []);

  async function upload() {
    if (!file) return;
    const body = new FormData(); body.set("material_type", type); body.set("file", file);
    try { const value = await apiRequest<Material>("/materials", { method: "POST", body }); setItems((current) => [value, ...current]); setSelected(value); setMessage("材料已上传，请确认结构化结果"); }
    catch (reason) { setError(reason instanceof Error ? reason.message : "上传失败"); }
  }

  async function confirmManual() {
    if (!selected || (entryMode === "course" ? !course.course_name : !experience.name)) return;
    const payload = entryMode === "course"
      ? { courses: [{ ...course, score: Number(course.score), full_score: Number(course.full_score), credit: course.credit ? Number(course.credit) : null }], experiences: [] }
      : { courses: [], experiences: [{ ...experience, start_date: experience.start_date || null, end_date: experience.end_date || null }] };
    try { await apiRequest(`/materials/${selected.id}/confirm`, { method: "POST", body: JSON.stringify(payload) }); setMessage("解析结果已确认并生成成长证据"); await load(); }
    catch (reason) { setError(reason instanceof Error ? reason.message : "确认失败"); }
  }

  async function aiParse() {
    if (!selected) return;
    setAiLoading(true); setError("");
    try {
      const response = await apiRequest<{ status: string; analysis: AIAnalysis | null }>(`/materials/${selected.id}/ai-parse`, { method: "POST" });
      if (!response.analysis) { setMessage("AI 当前不可用，你仍可继续人工录入。"); return; }
      setAnalysis(response.analysis);
      const parsedCourse = response.analysis.result_json.courses[0];
      const parsedExperience = response.analysis.result_json.experiences[0];
      if (parsedCourse) { setEntryMode("course"); setCourse({ ...emptyCourse, ...parsedCourse, score: String(parsedCourse.score ?? ""), full_score: String(parsedCourse.full_score ?? ""), credit: String(parsedCourse.credit ?? "") }); }
      else if (parsedExperience) { setEntryMode("experience"); setExperience({ ...emptyExperience, ...parsedExperience }); }
      setMessage("AI 草稿已回填，请核对后再确认。");
    } catch (reason) { setMessage(reason instanceof Error ? reason.message : "AI 当前不可用，你仍可继续人工录入。"); }
    finally { setAiLoading(false); }
  }

  async function confirmAI() {
    if (!analysis) return;
    try { await apiRequest(`/ai/analyses/${analysis.id}/confirm-material`, { method: "POST" }); setAnalysis(null); setMessage("AI 草稿已由你确认并生成成长证据"); await load(); }
    catch (reason) { setError(reason instanceof Error ? reason.message : "确认失败"); }
  }

  async function remove() {
    if (!selected) return;
    try { await apiRequest(`/materials/${selected.id}`, { method: "DELETE" }); setSelected(null); setAnalysis(null); setMessage("材料及其关联结果已删除"); await load(); }
    catch (reason) { setError(reason instanceof Error ? reason.message : "删除失败"); }
  }

  return <main className="mx-auto max-w-6xl p-6">
    <h1 className="text-2xl font-bold">材料中心</h1>
    {error && <p className="mt-3 text-red-600">{error}</p>}{message && <p className="mt-3 text-green-700">{message}</p>}
    <section className="mt-5 grid gap-3 border-b pb-5 md:grid-cols-[180px_1fr_auto]">
      <select aria-label="材料类型" className="border px-3 py-2" value={type} onChange={(event) => setType(event.target.value)}><option value="transcript">成绩单</option><option value="resume">简历</option><option value="course_grade">课程成绩截图</option><option value="research">论文或录用证明</option><option value="internship">实习证明</option><option value="competition">竞赛证书</option><option value="project">项目成果</option><option value="other">其他材料</option></select>
      <input aria-label="选择材料" type="file" accept=".pdf,.docx,.txt,.png,.jpg,.jpeg" onChange={(event) => setFile(event.target.files?.[0] || null)} />
      <button className="border bg-slate-900 px-4 py-2 text-white" onClick={upload} disabled={!file}>上传材料</button>
    </section>
    <div className="mt-5 grid gap-6 lg:grid-cols-2">
      <section><h2 className="font-semibold">已上传材料</h2>{loading ? <p>加载中...</p> : items.length === 0 ? <p className="text-gray-600">尚未上传材料。</p> : items.map((item) => <button key={item.id} className="mt-2 block w-full border p-3 text-left" onClick={() => { setSelected(item); setAnalysis(null); }}><b>{item.original_filename}</b><span className="block text-sm text-gray-600">解析：{item.parse_status} / 确认：{item.confirmation_status}</span></button>)}</section>
      <section><h2 className="font-semibold">解析结果确认</h2>{!selected ? <p className="text-gray-600">请选择一份材料。</p> : <div className="mt-2 grid gap-2">
        <p className="text-sm">提取文本：{selected.parsed_content?.extracted_text || "待人工补充"}</p>
        <button className="border px-4 py-2" onClick={aiParse} disabled={aiLoading || !selected.parsed_content?.extracted_text}>{aiLoading ? "AI 解析中..." : "AI 辅助解析"}</button>
        <select aria-label="录入类型" className="border px-3 py-2" value={entryMode} onChange={(event) => setEntryMode(event.target.value as "course" | "experience")}><option value="course">课程成绩</option><option value="experience">简历或经历</option></select>
        {entryMode === "course" ? <><input className="border px-3 py-2" placeholder="课程名称" value={course.course_name} onChange={(event) => setCourse({ ...course, course_name: event.target.value })} /><select aria-label="课程类别" className="border px-3 py-2" value={course.course_category} onChange={(event) => setCourse({ ...course, course_category: event.target.value })}><option value="mathematical_foundation">数学基础</option><option value="english">英语</option><option value="professional_knowledge">专业知识</option><option value="programming_tools">编程工具</option><option value="data_analysis">数据分析</option></select><input className="border px-3 py-2" placeholder="成绩" type="number" value={course.score} onChange={(event) => setCourse({ ...course, score: event.target.value })} /><input className="border px-3 py-2" placeholder="满分" type="number" value={course.full_score} onChange={(event) => setCourse({ ...course, full_score: event.target.value })} /><input className="border px-3 py-2" placeholder="学分（可选）" type="number" value={course.credit} onChange={(event) => setCourse({ ...course, credit: event.target.value })} /><input className="border px-3 py-2" placeholder="学期（可选）" value={course.semester} onChange={(event) => setCourse({ ...course, semester: event.target.value })} /><label><input type="checkbox" checked={course.is_core} onChange={(event) => setCourse({ ...course, is_core: event.target.checked })} /> 核心课程</label></> : <><select aria-label="经历类型" className="border px-3 py-2" value={experience.experience_type} onChange={(event) => setExperience({ ...experience, experience_type: event.target.value })}><option value="research">科研</option><option value="internship">实习</option><option value="project">项目</option><option value="competition">竞赛</option><option value="certificate">证书</option><option value="portfolio">作品集</option><option value="other">其他</option></select><input className="border px-3 py-2" placeholder="经历名称" value={experience.name} onChange={(event) => setExperience({ ...experience, name: event.target.value })} /><input className="border px-3 py-2" placeholder="组织或单位" value={experience.organization} onChange={(event) => setExperience({ ...experience, organization: event.target.value })} /><input className="border px-3 py-2" type="date" aria-label="开始时间" value={experience.start_date} onChange={(event) => setExperience({ ...experience, start_date: event.target.value })} /><input className="border px-3 py-2" type="date" aria-label="结束时间" value={experience.end_date} onChange={(event) => setExperience({ ...experience, end_date: event.target.value })} /><textarea className="border px-3 py-2" placeholder="经历描述" value={experience.description} onChange={(event) => setExperience({ ...experience, description: event.target.value })} /><textarea className="border px-3 py-2" placeholder="成果" value={experience.outcome} onChange={(event) => setExperience({ ...experience, outcome: event.target.value })} /></>}
        {analysis ? <button className="border bg-slate-900 px-4 py-2 text-white" onClick={confirmAI}>确认 AI 草稿并生成证据</button> : <button className="border bg-slate-900 px-4 py-2 text-white" onClick={confirmManual}>确认结构化结果</button>}
        <button className="border px-4 py-2 text-red-700" onClick={remove}>删除本人材料</button>
      </div>}</section>
    </div>
  </main>;
}
