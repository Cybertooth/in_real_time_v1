import { useEffect, useState } from 'react'
import { useStore } from '../store'
import type { Story } from '../types'
import Badge from '../components/shared/Badge'
import ConfirmDialog from '../components/shared/ConfirmDialog'

export default function DeploymentsView() {
  const stories = useStore((s) => s.stories)
  const loadStories = useStore((s) => s.loadStories)
  const undeployStory = useStore((s) => s.undeployStory)

  const [deleteTarget, setDeleteTarget] = useState<Story | null>(null)

  useEffect(() => {
    loadStories()
  }, [loadStories])

  const formatTime = (ts: string) => {
    try {
      return new Date(ts).toLocaleString()
    } catch {
      return ts
    }
  }

  const handleDelete = async () => {
    if (!deleteTarget) return
    const id = deleteTarget.id
    setDeleteTarget(null)
    await undeployStory(id)
  }

  return (
    <div className="p-8 max-w-6xl mx-auto">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold text-text mb-2">Deployments</h1>
          <p className="text-text-dim text-sm">
            Manage stories uploaded to Firebase. Undeploying a story removes it from Firestore and deletes all associated assets from storage.
          </p>
        </div>
        <button
          onClick={() => loadStories()}
          className="px-4 py-2 rounded-xl text-sm font-semibold cursor-pointer bg-surface border border-border text-text hover:bg-surface-raised transition-colors"
        >
          Refresh
        </button>
      </div>

      {stories.length === 0 ? (
        <div className="py-12 flex flex-col items-center justify-center border border-dashed border-border rounded-3xl bg-[rgba(255,255,255,0.02)]">
          <p className="text-text-dim">No stories found in Firestore.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {stories.map((story) => (
            <div key={story.id} className="group relative bg-surface border border-border rounded-3xl overflow-hidden flex flex-col hover:border-mint/30 transition-all duration-300">
              {/* Thumbnail */}
              <div className="aspect-video bg-surface-raised relative overflow-hidden flex items-center justify-center">
                {story.headlineImageUrl ? (
                  <img
                    src={story.headlineImageUrl}
                    alt={story.title}
                    className="w-full h-full object-cover"
                    onError={(e) => {
                      (e.target as HTMLImageElement).style.display = 'none'
                    }}
                  />
                ) : (
                  <div className="text-text-dim text-4xl opacity-20 italic">No Image</div>
                )}
                <div className="absolute top-3 left-3 flex gap-2">
                   <Badge variant="info">{story.storyMode}</Badge>
                </div>
              </div>

              {/* Content */}
              <div className="p-5 flex-1 flex flex-col gap-3">
                <div>
                  <h3 className="text-base font-semibold text-text mb-1 truncate" title={story.title}>
                    {story.title}
                  </h3>
                  <p className="text-xs text-text-dim font-mono">{story.id}</p>
                </div>

                <div className="flex flex-col gap-1 text-xs text-text-dim mt-auto">
                  <div className="flex justify-between items-center">
                    <span>Deployed</span>
                    <span className="text-text">{formatTime(story.createdAt)}</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span>Duration</span>
                    <span className="text-text">{story.storyDurationMinutes} min</span>
                  </div>
                </div>

                <button
                  onClick={() => setDeleteTarget(story)}
                  className="mt-2 w-full px-4 py-2 rounded-xl text-xs font-semibold cursor-pointer bg-danger-soft text-danger border border-danger/30 hover:brightness-110 transition-colors"
                >
                  Undeploy Story
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Delete confirmation */}
      <ConfirmDialog
        open={deleteTarget !== null}
        title="Undeploy Story?"
        description={`"${deleteTarget?.title}" (${deleteTarget?.id}) will be permanently removed from Firestore and Google Cloud Storage. The story will no longer be visible in the mobile app.`}
        confirmLabel="Undeploy"
        confirmVariant="danger"
        onConfirm={handleDelete}
        onCancel={() => setDeleteTarget(null)}
      />
    </div>
  )
}
