import React from 'react';
import { ArrowUpRight, History } from 'lucide-react';

export default function NoticeCard({ notice, onSelect }) {
  const isEnded = notice.status === 'ended' || notice.status === 'cancelled';
  const isWithdrawn = notice.status === 'withdrawn';
  const isUpcoming = notice.status === 'upcoming';
  const isActive = notice.status === 'active';

  // Status badge
  let statusBadge = (
    <span className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-semibold bg-[#141313] border border-[#34d399]/40 text-[#34d399]">
      <span
        style={{
          width: '6px',
          height: '6px',
          borderRadius: '50%',
          backgroundColor: '#34d399',
          boxShadow: '0 0 6px rgba(52, 211, 153, 0.8)',
        }}
      />
      <span>In effect now</span>
    </span>
  );

  if (isEnded) {
    statusBadge = (
      <span className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-medium bg-[#141313] border border-[#444748] text-[#8e9192]">
        <span className="w-1.5 h-1.5 rounded-full bg-[#8e9192]" />
        <span>Ended</span>
      </span>
    );
  } else if (isWithdrawn) {
    statusBadge = (
      <span className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-medium bg-[#141313] border border-[#fbbf24]/40 text-[#fbbf24]">
        <span className="w-1.5 h-1.5 rounded-full bg-[#fbbf24]" />
        <span>Withdrawn</span>
      </span>
    );
  } else if (isUpcoming) {
    statusBadge = (
      <span className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-medium bg-[#141313] border border-[#444748] text-[#c7c6c6]">
        <span className="w-1.5 h-1.5 rounded-full bg-[#c7c6c6]" />
        <span>Upcoming</span>
      </span>
    );
  }

  // When text
  let whenText = '';
  if (notice.valid_from_ist) {
    if (notice.valid_to_ist) {
      whenText = `${notice.valid_from_ist} – ${notice.valid_to_ist}`;
    } else {
      whenText = `${notice.valid_from_ist} – no end date announced`;
    }
  } else {
    whenText = 'Ongoing';
  }

  return (
    <article
      style={{
        backgroundColor: '#1c1b1b',
        borderColor: '#444748',
      }}
      className="border rounded-[20px] p-6 sm:p-7 mb-4 transition-all duration-300 hover:border-[#8e9192] hover:bg-[#201f1f] space-y-4 shadow-lg"
    >
      {/* Top Row: Status pill, Kind of notice pill, Operator pill */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex flex-wrap items-center gap-2.5">
          {statusBadge}

          {/* Kind of notice pill */}
          <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-[#141313] border border-[#444748] text-[#c7c6c6]">
            {notice.type}
          </span>
        </div>

        {/* Operator type pill */}
        <span
          style={{
            backgroundColor: '#141313',
            borderColor: '#444748',
          }}
          className="inline-flex items-center border rounded-md px-2.5 py-0.5 text-xs font-mono text-[#c7c6c6]"
        >
          {notice.operator_type}
        </span>
      </div>

      {/* Editorial Noto Serif Title */}
      <div>
        <button
          onClick={() => onSelect(notice.notice_id)}
          className="font-serif text-xl sm:text-2xl font-normal text-white hover:text-[#c7c6c6] text-left leading-snug transition-colors block w-full"
        >
          {notice.summary}
        </button>
      </div>

      {/* Metadata Row with bold labels, proper spacing & bullet separators */}
      <div className="flex flex-wrap items-center gap-x-4 gap-y-2 text-sm text-[#c7c6c6] pt-3 border-t border-[#444748]/40">
        <div className="inline-flex items-center gap-1.5">
          <span className="font-semibold text-[#8e9192]">Route:</span>
          <span className="font-mono text-white">{notice.route_id}</span>
        </div>

        <span className="text-[#8e9192] select-none">·</span>

        <div className="inline-flex items-center gap-1.5">
          <span className="font-semibold text-[#8e9192]">Area:</span>
          <span className="text-[#e5e2e1]">{notice.area}</span>
        </div>

        <span className="text-[#8e9192] select-none">·</span>

        <div className="inline-flex items-center gap-1.5">
          <span className="font-semibold text-[#8e9192]">When:</span>
          <span className="font-mono text-xs text-[#c7c6c6]">{whenText}</span>
        </div>
      </div>

      {/* Bottom Muted Provenance Row: Text links */}
      <div className="flex flex-wrap items-center justify-between text-xs text-[#8e9192] pt-3 border-t border-[#444748]/30 gap-3">
        <div className="inline-flex items-center gap-2">
          <span className="text-[#c7c6c6] font-medium">{notice.agency}</span>
          <span>·</span>
          <span className="font-mono text-[#8e9192]">{notice.checked_relative}</span>
        </div>

        <div className="inline-flex items-center gap-4">
          <button
            onClick={() => onSelect(notice.notice_id)}
            className="text-[#c7c6c6] hover:text-white inline-flex items-center gap-1.5 transition-colors"
          >
            <History className="w-3.5 h-3.5 text-[#8e9192]" />
            <span>details &amp; history</span>
          </button>

          {notice.source_url && (
            <a
              href={notice.source_url}
              target="_blank"
              rel="noreferrer"
              className="text-[#c7c6c6] hover:text-white inline-flex items-center gap-1 transition-colors"
            >
              <span>official notice</span>
              <ArrowUpRight className="w-3.5 h-3.5" />
            </a>
          )}
        </div>
      </div>
    </article>
  );
}
