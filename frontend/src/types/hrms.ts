export type Employee = {
  id: number
  name: string
  designation: string
  department: string
  joining_date: string
  manager_id: number | null
  contact: string
  email: string
  skills: string[]
  status: string
  bio: string
  flags: string[]
  termination_date: string | null
  documents: EmployeeDocument[]
}

export type EmployeeDocument = {
  id: number
  title: string
  file_name: string
  file_path: string
  content_type: string
  uploaded_at: string
}

export type OrgChartNode = {
  id: number
  name: string
  designation: string
  department: string
  reports: OrgChartNode[]
}

export type DashboardStats = {
  headcount: number
  open_positions: number
  approved_leave_today: number
  pending_reviews: number
  onboarding_questions: number
}

export type HrAnalytics = {
  headcount_by_department: Record<string, number>
  attrition_rate: number
  average_tenure_by_department: Record<string, number>
  open_vs_filled_positions: Record<string, number>
  leave_utilisation_rate: number
  ai_summary: string
}

export type MonthlySummary = {
  summary: string
  highlights: string[]
  risks: string[]
  recommended_actions: string[]
}

export type JobPosting = {
  id: number
  role: string
  job_description: string
  required_skills: string[]
  experience_level: string
  status: string
  created_at: string
}

export type Candidate = {
  id: number
  job_posting_id: number
  name: string
  email: string
  skills: string[]
  stage: string
  resume_filename: string
  match_percent: number
  match_reasoning: string
  strengths: string[]
  gaps: string[]
  interview_questions: string[]
  created_at: string
}

export type CandidateComparison = {
  candidate_id: number
  candidate_name: string
  current_stage: string
  match_percent: number
  strengths: string[]
  gaps: string[]
  recommendation: string
}

export type LeaveBalance = {
  employee_id: number
  sick: number
  casual: number
  earned: number
  wfh: number
}

export type LeaveRequest = {
  id: number
  employee_id: number
  manager_id: number | null
  leave_type: string
  start_date: string
  end_date: string
  reason: string
  status: string
  manager_comment: string
  ai_flags: string[]
  capacity_risk: string
  created_at: string
}

export type Attendance = {
  id: number
  employee_id: number
  record_date: string
  status: string
  notes: string
}

export type AttendanceSummary = {
  employee_id: number
  month: string
  totals: Record<string, number>
}

export type ReviewCycle = {
  id: number
  period_label: string
  start_date: string
  end_date: string
  employee_ids: number[]
  created_at: string
}

export type SelfAssessment = {
  id: number
  cycle_id: number
  employee_id: number
  achievements: string
  challenges: string
  goals: string
  self_rating: number
  created_at: string
}

export type ManagerReview = {
  id: number
  cycle_id: number
  employee_id: number
  manager_id: number
  quality: number
  delivery: number
  communication: number
  initiative: number
  teamwork: number
  manager_comments: string
  ai_summary: string
  mismatches: string[]
  development_actions: string[]
  created_at: string
}

export type ReviewSnapshot = {
  employee_id: number
  cycle_id: number
  self_assessment: SelfAssessment | null
  manager_review: ManagerReview | null
}

export type OnboardingRole = {
  id: number
  role_name: string
  checklist_template: Array<{
    title: string
    due_offset_days: number
    assignee: string
  }>
}

export type OnboardingTask = {
  id: number
  employee_id: number
  role_id: number | null
  title: string
  due_date: string | null
  assignee: string
  status: string
  created_at: string
}

export type PolicyDocument = {
  id: number
  title: string
  file_name: string
  file_path: string
  uploaded_at: string
}

export type OnboardingQuestion = {
  id: number
  employee_id: number | null
  question: string
  answer: string
  matched_doc_title: string
  created_at: string
}
