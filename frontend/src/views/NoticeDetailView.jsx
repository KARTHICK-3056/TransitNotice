import React, { useEffect, useState } from 'react';
import { ArrowLeft, ArrowUpRight, History, ShieldCheck } from 'lucide-react';
import { fetchNoticeDetail } from '../api';

export default function NoticeDetailView({ noticeId, onBack }) {
  const [notice, setNotice] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let isMounted = true;
    setLoading(true);
    fetchNoticeDetail(noticeId)
      .then((data) => {
        if (isMounted) {
          setNotice(data);
          setError(null);
        }
      })
      .catch((err) => {
        if (isMounted) setError(err.message);
      })
      .finally(() => {
        if (isMounted) setLoading(false);
      });
    return () => {
      isMounted = false;
    };
  }, [noticeId]);

  if (loading) {
    return (
      <div className="py-20 text-center text-xs font-mono text-[#8e9192] animate-pulse">
        Querying advisory provenance and revision timeline...
      </div>
    );
  }

  if (error || !notice) {
    return (
      <div className="space-y-4 py-8">
        <button
          onClick={onBack}
          className="inline-flex items-center gap-1.5 text-xs text-[#c7c6c6] hover:text-white font-mono"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>← Back to advisories</span>
        </button>
        <div className="bg-[#1c1b1b] border border-[#ffb4ab]/40 rounded-[20px] p-8 text-center text-[#ffb4ab] text-sm">
          {error || 'Advisory notice not found.'}
        </div>
      </div>
    );
  }

  const isEnded = notice.status === 'ended' || notice.status === 'cancelled';
  const isWithdrawn = notice.status === 'withdrawn';

  return (
    <div className="space-y-6 w-full">
      {/* Breadcrumb Back Button */}
      <div>
        <button
          onClick={onBack}
          className="inline-flex items-center gap-2 text-xs text-[#8e9192] hover:text-white transition-colors font-mono"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          <span>← Back to all notices</span>
        </button>
      </div>

      {/* Main Notice Box */}
      <section
        style={{
          backgroundColor: '#1c1b1b',
          borderColor: '#444748',
        }}
        className="border rounded-[20px] p-6 sm:p-8 space-y-6 shadow-xl"
      >
        {/* Status / Type / Operator Pills */}
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="flex flex-wrap items-center gap-2.5">
            <span
              className={`inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-semibold ${
                isEnded
                  ? 'bg-[#141313] border border-[#444748] text-[#8e9192]'
                  : isWithdrawn
                  ? 'bg-[#141313] border border-[#fbbf24]/40 text-[#fbbf24]'
                  : 'bg-[#141313] border border-[#34d399]/40 text-[#34d399]'
              }`}
            >
              <span
                style={{
                  width: '6px',
                  height: '6px',
                  borderRadius: '50%',
                  backgroundColor: isEnded ? '#8e9192' : '#34d399',
                  boxShadow: !isEnded ? '0 0 6px rgba(52, 211, 153, 0.8)' : 'none',
                }}
              />
              <span>{notice.status.toUpperCase()}</span>
            </span>

            <span className="px-3 py-1 rounded-full text-xs font-medium bg-[#141313] border border-[#444748] text-[#c7c6c6]">
              {notice.type}
            </span>

            <span className="px-2.5 py-1 rounded-md text-xs font-mono font-medium bg-[#141313] border border-[#444748] text-[#c7c6c6]">
              Rev {notice.revision_id}
            </span>
          </div>

          <span className="px-2.5 py-1 rounded-md text-xs font-mono font-medium bg-[#141313] border border-[#444748] text-[#c7c6c6]">
            {notice.operator_type}
          </span>
        </div>

        {/* Large Editorial Headline */}
        <div>
          <h1 className="font-serif font-light text-2xl sm:text-3xl text-white leading-snug tracking-tight">
            {notice.summary}
          </h1>
        </div>

        {/* 2-Column Key-Value Metadata Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-6 pt-5 border-t border-[#444748]/50 text-sm">
          <div className="space-y-4">
            <div>
              <span className="text-[#8e9192] block text-xs uppercase tracking-[0.15em] font-sans font-semibold mb-1">
                Notice Identifier
              </span>
              <span className="font-mono text-[#e5e2e1]">{notice.notice_id}</span>
            </div>

            <div>
              <span className="text-[#8e9192] block text-xs uppercase tracking-[0.15em] font-sans font-semibold mb-1">
                Agency / Provider
              </span>
              <span className="text-[#e5e2e1]">{notice.agency}</span>
            </div>

            <div>
              <span className="text-[#8e9192] block text-xs uppercase tracking-[0.15em] font-sans font-semibold mb-1">
                Routes / Corridors
              </span>
              <div className="flex flex-wrap gap-1.5 mt-1 font-mono">
                {notice.routes && notice.routes.length > 0 ? (
                  notice.routes.map((r) => (
                    <span
                      key={r}
                      className="px-2.5 py-0.5 rounded-full bg-[#141313] border border-[#444748] text-[#c7c6c6] text-xs"
                    >
                      {r}
                    </span>
                  ))
                ) : (
                  <span className="text-[#e5e2e1]">{notice.route_id}</span>
                )}
              </div>
            </div>

            <div>
              <span className="text-[#8e9192] block text-xs uppercase tracking-[0.15em] font-sans font-semibold mb-1">
                Stations / Stops
              </span>
              <div className="flex flex-wrap gap-1.5 mt-1">
                {notice.stations && notice.stations.length > 0 ? (
                  notice.stations.map((s) => (
                    <span
                      key={s}
                      className="px-2.5 py-0.5 rounded-md bg-[#141313] border border-[#444748] text-[#c7c6c6] text-xs"
                    >
                      {s}
                    </span>
                  ))
                ) : (
                  <span className="text-[#8e9192]">Network-wide</span>
                )}
              </div>
            </div>
          </div>

          <div className="space-y-4">
            <div>
              <span className="text-[#8e9192] block text-xs uppercase tracking-[0.15em] font-sans font-semibold mb-1">
                Geographic Zone
              </span>
              <span className="text-[#e5e2e1]">{notice.area}</span>
            </div>

            <div>
              <span className="text-[#8e9192] block text-xs uppercase tracking-[0.15em] font-sans font-semibold mb-1">
                Effective Window
              </span>
              <span className="font-mono text-xs text-[#e5e2e1]">
                {notice.valid_from_ist} &rarr; {notice.valid_to_ist || 'Open-Ended (Until Further Notice)'}
              </span>
            </div>

            <div>
              <span className="text-[#8e9192] block text-xs uppercase tracking-[0.15em] font-sans font-semibold mb-1">
                Provenance Freshness
              </span>
              <div className="flex items-center gap-1.5 mt-0.5">
                <ShieldCheck className="w-3.5 h-3.5 text-[#34d399]" />
                <span className="font-mono text-xs text-[#c7c6c6]">{notice.checked_relative}</span>
              </div>
            </div>

            <div>
              <span className="text-[#8e9192] block text-xs uppercase tracking-[0.15em] font-sans font-semibold mb-1">
                Source Provenance Link
              </span>
              <a
                href={notice.source_url}
                target="_blank"
                rel="noreferrer"
                className="inline-flex items-center gap-1 text-xs text-[#c7c6c6] hover:text-white underline underline-offset-4 mt-0.5"
              >
                <span className="truncate max-w-xs">{notice.source_url}</span>
                <ArrowUpRight className="w-3.5 h-3.5 shrink-0" />
              </a>
            </div>
          </div>
        </div>
      </section>

      {/* REVISION HISTORY TIMELINE */}
      <section
        style={{
          backgroundColor: '#1c1b1b',
          borderColor: '#444748',
        }}
        className="border rounded-[20px] p-6 sm:p-8 space-y-4 shadow-xl"
      >
        <div className="flex items-center justify-between pb-3 border-b border-[#444748]/50">
          <div className="flex items-center gap-2">
            <History className="w-4 h-4 text-[#8e9192]" />
            <h2 className="font-serif text-lg font-normal text-white">Revision History &amp; Provenance Diff</h2>
          </div>
          <span className="text-xs font-mono text-[#8e9192]">
            {notice.revisions ? notice.revisions.length : 0} prior {notice.revisions?.length === 1 ? 'revision' : 'revisions'}
          </span>
        </div>

        {!notice.revisions || notice.revisions.length === 0 ? (
          <div className="text-sm text-[#8e9192] italic py-4">
            Initial observation (Revision 1). No subsequent content changes or extensions recorded yet.
          </div>
        ) : (
          <div className="space-y-3 font-mono text-xs">
            {notice.revisions.map((rev) => (
              <div
                key={rev.revision_id}
                className="bg-[#141313] border border-[#444748] rounded-xl p-4 space-y-2"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="px-2.5 py-0.5 rounded-full bg-white/10 text-white font-bold text-xs">
                      v{rev.revision_id}
                    </span>
                    <span className="text-[#8e9192] text-xs">
                      Changed at: {rev.changed_at_ist || rev.changed_at}
                    </span>
                  </div>
                  <span className="text-xs text-[#8e9192]">
                    Status: <strong className="text-white">{rev.status}</strong>
                  </span>
                </div>

                <p className="text-[#e5e2e1] font-sans font-medium text-sm">
                  {rev.change_summary || 'Notice updated'}
                </p>

                <div className="text-xs text-[#8e9192] break-all">
                  SHA-256 Digest: <span className="text-[#c7c6c6]">{rev.content_hash}</span>
                </div>
              </div>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
