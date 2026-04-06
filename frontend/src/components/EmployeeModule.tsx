import { ModuleGuide } from "./ModuleGuide"
import { OrgChartTree } from "./OrgChartTree"
import { SectionCard } from "./SectionCard"
import type { Employee, OrgChartNode } from "../types/hrms"

type EmployeeModuleProps = {
  apiBase: string
  employeeSearch: string
  employees: Employee[]
  orgChart: OrgChartNode[]
  onCreateEmployee: (formData: FormData, reset: () => void) => void
  onSearchChange: (value: string) => void
  onUploadDocument: (formData: FormData, reset: () => void) => void
  visibleEmployees: Employee[]
}

export function EmployeeModule({
  apiBase,
  employeeSearch,
  employees,
  orgChart,
  onCreateEmployee,
  onSearchChange,
  onUploadDocument,
  visibleEmployees,
}: EmployeeModuleProps) {
  function employeeName(employeeId: number | null) {
    return employees.find((employee) => employee.id === employeeId)?.name ?? "Unassigned"
  }

  return (
    <SectionCard
      title="Employee List"
      eyebrow="Module 1"
      aside={<a href={`${apiBase}/employees/export/csv`}>Export CSV</a>}
    >
      <div className="section-stack" id="employees">
        <ModuleGuide
          items={[
            { label: "Step 1", title: "Find people fast", text: "Use search to quickly find anyone by name, skill, or team." },
            { label: "Step 2", title: "Add or update details", text: "Create an employee profile and upload important files in one place." },
            { label: "Step 3", title: "See the team structure", text: "Open the team structure section to understand reporting lines." },
          ]}
        />
        <div className="split-panel">
          <div className="panel-surface">
            <div className="panel-heading">
              <h3>Employee directory</h3>
              <input
                value={employeeSearch}
                onChange={(event) => onSearchChange(event.target.value)}
                placeholder="Search by name, skill, department..."
              />
            </div>
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Name</th>
                    <th>Role</th>
                    <th>Department</th>
                    <th>Manager</th>
                    <th>Alerts</th>
                  </tr>
                </thead>
                <tbody>
                  {visibleEmployees.map((employee) => (
                    <tr key={employee.id}>
                      <td>
                        <strong>{employee.name}</strong>
                        <span className="subtle">{employee.email}</span>
                      </td>
                      <td>{employee.designation}</td>
                      <td>{employee.department}</td>
                      <td>{employeeName(employee.manager_id)}</td>
                      <td>
                        <div className="badge-row">
                          {employee.flags.length ? (
                            employee.flags.map((flag) => (
                              <span key={flag} className="badge">
                                {flag}
                              </span>
                            ))
                          ) : (
                            <span className="subtle">No alerts</span>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          <div className="panel-surface">
            <div className="panel-heading">
              <h3>Add employee</h3>
              <span className="subtle">The profile summary and alerts are created automatically.</span>
            </div>
            <form
              className="form-grid"
              onSubmit={(event) => {
                event.preventDefault()
                onCreateEmployee(new FormData(event.currentTarget), () => event.currentTarget.reset())
              }}
            >
              <input name="name" placeholder="Full name" required />
              <input name="designation" placeholder="Job title" required />
              <input name="department" placeholder="Team or department" required />
              <input name="joining_date" type="date" required />
              <select name="manager_id" defaultValue="">
                <option value="">Choose manager</option>
                {employees.map((employee) => (
                  <option key={employee.id} value={employee.id}>
                    {employee.name}
                  </option>
                ))}
              </select>
              <input name="contact" placeholder="Contact" required />
              <input name="email" type="email" placeholder="Work email" required />
              <input name="skills" placeholder="Skills, comma separated" />
              <button type="submit">Add employee</button>
            </form>
            <hr />
            <div className="panel-heading">
              <h3>Upload employee file</h3>
            </div>
            <form
              className="form-grid"
              onSubmit={(event) => {
                event.preventDefault()
                onUploadDocument(new FormData(event.currentTarget), () => event.currentTarget.reset())
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
              <input name="title" placeholder="Document title" required />
              <input name="file" type="file" required />
              <button type="submit">Upload file</button>
            </form>
          </div>
        </div>

        <div className="panel-surface">
            <div className="panel-heading">
            <h3>Team structure</h3>
            <span className="subtle">See who reports to whom.</span>
          </div>
          <OrgChartTree nodes={orgChart} />
        </div>
      </div>
    </SectionCard>
  )
}
