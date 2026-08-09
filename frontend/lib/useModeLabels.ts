"use client";
import { useEffect, useState } from 'react';
import { apiRequest } from './api';

const immersive = { inventory:'系统背包', acquired:'获得物品', changes:'属性变化', review:'本周结算', progress:'主线推进', adjustment:'路径修正', nextPlan:'下周任务' };
const professional = { inventory:'成长证据', acquired:'新增成果', changes:'能力变化', review:'周度报告', progress:'目标进度', adjustment:'计划调整', nextPlan:'下周计划' };

export function useModeLabels() {
  const [labels, setLabels] = useState(immersive);
  useEffect(() => { apiRequest<{display_mode?:string}|null>('/profile').then(profile => setLabels(profile?.display_mode === 'professional' ? professional : immersive)).catch(() => undefined); }, []);
  return labels;
}
