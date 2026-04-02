import { useState, useEffect } from 'react'
import * as api from '../../api'
import type { StoryPackaging } from '../../types'
import Badge from '../shared/Badge'

const EMPTY_PACKAGING: StoryPackaging = {
  hook_line: '',
  promise_line: '',
  hero_artifact_type: '',
  hero_artifact_preview: null,
  tone_tags: [],
  audience_hook_type: '',
}

interface Props {
  runId: string
  onPackagingChange?: (packaging: StoryPackaging) => void
}

export default function StoryPackagingEditor({ runId, onPackagingChange }: Props) {
  const [packaging, setPackaging] = useState<StoryPackaging>(EMPTY_PACKAGING)
  const [loading, setLoading] = useState(true)
  const [generating, setGenerating] = useState(false)
  const [saving, setSaving] = useState(false)
  const [dirty, setDirty] = useState(false)
  const [toneInput, setToneInput] = useState('')

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    api.getPackaging(runId).then((p) => {
      if (cancelled) return
      setPackaging(p)
      onPackagingChange?.(p)
      setLoading(false)
    }).catch(() => {
      if (!cancelled) setLoading(false)
    })
    return () => { cancelled = true }
  }, [runId])

  const update = (patch: Partial<StoryPackaging>) => {
    const next = { ...packaging, ...patch }
    setPackaging(next)
    setDirty(true)
    onPackagingChange?.(next)
  }

  const handleGenerate = async () => {
    setGenerating(true)
    try {
      const p = await api.generatePackaging(runId)
      setPackaging(p)
      setDirty(false)
      onPackagingChange?.(p)
    } catch (err) {
      console.error('Failed to generate packaging', err)
    }
    setGenerating(false)
  }

  const handleSave = async () => {
    setSaving(true)
    try {
      const p = await api.updatePackaging(runId, packaging)
      setPackaging(p)
      setDirty(false)
      onPackagingChange?.(p)
    } catch (err) {
      console.error('Failed to save packaging', err)
    }
    setSaving(false)
  }

  const addToneTag = () => {
    const tag = toneInput.trim().toLowerCase()
    if (!tag || packaging.tone_tags.length >= 4 || packaging.tone_tags.includes(tag)) return
    update({ tone_tags: [...packaging.tone_tags, tag] })
    setToneInput('')
  }

  const removeToneTag = (tag: string) => {
    update({ tone_tags: packaging.tone_tags.filter((t) => t !== tag) })
  }

  if (loading) {
    return (
      <div className="py-4 text-center text-text-dim text-sm">Loading packaging...</div>
    )
  }

  const hasContent = packaging.hook_line || packaging.promise_line

  return (
    <div className="bg-surface border border-border rounded-2xl p-5 space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-text uppercase tracking-wider">
          Story Packaging
        </h3>
        <div className="flex gap-2">
          <button
            onClick={handleGenerate}
            disabled={generating}
            className="px-3 py-1.5 rounded-lg text-xs font-semibold cursor-pointer bg-mint/10 text-mint border border-mint/20 hover:bg-mint/20 transition-colors disabled:opacity-50"
          >
            {generating ? 'Generating...' : hasContent ? 'Regenerate' : 'Auto-Generate'}
          </button>
          {dirty && (
            <button
              onClick={handleSave}
              disabled={saving}
              className="px-3 py-1.5 rounded-lg text-xs font-semibold cursor-pointer bg-mint text-bg hover:brightness-110 transition-colors disabled:opacity-50"
            >
              {saving ? 'Saving...' : 'Save'}
            </button>
          )}
        </div>
      </div>

      {/* Hook Line */}
      <div>
        <label className="block text-xs text-text-dim mb-1">
          Hook Line <span className="text-text-dim/50">({packaging.hook_line.length}/140)</span>
        </label>
        <input
          type="text"
          value={packaging.hook_line}
          onChange={(e) => update({ hook_line: e.target.value.slice(0, 140) })}
          placeholder="One sentence that makes someone NEED to know what happens..."
          className="w-full px-3 py-2 rounded-lg bg-surface-raised border border-border text-text text-sm placeholder:text-text-dim/40 focus:outline-none focus:border-mint/40"
        />
      </div>

      {/* Promise Line */}
      <div>
        <label className="block text-xs text-text-dim mb-1">
          Promise Line <span className="text-text-dim/50">({packaging.promise_line.length}/140)</span>
        </label>
        <input
          type="text"
          value={packaging.promise_line}
          onChange={(e) => update({ promise_line: e.target.value.slice(0, 140) })}
          placeholder="What the reader will experience or discover..."
          className="w-full px-3 py-2 rounded-lg bg-surface-raised border border-border text-text text-sm placeholder:text-text-dim/40 focus:outline-none focus:border-mint/40"
        />
      </div>

      <div className="grid grid-cols-2 gap-4">
        {/* Hero Artifact Type */}
        <div>
          <label className="block text-xs text-text-dim mb-1">Hero Artifact Type</label>
          <select
            value={packaging.hero_artifact_type}
            onChange={(e) => update({ hero_artifact_type: e.target.value })}
            className="w-full px-3 py-2 rounded-lg bg-surface-raised border border-border text-text text-sm focus:outline-none focus:border-mint/40"
          >
            <option value="">Select...</option>
            <option value="chat">Chat</option>
            <option value="journal">Journal</option>
            <option value="email">Email</option>
            <option value="voice_note">Voice Note</option>
            <option value="social_post">Social Post</option>
            <option value="receipt">Receipt</option>
            <option value="phone_call">Phone Call</option>
          </select>
        </div>

        {/* Audience Hook Type */}
        <div>
          <label className="block text-xs text-text-dim mb-1">Audience Hook Type</label>
          <input
            type="text"
            value={packaging.audience_hook_type}
            onChange={(e) => update({ audience_hook_type: e.target.value })}
            placeholder="e.g. twisted-romance"
            className="w-full px-3 py-2 rounded-lg bg-surface-raised border border-border text-text text-sm placeholder:text-text-dim/40 focus:outline-none focus:border-mint/40"
          />
        </div>
      </div>

      {/* Hero Artifact Preview */}
      <div>
        <label className="block text-xs text-text-dim mb-1">Hero Artifact Preview</label>
        <div className="grid grid-cols-2 gap-2">
          <input
            type="text"
            value={packaging.hero_artifact_preview?.title ?? ''}
            onChange={(e) =>
              update({
                hero_artifact_preview: {
                  title: e.target.value,
                  body: packaging.hero_artifact_preview?.body ?? '',
                },
              })
            }
            placeholder="Preview title"
            className="px-3 py-2 rounded-lg bg-surface-raised border border-border text-text text-sm placeholder:text-text-dim/40 focus:outline-none focus:border-mint/40"
          />
          <input
            type="text"
            value={packaging.hero_artifact_preview?.body ?? ''}
            onChange={(e) =>
              update({
                hero_artifact_preview: {
                  title: packaging.hero_artifact_preview?.title ?? '',
                  body: e.target.value,
                },
              })
            }
            placeholder="Preview body (punchy line)"
            className="px-3 py-2 rounded-lg bg-surface-raised border border-border text-text text-sm placeholder:text-text-dim/40 focus:outline-none focus:border-mint/40"
          />
        </div>
      </div>

      {/* Tone Tags */}
      <div>
        <label className="block text-xs text-text-dim mb-1">Tone Tags (max 4)</label>
        <div className="flex flex-wrap gap-1.5 mb-2">
          {packaging.tone_tags.map((tag) => (
            <Badge key={tag} variant="info">
              {tag}
              <button
                onClick={() => removeToneTag(tag)}
                className="ml-1 cursor-pointer text-inherit opacity-60 hover:opacity-100"
              >
                &times;
              </button>
            </Badge>
          ))}
        </div>
        {packaging.tone_tags.length < 4 && (
          <div className="flex gap-2">
            <input
              type="text"
              value={toneInput}
              onChange={(e) => setToneInput(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && addToneTag()}
              placeholder="Add tag..."
              className="flex-1 px-3 py-1.5 rounded-lg bg-surface-raised border border-border text-text text-xs placeholder:text-text-dim/40 focus:outline-none focus:border-mint/40"
            />
            <button
              onClick={addToneTag}
              className="px-3 py-1.5 rounded-lg text-xs font-semibold cursor-pointer bg-surface-raised border border-border text-text-dim hover:text-text transition-colors"
            >
              Add
            </button>
          </div>
        )}
      </div>

      {/* Preview Card */}
      {hasContent && (
        <div className="mt-4 p-4 rounded-xl bg-[rgba(0,255,156,0.04)] border border-mint/10">
          <div className="text-[10px] text-mint/60 uppercase tracking-wider mb-2 font-semibold">Gallery Card Preview</div>
          <div className="text-sm font-semibold text-text mb-1">{packaging.hook_line || 'Hook line...'}</div>
          <div className="text-xs text-text-dim">{packaging.promise_line || 'Promise line...'}</div>
          {packaging.tone_tags.length > 0 && (
            <div className="flex gap-1 mt-2">
              {packaging.tone_tags.map((tag) => (
                <span key={tag} className="text-[10px] px-2 py-0.5 rounded-full bg-mint/10 text-mint/70">
                  {tag}
                </span>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
