interface StatusDotProps {
  status: string
}

export default function StatusDot({ status }: StatusDotProps) {
  const base = 'w-2 h-2 rounded-full flex-shrink-0'

  switch (status) {
    case 'succeeded':
      return (
        <span
          className={`${base} bg-mint`}
          style={{ boxShadow: '0 0 6px rgba(15, 230, 176, 0.6)' }}
        />
      )
    case 'running':
      return (
        <span
          className={`${base} bg-amber animate-pulse-dot`}
          style={{ boxShadow: '0 0 6px rgba(255, 183, 77, 0.6)' }}
        />
      )
    case 'failed':
      return (
        <span
          className={`${base} bg-danger`}
          style={{ boxShadow: '0 0 6px rgba(255, 82, 82, 0.6)' }}
        />
      )
    case 'skipped':
      return <span className={`${base} bg-text-dim opacity-50`} />
    case 'pending':
    case 'idle':
    default:
      return <span className={`${base} bg-text-dim`} />
  }
}
