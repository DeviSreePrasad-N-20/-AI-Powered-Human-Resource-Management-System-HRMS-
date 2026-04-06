import { useDeferredValue, useEffect, useState } from 'react'
import './App.css'
import { API_BASE, api } from './api/client'
import { AnalyticsSidebar } from './components/AnalyticsSidebar'
import { EmployeeModule } from './components/EmployeeModule'
import { LeaveModule } from './components/LeaveModule'
import { OnboardingModule } from './components/OnboardingModule'
import { PerformanceModule } from './components/PerformanceModule'
import { RecruitmentModule } from './components/RecruitmentModule'
import { StatCard } from './components/StatCard'
import type {
  Attendance,
  AttendanceSummary,
  Candidate,
  CandidateComparison,
  DashboardStats,
  Employee,
  HrAnalytics,
  JobPosting,
  LeaveBalance,
  LeaveRequest,
  MonthlySummary,
  OnboardingQuestion,
  OnboardingRole,
  OnboardingTask,
  OrgChartNode,
  PolicyDocument,
  ReviewCycle,
  ReviewSnapshot,
} from './types/hrms'
import { parseChecklist, slugList } from './utils/hrms'

type ModuleKey = 'employees' | 'recruitment' | 'leave' | 'performance' | 'onboarding' | 'analytics'

const MODULE_PAGES: Array<{ description: string; key: ModuleKey; label: string }> = [
  {
    key: 'employees',
    label: 'Employees',
    description: 'Add people, search the list, upload files, and understand the team structure.',
  },
  {
    key: 'recruitment',
    label: 'Hiring',
    description: 'Create jobs, review candidates, compare them, and move them through the hiring steps.',
  },
  {
    key: 'leave',
    label: 'Time Off',
    description: 'Check leave balance, approve requests, and save daily attendance.',
  },
  {
    key: 'performance',
    label: 'Feedback',
    description: 'Collect employee and manager feedback, create summaries, and download the final review.',
  },
  {
    key: 'onboarding',
    label: 'New Joiners',
    description: 'Assign starter tasks, upload help files, and answer common questions.',
  },
  {
    key: 'analytics',
    label: 'Insights',
    description: 'See company numbers, hiring progress, leave use, and the monthly summary.',
  },
]

function getHashPage(): ModuleKey {
  if (typeof window === 'undefined') {
    return 'employees'
  }

  const hash = window.location.hash.replace('#', '')
  const match = MODULE_PAGES.find((page) => page.key === hash)
  return match?.key ?? 'employees'
}

