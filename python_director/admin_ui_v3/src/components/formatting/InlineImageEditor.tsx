import { useState } from 'react'
import { regenerateImage } from '../../api'

interface InlineImageEditorProps {
  runId: string
  eventType: string
  index: number
  initialPrompt?: string
  initialImageUrl?: string
  hideImage?: boolean
  onImageUpdated?: (newImagePath: string, newPrompt: string) => void
}

export default function InlineImageEditor({
  runId,
  eventType,
  index,
  initialPrompt,
  initialImageUrl,
  hideImage = false,
  onImageUpdated,
}: InlineImageEditorProps) {
  const [prompt, setPrompt] = useState(initialPrompt || '')
  const [currentImageUrl, setCurrentImageUrl] = useState(initialImageUrl)
  const [isRegenerating, setIsRegenerating] = useState(false)
  const [error, setError] = useState<string | null>(null)

  if (!initialPrompt) return null

  const handleRegenerate = async () => {
    if (!prompt.trim()) return
    try {
      setIsRegenerating(true)
      setError(null)
      const res = await regenerateImage(runId, eventType, index, prompt)
      if (res.local_image_path) {
        setCurrentImageUrl(res.local_image_path)
        if (onImageUpdated) onImageUpdated(res.local_image_path, prompt)
      }
    } catch (err: any) {
      setError(err.message || 'Failed to regenerate image')
    } finally {
      setIsRegenerating(false)
    }
  }

  // Construct src url. If not uploaded to firebase yet, it's local.
  const isLocalPath = currentImageUrl?.startsWith('images/')
  const srcUrl = isLocalPath ? `/api/runs/${runId}/${currentImageUrl}` : currentImageUrl

  return (
    <div className="mt-2 border-t border-border pt-3 flex flex-col gap-3">
      {!hideImage && srcUrl && (
        <img
          src={srcUrl}
          alt={prompt}
          className="w-full h-auto max-h-[300px] object-cover rounded-md border border-border"
        />
      )}
      <div className="flex flex-col gap-1">
        <label className="text-xs font-semibold text-text-dim uppercase tracking-wider">
          Image Prompt
        </label>
        <textarea
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          className="w-full bg-surface border border-border rounded p-2 text-sm text-text focus:outline-none focus:border-primary resize-y min-h-[60px]"
          placeholder="Describe the image..."
        />
      </div>
      {error && <div className="text-red-500 text-xs">{error}</div>}
      <div className="flex justify-end">
        <button
          onClick={handleRegenerate}
          disabled={isRegenerating}
          className="px-3 py-1.5 bg-[#222] hover:bg-[#333] border border-border rounded text-xs text-text transition-colors disabled:opacity-50"
        >
          {isRegenerating ? 'Generating...' : 'Regenerate Image'}
        </button>
      </div>
    </div>
  )
}
