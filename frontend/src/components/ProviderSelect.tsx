import React from 'react';
import { nebTokens as t } from '../design';

const MODELS: Record<string, string[]> = {
  anthropic: ['claude-opus-4-7', 'claude-sonnet-4-6', 'claude-haiku-4-5-20251001'],
  openai:    ['gpt-4o', 'gpt-4o-mini', 'o1'],
  gemini:    ['gemini-1.5-pro', 'gemini-1.5-flash', 'gemini-2.0-flash'],
};

const FIELD_LABEL: React.CSSProperties = {
  fontSize: 9.5, fontWeight: 600, fontFamily: t.mono, color: t.textFaint,
  letterSpacing: 1.4, textTransform: 'uppercase', marginBottom: 5, display: 'block',
};
const SELECT: React.CSSProperties = {
  background: t.bgGlass, border: `1px solid ${t.border}`, color: t.textMuted,
  padding: '5px 8px', fontFamily: t.mono, fontSize: 11, width: '100%',
};

interface Props {
  provider: string; model: string;
  onProviderChange: (p: string) => void;
  onModelChange: (m: string) => void;
}

export function ProviderSelect({ provider, model, onProviderChange, onModelChange }: Props) {
  const models = MODELS[provider] ?? [];
  function handleProvider(p: string) {
    onProviderChange(p);
    onModelChange(MODELS[p]?.[0] ?? '');
  }
  return (
    <>
      <div>
        <label style={FIELD_LABEL}>Provider</label>
        <select value={provider} onChange={(e) => handleProvider(e.target.value)} style={SELECT}>
          <option value="anthropic">Anthropic</option>
          <option value="openai">OpenAI</option>
          <option value="gemini">Gemini</option>
        </select>
      </div>
      <div>
        <label style={FIELD_LABEL}>Model</label>
        <select value={model} onChange={(e) => onModelChange(e.target.value)} style={SELECT}>
          {models.map((m) => <option key={m} value={m}>{m}</option>)}
        </select>
      </div>
    </>
  );
}
