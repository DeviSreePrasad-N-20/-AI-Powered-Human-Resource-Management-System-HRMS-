type ModuleGuideProps = {
  items: Array<{
    label: string
    title: string
    text: string
  }>
}

export function ModuleGuide({ items }: ModuleGuideProps) {
  return (
    <div className="module-guide">
      {items.map((item) => (
        <article key={item.title} className="guide-card">
          <span className="guide-card__label">{item.label}</span>
          <strong>{item.title}</strong>
          <p>{item.text}</p>
        </article>
      ))}
    </div>
  )
}
