import type { ReactNode } from 'react'

interface BadgeProps {
  variant: 'success' | 'error' | 'warning' | 'default' | 'info'
  children: ReactNode
}

const variantClasses: Record<BadgeProps['variant'], string> = {
  success: 'bg-mint-soft text-mint',
  error: 'bg-danger-soft text-danger',
  warning: 'bg-amber-soft text-amber',
  default: 'bg-transparent text-text-dim border border-border',
  info: 'bg-[rgba(96,165,250,0.15)] text-[#60a5fa]',
}

export default function Badge({ variant, children }: BadgeProps) {
  return (
    <span
      className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-semibold uppercase ${variantClasses[variant]}`}
    >
      {children}
    </span>
  )
}
