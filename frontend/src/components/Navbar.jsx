import React, { useState, useEffect, useCallback } from 'react';
import { Menu, X } from 'lucide-react';

export default function Navbar({ currentRoute, onNavigate }) {
  const [scrolled, setScrolled] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  useEffect(() => {
    let ticking = false;
    let isScrolled = false;

    const handleScroll = () => {
      if (!ticking) {
        window.requestAnimationFrame(() => {
          const y = window.scrollY;
          // Smooth hysteresis: triggers at 25px, releases at 10px
          if (!isScrolled && y > 25) {
            isScrolled = true;
            setScrolled(true);
          } else if (isScrolled && y < 10) {
            isScrolled = false;
            setScrolled(false);
          }
          ticking = false;
        });
        ticking = true;
      }
    };

    window.addEventListener('scroll', handleScroll, { passive: true });
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const navItems = [
    { id: 'current', label: 'Current notices', path: '/' },
    { id: 'ended', label: 'Ended notices', path: '/ended' },
    { id: 'alerts', label: 'Get alerts', path: '/alerts' },
    { id: 'sources', label: 'Data sources', path: '/sources' },
  ];

  const handleNav = useCallback(
    (path) => {
      onNavigate(path);
      setMobileMenuOpen(false);
    },
    [onNavigate]
  );

  return (
    <header className="sticky top-0 z-50 w-full flex justify-center pointer-events-none transition-all duration-300">
      {/* Morphing Navbar Capsule */}
      <div
        style={{
          transition: 'all 450ms cubic-bezier(0.16, 1, 0.3, 1)',
          willChange: 'width, max-width, margin-top, border-radius, background-color, border-color, box-shadow, padding',
          ...(scrolled
            ? {
                width: 'min(1240px, calc(100% - 2rem))',
                maxWidth: '1240px',
                marginTop: '12px',
                borderRadius: '9999px',
                backgroundColor: 'rgba(12, 14, 21, 0.82)',
                backdropFilter: 'blur(20px)',
                WebkitBackdropFilter: 'blur(20px)',
                borderColor: 'rgba(255, 255, 255, 0.14)',
                boxShadow:
                  '0 20px 40px -15px rgba(0, 0, 0, 0.85), 0 0 0 1px rgba(255, 255, 255, 0.04), inset 0 1px 0 rgba(255, 255, 255, 0.1)',
                padding: '8px 20px',
              }
            : {
                width: '100%',
                maxWidth: '100%',
                marginTop: '0px',
                borderRadius: '0px',
                backgroundColor: 'rgba(7, 8, 11, 0.94)',
                backdropFilter: 'blur(10px)',
                WebkitBackdropFilter: 'blur(10px)',
                borderTopColor: 'transparent',
                borderLeftColor: 'transparent',
                borderRightColor: 'transparent',
                borderBottomColor: 'rgba(255, 255, 255, 0.08)',
                boxShadow: 'none',
                padding: '14px 0px',
              }),
        }}
        className="pointer-events-auto border flex items-center justify-between"
      >
        {/* Inner Content: Constant 1240px width matching <main> */}
        <div className="w-full max-w-[1240px] mx-auto px-4 sm:px-6 flex items-center justify-between">
          {/* Left: Brand mark (matching (A) Apex style) */}
          <button
            onClick={() => handleNav('/')}
            className="flex items-center text-left group shrink-0"
          >
            <div className="w-7 h-7 rounded-full bg-white text-black font-extrabold flex items-center justify-center text-xs shadow-sm group-hover:scale-105 transition-transform font-sans">
              T
            </div>
            <span className="font-bold tracking-tight text-base sm:text-lg text-white group-hover:text-slate-200 transition-colors font-sans ml-2.5">
              TransitNotice
            </span>
          </button>

          {/* Center: Navigation Links */}
          <nav className="hidden md:flex items-center space-x-7 text-sm font-medium">
            {navItems.map((item) => {
              const isActive =
                item.id === currentRoute ||
                (item.id === 'current' && currentRoute === 'detail');
              return (
                <button
                  key={item.id}
                  onClick={() => handleNav(item.path)}
                  className={`transition-colors duration-200 text-sm font-medium ${
                    isActive
                      ? 'text-white font-semibold'
                      : 'text-slate-400 hover:text-white'
                  }`}
                >
                  {item.label}
                </button>
              );
            })}
          </nav>

          {/* Right: Live Status + Action Button */}
          <div className="flex items-center space-x-4 shrink-0">
            <div className="hidden lg:flex items-center space-x-2 text-xs text-slate-300 font-mono">
              <span className="w-2 h-2 rounded-full bg-emerald-400 shadow-[0_0_8px_rgba(52,211,153,0.9)] animate-pulse" />
              <span className="text-slate-400 text-xs">LIVE FEED</span>
            </div>

            <button
              onClick={() => handleNav('/alerts')}
              className="bg-white text-black font-semibold text-xs sm:text-sm px-5 py-2 rounded-full hover:bg-slate-200 transition-all shadow-md active:scale-95 duration-150"
            >
              Get alerts
            </button>

            {/* Mobile Menu Hamburger */}
            <button
              onClick={() => setMobileMenuOpen((prev) => !prev)}
              className="md:hidden p-1.5 text-slate-300 hover:text-white"
              aria-label="Toggle Navigation Menu"
            >
              {mobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
            </button>
          </div>
        </div>
      </div>

      {/* Mobile Dropdown Menu */}
      {mobileMenuOpen && (
        <div
          style={{
            top: scrolled ? '76px' : '64px',
            transition: 'top 300ms cubic-bezier(0.16, 1, 0.3, 1)',
          }}
          className="absolute left-4 right-4 max-w-[1160px] mx-auto bg-[#0c0d14]/98 backdrop-blur-2xl border border-white/[0.14] rounded-2xl p-4 shadow-2xl flex flex-col space-y-2 font-sans pointer-events-auto"
        >
          {navItems.map((item) => {
            const isActive =
              item.id === currentRoute ||
              (item.id === 'current' && currentRoute === 'detail');
            return (
              <button
                key={item.id}
                onClick={() => handleNav(item.path)}
                className={`text-left px-4 py-2.5 rounded-xl text-sm transition-colors ${
                  isActive
                    ? 'bg-white/10 text-white font-semibold'
                    : 'text-slate-300 hover:bg-white/5 hover:text-white'
                }`}
              >
                {item.label}
              </button>
            );
          })}
        </div>
      )}
    </header>
  );
}
