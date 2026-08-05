export type User = {
  id: string;
  email: string;
  is_active: boolean;
};

export type Profile = {
  id: string;
  nickname?: string | null;
  learning_stage?: string | null;
  grade_level?: string | null;
  school?: string | null;
  major?: string | null;
  auxiliary_direction?: string | null;
  weekly_study_hours?: number | null;
  display_mode?: string | null;
};

export type Goal = {
  id: string;
  target_school?: string | null;
  target_college?: string | null;
  target_major?: string | null;
  target_year?: number | null;
  weekly_time?: number | null;
  current_stage?: string | null;
  remark?: string | null;
};

export type Task = {
  id: string;
  title: string;
  task_type: 'main' | 'support' | 'challenge' | 'subtask';
  parent_task_id?: string | null;
  status: string;
  deadline?: string | null;
  estimated_minutes?: number | null;
  completion_standard?: string | null;
  evidence_requirements?: string | null;
};

export type TimerSession = { id: string; task_id?: string | null; is_running: boolean; end_time?: string | null; elapsed_seconds: number };
export type Evaluation = { id: string; task_id: string; status: string; reason: string };
