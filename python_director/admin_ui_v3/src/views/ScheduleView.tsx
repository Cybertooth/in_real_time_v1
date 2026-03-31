import { useState, useEffect } from 'react'
import { useStore } from '../store'
import type { SchedulerConfig } from '../types'

export default function ScheduleView() {
  const schedulerConfig = useStore(s => s.schedulerConfig)
  const resetTemplates = useStore(s => s.resetTemplates)
  const updateSchedulerConfig = useStore(s => s.updateSchedulerConfig)
  const triggerSchedulerRunNow = useStore(s => s.triggerSchedulerRunNow)

  const [form, setForm] = useState<SchedulerConfig | null>(null)

  useEffect(() => {
    if (schedulerConfig) {
      setForm(schedulerConfig)
    }
  }, [schedulerConfig])

  if (!form) return <div className="p-6 text-text-dim">Loading scheduler config...</div>

  const handleChange = (field: keyof SchedulerConfig, value: unknown) => {
    setForm(prev => prev ? { ...prev, [field]: value } : prev)
  }

  const handleTagsChange = (val: string) => {
    const tags = val.split(',').map(s => s.trim()).filter(Boolean)
    handleChange('default_tags', tags)
  }

  const handleLangsChange = (val: string) => {
    const langs = val.split(',').map(s => s.trim()).filter(Boolean)
    handleChange('default_languages', langs)
  }

  const handleSave = async () => {
    await updateSchedulerConfig(form)
  }

  return (
    <div className="p-6 max-w-3xl mx-auto flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight mb-2">Automated Deployment Schedule</h1>
        <p className="text-text-dim">
          Configure when the system should automatically generate and deploy a new story.
          This relies on Google Cloud Scheduler triggering the `/api/scheduler/tick` endpoint periodically.
        </p>
      </div>

      <div className="bg-surface border border-border rounded-2xl p-6 flex flex-col gap-6">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg font-semibold">Enable Automation</h2>
            <p className="text-text-dim text-sm">Turn on or pause the automatic deployment pipeline.</p>
          </div>
          <label className="relative inline-flex items-center cursor-pointer">
            <input
              type="checkbox"
              className="sr-only peer"
              checked={form.enabled}
              onChange={(e) => handleChange('enabled', e.target.checked)}
            />
            <div className="w-11 h-6 bg-border peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-mint"></div>
          </label>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div className="flex flex-col gap-2">
            <label className="text-sm font-semibold text-text-dim">Pipeline Template</label>
            <select
              value={form.template_key}
              onChange={(e) => handleChange('template_key', e.target.value)}
              className="bg-[rgba(0,0,0,0.2)] border border-border rounded-lg px-3 py-2 text-sm focus:border-mint focus:outline-none transition-colors"
            >
              <option value="__active__">Use Active Pipeline</option>
              {resetTemplates.map((template) => (
                <option key={template.key} value={template.key}>
                  {template.name}
                </option>
              ))}
            </select>
          </div>
          <div className="flex flex-col gap-2">
            <label className="text-sm font-semibold text-text-dim">Frequency (Days)</label>
            <input
              type="number"
              min="1"
              value={form.frequency_days}
              onChange={(e) => handleChange('frequency_days', parseInt(e.target.value) || 1)}
              className="bg-[rgba(0,0,0,0.2)] border border-border rounded-lg px-3 py-2 text-sm focus:border-mint focus:outline-none transition-colors"
            />
          </div>
          <div className="flex flex-col gap-2">
            <label className="text-sm font-semibold text-text-dim">Time of Day (UTC)</label>
            <input
              type="time"
              value={form.time_of_day}
              onChange={(e) => handleChange('time_of_day', e.target.value)}
              className="bg-[rgba(0,0,0,0.2)] border border-border rounded-lg px-3 py-2 text-sm focus:border-mint focus:outline-none transition-colors"
            />
          </div>
        </div>

        <div className="flex flex-col gap-2">
          <label className="text-sm font-semibold text-text-dim">Retention Policy</label>
          <div className="flex items-center gap-3">
            <span className="text-sm">Keep latest</span>
            <input
              type="number"
              min="1"
              max="50"
              value={form.keep_count}
              onChange={(e) => handleChange('keep_count', parseInt(e.target.value) || 5)}
              className="bg-[rgba(0,0,0,0.2)] border border-border rounded-lg px-3 py-1 w-20 text-sm focus:border-mint focus:outline-none transition-colors text-center"
            />
            <span className="text-sm">auto-deployed stories online.</span>
          </div>
          <p className="text-xs text-text-dim mt-1">Older auto-deployed stories and their assets will be permanently deleted automatically.</p>
        </div>
      </div>

      <div className="bg-surface border border-border rounded-2xl p-6 flex flex-col gap-6">
        <div>
          <h2 className="text-lg font-semibold mb-1">Pipeline Default Parameters</h2>
          <p className="text-text-dim text-sm">These settings are used when the automated pipeline runs.</p>
        </div>

        <div className="flex flex-col gap-4">
          <div className="flex flex-col gap-2">
            <label className="text-sm font-semibold">Tags (comma-separated)</label>
            <input
              type="text"
              value={form.default_tags.join(', ')}
              onChange={(e) => handleTagsChange(e.target.value)}
              placeholder="thriller, action, dark"
              className="bg-[rgba(0,0,0,0.2)] border border-border rounded-lg px-3 py-2 text-sm focus:border-mint focus:outline-none transition-colors w-full"
            />
          </div>

          <div className="flex flex-col gap-2">
            <label className="text-sm font-semibold">Allowed Languages (comma-separated)</label>
            <input
              type="text"
              value={form.default_languages.join(', ')}
              onChange={(e) => handleLangsChange(e.target.value)}
              placeholder="en"
              className="bg-[rgba(0,0,0,0.2)] border border-border rounded-lg px-3 py-2 text-sm focus:border-mint focus:outline-none transition-colors w-full"
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="flex flex-col gap-2">
              <label className="text-sm font-semibold">Delivery Profile</label>
              <select
                value={form.delivery_profile}
                onChange={(e) => handleChange('delivery_profile', e.target.value)}
                className="bg-[rgba(0,0,0,0.2)] border border-border rounded-lg px-3 py-2 text-sm focus:border-mint focus:outline-none transition-colors"
              >
                <option value="standard">Standard (Higher Quality)</option>
                <option value="on_demand">On Demand (Faster)</option>
              </select>
            </div>

            <div className="flex flex-col gap-2">
              <label className="text-sm font-semibold">TTS Tier</label>
              <select
                value={form.tts_tier}
                onChange={(e) => handleChange('tts_tier', e.target.value)}
                className="bg-[rgba(0,0,0,0.2)] border border-border rounded-lg px-3 py-2 text-sm focus:border-mint focus:outline-none transition-colors"
              >
                <option value="premium">Premium (ElevenLabs)</option>
                <option value="cheap">Cheap (Edge TTS)</option>
              </select>
            </div>
          </div>
        </div>
      </div>

      <div className="flex justify-between items-center pt-2">
        <button
          onClick={triggerSchedulerRunNow}
          className="px-5 py-2.5 bg-surface border border-border rounded-xl text-sm font-medium hover:bg-surface-raised transition-colors flex items-center gap-2"
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polygon points="5 3 19 12 5 21 5 3"></polygon></svg>
          Force Run Now
        </button>
        <button
          onClick={handleSave}
          className="px-6 py-2.5 bg-mint text-black rounded-xl text-sm font-semibold shadow-glow hover:brightness-110 transition-all cursor-pointer"
        >
          Save Schedule Settings
        </button>
      </div>

      {form.last_run_at && (
        <div className="text-xs text-text-dim text-right">
          Last automated/forced run recorded at: {new Date(form.last_run_at).toLocaleString()}
        </div>
      )}
    </div>
  )
}
