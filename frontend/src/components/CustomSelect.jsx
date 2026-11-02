import React, { useState, useRef, useEffect } from 'react';
import { ChevronDown, Check } from 'lucide-react';

export default function CustomSelect({
  value,
  onChange,
  options = [],
  placeholder = 'Select...',
  disabled = false,
  className = '',
}) {
  const [open, setOpen] = useState(false);
  const containerRef = useRef(null);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleOutsideClick = (e) => {
      if (containerRef.current && !containerRef.current.contains(e.target)) {
        setOpen(false);
      }
    };
    if (open) {
      document.addEventListener('pointerdown', handleOutsideClick);
    }
    return () => document.removeEventListener('pointerdown', handleOutsideClick);
  }, [open]);

  // Close on Escape key
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Escape') setOpen(false);
    };
    if (open) {
      window.addEventListener('keydown', handleKeyDown);
    }
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [open]);

  // Find currently selected option
  const selectedOption = options.find((opt) => String(opt.value) === String(value));
  const displayLabel = selectedOption ? selectedOption.label : placeholder;

  return (
    <div ref={containerRef} className={`relative w-full ${className}`}>
      {/* Trigger Button */}
      <button
        type="button"
        disabled={disabled}
        onClick={() => setOpen((prev) => !prev)}
        className={`w-full flex items-center justify-between bg-[#141313] text-[#e5e2e1] border transition-all duration-150 rounded-lg px-3.5 py-2 text-sm font-sans text-left select-none ${
          open
            ? 'border-white/70 ring-1 ring-white/20 shadow-lg'
            : 'border-[#444748] hover:border-white/40'
        } ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}`}
        aria-haspopup="listbox"
        aria-expanded={open}
      >
        <span className="truncate pr-2 text-xs sm:text-sm font-medium">
          {displayLabel}
        </span>
        <ChevronDown
          className={`w-4 h-4 text-[#8e9192] shrink-0 transition-transform duration-200 ${
            open ? 'rotate-180 text-white' : ''
          }`}
        />
      </button>

      {/* Sleek Dark Dropdown Menu */}
      {open && (
        <div
          role="listbox"
          style={{
            scrollbarWidth: 'thin',
            scrollbarColor: 'rgba(255, 255, 255, 0.2) transparent',
          }}
          className="absolute z-50 left-0 right-0 top-full mt-1.5 max-h-60 overflow-y-auto bg-[#12151e]/98 backdrop-blur-2xl border border-white/[0.14] rounded-xl shadow-2xl shadow-black/90 p-1 space-y-0.5 animate-in fade-in zoom-in-95 duration-100"
        >
          {options.length === 0 ? (
            <div className="px-3.5 py-2.5 text-xs text-slate-500 font-sans">
              No options available
            </div>
          ) : (
            options.map((opt) => {
              const isSelected = String(opt.value) === String(value);
              return (
                <button
                  key={String(opt.value)}
                  type="button"
                  role="option"
                  aria-selected={isSelected}
                  onClick={() => {
                    onChange(opt.value);
                    setOpen(false);
                  }}
                  className={`w-full flex items-center justify-between text-left px-3 py-2 rounded-lg text-xs sm:text-sm transition-colors duration-100 font-sans group ${
                    isSelected
                      ? 'bg-white/[0.12] text-white font-medium'
                      : 'text-slate-300 hover:bg-white/[0.07] hover:text-white'
                  }`}
                >
                  <span className="truncate pr-2">{opt.label}</span>
                  <div className="flex items-center gap-1.5 shrink-0 ml-2">
                    {opt.count !== undefined && (
                      <span
                        className={`text-[10px] font-mono px-1.5 py-0.5 rounded ${
                          isSelected
                            ? 'bg-white/20 text-white'
                            : 'bg-white/[0.06] text-slate-400 group-hover:text-slate-200'
                        }`}
                      >
                        {opt.count}
                      </span>
                    )}
                    {isSelected && <Check className="w-3.5 h-3.5 text-white" />}
                  </div>
                </button>
              );
            })
          )}
        </div>
      )}
    </div>
  );
}

