import { useState } from 'react'
import type { GalleryPhoto } from '../../types'
import InlineImageEditor from '../formatting/InlineImageEditor'

interface ImagesViewProps {
  runId: string
  finalOutput: Record<string, unknown> | null | undefined
  headlineImagePath?: string | null
  headlineImagePrompt?: string | null
}

interface ArtifactImageItem {
  collection: string
  index: number
  label: string
  imagePrompt?: string | null
  localImagePath?: string | null
}

const TIER_COLORS: Record<string, string> = {
  atmospheric: 'bg-blue-900/40 text-blue-300 border-blue-700/40',
  diegetic: 'bg-emerald-900/40 text-emerald-300 border-emerald-700/40',
  document: 'bg-amber-900/40 text-amber-300 border-amber-700/40',
}

function ArtifactImageCard({
  runId,
  item,
  onUpdate,
}: {
  runId: string
  item: ArtifactImageItem
  onUpdate: (index: number, newPath: string, newPrompt: string) => void
}) {
  const [localPath, setLocalPath] = useState(item.localImagePath)
  const [prompt, setPrompt] = useState(item.imagePrompt)

  if (!prompt) return null

  const srcUrl = localPath?.startsWith('images/')
    ? `/api/runs/${runId}/${localPath}`
    : localPath

  return (
    <div className="bg-surface rounded-lg border border-border overflow-hidden">
      {srcUrl && (
        <img
          src={srcUrl}
          alt={prompt}
          className="w-full h-48 object-cover"
        />
      )}
      <div className="p-3 flex flex-col gap-2">
        <span className="text-xs text-text-dim font-semibold uppercase tracking-wider">
          {item.label}
        </span>
        <InlineImageEditor
          runId={runId}
          eventType={item.collection.replace(/s$/, '').replace('_post', '_post')}
          index={item.index}
          initialPrompt={prompt ?? undefined}
          initialImageUrl={localPath ?? undefined}
          hideImage={true}
          onImageUpdated={(newPath, newPrompt) => {
            setLocalPath(newPath)
            setPrompt(newPrompt)
            onUpdate(item.index, newPath, newPrompt)
          }}
        />
      </div>
    </div>
  )
}

function GalleryPhotoCard({
  runId,
  photo,
  globalIndex,
  onUpdate,
}: {
  runId: string
  photo: GalleryPhoto
  globalIndex: number
  onUpdate: (index: number, newPath: string, newPrompt: string) => void
}) {
  const [localPath, setLocalPath] = useState(photo.local_image_path)
  const [prompt, setPrompt] = useState(photo.image_prompt)

  const srcUrl = localPath?.startsWith('images/')
    ? `/api/runs/${runId}/${localPath}`
    : localPath

  const tierClass = TIER_COLORS[photo.tier] ?? 'bg-surface-raised text-text-dim border-border'

  return (
    <div className="bg-surface rounded-lg border border-border overflow-hidden flex flex-col">
      {srcUrl ? (
        <img src={srcUrl} alt={photo.subject} className="w-full h-48 object-cover" />
      ) : (
        <div className="w-full h-48 bg-surface-raised flex items-center justify-center text-text-dim text-xs">
          No image yet
        </div>
      )}
      <div className="p-3 flex flex-col gap-2 flex-1">
        <div className="flex items-center gap-2">
          <span className={`text-[10px] font-bold uppercase px-1.5 py-0.5 rounded border ${tierClass}`}>
            {photo.tier}
          </span>
          <span className="text-xs text-text font-semibold truncate">{photo.subject}</span>
        </div>
        {photo.caption && (
          <p className="text-xs text-text-dim italic">{photo.caption}</p>
        )}
        <InlineImageEditor
          runId={runId}
          eventType="gallery"
          index={globalIndex}
          initialPrompt={prompt ?? undefined}
          initialImageUrl={localPath ?? undefined}
          hideImage={true}
          onImageUpdated={(newPath, newPrompt) => {
            setLocalPath(newPath)
            setPrompt(newPrompt)
            onUpdate(globalIndex, newPath, newPrompt)
          }}
        />
      </div>
    </div>
  )
}

