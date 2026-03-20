import { useState, useEffect, useRef } from 'react'
import { useStore } from '../../store'
import * as api from '../../api'
import type { AppSettings } from '../../types'

export default function SettingsDialog() {
  const settingsOpen = useStore((s) => s.settingsOpen)
  const setSettingsOpen = useStore((s) => s.setSettingsOpen)
  const settings = useStore((s) => s.settings)
  const setSettings = useStore((s) => s.setSettings)
  const showToast = useStore((s) => s.showToast)
  const loadStudio = useStore((s) => s.loadStudio)

  const dialogRef = useRef<HTMLDialogElement>(null)

  const [geminiKey, setGeminiKey] = useState('')
  const [openaiKey, setOpenaiKey] = useState('')
  const [anthropicKey, setAnthropicKey] = useState('')
  const [openrouterKey, setOpenrouterKey] = useState('')
  const [googleCreds, setGoogleCreds] = useState('')

  useEffect(() => {
    if (settingsOpen) {
      setGeminiKey(settings?.settings.gemini_api_key || '')
      setOpenaiKey(settings?.settings.openai_api_key || '')
      setAnthropicKey(settings?.settings.anthropic_api_key || '')
      setOpenrouterKey(settings?.settings.openrouter_api_key || '')
      setGoogleCreds(settings?.settings.google_application_credentials || '')
      dialogRef.current?.showModal()
    } else {
      dialogRef.current?.close()
    }
  }, [settingsOpen, settings])

  const handleSave = async () => {
    const payload: AppSettings = {
      gemini_api_key: geminiKey || null,
      openai_api_key: openaiKey || null,
      anthropic_api_key: anthropicKey || null,
      openrouter_api_key: openrouterKey || null,
      google_application_credentials: googleCreds || null,
    }
    try {
      const result = await api.saveSettings(payload)
      setSettings(result)
      setSettingsOpen(false)
      showToast('Settings saved')
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Failed to save settings'
      showToast(msg, true)
    }
  }

  const handleFreshStart = async () => {
    if (
      !window.confirm(
        'This will clear all local data and reset the pipeline. Continue?',
      )
    )
      return
    try {
      localStorage.clear()
      await api.resetPipeline()
      setSettingsOpen(false)
      loadStudio()
      showToast('Fresh start complete')
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Failed to reset'
      showToast(msg, true)
    }
  }

  const inputClass =
    'bg-[#111] border border-border rounded-lg px-3 py-2 text-text text-sm w-full focus:border-mint outline-none'

  const statusBadge = (configured: boolean) =>
    configured ? (
      <span className="text-xs font-semibold text-mint bg-mint-soft px-2 py-0.5 rounded-full">
        READY
      </span>
    ) : (
      <span className="text-xs font-semibold text-danger bg-danger-soft px-2 py-0.5 rounded-full">
        MISSING
      </span>
    )

  return (
    <dialog
      ref={dialogRef}
      onClose={() => setSettingsOpen(false)}
      className="bg-bg border border-border rounded-2xl p-0 max-w-lg w-full backdrop:bg-black/60 text-text"
    >
      <div className="p-6 flex flex-col gap-5">
        <h2 className="text-lg font-semibold text-text">Settings</h2>

        <label className="flex flex-col gap-1">
          <div className="flex items-center justify-between">
            <span className="text-text-dim text-xs font-semibold uppercase tracking-wide">
              Gemini API Key
            </span>
            {settings && statusBadge(settings.status.gemini_configured)}
          </div>
          <input
            type="password"
            value={geminiKey}
            onChange={(e) => setGeminiKey(e.target.value)}
            placeholder="Enter Gemini API key..."
            className={inputClass}
          />
        </label>

        <label className="flex flex-col gap-1">
          <div className="flex items-center justify-between">
            <span className="text-text-dim text-xs font-semibold uppercase tracking-wide">
              OpenAI API Key
            </span>
            {settings && statusBadge(settings.status.openai_configured)}
          </div>
          <input
            type="password"
            value={openaiKey}
            onChange={(e) => setOpenaiKey(e.target.value)}
            placeholder="Enter OpenAI API key..."
            className={inputClass}
          />
        </label>

        <label className="flex flex-col gap-1">
          <div className="flex items-center justify-between">
            <span className="text-text-dim text-xs font-semibold uppercase tracking-wide">
              Anthropic API Key
            </span>
            {settings && statusBadge(settings.status.anthropic_configured)}
          </div>
          <input
            type="password"
            value={anthropicKey}
            onChange={(e) => setAnthropicKey(e.target.value)}
            placeholder="Enter Anthropic API key..."
            className={inputClass}
          />
        </label>

        <label className="flex flex-col gap-1">
          <div className="flex items-center justify-between">
            <span className="text-text-dim text-xs font-semibold uppercase tracking-wide">
              OpenRouter API Key
            </span>
            {settings && statusBadge(settings.status.openrouter_configured)}
          </div>
          <input
            type="password"
            value={openrouterKey}
            onChange={(e) => setOpenrouterKey(e.target.value)}
            placeholder="Enter OpenRouter API key..."
            className={inputClass}
          />
          <p className="text-text-dim text-xs mt-0.5">
            Access Llama, Qwen, DeepSeek, Mistral and many others via openrouter.ai
          </p>
        </label>

        <label className="flex flex-col gap-1">
          <div className="flex items-center justify-between">
            <span className="text-text-dim text-xs font-semibold uppercase tracking-wide">
              Google Credentials Path
            </span>
            {settings && statusBadge(settings.status.google_credentials_configured)}
          </div>
          <input
            type="text"
            value={googleCreds}
            onChange={(e) => setGoogleCreds(e.target.value)}
            placeholder="/path/to/credentials.json"
            className={inputClass}
          />
        </label>

        <div className="flex items-center gap-2 mt-2">
          <button
            type="button"
            onClick={handleSave}
            className="px-4 py-2 rounded-xl text-sm font-semibold cursor-pointer bg-mint text-black hover:brightness-110 transition-colors"
          >
            Save
          </button>
          <button
            type="button"
            onClick={() => setSettingsOpen(false)}
            className="px-4 py-2 rounded-xl text-sm font-semibold cursor-pointer bg-surface border border-border text-text hover:bg-surface-raised transition-colors"
          >
            Cancel
          </button>
          <div className="flex-1" />
          <button
            type="button"
            onClick={handleFreshStart}
            className="px-4 py-2 rounded-xl text-sm font-semibold cursor-pointer bg-danger-soft text-danger border border-danger/30 hover:brightness-110 transition-colors"
          >
            Fresh Start
          </button>
        </div>
      </div>
    </dialog>
  )
}
