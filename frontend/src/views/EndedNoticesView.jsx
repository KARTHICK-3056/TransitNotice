import React from 'react';
import SourceBadges from '../components/SourceBadges';
import FilterPanel from '../components/FilterPanel';
import NoticeCard from '../components/NoticeCard';

export default function EndedNoticesView({
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
  return (
    <div className="space-y-8">
      {/* Hero Header */}
      <section className="space-y-3">
        <span className="text-xs font-semibold text-[#8e9192] tracking-[0.2em] uppercase font-sans">
          Archived &amp; Completed Advisories
        </span>
        <h1 className="text-4xl md:text-5xl font-light text-white leading-tight tracking-tight font-serif">
          Ended &amp; archived notices
        </h1>
        <p className="text-[#c7c6c6] text-base md:text-lg font-light leading-relaxed max-w-3xl">
          Historical record of resolved track repairs, completed road diversions, and withdrawn service advisories for auditing and research.
        </p>

        {/* Provenance Badges */}
        <SourceBadges sources={sources} onNavigate={onNavigate} />
      </section>

      {/* 2-Section Faceted Filter */}
      <FilterPanel
        filters={{ ...filters, show: filters.show || 'ended' }}
        onChange={onFilterChange}
        onReset={onFilterReset}
        facets={facets}
        totalCount={totalCount}
      />

      {/* Notices List */}
      <section className="space-y-4">
        {loading && (
          <div className="text-center py-16 text-xs font-mono text-[#8e9192] animate-pulse">
            Querying archived transport notices...
          </div>
        )}

        {!loading && notices.length === 0 && (
          <div className="bg-[#1c1b1b] border border-[#444748] rounded-[20px] p-12 text-center space-y-4 shadow-xl">
            <p className="text-base font-serif font-normal text-white">No ended notices found matching criteria</p>
            <p className="text-sm text-[#8e9192]">All historical records have been audited.</p>
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
  );
}