export default function ImagesView({ runId, finalOutput, headlineImagePath, headlineImagePrompt }: ImagesViewProps) {
  const [headlinePath, setHeadlinePath] = useState(headlineImagePath)
  const [headlinePrompt, setHeadlinePrompt] = useState(headlineImagePrompt)

  if (!finalOutput) {
    return (
      <div className="p-8 text-center text-text-dim text-sm">
        No story output available yet.
      </div>
    )
  }

  const gallery = (finalOutput.photo_gallery as GalleryPhoto[] | undefined) ?? []

  // Collect per-artifact images
  const artifactImages: ArtifactImageItem[] = []
  const COLLECTIONS: { key: string; label: string; eventType: string }[] = [
    { key: 'social_posts', label: 'Social Post', eventType: 'social_post' },
    { key: 'journals', label: 'Journal', eventType: 'journal' },
    { key: 'emails', label: 'Email', eventType: 'email' },
    { key: 'chats', label: 'Chat', eventType: 'chat' },
  ]
  for (const { key, label } of COLLECTIONS) {
    const items = (finalOutput[key] as Record<string, unknown>[] | undefined) ?? []
    items.forEach((item, i) => {
      if (item.image_prompt) {
        artifactImages.push({
          collection: key,
          index: i,
          label: `${label} #${i + 1}`,
          imagePrompt: item.image_prompt as string,
          localImagePath: item.local_image_path as string | null,
        })
      }
    })
  }

  const headlineSrc = headlinePath?.startsWith('images/')
    ? `/api/runs/${runId}/${headlinePath}`
    : headlinePath

  const hasAnyImages = headlinePrompt || gallery.length > 0 || artifactImages.length > 0

  if (!hasAnyImages) {
    return (
      <div className="p-8 text-center text-text-dim text-sm">
        No images generated yet. Run the pipeline to generate images.
      </div>
    )
  }

  return (
    <div className="p-4 flex flex-col gap-8">

      {/* Headline */}
      {headlinePrompt && (
        <section>
          <h3 className="text-sm font-semibold text-text-dim uppercase tracking-wider mb-3">Headline</h3>
          <div className="bg-surface rounded-lg border border-border overflow-hidden">
            {headlineSrc && (
              <img src={headlineSrc} alt="Headline" className="w-full max-h-[400px] object-cover" />
            )}
            <div className="p-4">
              <InlineImageEditor
                runId={runId}
                eventType="headline"
                index={0}
                initialPrompt={headlinePrompt}
                initialImageUrl={headlinePath ?? undefined}
                onImageUpdated={(newPath, newPrompt) => {
                  setHeadlinePath(newPath)
                  setHeadlinePrompt(newPrompt)
                }}
              />
            </div>
          </div>
        </section>
      )}

      {/* Gallery */}
      {gallery.length > 0 && (
        <section>
          <h3 className="text-sm font-semibold text-text-dim uppercase tracking-wider mb-3">
            Gallery ({gallery.length} photos)
          </h3>
          <div className="grid grid-cols-2 gap-3 lg:grid-cols-3">
            {gallery.map((photo, i) => (
              <GalleryPhotoCard
                key={photo.photo_id || i}
                runId={runId}
                photo={photo}
                globalIndex={i}
                onUpdate={() => {}}
              />
            ))}
          </div>
        </section>
      )}

      {/* Artifact images */}
      {artifactImages.length > 0 && (
        <section>
          <h3 className="text-sm font-semibold text-text-dim uppercase tracking-wider mb-3">
            Artifact Images ({artifactImages.length})
          </h3>
          <div className="grid grid-cols-2 gap-3 lg:grid-cols-3">
            {artifactImages.map((item) => (
              <ArtifactImageCard
                key={`${item.collection}_${item.index}`}
                runId={runId}
                item={item}
                onUpdate={() => {}}
              />
            ))}
          </div>
        </section>
      )}
    </div>
  )
}
