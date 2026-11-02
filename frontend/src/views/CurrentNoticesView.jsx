import React from 'react';
import { ArrowRight } from 'lucide-react';
import SourceBadges from '../components/SourceBadges';
import FilterPanel from '../components/FilterPanel';
import NoticeCard from '../components/NoticeCard';

export default function CurrentNoticesView({
  notices = [],
  sources = [],
  facets = {},
  totalCount = 0,
  filters,
  onFilterChange,
  onFilterReset,
  onSelectNotice,
  onNavigate,
  loading = false,
}) {
  const scrollToNotices = () => {
    const el = document.getElementById('notices-section');
    if (el) {
      el.scrollIntoView({ behavior: 'smooth' });
    }
  };

  return (
    <div className="space-y-12 pb-16">
      {/* Front Page Hero Section (matching Apex minimalist aesthetic) */}
      <section className="relative pt-6 pb-12 sm:pt-10 sm:pb-16 flex flex-col items-center text-center">
        {/* Subtle radial glow background */}
        <div 
          className="absolute -top-12 left-1/2 -translate-x-1/2 w-[600px] h-[350px] pointer-events-none opacity-40 blur-3xl -z-10"
          style={{
            background: 'radial-gradient(circle, rgba(255, 255, 255, 0.08) 0%, rgba(255, 255, 255, 0.02) 45%, transparent 70%)',
          }}
        />

        {/* Top Status Pill */}
        <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-[#11131a]/90 border border-white/10 text-xs font-medium text-slate-300 shadow-sm backdrop-blur-md mb-8 hover:border-white/20 transition-colors">
          <span className="w-2 h-2 rounded-full bg-emerald-400 shadow-[0_0_8px_rgba(52,211,153,0.9)] animate-pulse" />
          <span>Live Transit Intelligence · Tamil Nadu</span>
        </div>

        {/* Big Bold Headline */}
        <h1 className="text-5xl sm:text-6xl md:text-7xl font-extrabold tracking-tight font-sans leading-[1.08] max-w-4xl mx-auto">
          <span className="block text-white">Travel faster.</span>
          <span className="block text-slate-400 mt-1">Track smarter.</span>
        </h1>

        {/* Clean Subtitle / Description */}
        <p className="mt-6 text-base sm:text-lg md:text-xl text-slate-400 max-w-2xl mx-auto font-normal leading-relaxed">
          The unified platform for Chennai Metro &amp; Tamil Nadu transit. Built for clarity, verified by cryptographic SHA-256 diffs. Real-time road diversions, gate closures, and route alerts.
        </p>

        {/* Action Buttons / CTAs */}
        <div className="mt-8 flex flex-col sm:flex-row items-center gap-4 justify-center">
          <button
            onClick={scrollToNotices}
            className="w-full sm:w-auto bg-white text-black font-semibold text-sm sm:text-base px-7 py-3 rounded-full hover:bg-slate-200 transition-all shadow-[0_0_30px_rgba(255,255,255,0.18)] flex items-center justify-center gap-2 group active:scale-95 duration-150"
          >
            Explore Notices
            <ArrowRight className="w-4 h-4 transition-transform group-hover:translate-x-1" />
          </button>
          <button
            onClick={() => onNavigate('/alerts')}
            className="w-full sm:w-auto bg-[#11131a]/90 hover:bg-[#1a1d28] text-slate-300 hover:text-white font-medium text-sm sm:text-base px-7 py-3 rounded-full border border-white/10 hover:border-white/25 transition-all active:scale-95 duration-150"
          >
            Get Alerts
          </button>
        </div>

        {/* Verified Networks Indicator */}
        <div className="mt-12 flex flex-col items-center gap-2.5">
          <div className="flex flex-wrap items-center justify-center gap-2 text-xs font-sans">
            <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-white/[0.04] border border-white/[0.08] text-slate-300">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
              <span>Chennai Metro (Blue &amp; Green)</span>
            </span>
            <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-white/[0.04] border border-white/[0.08] text-slate-300">
              <span className="w-1.5 h-1.5 rounded-full bg-sky-400" />
              <span>Phase II Corridors 3, 4, 5</span>
            </span>
            <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-white/[0.04] border border-white/[0.08] text-slate-300">
              <span className="w-1.5 h-1.5 rounded-full bg-amber-400" />
              <span>TN Intercity Express Routes</span>
            </span>
          </div>
          <p className="text-[11px] text-slate-500 font-mono">
            Verified across 250+ service updates · Cryptographic SHA-256 provenance
          </p>
        </div>
      </section>

      {/* Existing Components (Cleanly kept with anchor for direct navigation) */}
      <div id="notices-section" className="space-y-6 pt-2">
        {/* Source Provenance Badges */}
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <h2 className="text-base sm:text-lg font-semibold text-white tracking-tight">
              Live Network Status
            </h2>
            <span className="text-xs font-mono text-slate-400">
              {totalCount} total advisories
            </span>
          </div>
          <SourceBadges sources={sources} onNavigate={onNavigate} />
        </div>

        {/* 2-Section Faceted Filter Panel */}
        <FilterPanel
          filters={filters}
          onChange={onFilterChange}
          onReset={onFilterReset}
          facets={facets}
          totalCount={totalCount}
        />

        {/* Notices List */}
        <section className="space-y-3">
          {loading && (
            <div className="text-center py-16 text-xs font-mono text-slate-400 animate-pulse">
              Loading verified transport notices...
            </div>
          )}

          {!loading && notices.length === 0 && (
            <div className="bg-[#0c0d12]/90 border border-white/[0.08] rounded-2xl p-12 text-center space-y-4 shadow-xl">
              <p className="text-base font-medium text-white">No active transport notices found</p>
              <p className="text-xs text-slate-400">Try adjusting your filter options or clearing all filters.</p>
              <button
                onClick={onFilterReset}
                className="px-5 py-2 rounded-full border border-white/20 text-xs font-medium text-slate-300 hover:text-white hover:border-white transition-colors"
              >
                Reset Filters
              </button>
            </div>
          )}

          {!loading &&
            notices.map((notice) => (
              <NoticeCard
                key={notice.notice_id}
                notice={notice}
                onSelect={onSelectNotice}
              />
            ))}
        </section>
      </div>
    </div>
  );
}
