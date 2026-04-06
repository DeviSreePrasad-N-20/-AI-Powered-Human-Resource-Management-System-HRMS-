import { ModuleGuide } from "./ModuleGuide"
import { SectionCard } from "./SectionCard"
import type { Employee, ReviewCycle, ReviewSnapshot } from "../types/hrms"

const REVIEW_FIELDS = [
  { label: "Work quality", name: "quality" },
  { label: "On-time delivery", name: "delivery" },
  { label: "Communication", name: "communication" },
  { label: "Ownership", name: "initiative" },
  { label: "Teamwork", name: "teamwork" },
]

type PerformanceModuleProps = {
  apiBase: string
  employees: Employee[]
  onCreateCycle: (formData: FormData, reset: () => void) => void
  onSaveManagerReview: (formData: FormData) => void
  onSaveSelfAssessment: (formData: FormData) => void
  onSelectedReviewCycleIdChange: (cycleId: number) => void
  onSelectedReviewEmployeeIdChange: (employeeId: number) => void
  reviewCycles: ReviewCycle[]
  reviewEmployees: Employee[]
  reviewSnapshot: ReviewSnapshot | null
  selectedReviewCycleId: number | null
  selectedReviewEmployeeId: number | null
}

export function PerformanceModule({
  apiBase,
  employees,
  onCreateCycle,
  onSaveManagerReview,
  onSaveSelfAssessment,
  onSelectedReviewCycleIdChange,
  onSelectedReviewEmployeeIdChange,
  reviewCycles,
  reviewEmployees,
  reviewSnapshot,
  selectedReviewCycleId,
  selectedReviewEmployeeId,
}: PerformanceModuleProps) {
  return (
    <SectionCard title="Employee Feedback" eyebrow="Module 4">
      <div className="section-stack" id="performance">
        <ModuleGuide
          items={[
            { label: "Step 1", title: "Create a review period", text: "Choose the review name, dates, and the employees included." },
            { label: "Step 2", title: "Collect feedback", text: "Save the employee review first, then add manager feedback." },
            { label: "Step 3", title: "Download the final review", text: "Use the auto-written summary and export the PDF when ready." },
          ]}
        />
        <div className="split-panel">
          <div className="panel-surface">
            <div className="panel-heading">
              <h3>Review periods</h3>
              <span className="subtle">Create a review period and pick the employees included in it.</span>
            </div>
            <div className="stack-list">
              {reviewCycles.map((cycle) => (
                <button
                  key={cycle.id}
                  type="button"
                  className={`select-card ${selectedReviewCycleId === cycle.id ? "is-active" : ""}`}
                  onClick={() => onSelectedReviewCycleIdChange(cycle.id)}
                >
                  <strong>{cycle.period_label}</strong>
                  <span>
                    {cycle.start_date} to {cycle.end_date}
                  </span>
                  <small>{cycle.employee_ids.length} employees</small>
                </button>
              ))}
            </div>
            <hr />
            <form
              className="form-grid"
              onSubmit={(event) => {
                event.preventDefault()
                onCreateCycle(new FormData(event.currentTarget), () => event.currentTarget.reset())
              }}
            >
              <input name="period_label" placeholder="Review name" required />
              <input name="start_date" type="date" required />
              <input name="end_date" type="date" required />
              <input name="employee_ids" placeholder="Employee IDs, comma separated" required />
              <button type="submit">Create review period</button>
            </form>
          </div>

          <div className="panel-surface">
            <div className="panel-heading">
              <h3>Choose employee</h3>
              <span className="subtle">Pick an employee and download the final PDF when ready.</span>
            </div>
            <select
              value={selectedReviewEmployeeId ?? ""}
              onChange={(event) => onSelectedReviewEmployeeIdChange(Number(event.target.value))}
            >
              {reviewEmployees.map((employee) => (
                <option key={employee.id} value={employee.id}>
                  {employee.name}
                </option>
              ))}
            </select>
            {selectedReviewCycleId && selectedReviewEmployeeId ? (
              <a className="button-link" href={`${apiBase}/performance/reviews/${selectedReviewCycleId}/${selectedReviewEmployeeId}/export`}>
                Download review PDF
              </a>
            ) : null}

            <div className="review-summary">
              <h4>Auto-written summary</h4>
              <p>{reviewSnapshot?.manager_review?.ai_summary ?? "Save employee and manager feedback to generate the summary."}</p>
              <div className="badge-row">
                {(reviewSnapshot?.manager_review?.mismatches ?? []).map((item) => (
                  <span key={item} className="badge badge--warning">
                    Rating difference
                  </span>
                ))}
              </div>
              <h4>Suggested next steps</h4>
              <ul className="clean-list">
                {(reviewSnapshot?.manager_review?.development_actions ?? []).map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            </div>
          </div>
        </div>

        <div className="split-panel">
          <div className="panel-surface">
            <div className="panel-heading">
              <h3>Employee self review</h3>
              <span className="subtle">The employee explains what went well, what was hard, and the next goals.</span>
            </div>
            <form
              className="form-grid"
              onSubmit={(event) => {
                event.preventDefault()
                onSaveSelfAssessment(new FormData(event.currentTarget))
              }}
            >
              <textarea name="achievements" placeholder="What went well?" required />
              <textarea name="challenges" placeholder="What was difficult?" required />
              <textarea name="goals" placeholder="Goals for the next period" required />
              <select name="self_rating" defaultValue="4">
                {[1, 2, 3, 4, 5].map((value) => (
                  <option key={value} value={value}>
                    Employee rating: {value}
                  </option>
                ))}
              </select>
              <button type="submit">Save employee review</button>
            </form>
          </div>

          <div className="panel-surface">
            <div className="panel-heading">
              <h3>Manager feedback</h3>
              <span className="subtle">Rate the employee using simple work areas and add a short comment.</span>
            </div>
            <form
              className="form-grid"
              onSubmit={(event) => {
                event.preventDefault()
                onSaveManagerReview(new FormData(event.currentTarget))
              }}
            >
              <select name="manager_id" required defaultValue="">
                <option value="">Choose manager</option>
                {employees.map((employee) => (
                  <option key={employee.id} value={employee.id}>
                    {employee.name}
                  </option>
                ))}
              </select>
              {REVIEW_FIELDS.map((field) => (
                <select key={field.name} name={field.name} defaultValue="4">
                  {[1, 2, 3, 4, 5].map((value) => (
                    <option key={value} value={value}>
                      {field.label}: {value}
                    </option>
                  ))}
                </select>
              ))}
              <textarea name="manager_comments" placeholder="Manager comment" required />
              <button type="submit">Save manager feedback</button>
            </form>
          </div>
        </div>
      </div>
    </SectionCard>
  )
}
