import React, { useState, useMemo } from 'react';
import { Search, X } from 'lucide-react';
import CustomSelect from './CustomSelect';

export default function FilterPanel({
  filters,
  onChange,
  onReset,
  facets = {},
  totalCount = 0,
}) {
  const [searchOpen, setSearchOpen] = useState(Boolean(filters.q));

  const handleSelect = (key, value) => {
    onChange({ ...filters, [key]: value });
  };

  const removeFilter = (key) => {
    const updated = { ...filters };
    delete updated[key];
    onChange(updated);
  };

  // Generate next 7 IST calendar dates for Travel Day dropdown
  const next7Days = useMemo(() => {
    const list = [];
    const now = new Date();
    for (let i = 0; i < 7; i++) {
      const d = new Date(now.getTime() + i * 24 * 60 * 60 * 1000);
      const yyyy = d.getFullYear();
      const mm = String(d.getMonth() + 1).padStart(2, '0');
      const dd = String(d.getDate()).padStart(2, '0');
      const iso = `${yyyy}-${mm}-${dd}`;
      const dayName = d.toLocaleDateString('en-US', { weekday: 'short' });
      const monthName = d.toLocaleDateString('en-US', { month: 'short' });
      let label = `${dayName}, ${dd} ${monthName}`;
      if (i === 0) label = `Today (${dayName}, ${dd} ${monthName})`;
      else if (i === 1) label = `Tomorrow (${dayName}, ${dd} ${monthName})`;
      list.push({ value: iso, label });
    }
    return list;
  }, []);

  // Helper to build options with facet count
  const buildOptions = (facetMap = {}, allLabel = 'All') => {
    const list = [{ value: 'all', label: allLabel }];
    if (!facetMap) return list;
    const entries = Object.entries(facetMap).filter(([_, count]) => count > 0);
    entries.forEach(([name, count]) => {
      list.push({ value: name, label: name, count });
    });
    return list;
  };

  const operatorOptions = useMemo(
    () => buildOptions(facets.operator_types, 'All operators'),
    [facets.operator_types]
  );
  const agencyOptions = useMemo(
    () => buildOptions(facets.agencies, 'All agencies'),
    [facets.agencies]
  );
  const routeOptions = useMemo(
    () => buildOptions(facets.routes, 'All routes'),
    [facets.routes]
  );
  const stationOptions = useMemo(
    () => buildOptions(facets.stations, 'All stations'),
    [facets.stations]
  );
  const areaOptions = useMemo(
    () => buildOptions(facets.areas, 'All areas'),
    [facets.areas]
  );
  const typeOptions = useMemo(
    () => buildOptions(facets.types, 'All types'),
    [facets.types]
  );
  const yearOptions = useMemo(
    () => buildOptions(facets.years, 'All years'),
    [facets.years]
  );

  const showOptions = useMemo(
    () => [
      { value: 'all', label: 'Everything', count: totalCount },
      { value: 'in_effect_now', label: 'In effect now' },
      { value: 'upcoming', label: 'Upcoming' },
      { value: 'ended', label: 'Ended' },
      { value: 'withdrawn', label: 'Withdrawn' },
    ],
    [totalCount]
  );

  const travelDayOptions = useMemo(
    () => [
      { value: '', label: 'Any day' },
      ...next7Days.map((d) => ({ value: d.value, label: d.label })),
    ],
    [next7Days]
  );

  const endDateOptions = useMemo(
    () => [
      { value: 'all', label: 'Any window' },
      { value: 'open_ended', label: 'Open-ended only' },
      { value: 'has_end_date', label: 'Specific end date' },
    ],
    []
  );

  const sortOptions = useMemo(
    () => [
      { value: 'newest', label: 'Current first, then newest' },
      { value: 'oldest', label: 'Oldest first' },
      { value: 'expiring_soon', label: 'Expiring soon' },
    ],
    []
  );

  const activeKeys = Object.entries(filters).filter(
    ([k, v]) => v && v !== 'all' && v !== ''
  );

  return (
    <div
      style={{
        backgroundColor: '#1c1b1b',
        borderColor: '#444748',
      }}
      className="border rounded-[20px] p-6 sm:p-8 space-y-6 shadow-2xl"
    >
      {/* SECTION 1: WHO & WHERE */}
      <div className="space-y-3">
        <div className="text-xs font-semibold text-[#8e9192] tracking-[0.2em] uppercase font-sans">
          Who &amp; Where
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {/* Operator Type */}
          <div>
            <label className="block text-xs text-[#c7c6c6] mb-1.5 font-medium font-sans">
              Operator type
            </label>
            <CustomSelect
              value={filters.operator_type || 'all'}
              onChange={(val) => handleSelect('operator_type', val)}
              options={operatorOptions}
            />
          </div>

          {/* Agency */}
          <div>
            <label className="block text-xs text-[#c7c6c6] mb-1.5 font-medium font-sans">
              Agency
            </label>
            <CustomSelect
              value={filters.agency || 'all'}
              onChange={(val) => handleSelect('agency', val)}
              options={agencyOptions}
            />
          </div>

          {/* Route / Corridor */}
          <div>
            <label className="block text-xs text-[#c7c6c6] mb-1.5 font-medium font-sans">
              Route / corridor
            </label>
            <CustomSelect
              value={filters.route || 'all'}
              onChange={(val) => handleSelect('route', val)}
              options={routeOptions}
            />
          </div>

          {/* Station / Location */}
          <div>
            <label className="block text-xs text-[#c7c6c6] mb-1.5 font-medium font-sans">
              Station / location
            </label>
            <CustomSelect
              value={filters.station || 'all'}
              onChange={(val) => handleSelect('station', val)}
              options={stationOptions}
            />
          </div>

          {/* Area */}
          <div className="sm:col-span-2 lg:col-span-4">
            <label className="block text-xs text-[#c7c6c6] mb-1.5 font-medium font-sans">
              Area / region
            </label>
            <CustomSelect
              value={filters.area || 'all'}
              onChange={(val) => handleSelect('area', val)}
              options={areaOptions}
            />
          </div>
        </div>
      </div>

      {/* SECTION 2: WHAT & WHEN */}
      <div className="border-t border-[#444748]/60 pt-5 space-y-3">
        <div className="text-xs font-semibold text-[#8e9192] tracking-[0.2em] uppercase font-sans">
          What &amp; When
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {/* Kind of Notice */}
          <div>
            <label className="block text-xs text-[#c7c6c6] mb-1.5 font-medium font-sans">
              Kind of notice
            </label>
            <CustomSelect
              value={filters.type || 'all'}
              onChange={(val) => handleSelect('type', val)}
              options={typeOptions}
            />
          </div>

          {/* Show / Status */}
          <div>
            <label className="block text-xs text-[#c7c6c6] mb-1.5 font-medium font-sans">
              Show
            </label>
            <CustomSelect
              value={filters.show || 'all'}
              onChange={(val) => handleSelect('show', val)}
              options={showOptions}
            />
          </div>

          {/* Travel Day (next 7 days) */}
          <div>
            <label className="block text-xs text-[#c7c6c6] mb-1.5 font-medium font-sans">
              Travel day (next 7 days)
            </label>
            <CustomSelect
              value={filters.travel_day || ''}
              onChange={(val) => handleSelect('travel_day', val)}
              options={travelDayOptions}
            />
          </div>

          {/* Year */}
          <div>
            <label className="block text-xs text-[#c7c6c6] mb-1.5 font-medium font-sans">
              Year
            </label>
            <CustomSelect
              value={filters.year || 'all'}
              onChange={(val) => handleSelect('year', val)}
              options={yearOptions}
            />
          </div>

          {/* End Date */}
          <div>
            <label className="block text-xs text-[#c7c6c6] mb-1.5 font-medium font-sans">
              End date
            </label>
            <CustomSelect
              value={filters.end_date || 'all'}
              onChange={(val) => handleSelect('end_date', val)}
              options={endDateOptions}
            />
          </div>

          {/* Sort */}
          <div className="sm:col-span-1 lg:col-span-3">
            <label className="block text-xs text-[#c7c6c6] mb-1.5 font-medium font-sans">
              Sort
            </label>
            <CustomSelect
              value={filters.sort || 'newest'}
              onChange={(val) => handleSelect('sort', val)}
              options={sortOptions}
            />
          </div>
        </div>

        {/* Free text search */}
        <div className="pt-2">
          {!searchOpen ? (
            <button
              onClick={() => setSearchOpen(true)}
              className="inline-flex items-center gap-2 text-xs text-[#c7c6c6] hover:text-white transition-colors font-sans"
            >
              <Search className="w-3.5 h-3.5 text-[#8e9192]" />
              <span>+ Search by keywords (optional)</span>
            </button>
          ) : (
            <div className="flex items-center gap-2 pt-1">
              <div className="relative flex-1">
                <Search className="w-4 h-4 absolute left-3.5 top-3 text-[#8e9192]" />
                <input
                  type="text"
                  placeholder="Search keywords in diversion text, station name, route, or summary..."
                  value={filters.q || ''}
                  onChange={(e) => handleSelect('q', e.target.value)}
                  className="w-full pl-10 pr-4 py-2 bg-[#141313] border border-[#444748] rounded-lg text-sm text-[#e5e2e1] placeholder-[#8e9192] focus:outline-none focus:border-white transition-colors"
                />
              </div>
              <button
                onClick={() => {
                  removeFilter('q');
                  setSearchOpen(false);
                }}
                className="p-2 text-[#8e9192] hover:text-white transition-colors"
                title="Close search"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          )}
        </div>
      </div>

      {/* ACTIVE FILTER CHIPS ROW */}
      <div className="flex flex-wrap items-center justify-between gap-3 pt-4 border-t border-[#444748]/60">
        <div className="flex flex-wrap items-center gap-2 text-xs">
          <span className="font-mono font-medium text-[#c7c6c6] mr-1">
            {totalCount} {totalCount === 1 ? 'notice' : 'notices'}
          </span>

          {activeKeys.map(([k, v]) => (
            <span
              key={k}
              style={{
                backgroundColor: '#141313',
                borderColor: '#444748',
              }}
              className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full border text-xs text-[#c7c6c6]"
            >
              <span className="text-[#8e9192]">{k}:</span>
              <span className="font-medium text-white">{v}</span>
              <button
                onClick={() => removeFilter(k)}
                className="hover:text-white ml-0.5"
              >
                <X className="w-3 h-3" />
              </button>
            </span>
          ))}
        </div>

        {activeKeys.length > 0 && (
          <button
            onClick={onReset}
            className="text-xs text-[#8e9192] hover:text-white transition-colors underline underline-offset-4 font-mono"
          >
            Clear all
          </button>
        )}
      </div>
    </div>
  );
}
