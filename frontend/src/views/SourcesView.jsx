import React, { useEffect, useState } from 'react';
import { Database, ArrowUpRight, ShieldCheck } from 'lucide-react';
import { fetchSources, triggerAdminRefresh } from '../api';

export default function SourcesView() {
  const [data, setData] = useState({ sources: [], recent_runs: [] });
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const loadData = () => {
    setLoading(true);
    fetchSources()
      .then((res) => setData(res))
      .catch((err) => console.error(err))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleManualSync = async () => {
    setRefreshing(true);
    try {
      await triggerAdminRefresh();
      loadData();
    } catch (e) {
      console.error(e);
    } finally {
      setRefreshing(false);
    }
  };

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="space-y-2">
          <span className="text-xs font-semibold text-[#8e9192] tracking-[0.2em] uppercase font-sans">
            Provenance &amp; Telemetry Audits
          </span>
          <h1 className="text-4xl md:text-5xl font-light text-white leading-tight tracking-tight font-serif">
            Data sources &amp; provenance
          </h1>
          <p className="text-[#c7c6c6] text-base md:text-lg font-light leading-relaxed max-w-2xl">
            Real-time health audits, rate limits, robots.txt compliance, and fetch telemetry for Tamil Nadu transit portals.
          </p>
        </div>
        <div>
          <button
            onClick={handleManualSync}
            disabled={refreshing}
            className="px-6 py-2.5 rounded-full bg-white text-[#141313] hover:bg-[#e2e2e2] font-semibold text-xs transition-all shadow-md disabled:opacity-50 font-sans"
          >
            {refreshing ? 'Polling sources...' : 'Trigger Manual Poll'}
          </button>
        </div>
      </div>

      {/* 1. SOURCE STATUS & PROVENANCE TABLE */}
      <section
        style={{
          backgroundColor: '#1c1b1b',
          borderColor: '#444748',
        }}
        className="border rounded-[20px] overflow-hidden shadow-xl p-6 sm:p-8 space-y-4"
      >
        <div className="flex items-center gap-2 pb-3 border-b border-[#444748]/60">
          <Database className="w-4 h-4 text-[#8e9192]" />
          <h2 className="font-serif text-lg font-normal text-white">Configured Sources &amp; Health</h2>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs font-mono">
            <thead>
              <tr className="text-[#8e9192] uppercase tracking-[0.1em] border-b border-[#444748]/50">
                <th className="py-3 px-3 font-semibold font-sans">Source</th>
                <th className="py-3 px-3 font-semibold font-sans">State</th>
                <th className="py-3 px-3 font-semibold font-sans">Last Attempt</th>
                <th className="py-3 px-3 font-semibold font-sans">Last Success</th>
                <th className="py-3 px-3 font-semibold font-sans text-center">Failures</th>
                <th className="py-3 px-3 font-semibold font-sans">Next Run</th>
                <th className="py-3 px-3 font-semibold font-sans">Last Error</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#444748]/30">
              {data.sources.map((s) => {
                const isLive = s.state === 'LIVE';
                return (
                  <tr key={s.source_key} className="hover:bg-[#141313] transition-colors">
                    <td className="py-3.5 px-3">
                      <div className="font-sans font-semibold text-white text-sm">{s.label}</div>
                      <div className="flex items-center gap-2 mt-0.5 text-xs text-[#8e9192]">
                        <span>{s.agency}</span>
                        <span>·</span>
                        <span className="text-[#c7c6c6]">{s.operator_type}</span>
                        <span>·</span>
                        <a
                          href={s.base_url}
                          target="_blank"
                          rel="noreferrer"
                          className="text-[#c7c6c6] hover:text-white underline underline-offset-4 inline-flex items-center gap-0.5"
                        >
                          <span>feed</span>
                          <ArrowUpRight className="w-2.5 h-2.5" />
                        </a>
                      </div>
                    </td>
                    <td className="py-3.5 px-3 whitespace-nowrap">
                      <span
                        className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold ${
                          isLive
                            ? 'bg-[#141313] border border-[#34d399]/40 text-[#34d399]'
                            : 'bg-[#141313] border border-[#ffb4ab]/40 text-[#ffb4ab]'
                        }`}
                      >
                        <span
                          style={{
                            width: '6px',
                            height: '6px',
                            borderRadius: '50%',
                            backgroundColor: isLive ? '#34d399' : '#ffb4ab',
                            boxShadow: isLive ? '0 0 6px rgba(52, 211, 153, 0.8)' : 'none',
                          }}
                        />
                        <span>{s.state}</span>
                      </span>
                      <div className="text-xs text-[#8e9192] mt-1">{s.last_success_relative}</div>
                    </td>
                    <td className="py-3.5 px-3 text-xs text-[#c7c6c6] whitespace-nowrap">{s.last_attempt_relative}</td>
                    <td className="py-3.5 px-3 text-xs text-[#c7c6c6] whitespace-nowrap">{s.last_success_relative}</td>
                    <td className="py-3.5 px-3 text-center">
                      <span
                        className={`px-2 py-0.5 rounded text-xs ${
                          s.consecutive_failures > 0
                            ? 'bg-[#141313] border border-[#ffb4ab] text-[#ffb4ab] font-bold'
                            : 'text-[#8e9192]'
                        }`}
                      >
                        {s.consecutive_failures}
                      </span>
                    </td>
                    <td className="py-3.5 px-3 text-xs text-[#c7c6c6] whitespace-nowrap">
                      {s.next_run_at ? new Date(s.next_run_at).toLocaleTimeString() : 'Pending'}
                    </td>
                    <td className="py-3.5 px-3 text-xs text-[#8e9192] max-w-xs truncate" title={s.last_error || 'Clean'}>
                      {s.last_error ? s.last_error.substring(0, 45) + '...' : <span>None</span>}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </section>

      {/* 2. RECENT FETCH RUNS TABLE */}
      <section
        style={{
          backgroundColor: '#1c1b1b',
          borderColor: '#444748',
        }}
        className="border rounded-[20px] overflow-hidden shadow-xl p-6 sm:p-8 space-y-4"
      >
        <div className="flex items-center gap-2 pb-3 border-b border-[#444748]/60">
          <ShieldCheck className="w-4 h-4 text-[#8e9192]" />
          <h2 className="font-serif text-lg font-normal text-white">Recent Scrape Runs &amp; Telemetry</h2>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs font-mono">
            <thead>
              <tr className="text-[#8e9192] uppercase tracking-[0.1em] border-b border-[#444748]/50">
                <th className="py-3 px-3 font-semibold font-sans">Started At</th>
                <th className="py-3 px-3 font-semibold font-sans">Source</th>
                <th className="py-3 px-3 font-semibold font-sans">Outcome</th>
                <th className="py-3 px-3 font-semibold font-sans">HTTP</th>
                <th className="py-3 px-3 font-semibold font-sans">Parsed / New / Rev / Withdrawn</th>
                <th className="py-3 px-3 font-semibold font-sans">Diagnostics</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#444748]/30">
              {data.recent_runs.map((run) => (
                <tr key={run.run_id} className="hover:bg-[#141313] transition-colors">
                  <td className="py-3 px-3 text-xs text-[#8e9192] whitespace-nowrap">
                    {run.started_at ? new Date(run.started_at).toLocaleTimeString() : 'N/A'}
                  </td>
                  <td className="py-3 px-3 text-[#e5e2e1] font-sans font-medium text-sm">
                    {run.source_label || `Source #${run.source_id}`}
                  </td>
                  <td className="py-3 px-3 whitespace-nowrap">
                    <span
                      className={`px-2.5 py-0.5 rounded-full text-xs font-semibold ${
                        run.outcome === 'ok'
                          ? 'bg-[#141313] border border-[#34d399]/40 text-[#34d399]'
                          : run.outcome === 'blocked'
                          ? 'bg-[#141313] border border-[#fbbf24]/40 text-[#fbbf24]'
                          : 'bg-[#141313] border border-[#ffb4ab]/40 text-[#ffb4ab]'
                      }`}
                    >
                      {run.outcome.toUpperCase()}
                    </span>
                  </td>
                  <td className="py-3 px-3 text-xs text-[#c7c6c6]">{run.http_status || '-'}</td>
                  <td className="py-3 px-3 text-xs text-[#c7c6c6]">
                    <span>{run.items_parsed}</span> /{' '}
                    <span className="text-[#34d399]">+{run.new_count}</span> /{' '}
                    <span className="text-[#e5e2e1]">~{run.revised_count}</span> /{' '}
                    <span className="text-[#8e9192]">-{run.withdrawn_count}</span>
                  </td>
                  <td className="py-3 px-3 text-xs text-[#8e9192] max-w-xs truncate" title={run.error || 'Clean run'}>
                    {run.error ? run.error : 'Clean run'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}
