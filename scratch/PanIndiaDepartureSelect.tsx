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
}

export const PanIndiaDepartureSelect: React.FC<PanIndiaDepartureSelectProps> = ({
  value,
  onChange,
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
    const query = searchTerm.toLowerCase().trim();

    return PAN_INDIA_AIRPORTS.filter((airport) => {
      if (selectedRegion !== 'all' && airport.region.toLowerCase() !== selectedRegion.toLowerCase()) {
        return false;
      }

      if (!query) return true;

      if (airport.code.toLowerCase().includes(query)) return true;
      if (airport.city.toLowerCase().includes(query)) return true;
      if (airport.name.toLowerCase().includes(query)) return true;
      if (airport.state.toLowerCase().includes(query)) return true;

      return false;
    });
  }, [searchTerm, selectedRegion]);

  const handleSelect = (airport: DepartureAirport) => {
    onChange(airport.city);
    setSearchTerm(airport.city);
    setIsOpen(false);
  };

  const handleClear = () => {
    onChange('');
    setSearchTerm('');
  };

  return (
    <div className="space-y-2" ref={containerRef}>
      <label className="block text-xs font-bold uppercase tracking-wider text-slate-600">
        Departure City (Origin)
      </label>

      {/* Input Field with Dropdown Indicator */}
      <div className="relative">
        <Plane className="w-4 h-4 text-slate-400 absolute left-3.5 top-3.5" />
        <input
          type="text"
          value={searchTerm}
          onFocus={() => setIsOpen(true)}
          onChange={(e) => {
            setSearchTerm(e.target.value);
            onChange(e.target.value);
            setIsOpen(true);
          }}
          placeholder="Search departure city or airport (e.g. Delhi, Mumbai, BLR)..."
          className="w-full pl-10 pr-20 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-sm font-medium text-slate-800 placeholder-slate-400 focus:bg-white focus:border-accent-600 focus:ring-2 focus:ring-accent-500/10 transition"
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
                <span>Pan-India Commercial Departure Airports</span>
              </div>
              <span className="text-[11px] text-slate-500 font-medium">
                {filteredAirports.length} airports
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
                { id: 'northeast', label: 'Northeast' },
                { id: 'central', label: 'Central' },
                { id: 'islands', label: 'Islands' },
              ].map((tab) => (
                <button
                  key={tab.id}
                  type="button"
                  onClick={() => setSelectedRegion(tab.id)}
                  className={`px-2.5 py-1 rounded-lg font-semibold shrink-0 transition ${
                    selectedRegion === tab.id
                      ? 'bg-primary-900 text-white shadow-2xs'
                      : 'bg-slate-100 text-slate-600 hover:bg-slate-200 hover:text-slate-900'
                  }`}
                >
                  {tab.label}
                </button>
              ))}
            </div>

            {/* Scrollable Airport List */}
            <div className="overflow-y-auto p-2 space-y-1 divide-y divide-slate-100">
              {filteredAirports.length > 0 ? (
                filteredAirports.map((airport: DepartureAirport) => (
                  <button
                    key={airport.code}
                    type="button"
                    onClick={() => handleSelect(airport)}
                    className="w-full text-left p-2.5 rounded-xl hover:bg-blue-50/70 transition flex items-center justify-between gap-3 group pt-2 first:pt-1"
                  >
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 rounded-xl bg-blue-100/70 text-blue-800 font-mono font-bold text-xs flex items-center justify-center shrink-0 border border-blue-200/80 shadow-2xs">
                        {airport.code}
                      </div>
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="font-bold text-sm text-slate-900 group-hover:text-blue-700 transition">
                            {airport.city}
                          </span>
                          {airport.isMajorHub && (
                            <span className="px-1.5 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider bg-emerald-50 text-emerald-700 border border-emerald-200">
                              Major Hub
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
                <div className="p-6 text-center text-slate-500 text-xs">
                  <p className="font-bold text-slate-700">No airports match &ldquo;{searchTerm}&rdquo;</p>
                  <p className="text-[11px] text-slate-400 mt-1">
                    Try searching by airport city (e.g. Delhi, Mumbai, Bengaluru), state, or 3-letter IATA code (DEL, BOM).
                  </p>
                </div>
              )}
            </div>

            {/* Footer Tip */}
            <div className="p-2 bg-slate-50 border-t border-slate-100 text-[10px] text-slate-400 text-center font-medium">
              Selecting your nearest airport discovers live commercial flights and indicative fares.
            </div>
          </div>
        )}
      </div>

      {/* Prebuilt Quick-Pick Departure Hub Pills */}
      <div className="pt-1">
        <div className="flex items-center gap-1.5 text-[11px] text-slate-400 font-bold uppercase tracking-wider mb-1.5">
          <Sparkles className="w-3.5 h-3.5 text-blue-500" />
          <span>Major Departure Airport Gateways:</span>
        </div>
        <div className="flex flex-wrap items-center gap-1.5">
          {POPULAR_DEPARTURE_PILLS.map((pill) => {
            const isSelected = value.toLowerCase() === pill.value.toLowerCase() || value.toUpperCase().includes(pill.code);
            return (
              <button
                key={pill.code}
                type="button"
                onClick={() => {
                  onChange(pill.value);
                  setSearchTerm(pill.value);
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
