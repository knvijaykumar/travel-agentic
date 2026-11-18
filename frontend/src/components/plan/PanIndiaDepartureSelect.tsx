import React, { useState, useRef, useEffect, useMemo } from 'react';
import { Plane, Search, X, ChevronDown, Building2, Sparkles } from 'lucide-react';
import {
  PAN_INDIA_AIRPORTS,
  POPULAR_DEPARTURE_PILLS,
  DepartureAirport,
} from '../../data/panIndiaLocations';

interface PanIndiaDepartureSelectProps {
  value: string;
  onChange: (city: string) => void;
  required?: boolean;
  error?: string;
  placeholder?: string;
}

export const PanIndiaDepartureSelect: React.FC<PanIndiaDepartureSelectProps> = ({
  value,
  onChange,
  required = true,
  error,
  placeholder = 'e.g. Delhi, Mumbai, Bengaluru'
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [searchTerm, setSearchTerm] = useState(value);
  const [selectedRegion, setSelectedRegion] = useState<string>('all');
  const containerRef = useRef<HTMLDivElement>(null);

  // Sync internal input when external value changes
  useEffect(() => {
    setSearchTerm(value);
  }, [value]);

  // Handle outside click
  useEffect(() => {
    const handleOutsideClick = (event: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };
    document.addEventListener('mousedown', handleOutsideClick);
    return () => {
      document.removeEventListener('mousedown', handleOutsideClick);
    };
  }, []);

  // Filter airports by search term and region
  const filteredAirports = useMemo(() => {
    const raw = (searchTerm || '').toLowerCase().trim();
    const clean = raw.replace(/[()]/g, ' ').trim();
    const terms = clean.split(/\s+/).filter(Boolean);

    return PAN_INDIA_AIRPORTS.filter((airport) => {
      if (selectedRegion !== 'all' && airport.region.toLowerCase() !== selectedRegion.toLowerCase()) {
        return false;
      }

      if (terms.length === 0) return true;

      return terms.some(term =>
        airport.code.toLowerCase().includes(term) ||
        airport.city.toLowerCase().includes(term) ||
        airport.name.toLowerCase().includes(term) ||
        airport.state.toLowerCase().includes(term)
      );
    });
  }, [searchTerm, selectedRegion]);

  const handleSelect = (airport: DepartureAirport) => {
    const formatted = `${airport.city} (${airport.code})`;
    onChange(formatted);
    setSearchTerm(formatted);
    setIsOpen(false);
  };

  const handleClear = () => {
    onChange('');
    setSearchTerm('');
    setSelectedRegion('all');
    setIsOpen(true);
  };

  return (
    <div className="space-y-2" ref={containerRef}>
      <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 flex items-center justify-between">
        <span>
          DEPARTURE CITY (ORIGIN) {required && <span className="text-red-500">*</span>}
        </span>
        <span className="text-[10px] text-blue-600 font-semibold lowercase tracking-normal">
          Pan-India Commercial Airports
        </span>
      </label>

      {/* Input Field with Dropdown Indicator */}
      <div className="relative">
        <Plane className="w-4 h-4 text-blue-600 absolute left-3.5 top-3.5" />
        <input
          type="text"
          required={required}
          value={searchTerm}
          onFocus={() => setIsOpen(true)}
          onChange={(e) => {
            setSearchTerm(e.target.value);
            onChange(e.target.value);
            setIsOpen(true);
          }}
          placeholder={placeholder}
          className={`w-full pl-10 pr-20 py-2.5 rounded-xl text-xs font-semibold bg-slate-50 focus:bg-white transition-all ${
            error
              ? 'border-2 border-rose-400 focus:ring-2 focus:ring-rose-400 bg-rose-50/20'
              : 'border border-slate-300 focus:ring-2 focus:ring-blue-500 focus:border-blue-500'
          }`}
        />

        <div className="absolute right-2.5 top-2.5 flex items-center gap-1">
          {searchTerm && (
            <button
              type="button"
              onClick={handleClear}
              className="p-1 text-slate-400 hover:text-slate-600 rounded-md hover:bg-slate-200/60 transition"
              title="Clear input"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          )}
          <button
            type="button"
            onClick={() => setIsOpen((prev) => !prev)}
            className="p-1 text-slate-400 hover:text-slate-600 rounded-md hover:bg-slate-200/60 transition"
            title="Toggle Departure Airports"
          >
            <ChevronDown className={`w-4 h-4 transition-transform duration-200 ${isOpen ? 'rotate-180' : ''}`} />
          </button>
        </div>

        {/* Dropdown Menu for Departure Airports */}
        {isOpen && (
          <div className="absolute left-0 right-0 top-full mt-2 bg-white rounded-2xl border border-slate-200 shadow-2xl z-50 overflow-hidden animate-in fade-in duration-150 max-h-[420px] flex flex-col">
            {/* Header */}
            <div className="p-3 bg-slate-50 border-b border-slate-100 flex items-center justify-between gap-2 shrink-0">
              <div className="flex items-center gap-1.5 text-xs font-bold text-slate-800">
                <Plane className="w-4 h-4 text-blue-600" />
                <span>Pan-India Departure Airports & Hubs</span>
              </div>
              <span className="text-[11px] text-slate-500 font-medium">
                {filteredAirports.length} available
              </span>
            </div>

            {/* Region Filter Chips */}
            <div className="px-3 py-2 border-b border-slate-100 flex items-center gap-1 overflow-x-auto scrollbar-none bg-white shrink-0 text-[11px]">
              {[
                { id: 'all', label: 'All Airports' },
                { id: 'north', label: 'North' },
                { id: 'south', label: 'South' },
                { id: 'west', label: 'West' },
                { id: 'east', label: 'East' },
                { id: 'central', label: 'Central' },
                { id: 'northeast', label: 'Northeast' },
              ].map((tab) => (
                <button
                  key={tab.id}
                  type="button"
                  onClick={() => setSelectedRegion(tab.id)}
                  className={`px-2.5 py-1 rounded-lg font-semibold shrink-0 transition ${
                    selectedRegion === tab.id
                      ? 'bg-blue-600 text-white shadow-xs'
                      : 'bg-slate-100 text-slate-600 hover:bg-slate-200 hover:text-slate-900'
                  }`}
                >
                  {tab.label}
                </button>
              ))}
            </div>

            {/* Airport List */}
            <div className="overflow-y-auto p-2 space-y-1 divide-y divide-slate-100">
              {filteredAirports.length > 0 ? (
                filteredAirports.map((airport: DepartureAirport) => (
                  <button
                    key={airport.code}
                    type="button"
                    onClick={() => handleSelect(airport)}
                    className="w-full text-left p-2.5 rounded-xl hover:bg-blue-50/70 transition flex items-center justify-between gap-3 group pt-2 first:pt-2"
                  >
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 rounded-xl bg-blue-100 text-blue-700 flex flex-col items-center justify-center font-bold text-xs tracking-wider shrink-0 group-hover:bg-blue-600 group-hover:text-white transition">
                        <span>{airport.code}</span>
                      </div>
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="font-bold text-sm text-slate-900 group-hover:text-blue-600 transition">
                            {airport.city}
                          </span>
                          {airport.isMajorHub && (
                            <span className="px-1.5 py-0.5 rounded text-[10px] font-bold bg-amber-50 text-amber-700 border border-amber-200">
                              Primary Hub
                            </span>
                          )}
                          <span className="text-[11px] text-slate-400 font-medium">
                            &bull; {airport.state}
                          </span>
                        </div>
                        <p className="text-[11px] text-slate-500 mt-0.5 line-clamp-1">
                          {airport.name}
                        </p>
                      </div>
                    </div>

                    <span className="text-xs font-semibold text-blue-600 opacity-0 group-hover:opacity-100 transition shrink-0">
                      Select &rarr;
                    </span>
                  </button>
                ))
              ) : (
                <div className="p-6 text-center text-slate-500 text-xs space-y-2">
                  <p className="font-bold text-slate-700">No airports match &ldquo;{searchTerm}&rdquo;</p>
                  <p className="text-[11px] text-slate-400">
                    Try searching by airport code (e.g. DEL, BOM, BLR) or city name.
                  </p>
                  <button
                    type="button"
                    onClick={() => {
                      setSearchTerm('');
                      setSelectedRegion('all');
                    }}
                    className="inline-block px-3 py-1 bg-blue-50 text-blue-600 font-bold text-xs rounded-lg hover:bg-blue-100 transition"
                  >
                    View All Commercial Airports
                  </button>
                </div>
              )}
            </div>

            {/* Footer */}
            <div className="p-2 bg-slate-50 border-t border-slate-100 text-[10px] text-slate-400 text-center font-medium">
              Only verified commercial departure airports are included for real-time flight route search.
            </div>
          </div>
        )}
      </div>

      {error && (
        <p className="text-[11px] text-rose-600 font-medium flex items-center space-x-1">
          <span>⚠</span>
          <span>{error}</span>
        </p>
      )}

      {/* Prebuilt Quick-Pick Departure Hub Pills */}
      <div className="pt-1">
        <div className="flex items-center gap-1.5 text-[11px] text-slate-500 font-bold uppercase tracking-wider mb-1.5">
          <Sparkles className="w-3.5 h-3.5 text-blue-600" />
          <span>Popular Departure Hubs:</span>
        </div>
        <div className="flex flex-wrap items-center gap-1.5">
          {POPULAR_DEPARTURE_PILLS.map((pill) => {
            const isSelected = value.toLowerCase().includes(pill.value.toLowerCase()) || value.includes(pill.code);
            return (
              <button
                key={pill.label}
                type="button"
                onClick={() => {
                  const formatted = `${pill.value} (${pill.code})`;
                  onChange(formatted);
                  setSearchTerm(formatted);
                }}
                className={`px-2.5 py-1 rounded-lg text-xs font-semibold transition border ${
                  isSelected
                    ? 'bg-blue-600 text-white border-blue-600 shadow-xs'
                    : 'bg-white hover:bg-slate-50 text-slate-700 border-slate-200 hover:border-slate-300'
                }`}
              >
                {pill.label}
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
};
