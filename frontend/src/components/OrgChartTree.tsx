import type { OrgChartNode } from '../types/hrms'

type OrgChartTreeProps = {
  nodes: OrgChartNode[]
}

function Branch({ node }: { node: OrgChartNode }) {
  return (
    <li className="org-node">
      <div className="org-node__card">
        <strong>{node.name}</strong>
        <span>{node.designation}</span>
        <small>{node.department}</small>
      </div>
      {node.reports.length > 0 ? (
        <ul className="org-children">
          {node.reports.map((report) => (
            <Branch key={report.id} node={report} />
          ))}
        </ul>
      ) : null}
    </li>
  )
}

export function OrgChartTree({ nodes }: OrgChartTreeProps) {
  if (!nodes.length) {
    return <p className="muted">No org chart data yet.</p>
  }

  return (
    <ul className="org-tree">
      {nodes.map((node) => (
        <Branch key={node.id} node={node} />
      ))}
    </ul>
  )
}
