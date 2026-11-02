import React, { useState, useEffect, useCallback } from 'react';
import Navbar from './components/Navbar';
import CurrentNoticesView from './views/CurrentNoticesView';
import EndedNoticesView from './views/EndedNoticesView';
import NoticeDetailView from './views/NoticeDetailView';
import AlertsView from './views/AlertsView';
import SourcesView from './views/SourcesView';
import { fetchNotices } from './api';

export default function App() {
  const [path, setPath] = useState(window.location.pathname || '/');
  const [notices, setNotices] = useState([]);
  const [facets, setFacets] = useState({});
  const [sources, setSources] = useState([]);
  const [totalCount, setTotalCount] = useState(0);
  const [loading, setLoading] = useState(false);
  const [isRefreshing, setIsRefreshing] = useState(false);

  // Filters state
  const [filters, setFilters] = useState({
    operator_type: 'all',
    agency: 'all',
    route: 'all',
    station: 'all',
    area: 'all',
    type: 'all',
    show: 'all',
    travel_day: '',
    year: 'all',
    end_date: 'all',
    sort: 'newest',
    q: '',
  });

  // Client-side router
  const navigate = useCallback((newPath) => {
    window.history.pushState({}, '', newPath);
    setPath(newPath);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }, []);

  useEffect(() => {
    const onPop = () => setPath(window.location.pathname || '/');
    window.addEventListener('popstate', onPop);
    return () => window.removeEventListener('popstate', onPop);
  }, []);

  // Fetch notices based on current filters and path
  const loadNotices = useCallback(async (isBackground = false) => {
    if (!isBackground) setLoading(true);
    setIsRefreshing(true);
    try {
      const activeShow = path === '/ended' ? (filters.show !== 'all' ? filters.show : 'ended') : filters.show;
      const res = await fetchNotices({ ...filters, show: activeShow });
      setNotices(res.notices || []);
      setFacets(res.facets || {});
      setSources(res.sources_summary || []);
      setTotalCount(res.total || 0);
    } catch (e) {
      console.error('Failed to load notices:', e);
    } finally {
      if (!isBackground) setLoading(false);
      setIsRefreshing(false);
    }
  }, [filters, path]);

  useEffect(() => {
    if (path === '/' || path === '/ended') {
      loadNotices();
    }
  }, [loadNotices, path]);

  // Periodic 15-second background auto-refresh
  useEffect(() => {
    const timer = setInterval(() => {
      loadNotices(true);
    }, 15000);
    return () => clearInterval(timer);
  }, [loadNotices]);

  // Determine current active view
  let currentRoute = 'current';
  let noticeDetailId = null;

  if (path === '/ended') {
    currentRoute = 'ended';
  } else if (path === '/alerts') {
    currentRoute = 'alerts';
  } else if (path === '/sources') {
    currentRoute = 'sources';
  } else if (path.startsWith('/notices/')) {
    currentRoute = 'detail';
    noticeDetailId = decodeURIComponent(path.replace('/notices/', ''));
  }

  const handleSelectNotice = (id) => {
    navigate(`/notices/${encodeURIComponent(id)}`);
  };

  const handleFilterReset = () => {
    setFilters({
      operator_type: 'all',
      agency: 'all',
      route: 'all',
      station: 'all',
      area: 'all',
      type: 'all',
      show: path === '/ended' ? 'ended' : 'all',
      travel_day: '',
      year: 'all',
      end_date: 'all',
      sort: 'newest',
      q: '',
    });
  };

  return (
    <div className="min-h-screen bg-[#07080b] text-[#e5e2e1] flex flex-col font-sans selection:bg-white/20 selection:text-white">
      {/* Floating Capsule Navbar (matching COMPUTE™ design) */}
      <Navbar
        currentRoute={currentRoute}
        onNavigate={navigate}
      />

      {/* Main Content Area */}
      <main className="flex-1 max-w-[1240px] w-full mx-auto px-4 sm:px-6 py-6 sm:py-8">
        {currentRoute === 'current' && (
          <CurrentNoticesView
            notices={notices}
            sources={sources}
            facets={facets}
            totalCount={totalCount}
            filters={filters}
            onFilterChange={setFilters}
            onFilterReset={handleFilterReset}
            onSelectNotice={handleSelectNotice}
            onNavigate={navigate}
            loading={loading}
          />
        )}

        {currentRoute === 'ended' && (
          <EndedNoticesView
            notices={notices}
            sources={sources}
            facets={facets}
            totalCount={totalCount}
            filters={filters}
            onFilterChange={setFilters}
            onFilterReset={handleFilterReset}
            onSelectNotice={handleSelectNotice}
            onNavigate={navigate}
            loading={loading}
          />
        )}

        {currentRoute === 'detail' && noticeDetailId && (
          <NoticeDetailView
            noticeId={noticeDetailId}
            onBack={() => navigate('/')}
          />
        )}

        {currentRoute === 'alerts' && <AlertsView />}

        {currentRoute === 'sources' && <SourcesView />}
      </main>

      {/* High-End Minimalist Footer */}
      <footer className="border-t border-white/[0.08] py-12 mt-16 bg-[#07080b] text-xs font-sans text-slate-500">
        <div className="max-w-[1240px] mx-auto px-4 sm:px-6 flex flex-col md:flex-row justify-between items-start md:items-end gap-6">
          <div className="space-y-2 max-w-md">
            <div className="text-xl font-bold tracking-wider text-white uppercase font-sans">
              TRANSITNOTICE <span className="text-[10px] text-slate-400 font-normal">™</span>
            </div>
            <p className="text-slate-400 text-xs leading-relaxed font-light">
              Autonomous service update tracker, road diversions, and transit advisories across Chennai Metro and Tamil Nadu networks.
            </p>
          </div>
          <div className="flex flex-col md:items-end gap-2 text-xs text-slate-400">
            <div className="font-mono text-[11px] text-slate-300">
              robots.txt compliant · 1 req/sec rate limit · SHA-256 provenance
            </div>
            <div className="text-[11px] text-slate-500">
              &copy; 2026 TransitNotice. Distributed transit intelligence.
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
