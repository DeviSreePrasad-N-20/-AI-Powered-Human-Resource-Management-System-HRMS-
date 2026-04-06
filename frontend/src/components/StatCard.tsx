type StatCardProps = {
  label: string
  value: string | number
  accent?: string
}

export function StatCard({ label, value, accent }: StatCardProps) {
  return (
    <article className="stat-card">
      <p>{label}</p>
      <strong style={accent ? { color: accent } : undefined}>{value}</strong>
    </article>
  )
}
