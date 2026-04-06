export function formatDate(value?: string | null) {
  if (!value) {
    return 'NA'
  }

  return new Date(value).toLocaleDateString()
}

export function slugList(value: FormDataEntryValue | null) {
  if (typeof value !== 'string') {
    return []
  }

  return value
    .split(',')
    .map((item) => item.trim())
    .filter(Boolean)
}

export function parseChecklist(value: string) {
  return value
    .split('\n')
    .map((line) => line.trim())
    .filter(Boolean)
    .map((line) => {
      const [title, due, assignee] = line.split('|').map((part) => part.trim())
      return {
        title: title || 'Checklist item',
        due_offset_days: Number(due || '0'),
        assignee: assignee || 'HR',
      }
    })
}
