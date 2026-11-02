import React, { useState, useEffect } from 'react';
import { Bell, CheckCircle2, AlertCircle } from 'lucide-react';
import { fetchAlertOptions, subscribeAlerts } from '../api';

export default function AlertsView() {
  const [options, setOptions] = useState({
    routes: [],
    stations: [],
    areas: [],
    types: [],
  });
  const [email, setEmail] = useState('');
  const [selectedRoutes, setSelectedRoutes] = useState([]);
  const [selectedStations, setSelectedStations] = useState([]);
  const [selectedAreas, setSelectedAreas] = useState([]);
  const [selectedTypes, setSelectedTypes] = useState([]);

  const [loading, setLoading] = useState(false);
  const [statusMsg, setStatusMsg] = useState(null);
  const [isError, setIsError] = useState(false);

  useEffect(() => {
    fetchAlertOptions()
      .then((data) => setOptions(data))
      .catch((err) => console.error('Alert options error:', err));
  }, []);

  const toggleItem = (list, setList, item) => {
    if (list.includes(item)) {
      setList(list.filter((x) => x !== item));
    } else {
      setList([...list, item]);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!email || !email.includes('@')) {
      setIsError(true);
      setStatusMsg('Please provide a valid email address.');
      return;
    }

    setLoading(true);
    setStatusMsg(null);
    try {
      const res = await subscribeAlerts(email, {
        routes: selectedRoutes,
        stations: selectedStations,
        areas: selectedAreas,
        types: selectedTypes,
      });
      setIsError(false);
      setStatusMsg(res.message || 'Alert preferences successfully registered.');
    } catch (err) {
      setIsError(true);
      setStatusMsg(err.message || 'Failed to register alert preferences.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="w-full space-y-8">
      {/* Header */}
      <div className="space-y-3">
        <span className="text-xs font-semibold text-[#8e9192] tracking-[0.2em] uppercase font-sans">
          Notification Preferences
        </span>
        <h1 className="text-4xl md:text-5xl font-light text-white leading-tight tracking-tight font-serif">
          Get transit alerts
        </h1>
        <p className="text-[#c7c6c6] text-base md:text-lg font-light leading-relaxed">
          Subscribe to deduplicated Tamil Nadu transit advisories. You will receive exactly one notification when an advisory is opened or revised.
        </p>
      </div>

      <form
        onSubmit={handleSubmit}
        style={{
          backgroundColor: '#1c1b1b',
          borderColor: '#444748',
        }}
        className="border rounded-[20px] p-6 sm:p-8 space-y-6 shadow-2xl"
      >
        {/* Email Input */}
        <div>
          <label className="block text-xs font-semibold uppercase tracking-[0.15em] text-[#8e9192] mb-2 font-sans">
            Notification Email
          </label>
          <input
            type="email"
            required
            placeholder="commuter@tamilnadu.transit"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="w-full bg-[#141313] border border-[#444748] rounded-lg px-4 py-3 text-sm text-white placeholder-[#8e9192] focus:outline-none focus:border-white font-mono transition-colors"
          />
        </div>

        {/* Checkbox Section: ROUTES */}
        <div className="space-y-3 pt-3 border-t border-[#444748]/50">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-[0.15em] text-[#8e9192] font-sans">
              Routes / Corridors
            </span>
            <span className="text-xs text-[#8e9192] font-mono">
              {selectedRoutes.length} selected
            </span>
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-2.5">
            {options.routes.map((r) => {
              const active = selectedRoutes.includes(r);
              return (
                <label
                  key={r}
                  onClick={() => toggleItem(selectedRoutes, setSelectedRoutes, r)}
                  className={`px-3 py-2 rounded-lg border text-xs font-mono cursor-pointer transition-colors flex items-center justify-between ${
                    active
                      ? 'bg-white/10 border-white text-white font-semibold'
                      : 'bg-[#141313] border-[#444748] text-[#c7c6c6] hover:border-[#8e9192]'
                  }`}
                >
                  <span className="truncate">{r}</span>
                </label>
              );
            })}
          </div>
        </div>

        {/* Checkbox Section: AREAS */}
        <div className="space-y-3 pt-3 border-t border-[#444748]/50">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-[0.15em] text-[#8e9192] font-sans">
              Geographic Areas
            </span>
            <span className="text-xs text-[#8e9192] font-mono">
              {selectedAreas.length} selected
            </span>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2.5">
            {options.areas.map((a) => {
              const active = selectedAreas.includes(a);
              return (
                <label
                  key={a}
                  onClick={() => toggleItem(selectedAreas, setSelectedAreas, a)}
                  className={`px-3 py-2 rounded-lg border text-xs cursor-pointer transition-colors flex items-center justify-between ${
                    active
                      ? 'bg-white/10 border-white text-white font-semibold'
                      : 'bg-[#141313] border-[#444748] text-[#c7c6c6] hover:border-[#8e9192]'
                  }`}
                >
                  <span className="truncate">{a}</span>
                </label>
              );
            })}
          </div>
        </div>

        {/* Checkbox Section: TYPES */}
        <div className="space-y-3 pt-3 border-t border-[#444748]/50">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-[0.15em] text-[#8e9192] font-sans">
              Notice Types
            </span>
            <span className="text-xs text-[#8e9192] font-mono">
              {selectedTypes.length} selected
            </span>
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-2.5">
            {options.types.map((t) => {
              const active = selectedTypes.includes(t);
              return (
                <label
                  key={t}
                  onClick={() => toggleItem(selectedTypes, setSelectedTypes, t)}
                  className={`px-3 py-2 rounded-lg border text-xs cursor-pointer transition-colors flex items-center justify-between ${
                    active
                      ? 'bg-white/10 border-white text-white font-semibold'
                      : 'bg-[#141313] border-[#444748] text-[#c7c6c6] hover:border-[#8e9192]'
                  }`}
                >
                  <span className="truncate">{t}</span>
                </label>
              );
            })}
          </div>
        </div>

        {/* Feedback message */}
        {statusMsg && (
          <div
            className={`p-4 rounded-xl border text-sm flex items-center gap-2.5 ${
              isError
                ? 'bg-[#141313] border-[#ffb4ab]/40 text-[#ffb4ab]'
                : 'bg-[#141313] border-[#34d399]/40 text-[#34d399]'
            }`}
          >
            {isError ? <AlertCircle className="w-4 h-4 shrink-0" /> : <CheckCircle2 className="w-4 h-4 shrink-0" />}
            <span>{statusMsg}</span>
          </div>
        )}

        {/* Submit */}
        <div className="pt-2">
          <button
            type="submit"
            disabled={loading}
            className="w-full sm:w-auto px-8 py-3 rounded-full bg-white text-[#141313] hover:bg-[#e2e2e2] font-semibold text-sm transition-all shadow-lg disabled:opacity-50"
          >
            {loading ? 'Registering...' : 'Save Subscription Preferences'}
          </button>
        </div>
      </form>
    </div>
  );
}
