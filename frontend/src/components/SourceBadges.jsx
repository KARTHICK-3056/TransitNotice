import React from 'react';
import { ArrowUpRight } from 'lucide-react';

export default function SourceBadges({ sources = [], onNavigate }) {
  if (!sources || sources.length === 0) return null;

  return (
    <div className="flex flex-wrap items-center gap-2.5 pt-3 text-xs text-[#c7c6c6]">
      <span className="font-sans text-xs uppercase tracking-[0.15em] text-[#8e9192] font-semibold">
        Data checked:
      </span>
      {sources.map((s) => {
        const isUpToDate = s.state === 'up to date';
        const isError = s.state === 'error';
        const dotColor = isUpToDate ? '#34d399' : isError ? '#ffb4ab' : '#fbbf24';

        return (
          <div
            key={s.source_key}
            style={{
              backgroundColor: '#1c1b1b',
              borderColor: '#444748',
            }}
            className="inline-flex items-center gap-2 px-3 py-1 rounded-full border text-xs text-[#c7c6c6] transition-all hover:border-[#8e9192]"
          >
            <span
              style={{
                backgroundColor: dotColor,
                boxShadow: isUpToDate ? '0 0 6px rgba(52, 211, 153, 0.7)' : 'none',
              }}
              className="w-1.5 h-1.5 rounded-full shrink-0"
            />
            <span className="text-[#e5e2e1] font-medium">{s.label}</span>
            <span className="text-[#8e9192]">·</span>
            <span className="font-mono text-xs text-[#8e9192]">{s.state}</span>
          </div>
        );
      })}

      <button
        onClick={() => onNavigate('/sources')}
        className="inline-flex items-center gap-0.5 text-xs text-[#c7c6c6] hover:text-white underline underline-offset-4 ml-1 transition-colors"
      >
        <span>details</span>
        <ArrowUpRight className="w-3 h-3" />
      </button>
    </div>
  );
}
