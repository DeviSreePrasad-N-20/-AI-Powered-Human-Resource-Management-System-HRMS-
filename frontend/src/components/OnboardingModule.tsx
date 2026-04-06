import { ModuleGuide } from "./ModuleGuide"
import { SectionCard } from "./SectionCard"
import type { Employee, OnboardingQuestion, OnboardingRole, OnboardingTask, PolicyDocument } from "../types/hrms"
import { formatDate } from "../utils/hrms"

const TASK_STATUSES = ["Pending", "In Progress", "Completed"]

type OnboardingModuleProps = {
  employees: Employee[]
  onboardingQuestions: OnboardingQuestion[]
  onAskQuestion: (formData: FormData, reset: () => void) => void
  onAssignRole: () => void
  onCreateRole: (formData: FormData, reset: () => void) => void
  onSelectedOnboardingEmployeeIdChange: (employeeId: number) => void
  onSelectedRoleIdChange: (roleId: number) => void
  onUpdateTask: (taskId: number, status: string) => void
  onUploadPolicy: (formData: FormData, reset: () => void) => void
  policyDocuments: PolicyDocument[]
  roles: OnboardingRole[]
  selectedOnboardingEmployeeId: number | null
  selectedRoleId: number | null
  tasks: OnboardingTask[]
}

export function OnboardingModule({
  employees,
  onboardingQuestions,
  onAskQuestion,
  onAssignRole,
  onCreateRole,
  onSelectedOnboardingEmployeeIdChange,
  onSelectedRoleIdChange,
  onUpdateTask,
  onUploadPolicy,
  policyDocuments,
  roles,
  selectedOnboardingEmployeeId,
  selectedRoleId,
  tasks,
}: OnboardingModuleProps) {
  return (
    <SectionCard title="New Joiner Help" eyebrow="Module 5">
      <div className="section-stack" id="onboarding">
        <ModuleGuide
          items={[
            { label: "Step 1", title: "Create a starter checklist", text: "Build a simple checklist for each role, like engineer or designer." },
            { label: "Step 2", title: "Assign it to a person", text: "Choose the employee and assign the checklist so progress is easy to track." },
            { label: "Step 3", title: "Answer questions", text: "Upload policy files and let the helper answer common new-joiner questions." },
          ]}
        />

        <div className="split-panel">
          <div className="panel-surface">
            <div className="panel-heading">
              <h3>Role checklists</h3>
              <span className="subtle">Pick a role to reuse its starter checklist.</span>
            </div>
            <div className="stack-list">
              {roles.map((role) => (
                <button
                  key={role.id}
                  type="button"
                  className={`select-card ${selectedRoleId === role.id ? "is-active" : ""}`}
                  onClick={() => onSelectedRoleIdChange(role.id)}
                >
                  <strong>{role.role_name}</strong>
                  <small>{role.checklist_template.length} checklist items</small>
                </button>
              ))}
            </div>
            <hr />
            <form
              className="form-grid"
              onSubmit={(event) => {
                event.preventDefault()
                onCreateRole(new FormData(event.currentTarget), () => event.currentTarget.reset())
              }}
            >
              <input name="role_name" placeholder="Role name" required />
              <textarea
                name="checklist_template"
                placeholder="One line for each item: task title | due after how many days | assignee"
                required
              />
              <button type="submit">Create checklist</button>
            </form>
          </div>

          <div className="panel-surface">
            <div className="panel-heading">
              <h3>Assign checklist</h3>
              <span className="subtle">Choose a person and give them the selected starter checklist.</span>
            </div>
            <div className="inline-toolbar">
              <select
                value={selectedOnboardingEmployeeId ?? ""}
                onChange={(event) => onSelectedOnboardingEmployeeIdChange(Number(event.target.value))}
              >
                {employees.map((employee) => (
                  <option key={employee.id} value={employee.id}>
                    {employee.name}
                  </option>
                ))}
              </select>
              <button type="button" onClick={onAssignRole}>
                Assign checklist
              </button>
            </div>

            <div className="stack-list">
              {tasks.map((task) => (
                <div key={task.id} className="task-row">
                  <div>
                    <strong>{task.title}</strong>
                    <span>
                      Due {formatDate(task.due_date)} · {task.assignee}
                    </span>
                  </div>
                  <select value={task.status} onChange={(event) => onUpdateTask(task.id, event.target.value)}>
                    {TASK_STATUSES.map((status) => (
                      <option key={status} value={status}>
                        {status}
                      </option>
                    ))}
                  </select>
                </div>
              ))}
            </div>
          </div>
        </div>

        <div className="split-panel">
          <div className="panel-surface">
            <div className="panel-heading">
              <h3>Policy files</h3>
              <span className="subtle">Upload files the helper can use to answer questions.</span>
            </div>
            <form
              className="form-grid"
              onSubmit={(event) => {
                event.preventDefault()
                onUploadPolicy(new FormData(event.currentTarget), () => event.currentTarget.reset())
              }}
            >
              <input name="title" placeholder="File title" required />
              <input name="file" type="file" accept=".pdf,.txt,.md" required />
              <button type="submit">Upload file</button>
            </form>
            <div className="stack-list">
              {policyDocuments.map((document) => (
                <div key={document.id} className="simple-row">
                  <strong>{document.title}</strong>
                  <span>{document.file_name}</span>
                </div>
              ))}
            </div>
          </div>

          <div className="panel-surface">
            <div className="panel-heading">
              <h3>Question helper</h3>
              <span className="subtle">It answers only from uploaded files and sends the user to HR if nothing matches.</span>
            </div>
            <form
              className="form-grid"
              onSubmit={(event) => {
                event.preventDefault()
                onAskQuestion(new FormData(event.currentTarget), () => event.currentTarget.reset())
              }}
            >
              <select name="employee_id" defaultValue="">
                <option value="">Choose employee</option>
                {employees.map((employee) => (
                  <option key={employee.id} value={employee.id}>
                    {employee.name}
                  </option>
                ))}
              </select>
              <textarea name="question" placeholder="Ask about leave, work from home, tools, or any policy file" required />
              <button type="submit">Ask question</button>
            </form>
            <div className="stack-list">
              {onboardingQuestions.slice(0, 5).map((question) => (
                <article key={question.id} className="question-card">
                  <strong>{question.question}</strong>
                  <p>{question.answer}</p>
                  <span>{question.matched_doc_title || "Sent to HR"}</span>
                </article>
              ))}
            </div>
          </div>
        </div>
      </div>
    </SectionCard>
  )
}
