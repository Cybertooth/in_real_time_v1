import { useState, useEffect, useRef } from 'react'
import type { KeyboardEvent } from 'react'
import * as api from '../../api'

interface RunDialogProps {
  open: boolean
  onClose: () => void
  onStart: (
    seedPrompt: string,
    tags: string[],
    allowedLanguages: string[],
    options: { stagedWorkflow: boolean; deliveryProfile: 'standard' | 'on_demand' },
  ) => void
  initialSeedPrompt?: string
  initialTags?: string[]
  initialAllowedLanguages?: string[]
  initialMode?: 'same' | 'new'
  title?: string
  submitLabel?: string
}

export default function RunDialog({
  open,
  onClose,
  onStart,
  initialSeedPrompt = '',
  initialTags = [],
  initialAllowedLanguages = [],
  initialMode,
  title = 'Start Dry Run',
  submitLabel = 'Start Run',
}: RunDialogProps) {
  const dialogRef = useRef<HTMLDialogElement>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const [seedPrompt, setSeedPrompt] = useState(initialSeedPrompt)
  const [tags, setTags] = useState<string[]>(initialTags)
  const [tagInput, setTagInput] = useState('')
  const [allowedLanguages, setAllowedLanguages] = useState<string[]>(initialAllowedLanguages)
  const [languageInput, setLanguageInput] = useState('')
  const [generatingSeed, setGeneratingSeed] = useState(false)
  const [seedGenError, setSeedGenError] = useState<string | null>(null)
  const [mode, setMode] = useState<'same' | 'new'>(initialMode ?? 'same')
  const [stagedWorkflow, setStagedWorkflow] = useState(true)
  const [deliveryProfile, setDeliveryProfile] = useState<'standard' | 'on_demand'>('standard')
  // Show mode toggle only for retries (when a previous seed prompt exists)
  const isRetry = Boolean(initialSeedPrompt)

  // Sync initial values when the dialog opens (e.g. re-run pre-populates)
  useEffect(() => {
    if (open) {
      const openMode = initialMode ?? 'same'
      setMode(openMode)
      setSeedPrompt(openMode === 'new' ? '' : initialSeedPrompt)
      setTags(initialTags)
      setAllowedLanguages(initialAllowedLanguages)
      setTagInput('')
      setLanguageInput('')
      setGeneratingSeed(false)
      setSeedGenError(null)
      setStagedWorkflow(true)
      setDeliveryProfile('standard')
      dialogRef.current?.showModal()
      if (openMode === 'new') {
        setTimeout(() => textareaRef.current?.focus(), 50)
      }
    } else {
      dialogRef.current?.close()
    }
  }, [open]) // eslint-disable-line react-hooks/exhaustive-deps — deps intentionally omitted; effect should only run on open/close, not mid-session prop changes

  const addTag = () => {
    const trimmed = tagInput.trim()
    if (trimmed && !tags.includes(trimmed)) {
      setTags((prev) => [...prev, trimmed])
    }
    setTagInput('')
  }

  const handleTagKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' || e.key === ',') {
      e.preventDefault()
      addTag()
    } else if (e.key === 'Backspace' && tagInput === '' && tags.length > 0) {
      setTags((prev) => prev.slice(0, -1))
    }
  }

  const addLanguage = () => {
    const trimmed = languageInput.trim()
    if (trimmed && !allowedLanguages.some((lang) => lang.toLowerCase() === trimmed.toLowerCase())) {
      setAllowedLanguages((prev) => [...prev, trimmed])
    }
    setLanguageInput('')
  }

  const handleLanguageKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' || e.key === ',') {
      e.preventDefault()
      addLanguage()
    } else if (e.key === 'Backspace' && languageInput === '' && allowedLanguages.length > 0) {
      setAllowedLanguages((prev) => prev.slice(0, -1))
    }
  }

  const handleGenerateRandomSeed = async () => {
    setGeneratingSeed(true)
    setSeedGenError(null)
    try {
      const result = await api.generateRandomSeedPrompt(tags, allowedLanguages)
      setSeedPrompt(result.seed_prompt.trim())
    } catch (err) {
      setSeedGenError(err instanceof Error ? err.message : 'Failed to generate random seed.')
    } finally {
      setGeneratingSeed(false)
    }
  }

  const handleStart = () => {
    onStart(seedPrompt.trim(), tags, allowedLanguages, { stagedWorkflow, deliveryProfile })
    setSeedPrompt('')
    setTags([])
    setAllowedLanguages([])
    setTagInput('')
    setLanguageInput('')
    setSeedGenError(null)
  }

  return (
    <dialog
      ref={dialogRef}
      onClose={onClose}
      className="bg-bg border border-border rounded-2xl p-0 max-w-lg w-full backdrop:bg-black/60 text-text"
    >
      <div className="p-6 flex flex-col gap-5">
        <div>
          <h2 className="text-lg font-semibold text-text">{title}</h2>
          <p className="text-xs text-text-dim mt-1">
            Optionally steer the story with a seed prompt and genre tags.
          </p>
        </div>

        {isRetry && (
          <div className="flex gap-1 p-1 bg-surface rounded-xl border border-border w-fit">
            {(['same', 'new'] as const).map((m) => (
              <button
                key={m}
                type="button"
                onClick={() => {
                  setMode(m)
                  setSeedPrompt(m === 'new' ? '' : initialSeedPrompt)
                }}
                className={`px-3 py-1 rounded-lg text-xs font-semibold transition-colors cursor-pointer ${
                  mode === m
                    ? 'bg-mint text-black'
                    : 'text-text-dim hover:text-text'
                }`}
              >
                {m === 'same' ? 'Same Seed' : 'New Seed'}
              </button>
            ))}
          </div>
        )}

        <label className="flex flex-col gap-1.5">
          <div className="flex items-center justify-between gap-2">
            <span className="text-text-dim text-xs font-semibold uppercase tracking-wide">
              Seed Prompt
            </span>
            <button
              type="button"
              onClick={handleGenerateRandomSeed}
              disabled={generatingSeed}
              className={`px-2.5 py-1 rounded-lg text-[11px] font-semibold border transition-colors ${
                generatingSeed
                  ? 'border-border text-text-dim bg-surface cursor-not-allowed opacity-70'
                  : 'border-mint/40 text-mint hover:border-mint hover:bg-mint/10 cursor-pointer'
              }`}
            >
              {generatingSeed ? 'Generating...' : 'Random Idea'}
            </button>
          </div>
          <textarea
            ref={textareaRef}
            value={seedPrompt}
            onChange={(e) => setSeedPrompt(e.target.value)}
            placeholder="e.g. A missing detective whose own cold case resurfaces the night before her retirement…"
            rows={4}
            className="bg-[#111] border border-border rounded-lg px-3 py-2 text-text text-sm w-full focus:border-mint outline-none resize-none"
          />
          <p className="text-text-dim text-xs">
            Injected into the creative brainstorm prompt to steer the story.
          </p>
          {seedGenError && (
            <p className="text-danger text-xs">{seedGenError}</p>
          )}
        </label>

        <label className="flex flex-col gap-1.5">
          <span className="text-text-dim text-xs font-semibold uppercase tracking-wide">
            Category Tags
          </span>
          <div className="bg-[#111] border border-border rounded-lg px-3 py-2 flex flex-wrap gap-2 min-h-[42px] focus-within:border-mint">
            {tags.map((tag) => (
              <span
                key={tag}
                className="flex items-center gap-1 bg-mint/10 text-mint text-xs font-semibold px-2 py-0.5 rounded-full"
              >
                {tag}
                <button
                  type="button"
                  onClick={() => setTags((prev) => prev.filter((t) => t !== tag))}
                  className="text-mint/60 hover:text-mint cursor-pointer bg-transparent border-none text-sm leading-none"
                >
                  ×
                </button>
              </span>
            ))}
            <input
              type="text"
              value={tagInput}
              onChange={(e) => setTagInput(e.target.value)}
              onKeyDown={handleTagKeyDown}
              onBlur={addTag}
              placeholder={tags.length === 0 ? 'Add tags (Enter to confirm)…' : ''}
              className="bg-transparent text-text text-sm outline-none flex-1 min-w-[120px]"
            />
          </div>
          <p className="text-text-dim text-xs">
            e.g. police-thriller, domestic-drama, workplace-intrigue
          </p>
        </label>

        <label className="flex flex-col gap-1.5">
          <span className="text-text-dim text-xs font-semibold uppercase tracking-wide">
            Allowed Languages
          </span>
          <div className="bg-[#111] border border-border rounded-lg px-3 py-2 flex flex-wrap gap-2 min-h-[42px] focus-within:border-mint">
            {allowedLanguages.map((language) => (
              <span
                key={language}
                className="flex items-center gap-1 bg-sky-500/10 text-sky-300 text-xs font-semibold px-2 py-0.5 rounded-full"
              >
                {language}
                <button
                  type="button"
                  onClick={() => setAllowedLanguages((prev) => prev.filter((l) => l !== language))}
                  className="text-sky-300/70 hover:text-sky-200 cursor-pointer bg-transparent border-none text-sm leading-none"
                >
                  ×
                </button>
              </span>
            ))}
            <input
              type="text"
              value={languageInput}
              onChange={(e) => setLanguageInput(e.target.value)}
              onKeyDown={handleLanguageKeyDown}
              onBlur={addLanguage}
              placeholder={allowedLanguages.length === 0 ? 'e.g. English, Hindi, Bengali, Japanese…' : ''}
              className="bg-transparent text-text text-sm outline-none flex-1 min-w-[120px]"
            />
          </div>
          <p className="text-text-dim text-xs">
            Restricts generated story artifacts to these languages. Add multiple for mixed-language stories.
          </p>
        </label>

        <label className="flex flex-col gap-1.5">
          <span className="text-text-dim text-xs font-semibold uppercase tracking-wide">
            Dry-Run Workflow
          </span>
          <select
            value={stagedWorkflow ? 'staged' : 'full'}
            onChange={(e) => setStagedWorkflow(e.target.value === 'staged')}
            className="bg-[#111] border border-border rounded-lg px-3 py-2 text-text text-sm"
          >
            <option value="staged">Staged (Approval Gates)</option>
            <option value="full">Full (One Shot)</option>
          </select>
          <p className="text-text-dim text-xs">
            Staged runs pause at each generation stage so you can approve before spending more tokens.
          </p>
        </label>

        <label className="flex flex-col gap-1.5">
          <span className="text-text-dim text-xs font-semibold uppercase tracking-wide">
            Delivery Profile Hint
          </span>
          <select
            value={deliveryProfile}
            onChange={(e) => setDeliveryProfile(e.target.value as 'standard' | 'on_demand')}
            className="bg-[#111] border border-border rounded-lg px-3 py-2 text-text text-sm"
          >
            <option value="standard">Standard Realtime</option>
            <option value="on_demand">On-Demand Burst</option>
          </select>
          <p className="text-text-dim text-xs">
            Adds generation guidance for bursty session-based pacing when using subscription on-demand stories.
          </p>
        </label>

        <div className="flex items-center gap-2 mt-1">
          <button
            type="button"
            onClick={handleStart}
            className="px-4 py-2 rounded-xl text-sm font-semibold cursor-pointer bg-mint text-black hover:brightness-110 transition-colors"
          >
            {submitLabel}
          </button>
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-2 rounded-xl text-sm font-semibold cursor-pointer bg-surface border border-border text-text hover:bg-surface-raised transition-colors"
          >
            Cancel
          </button>
        </div>
      </div>
    </dialog>
  )
}