function App() {
  const [loading, setLoading] = useState(true)
  const [notice, setNotice] = useState('')
  const [error, setError] = useState('')

  const [dashboard, setDashboard] = useState<DashboardStats | null>(null)
  const [analytics, setAnalytics] = useState<HrAnalytics | null>(null)
  const [monthlySummary, setMonthlySummary] = useState<MonthlySummary | null>(null)
  const [employees, setEmployees] = useState<Employee[]>([])
  const [orgChart, setOrgChart] = useState<OrgChartNode[]>([])
  const [jobs, setJobs] = useState<JobPosting[]>([])
  const [candidatesByJob, setCandidatesByJob] = useState<Record<number, Candidate[]>>({})
  const [leaveBalances, setLeaveBalances] = useState<LeaveBalance[]>([])
  const [leaveRequests, setLeaveRequests] = useState<LeaveRequest[]>([])
  const [leaveCalendar, setLeaveCalendar] = useState<Record<string, Array<{ department: string; employee: string; type: string }>>>({})
  const [leaveInsights, setLeaveInsights] = useState<{ flags: string[]; capacity_risk_overview: string[] }>({
    flags: [],
    capacity_risk_overview: [],
  })
  const [reviewCycles, setReviewCycles] = useState<ReviewCycle[]>([])
  const [roles, setRoles] = useState<OnboardingRole[]>([])
  const [tasks, setTasks] = useState<OnboardingTask[]>([])
  const [policyDocuments, setPolicyDocuments] = useState<PolicyDocument[]>([])
  const [onboardingQuestions, setOnboardingQuestions] = useState<OnboardingQuestion[]>([])
  const [questionAnalytics, setQuestionAnalytics] = useState<Array<{ question: string; count: number }>>([])
  const [candidateComparison, setCandidateComparison] = useState<CandidateComparison[]>([])
  const [attendanceSummary, setAttendanceSummary] = useState<AttendanceSummary | null>(null)
  const [reviewSnapshot, setReviewSnapshot] = useState<ReviewSnapshot | null>(null)

  const [selectedJobId, setSelectedJobId] = useState<number | null>(null)
  const [selectedCandidateIds, setSelectedCandidateIds] = useState<number[]>([])
  const [selectedReviewCycleId, setSelectedReviewCycleId] = useState<number | null>(null)
  const [selectedReviewEmployeeId, setSelectedReviewEmployeeId] = useState<number | null>(null)
  const [selectedAttendanceEmployeeId, setSelectedAttendanceEmployeeId] = useState<number | null>(null)
  const [selectedOnboardingEmployeeId, setSelectedOnboardingEmployeeId] = useState<number | null>(null)
  const [selectedRoleId, setSelectedRoleId] = useState<number | null>(null)
  const [employeeSearch, setEmployeeSearch] = useState('')
  const [attendanceMonth, setAttendanceMonth] = useState(new Date().toISOString().slice(0, 7))
  const [activePage, setActivePage] = useState<ModuleKey>(getHashPage)
  const deferredSearch = useDeferredValue(employeeSearch)

  async function runAction(action: () => Promise<void>, successMessage: string, reset?: () => void) {
    setError('')
    setNotice('')

    try {
      await action()
      setNotice(successMessage)
      reset?.()
    } catch (actionError) {
      setError(actionError instanceof Error ? actionError.message : 'Something went wrong.')
    }
  }

  async function refreshTasks(employeeId: number) {
    setTasks(await api.get<OnboardingTask[]>(`/onboarding/tasks/${employeeId}`))
  }

  async function refreshAttendanceSummary(employeeId: number, month: string) {
    setAttendanceSummary(
      await api.get<AttendanceSummary>(`/leave/attendance/summary?employee_id=${employeeId}&month=${month}`),
    )
  }

  async function refreshLeaveCalendar(month: string) {
    setLeaveCalendar(await api.get<Record<string, Array<{ department: string; employee: string; type: string }>>>(`/leave/calendar?month=${month}`))
  }

  async function refreshReviewSnapshot(cycleId: number, employeeId: number) {
    setReviewSnapshot(await api.get<ReviewSnapshot>(`/performance/reviews/${cycleId}/${employeeId}`))
  }

  async function refreshAll() {
    setLoading(true)
    setError('')

    try {
      const [
        dashboardData,
        analyticsData,
        monthlyData,
        employeeData,
        orgChartData,
        jobData,
        balanceData,
        leaveRequestData,
        leaveCalendarData,
        leaveInsightData,
        reviewCycleData,
        roleData,
        policyData,
        questionData,
        questionAnalyticsData,
      ] = await Promise.all([
        api.get<DashboardStats>('/dashboard'),
        api.get<HrAnalytics>('/analytics/hr'),
        api.get<MonthlySummary>('/analytics/monthly-summary'),
        api.get<Employee[]>('/employees'),
        api.get<OrgChartNode[]>('/employees/org-chart'),
        api.get<JobPosting[]>('/recruitment/jobs'),
        api.get<LeaveBalance[]>('/leave/balances'),
        api.get<LeaveRequest[]>('/leave/requests'),
        api.get<Record<string, Array<{ department: string; employee: string; type: string }>>>(`/leave/calendar?month=${attendanceMonth}`),
        api.get<{ flags: string[]; capacity_risk_overview: string[] }>('/leave/insights'),
        api.get<ReviewCycle[]>('/performance/cycles'),
        api.get<OnboardingRole[]>('/onboarding/roles'),
        api.get<PolicyDocument[]>('/onboarding/documents'),
        api.get<OnboardingQuestion[]>('/onboarding/questions'),
        api.get<Array<{ question: string; count: number }>>('/onboarding/question-analytics'),
      ])

      const candidateEntries = await Promise.all(
        jobData.map(async (job) => [job.id, await api.get<Candidate[]>(`/recruitment/jobs/${job.id}/candidates`)] as const),
      )

      setDashboard(dashboardData)
      setAnalytics(analyticsData)
      setMonthlySummary(monthlyData)
      setEmployees(employeeData)
      setOrgChart(orgChartData)
      setJobs(jobData)
      setCandidatesByJob(Object.fromEntries(candidateEntries))
      setLeaveBalances(balanceData)
      setLeaveRequests(leaveRequestData)
      setLeaveCalendar(leaveCalendarData)
      setLeaveInsights(leaveInsightData)
      setReviewCycles(reviewCycleData)
      setRoles(roleData)
      setPolicyDocuments(policyData)
      setOnboardingQuestions(questionData)
      setQuestionAnalytics(questionAnalyticsData)

      setSelectedJobId((previous) => (previous && jobData.some((job) => job.id === previous) ? previous : jobData[0]?.id ?? null))
      setSelectedAttendanceEmployeeId((previous) =>
        previous && employeeData.some((employee) => employee.id === previous) ? previous : employeeData[0]?.id ?? null,
      )
      setSelectedOnboardingEmployeeId((previous) =>
        previous && employeeData.some((employee) => employee.id === previous) ? previous : employeeData[0]?.id ?? null,
      )
      setSelectedRoleId((previous) => (previous && roleData.some((role) => role.id === previous) ? previous : roleData[0]?.id ?? null))
      setSelectedReviewCycleId((previous) =>
        previous && reviewCycleData.some((cycle) => cycle.id === previous) ? previous : reviewCycleData[0]?.id ?? null,
      )
      setSelectedReviewEmployeeId((previous) => {
        const cycle = reviewCycleData[0]
        if (!cycle) {
          return null
        }
        if (previous && cycle.employee_ids.includes(previous)) {
          return previous
        }
        return cycle.employee_ids[0] ?? null
      })
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : 'Failed to load HRMS data.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    void refreshAll()
    // Initial bootstrap happens once on mount.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  useEffect(() => {
    function syncPageFromHash() {
      setActivePage(getHashPage())
    }

    window.addEventListener('hashchange', syncPageFromHash)
    return () => window.removeEventListener('hashchange', syncPageFromHash)
  }, [])

  useEffect(() => {
    if (selectedOnboardingEmployeeId) {
      void refreshTasks(selectedOnboardingEmployeeId)
    }
  }, [selectedOnboardingEmployeeId])

  useEffect(() => {
    if (selectedAttendanceEmployeeId) {
      void refreshAttendanceSummary(selectedAttendanceEmployeeId, attendanceMonth)
    }
    void refreshLeaveCalendar(attendanceMonth)
  }, [selectedAttendanceEmployeeId, attendanceMonth])

  useEffect(() => {
    if (selectedReviewCycleId && selectedReviewEmployeeId) {
      void refreshReviewSnapshot(selectedReviewCycleId, selectedReviewEmployeeId)
    } else {
      setReviewSnapshot(null)
    }
  }, [selectedReviewCycleId, selectedReviewEmployeeId])

  const selectedJob = jobs.find((job) => job.id === selectedJobId) ?? null
  const selectedCandidates = selectedJobId ? candidatesByJob[selectedJobId] ?? [] : []
  const selectedCycle = reviewCycles.find((cycle) => cycle.id === selectedReviewCycleId) ?? null
  const reviewEmployees = selectedCycle
    ? employees.filter((employee) => selectedCycle.employee_ids.includes(employee.id))
    : employees
  const activeModule = MODULE_PAGES.find((page) => page.key === activePage) ?? MODULE_PAGES[0]
  const visibleEmployees = employees.filter((employee) => {
    const query = deferredSearch.trim().toLowerCase()
    if (!query) {
      return true
    }
    return [
      employee.name,
      employee.designation,
      employee.department,
      employee.email,
      employee.contact,
      employee.skills.join(' '),
    ]
      .join(' ')
      .toLowerCase()
      .includes(query)
  })

  function navigateToPage(page: ModuleKey) {
    setActivePage(page)
    if (window.location.hash !== `#${page}`) {
      window.location.hash = page
    }
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  const activeModuleView = (() => {
    switch (activePage) {
      case 'employees':
        return (
          <EmployeeModule
            apiBase={API_BASE}
            employeeSearch={employeeSearch}
            employees={employees}
            orgChart={orgChart}
            onCreateEmployee={(formData, reset) =>
              void runAction(async () => {
                await api.postJson('/employees', {
                  name: formData.get('name'),
                  designation: formData.get('designation'),
                  department: formData.get('department'),
                  joining_date: formData.get('joining_date'),
                  manager_id: Number(formData.get('manager_id') || 0) || null,
                  contact: formData.get('contact'),
                  email: formData.get('email'),
                  skills: slugList(formData.get('skills')),
                  termination_date: null,
                  status: 'active',
                })
                await refreshAll()
              }, 'Employee created.', reset)
            }
            onSearchChange={setEmployeeSearch}
            onUploadDocument={(formData, reset) =>
              void runAction(async () => {
                const payload = new FormData()
                const file = formData.get('file')
                if (!(file instanceof File) || file.size === 0) {
                  throw new Error('Please choose a document file.')
                }
                payload.append('title', String(formData.get('title') || 'Document'))
                payload.append('file', file)
                await api.postForm(`/employees/${Number(formData.get('employee_id'))}/documents`, payload)
                await refreshAll()
              }, 'Employee document uploaded.', reset)
            }
            visibleEmployees={visibleEmployees}
          />
        )
      case 'recruitment':
        return (
          <RecruitmentModule
            candidateComparison={candidateComparison}
            jobs={jobs}
            onAddCandidate={(jobId, formData, reset) =>
              void runAction(async () => {
                if (!jobId) {
                  throw new Error('Select a job before adding a candidate.')
                }
                const payload = new FormData()
                const file = formData.get('file')
                if (!(file instanceof File) || file.size === 0) {
                  throw new Error('Please attach a resume PDF.')
                }
                payload.append('name', String(formData.get('name') || ''))
                payload.append('email', String(formData.get('email') || ''))
                payload.append('skills', String(formData.get('skills') || ''))
                payload.append('file', file)
                await api.postForm(`/recruitment/jobs/${jobId}/candidates`, payload)
                await refreshAll()
              }, 'Candidate added and AI-scored.', reset)
            }
            onCompare={() =>
              void runAction(async () => {
                if (selectedCandidateIds.length < 2) {
                  throw new Error('Select at least two candidates for comparison.')
                }
                setCandidateComparison(
                  await api.get<CandidateComparison[]>(
                    `/recruitment/compare?candidate_ids=${selectedCandidateIds.join(',')}`,
                  ),
                )
              }, 'Candidate comparison ready.')
            }
            onCreateJob={(formData, reset) =>
              void runAction(async () => {
                await api.postJson('/recruitment/jobs', {
                  role: formData.get('role'),
                  job_description: formData.get('job_description'),
                  required_skills: slugList(formData.get('required_skills')),
                  experience_level: formData.get('experience_level'),
                })
                await refreshAll()
              }, 'Job posting created.', reset)
            }
            onSelectedCandidateIdsChange={setSelectedCandidateIds}
            onSelectedJobIdChange={(jobId) => {
              setSelectedJobId(jobId)
              setSelectedCandidateIds([])
              setCandidateComparison([])
            }}
            onUpdateStage={(candidateId, stage) =>
              void runAction(async () => {
                await api.patchJson(`/recruitment/candidates/${candidateId}/stage`, { stage })
                await refreshAll()
              }, `Candidate moved to ${stage}.`)
            }
            selectedCandidateIds={selectedCandidateIds}
            selectedCandidates={selectedCandidates}
            selectedJob={selectedJob}
            selectedJobId={selectedJobId}
          />
        )
      case 'leave':
        return (
          <LeaveModule
            attendanceMonth={attendanceMonth}
            attendanceSummary={attendanceSummary}
            employees={employees}
            insights={leaveInsights}
            leaveCalendar={leaveCalendar}
            leaveBalances={leaveBalances}
            leaveRequests={leaveRequests}
            onAttendanceMonthChange={setAttendanceMonth}
            onCreateLeaveRequest={(formData, reset) =>
              void runAction(async () => {
                await api.postJson('/leave/requests', {
                  employee_id: Number(formData.get('employee_id')),
                  manager_id: Number(formData.get('manager_id') || 0) || null,
                  leave_type: formData.get('leave_type'),
                  start_date: formData.get('start_date'),
                  end_date: formData.get('end_date'),
                  reason: formData.get('reason'),
                })
                await refreshAll()
              }, 'Leave request submitted.', reset)
            }
            onDecideLeave={(leaveId, status) =>
              void runAction(async () => {
                await api.patchJson(`/leave/requests/${leaveId}`, {
                  status,
                  manager_comment: `${status} via dashboard.`,
                })
                await refreshAll()
              }, `Leave ${status.toLowerCase()}.`)
            }
            onMarkAttendance={(formData, reset) =>
              void runAction(async () => {
                await api.postJson<Attendance>('/leave/attendance', {
                  employee_id: Number(formData.get('employee_id')),
                  record_date: formData.get('record_date'),
                  status: formData.get('status'),
                  notes: formData.get('notes'),
                })
                await refreshAll()
              }, 'Attendance updated.', reset)
            }
            onSelectedAttendanceEmployeeIdChange={setSelectedAttendanceEmployeeId}
            selectedAttendanceEmployeeId={selectedAttendanceEmployeeId}
          />
        )
      case 'performance':
        return (
          <PerformanceModule
            apiBase={API_BASE}
            employees={employees}
            onCreateCycle={(formData, reset) =>
              void runAction(async () => {
                await api.postJson('/performance/cycles', {
                  period_label: formData.get('period_label'),
                  start_date: formData.get('start_date'),
                  end_date: formData.get('end_date'),
                  employee_ids: slugList(formData.get('employee_ids')).map(Number),
                })
                await refreshAll()
              }, 'Review cycle created.', reset)
            }
            onSaveManagerReview={(formData) =>
              void runAction(async () => {
                if (!selectedReviewCycleId || !selectedReviewEmployeeId) {
                  throw new Error('Choose a review cycle and employee first.')
                }
                await api.postJson('/performance/manager-reviews', {
                  cycle_id: selectedReviewCycleId,
                  employee_id: selectedReviewEmployeeId,
                  manager_id: Number(formData.get('manager_id')),
                  quality: Number(formData.get('quality')),
                  delivery: Number(formData.get('delivery')),
                  communication: Number(formData.get('communication')),
                  initiative: Number(formData.get('initiative')),
                  teamwork: Number(formData.get('teamwork')),
                  manager_comments: formData.get('manager_comments'),
                })
                await refreshAll()
                await refreshReviewSnapshot(selectedReviewCycleId, selectedReviewEmployeeId)
              }, 'Manager review saved and AI summary refreshed.')
            }
            onSaveSelfAssessment={(formData) =>
              void runAction(async () => {
                if (!selectedReviewCycleId || !selectedReviewEmployeeId) {
                  throw new Error('Choose a review cycle and employee first.')
                }
                await api.postJson('/performance/self-assessments', {
                  cycle_id: selectedReviewCycleId,
                  employee_id: selectedReviewEmployeeId,
                  achievements: formData.get('achievements'),
                  challenges: formData.get('challenges'),
                  goals: formData.get('goals'),
                  self_rating: Number(formData.get('self_rating')),
                })
                await refreshReviewSnapshot(selectedReviewCycleId, selectedReviewEmployeeId)
              }, 'Self assessment saved.')
            }
            onSelectedReviewCycleIdChange={(cycleId) => {
              const cycle = reviewCycles.find((item) => item.id === cycleId)
              setSelectedReviewCycleId(cycleId)
              setSelectedReviewEmployeeId(cycle?.employee_ids[0] ?? null)
            }}
            onSelectedReviewEmployeeIdChange={setSelectedReviewEmployeeId}
            reviewCycles={reviewCycles}
            reviewEmployees={reviewEmployees}
            reviewSnapshot={reviewSnapshot}
            selectedReviewCycleId={selectedReviewCycleId}
            selectedReviewEmployeeId={selectedReviewEmployeeId}
          />
        )
      case 'onboarding':
        return (
          <OnboardingModule
            employees={employees}
            onboardingQuestions={onboardingQuestions}
            onAskQuestion={(formData, reset) =>
              void runAction(async () => {
                await api.postJson('/onboarding/ask', {
                  employee_id: Number(formData.get('employee_id') || 0) || null,
                  question: formData.get('question'),
                })
                await refreshAll()
              }, 'Question answered.', reset)
            }
            onAssignRole={() =>
              void runAction(async () => {
                if (!selectedRoleId || !selectedOnboardingEmployeeId) {
                  throw new Error('Choose both an employee and a role checklist.')
                }
                await api.postJson(`/onboarding/roles/${selectedRoleId}/assign/${selectedOnboardingEmployeeId}`, {})
                await refreshTasks(selectedOnboardingEmployeeId)
              }, 'Checklist assigned.')
            }
            onCreateRole={(formData, reset) =>
              void runAction(async () => {
                await api.postJson('/onboarding/roles', {
                  role_name: formData.get('role_name'),
                  checklist_template: parseChecklist(String(formData.get('checklist_template') || '')),
                })
                await refreshAll()
              }, 'Onboarding role created.', reset)
            }
            onSelectedOnboardingEmployeeIdChange={setSelectedOnboardingEmployeeId}
            onSelectedRoleIdChange={setSelectedRoleId}
            onUpdateTask={(taskId, status) =>
              void runAction(async () => {
                await api.patchJson(`/onboarding/tasks/${taskId}`, { status })
                if (selectedOnboardingEmployeeId) {
                  await refreshTasks(selectedOnboardingEmployeeId)
                }
              }, 'Task updated.')
            }
            onUploadPolicy={(formData, reset) =>
              void runAction(async () => {
                const payload = new FormData()
                const file = formData.get('file')
                if (!(file instanceof File) || file.size === 0) {
                  throw new Error('Please attach a policy document.')
                }
                payload.append('title', String(formData.get('title') || 'Policy'))
                payload.append('file', file)
                await api.postForm('/onboarding/documents', payload)
                await refreshAll()
              }, 'Policy uploaded.', reset)
            }
            policyDocuments={policyDocuments}
            roles={roles}
            selectedOnboardingEmployeeId={selectedOnboardingEmployeeId}
            selectedRoleId={selectedRoleId}
            tasks={tasks}
          />
        )
      case 'analytics':
        return (
          <AnalyticsSidebar
            analytics={analytics}
            monthlySummary={monthlySummary}
            questionAnalytics={questionAnalytics}
            standalone
          />
        )
      default:
        return null
    }
  })()

  return (
    <div className="app-shell">
      <header className="hero-panel">
        <div>
          <p className="eyebrow">Simple HR dashboard</p>
          <h1>Human Resource Management System</h1>
          <p className="hero-copy">
            A clean HR app with separate pages for employees, hiring, time off, feedback, new joiners, and insights.
          </p>
        </div>
        <div className="hero-actions">
          {MODULE_PAGES.map((page) => (
            <button
              key={page.key}
              type="button"
              className={`nav-button ${activePage === page.key ? 'is-active' : ''}`}
              onClick={() => navigateToPage(page.key)}
            >
              <span>{page.label}</span>
              <small>{page.description}</small>
            </button>
          ))}
        </div>
      </header>

      {error ? <div className="banner banner--error">{error}</div> : null}
      {notice ? <div className="banner banner--success">{notice}</div> : null}
      {loading ? <div className="banner">Loading the HRMS workspace...</div> : null}

      <section className="stats-grid">
        <StatCard label="Employees" value={dashboard?.headcount ?? '--'} accent="#1c7c54" />
        <StatCard label="Open jobs" value={dashboard?.open_positions ?? '--'} accent="#d9480f" />
        <StatCard label="On leave today" value={dashboard?.approved_leave_today ?? '--'} accent="#2563eb" />
        <StatCard label="Reviews left" value={dashboard?.pending_reviews ?? '--'} accent="#7c3aed" />
        <StatCard label="Questions asked" value={dashboard?.onboarding_questions ?? '--'} accent="#9a3412" />
      </section>

      <div className="page-stage">
        <section className="page-intro">
          <p className="eyebrow">Open page</p>
          <h2>{activeModule.label}</h2>
          <p>{activeModule.description}</p>
        </section>
        <div className="page-content">{activeModuleView}</div>
      </div>
    </div>
  )
}

export default App
