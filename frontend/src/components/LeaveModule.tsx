import { ModuleGuide } from "./ModuleGuide"
import { SectionCard } from "./SectionCard"
import type { AttendanceSummary, Employee, LeaveBalance, LeaveRequest } from "../types/hrms"

const LEAVE_TYPES = ["Sick", "Casual", "Earned", "WFH"]
const ATTENDANCE_OPTIONS = ["Present", "WFH", "Half Day", "Absent"]

type LeaveModuleProps = {
  attendanceMonth: string
  attendanceSummary: AttendanceSummary | null
  employees: Employee[]
  insights: { flags: string[]; capacity_risk_overview: string[] }
  leaveCalendar: Record<string, Array<{ department: string; employee: string; type: string }>>
  leaveBalances: LeaveBalance[]
  leaveRequests: LeaveRequest[]
  onAttendanceMonthChange: (value: string) => void
  onCreateLeaveRequest: (formData: FormData, reset: () => void) => void
  onDecideLeave: (leaveId: number, status: string) => void
  onMarkAttendance: (formData: FormData, reset: () => void) => void
  onSelectedAttendanceEmployeeIdChange: (employeeId: number) => void
  selectedAttendanceEmployeeId: number | null
}

export function LeaveModule({
  attendanceMonth,
  attendanceSummary,
  employees,
  insights,
  leaveCalendar,
  leaveBalances,
  leaveRequests,
  onAttendanceMonthChange,
  onCreateLeaveRequest,
  onDecideLeave,
  onMarkAttendance,
  onSelectedAttendanceEmployeeIdChange,
  selectedAttendanceEmployeeId,
}: LeaveModuleProps) {
  function employeeName(employeeId: number | null) {
    return employees.find((employee) => employee.id === employeeId)?.name ?? "Unassigned"
  }

  return (
    <SectionCard title="Leave and Attendance" eyebrow="Module 3">
      <div className="section-stack" id="leave">
        <ModuleGuide
          items={[
            { label: "Step 1", title: "Check leave left", text: "See how many leave days each employee still has before applying." },
            { label: "Step 2", title: "Send or approve requests", text: "Create a leave request and review requests waiting for approval." },
            { label: "Step 3", title: "Mark attendance", text: "Save the daily status and check the monthly attendance count." },
          ]}
        />
        <div className="split-panel">
          <div className="panel-surface">
            <div className="panel-heading">
              <h3>Leave balance</h3>
              <span className="subtle">Each employee is shown in one simple horizontal row.</span>
            </div>
            <div className="leave-balance-list">
              {leaveBalances.map((balance) => (
                <div key={balance.employee_id} className="leave-balance-card">
                  <strong>{employeeName(balance.employee_id)}</strong>
                  <div className="leave-metric-grid">
                    <span className="badge">Sick: {balance.sick}</span>
                    <span className="badge">Casual: {balance.casual}</span>
                    <span className="badge">Earned: {balance.earned}</span>
                    <span className="badge">WFH: {balance.wfh}</span>
                  </div>
                </div>
              ))}
            </div>
            <hr />
            <form
              className="form-grid"
              onSubmit={(event) => {
                event.preventDefault()
                onCreateLeaveRequest(new FormData(event.currentTarget), () => event.currentTarget.reset())
              }}
            >
              <select name="employee_id" required defaultValue="">
                <option value="">Choose employee</option>
                {employees.map((employee) => (
                  <option key={employee.id} value={employee.id}>
                    {employee.name}
                  </option>
                ))}
              </select>
              <select name="manager_id" defaultValue="">
                <option value="">Choose manager</option>
                {employees.map((employee) => (
                  <option key={employee.id} value={employee.id}>
                    {employee.name}
                  </option>
                ))}
              </select>
              <select name="leave_type" required defaultValue="">
                <option value="">Choose leave type</option>
                {LEAVE_TYPES.map((type) => (
                  <option key={type} value={type}>
                    {type}
                  </option>
                ))}
              </select>
              <input name="start_date" type="date" required />
              <input name="end_date" type="date" required />
              <textarea name="reason" placeholder="Why is this leave needed?" required />
              <button type="submit">Send leave request</button>
            </form>
          </div>

          <div className="panel-surface">
            <div className="panel-heading">
              <h3>Daily attendance</h3>
              <span className="subtle">Mark work status and see the monthly count on the same page.</span>
            </div>
            <form
              className="form-grid"
              onSubmit={(event) => {
                event.preventDefault()
                onMarkAttendance(new FormData(event.currentTarget), () => event.currentTarget.reset())
              }}
            >
              <select name="employee_id" required defaultValue="">
                <option value="">Choose employee</option>
                {employees.map((employee) => (
                  <option key={employee.id} value={employee.id}>
                    {employee.name}
                  </option>
                ))}
              </select>
              <input name="record_date" type="date" required />
              <select name="status" required defaultValue="">
                <option value="">Choose status</option>
                {ATTENDANCE_OPTIONS.map((status) => (
                  <option key={status} value={status}>
                    {status}
                  </option>
                ))}
              </select>
              <input name="notes" placeholder="Short note (optional)" />
              <button type="submit">Save attendance</button>
            </form>

            <div className="inline-toolbar">
              <select
                value={selectedAttendanceEmployeeId ?? ""}
                onChange={(event) => onSelectedAttendanceEmployeeIdChange(Number(event.target.value))}
              >
                {employees.map((employee) => (
                  <option key={employee.id} value={employee.id}>
                    {employee.name}
                  </option>
                ))}
              </select>
              <input value={attendanceMonth} type="month" onChange={(event) => onAttendanceMonthChange(event.target.value)} />
            </div>

            <div className="badge-row">
              {Object.entries(attendanceSummary?.totals ?? {}).map(([status, total]) => (
                <span key={status} className="badge">
                  {status}: {total}
                </span>
              ))}
            </div>
          </div>
        </div>

        <div className="panel-surface">
          <div className="panel-heading">
            <h3>Leave requests and smart alerts</h3>
            <span className="subtle">Approve requests and quickly spot patterns that need attention.</span>
          </div>
          <div className="request-grid">
            {leaveRequests.map((request) => (
              <article key={request.id} className="request-card">
                <strong>
                  {employeeName(request.employee_id)} · {request.leave_type}
                </strong>
                <span>
                  {request.start_date} to {request.end_date}
                </span>
                <p>{request.reason}</p>
                <div className="badge-row">
                  <span className="badge">{request.status}</span>
                  {request.ai_flags.map((flag) => (
                    <span key={flag} className="badge badge--warning">
                      {flag}
                    </span>
                  ))}
                </div>
                <small>{request.capacity_risk}</small>
                <div className="button-row">
                  <button type="button" onClick={() => onDecideLeave(request.id, "Approved")}>
                    Approve
                  </button>
                  <button type="button" className="secondary" onClick={() => onDecideLeave(request.id, "Rejected")}>
                    Reject
                  </button>
                </div>
              </article>
            ))}
          </div>
          <div className="insight-grid">
            <div>
              <h4>Repeated leave patterns</h4>
              <ul className="clean-list">
                {(insights.flags.length ? insights.flags : ["No repeated pattern found"]).map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            </div>
            <div>
              <h4>Team workload risk</h4>
              <ul className="clean-list">
                {insights.capacity_risk_overview.map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            </div>
          </div>
          <div>
            <h4>Team leave calendar</h4>
            <div className="stack-list">
              {Object.entries(leaveCalendar).length ? (
                Object.entries(leaveCalendar)
                  .sort(([left], [right]) => left.localeCompare(right))
                  .map(([day, entries]) => (
                    <div key={day} className="simple-row">
                      <strong>{day}</strong>
                      <span>{entries.map((entry) => `${entry.employee} (${entry.type})`).join(", ")}</span>
                    </div>
                  ))
              ) : (
                <span className="subtle">No approved leave planned for this month.</span>
              )}
            </div>
          </div>
        </div>
      </div>
    </SectionCard>
  )
}
