import { SectionCard } from "./SectionCard"
import type { HrAnalytics, MonthlySummary } from "../types/hrms"

type AnalyticsSidebarProps = {
  analytics: HrAnalytics | null
  monthlySummary: MonthlySummary | null
  questionAnalytics: Array<{ question: string; count: number }>
  standalone?: boolean
}

export function AnalyticsSidebar({
  analytics,
  monthlySummary,
  questionAnalytics,
  standalone = false,
}: AnalyticsSidebarProps) {
  return (
    <aside className={standalone ? "analytics-page" : "content-side"} id="analytics">
      <SectionCard title="Company Insights" eyebrow="Module 6">
        <div className="section-stack">
          <div className="panel-surface">
            <div className="panel-heading">
              <h3>People in each department</h3>
              <span className="subtle">A quick view of how your team is distributed.</span>
            </div>
            <div className="bar-list">
              {Object.entries(analytics?.headcount_by_department ?? {}).map(([department, total]) => (
                <div key={department} className="bar-row">
                  <span>{department}</span>
                  <div>
                    <i style={{ width: `${Math.max(total * 18, 20)}px` }} />
                    <strong>{total}</strong>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="panel-surface">
            <div className="panel-heading">
              <h3>Main numbers</h3>
            </div>
            <div className="metric-stack">
              <div className="simple-row">
                <strong>People who left</strong>
                <span>{analytics?.attrition_rate ?? 0}%</span>
              </div>
              <div className="simple-row">
                <strong>Leave used</strong>
                <span>{analytics?.leave_utilisation_rate ?? 0}%</span>
              </div>
              <div className="simple-row">
                <strong>Jobs to fill</strong>
                <span>{analytics?.open_vs_filled_positions.open ?? 0}</span>
              </div>
              <div className="simple-row">
                <strong>Jobs filled</strong>
                <span>{analytics?.open_vs_filled_positions.filled ?? 0}</span>
              </div>
            </div>
          </div>

          <div className="panel-surface">
            <div className="panel-heading">
              <h3>Average time in the company</h3>
            </div>
            <div className="metric-stack">
              {Object.entries(analytics?.average_tenure_by_department ?? {}).map(([department, years]) => (
                <div key={department} className="simple-row">
                  <strong>{department}</strong>
                  <span>{years} years</span>
                </div>
              ))}
            </div>
          </div>

          <div className="panel-surface">
            <div className="panel-heading">
              <h3>Monthly summary</h3>
              <span className="subtle">A simple overview of highlights, risks, and next actions.</span>
            </div>
            <p>{monthlySummary?.summary ?? analytics?.ai_summary}</p>
            <h4>What looks good</h4>
            <ul className="clean-list">
              {(monthlySummary?.highlights ?? []).map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
            <h4>What needs attention</h4>
            <ul className="clean-list">
              {(monthlySummary?.risks ?? []).map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
            <h4>Next actions</h4>
            <ul className="clean-list">
              {(monthlySummary?.recommended_actions ?? []).map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          </div>

          <div className="panel-surface">
            <div className="panel-heading">
              <h3>Common new-joiner questions</h3>
            </div>
            <ul className="clean-list">
              {questionAnalytics.map((entry) => (
                <li key={entry.question}>
                  {entry.question} <span className="subtle">({entry.count})</span>
                </li>
              ))}
            </ul>
          </div>
        </div>
      </SectionCard>
    </aside>
  )
}
