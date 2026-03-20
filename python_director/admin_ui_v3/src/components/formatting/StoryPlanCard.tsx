interface StoryPlanCardProps {
  data: Record<string, unknown>
}

export default function StoryPlanCard({ data }: StoryPlanCardProps) {
  const title = data.title as string | undefined
  const coreConflict = (data.core_conflict || data.conflict) as string | undefined
  const characters = (data.characters || []) as Record<string, unknown>[]
  const acts = (data.acts || data.act_summaries || []) as Record<string, unknown>[]

  return (
    <div className="glass-panel p-4 flex flex-col gap-4">
      {/* Title */}
      {title && (
        <h3 className="text-lg font-semibold text-text">{title}</h3>
      )}

      {/* Core conflict */}
      {coreConflict && (
        <div>
          <span className="text-text-dim text-xs font-semibold uppercase tracking-wide block mb-1">
            Core Conflict
          </span>
          <p className="text-sm text-text">{coreConflict}</p>
        </div>
      )}

      {/* Characters */}
      {characters.length > 0 && (
        <div>
          <span className="text-text-dim text-xs font-semibold uppercase tracking-wide block mb-2">
            Characters
          </span>
          <div className="grid grid-cols-1 gap-2">
            {characters.map((char, i) => (
              <div
                key={i}
                className="bg-[#111] border border-border rounded-lg p-3"
              >
                <span className="text-sm font-semibold text-mint block">
                  {String(char.name || `Character ${i + 1}`)}
                </span>
                {char.background != null && (
                  <p className="text-xs text-text-dim mt-1">
                    {String(char.background)}
                  </p>
                )}
                {char.arc != null && (
                  <p className="text-xs text-amber mt-1">
                    Arc: {String(char.arc)}
                  </p>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Acts */}
      {acts.length > 0 && (
        <div>
          <span className="text-text-dim text-xs font-semibold uppercase tracking-wide block mb-2">
            Act Summaries
          </span>
          <div className="flex flex-col gap-2">
            {acts.map((act, i) => (
              <div
                key={i}
                className="bg-[#111] border border-border rounded-lg p-3"
              >
                <span className="text-sm font-semibold text-text block mb-1">
                  {String(act.title || act.name || `Act ${i + 1}`)}
                </span>
                <p className="text-sm text-text-dim">
                  {String(act.summary || act.description || '')}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
