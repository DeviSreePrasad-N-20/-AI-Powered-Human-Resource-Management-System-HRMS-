import { ModuleGuide } from "./ModuleGuide"
import { SectionCard } from "./SectionCard"
import type { Candidate, CandidateComparison, JobPosting } from "../types/hrms"

const STAGES = ["Applied", "Screening", "Interview", "Offer", "Hired", "Rejected"]

type RecruitmentModuleProps = {
  candidateComparison: CandidateComparison[]
  jobs: JobPosting[]
  onAddCandidate: (jobId: number | null, formData: FormData, reset: () => void) => void
  onCompare: () => void
  onCreateJob: (formData: FormData, reset: () => void) => void
  onSelectedCandidateIdsChange: (candidateIds: number[]) => void
  onSelectedJobIdChange: (jobId: number) => void
  onUpdateStage: (candidateId: number, stage: string) => void
  selectedCandidateIds: number[]
  selectedCandidates: Candidate[]
  selectedJob: JobPosting | null
  selectedJobId: number | null
}

export function RecruitmentModule({
  candidateComparison,
  jobs,
  onAddCandidate,
  onCompare,
  onCreateJob,
  onSelectedCandidateIdsChange,
  onSelectedJobIdChange,
  onUpdateStage,
  selectedCandidateIds,
  selectedCandidates,
  selectedJob,
  selectedJobId,
}: RecruitmentModuleProps) {
  return (
    <SectionCard title="Hiring and Candidates" eyebrow="Module 2">
      <div className="section-stack" id="recruitment">
        <ModuleGuide
          items={[
            { label: "Step 1", title: "Create a job", text: "Start by adding the role, work details, and the skills you want." },
            { label: "Step 2", title: "Add candidates", text: "Upload resumes and let the system show strengths, gaps, and fit score." },
            { label: "Step 3", title: "Compare and move forward", text: "Pick the best candidates and move them to the next hiring step." },
          ]}
        />
        <div className="split-panel">
          <div className="panel-surface">
            <div className="panel-heading">
              <h3>Open jobs</h3>
              <span className="subtle">Create a role and choose it to see the candidates for that job.</span>
            </div>
            <div className="stack-list">
              {jobs.map((job) => (
                <button
                  key={job.id}
                  className={`select-card ${selectedJobId === job.id ? "is-active" : ""}`}
                  type="button"
                  onClick={() => onSelectedJobIdChange(job.id)}
                >
                  <strong>{job.role}</strong>
                  <span>{job.experience_level}</span>
                  <small>{job.required_skills.join(", ")}</small>
                </button>
              ))}
            </div>
            <hr />
            <form
              className="form-grid"
              onSubmit={(event) => {
                event.preventDefault()
                onCreateJob(new FormData(event.currentTarget), () => event.currentTarget.reset())
              }}
            >
              <input name="role" placeholder="Job title" required />
              <input name="experience_level" placeholder="Experience needed" required />
              <textarea name="job_description" placeholder="What should this person do?" required />
              <input name="required_skills" placeholder="Main skills needed, comma separated" required />
              <button type="submit">Create job</button>
            </form>
          </div>

          <div className="panel-surface">
            <div className="panel-heading">
              <h3>{selectedJob?.role ?? "Candidates"}</h3>
              <span className="subtle">{selectedJob?.job_description ?? "Choose a job to add and review candidates."}</span>
            </div>
            <form
              className="form-grid"
              onSubmit={(event) => {
                event.preventDefault()
                onAddCandidate(selectedJobId, new FormData(event.currentTarget), () => event.currentTarget.reset())
              }}
            >
              <input name="name" placeholder="Candidate name" required />
              <input name="email" type="email" placeholder="Candidate email" />
              <input name="skills" placeholder="Candidate skills, comma separated" />
              <input name="file" type="file" accept=".pdf,.txt,.md" required />
              <button type="submit">Add candidate</button>
            </form>
          </div>
        </div>

        <div className="panel-surface">
          <div className="panel-heading">
            <h3>Compare candidates</h3>
            <button type="button" onClick={onCompare}>
              Compare selected
            </button>
          </div>
          <div className="candidate-grid">
            {selectedCandidates.map((candidate) => (
              <article key={candidate.id} className="candidate-card">
                <label className="checkbox-row">
                  <input
                    type="checkbox"
                    checked={selectedCandidateIds.includes(candidate.id)}
                    onChange={(event) => {
                      onSelectedCandidateIdsChange(
                        event.target.checked
                          ? [...selectedCandidateIds, candidate.id]
                          : selectedCandidateIds.filter((id) => id !== candidate.id),
                      )
                    }}
                  />
                  <strong>{candidate.name}</strong>
                </label>
                <p className="score">{candidate.match_percent}% fit for this job</p>
                <p>{candidate.match_reasoning}</p>
                <div className="badge-row">
                  {candidate.strengths.map((strength) => (
                    <span key={strength} className="badge badge--success">
                      Strong in: {strength}
                    </span>
                  ))}
                  {candidate.gaps.map((gap) => (
                    <span key={gap} className="badge badge--warning">
                      Needs: {gap}
                    </span>
                  ))}
                </div>
                <select value={candidate.stage} onChange={(event) => onUpdateStage(candidate.id, event.target.value)}>
                  {STAGES.map((stage) => (
                    <option key={stage} value={stage}>
                      {stage}
                    </option>
                  ))}
                </select>
                <details>
                  <summary>Suggested interview questions</summary>
                  <ul className="clean-list">
                    {candidate.interview_questions.map((question) => (
                      <li key={question}>{question}</li>
                    ))}
                  </ul>
                </details>
              </article>
            ))}
          </div>

          {candidateComparison.length > 0 ? (
            <div className="comparison-grid">
              {candidateComparison.map((candidate) => (
                <article key={candidate.candidate_id} className="comparison-card">
                  <strong>{candidate.candidate_name}</strong>
                  <span>{candidate.match_percent}% fit</span>
                  <p>{candidate.recommendation}</p>
                </article>
              ))}
            </div>
          ) : null}
        </div>
      </div>
    </SectionCard>
  )
}
