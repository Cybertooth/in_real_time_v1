import { useStore } from '../../store'

export default function Toast() {
  const toast = useStore((s) => s.toast)

  return (
    <div
      className={`fixed bottom-6 left-1/2 -translate-x-1/2 z-50 transition-all duration-300 ${
        toast ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4 pointer-events-none'
      }`}
    >
      {toast && (
        <div
          className={`px-5 py-2.5 rounded-full text-sm font-medium backdrop-blur-xl border ${
            toast.isError
              ? 'bg-danger-soft text-danger border-danger/30'
              : 'bg-mint-soft text-mint border-mint/30'
          }`}
        >
          {toast.message}
        </div>
      )}
    </div>
  )
}
