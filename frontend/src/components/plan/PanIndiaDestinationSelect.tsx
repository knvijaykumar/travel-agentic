import React, { useState, useRef, useEffect, useMemo } from 'react';
import { MapPin, Search, X, ChevronDown, Compass, Sparkles } from 'lucide-react';
import {
  PAN_INDIA_STATES_AND_UTS,
  POPULAR_DESTINATION_PILLS,
  IndianStateOrUT,
} from '../../data/panIndiaLocations';

interface PanIndiaDestinationSelectProps {
  value: string;
  onChange: (destination: string) => void;
  required?: boolean;
  error?: string;
  placeholder?: string;
}

export const PanIndiaDestinationSelect: React.FC<PanIndiaDestinationSelectProps> = ({
  value,
  onChange,
  required = true,
  error,
  placeholder = "e.g. Goa, Jaipur, Bengaluru"
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [searchTerm, setSearchTerm] = useState(value);
  const [selectedRegion, setSelectedRegion] = useState<string>('all');
  const containerRef = useRef<HTMLDivElement>(null);

  // Keep internal input text in sync when external value changes
  useEffect(() => {
    setSearchTerm(value);
  }, [value]);

  // Handle outside click to close dropdown
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

  // Filter states and cities based on search term and region tab
  const filteredEntities = useMemo(() => {
    const raw = (searchTerm || '').toLowerCase().trim();
    // Clean punctuation like commas, parentheses
    const clean = raw.replace(/[,()]/g, ' ').trim();
    const terms = clean.split(/\s+/).filter(Boolean);

    return PAN_INDIA_STATES_AND_UTS.filter((entity) => {
      // Region filter
      if (selectedRegion !== 'all' && entity.region.toLowerCase() !== selectedRegion.toLowerCase()) {
        return false;
      }

      if (terms.length === 0) return true;

      // Match state name
      if (terms.some(t => entity.name.toLowerCase().includes(t))) return true;
      // Match popular cities
      if (terms.some(t => entity.popularCities.some(c => c.toLowerCase().includes(t) || t.includes(c.toLowerCase())))) return true;
      // Match key attractions
      if (terms.some(t => entity.keyAttractions.some(a => a.toLowerCase().includes(t)))) return true;
      // Match region
      if (terms.some(t => entity.region.toLowerCase().includes(t))) return true;

      return false;
    });
  }, [searchTerm, selectedRegion]);

  const handleSelect = (destinationName: string) => {
    onChange(destinationName);
    setSearchTerm(destinationName);
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
          DESTINATION CITY / REGION {required && <span className="text-red-500">*</span>}
        </span>
        <span className="text-[10px] text-blue-600 font-semibold lowercase tracking-normal">
          Pan-India: 28 States & 8 UTs
        </span>
      </label>

      {/* Input Field with Dropdown Indicator */}
      <div className="relative">
        <MapPin className="w-4 h-4 text-blue-600 absolute left-3.5 top-3.5" />
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
            title="Toggle Pan-India Options"
          >
            <ChevronDown className={`w-4 h-4 transition-transform duration-200 ${isOpen ? 'rotate-180' : ''}`} />
          </button>
        </div>

        {/* Dropdown Menu for Pan-India Prebuilt Options */}
        {isOpen && (
          <div className="absolute left-0 right-0 top-full mt-2 bg-white rounded-2xl border border-slate-200 shadow-2xl z-50 overflow-hidden animate-in fade-in duration-150 max-h-[460px] flex flex-col">
            {/* Header with region tabs */}
            <div className="p-3 bg-slate-50 border-b border-slate-100 flex items-center justify-between gap-2 shrink-0">
              <div className="flex items-center gap-1.5 text-xs font-bold text-slate-800">
                <Compass className="w-4 h-4 text-blue-600" />
                <span>Pan-India Destination Directory (36 States & UTs)</span>
              </div>
              <span className="text-[11px] text-slate-500 font-medium">
                {filteredEntities.length} matching
              </span>
            </div>

            {/* Region Filter Chips */}
            <div className="px-3 py-2 border-b border-slate-100 flex items-center gap-1 overflow-x-auto scrollbar-none bg-white shrink-0 text-[11px]">
              {[
                { id: 'all', label: 'All India (36)' },
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
                  onClick={() => {
                    setSelectedRegion(tab.id);
                  }}
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

            {/* Scrollable List of States and Cities */}
            <div className="overflow-y-auto p-2 space-y-1.5 divide-y divide-slate-100">
              {filteredEntities.length > 0 ? (
                filteredEntities.map((entity: IndianStateOrUT) => (
                  <div key={entity.id} className="pt-2 first:pt-0">
                    {/* Main State / UT row */}
                    <button
                      type="button"
                      onClick={() => handleSelect(entity.name)}
                      className="w-full text-left p-2.5 rounded-xl hover:bg-blue-50/70 transition flex items-start justify-between gap-3 group"
                    >
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="font-bold text-sm text-slate-900 group-hover:text-blue-600 transition">
                            {entity.name}
                          </span>
                          <span
                            className={`px-1.5 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider ${
                              entity.type === 'state'
                                ? 'bg-blue-50 text-blue-700 border border-blue-200'
                                : 'bg-purple-50 text-purple-700 border border-purple-200'
                            }`}
                          >
                            {entity.type === 'state' ? 'State' : 'UT'}
                          </span>
                          <span className="text-[11px] text-slate-400 font-medium">
                            &bull; {entity.region} India
                          </span>
                        </div>
                        <p className="text-[11px] text-slate-500 mt-0.5 line-clamp-1">
                          {entity.tagline}
                        </p>
                      </div>

                      <span className="text-xs font-semibold text-blue-600 opacity-0 group-hover:opacity-100 transition shrink-0 self-center">
                        Select &rarr;
                      </span>
                    </button>

                    {/* Popular sub-cities & attractions pills */}
                    <div className="pl-3 pr-2 pb-1.5 pt-0.5 flex flex-wrap items-center gap-1.5">
                      <span className="text-[10px] text-slate-400 font-bold uppercase tracking-wider">
                        Explore:
                      </span>
                      {entity.popularCities.map((city) => (
                        <button
                          key={city}
                          type="button"
                          onClick={() => handleSelect(`${city}, ${entity.name}`)}
                          className="px-2 py-0.5 bg-slate-100 hover:bg-blue-100 text-slate-700 hover:text-blue-800 rounded-md text-[11px] font-medium transition"
                        >
                          {city}
                        </button>
                      ))}
                    </div>
                  </div>
                ))
              ) : (
                <div className="p-6 text-center text-slate-500 text-xs space-y-2">
                  <p className="font-bold text-slate-700">No destinations match &ldquo;{searchTerm}&rdquo;</p>
                  <p className="text-[11px] text-slate-400">
                    Try searching by state name (e.g. Rajasthan, Kerala, Assam), city (e.g. Jaipur, Kochi), or clear filters.
                  </p>
                  <button
                    type="button"
                    onClick={() => {
                      setSearchTerm('');
                      setSelectedRegion('all');
                    }}
                    className="inline-block px-3 py-1 bg-blue-50 text-blue-600 font-bold text-xs rounded-lg hover:bg-blue-100 transition"
                  >
                    View All 36 States & UTs
                  </button>
                </div>
              )}
            </div>

            {/* Footer with quick tip */}
            <div className="p-2 bg-slate-50 border-t border-slate-100 text-[10px] text-slate-400 text-center font-medium">
              Click any state or specific city to auto-configure your travel itinerary.
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

      {/* Prebuilt Quick-Pick Destination Pills */}
      <div className="pt-1">
        <div className="flex items-center gap-1.5 text-[11px] text-slate-500 font-bold uppercase tracking-wider mb-1.5">
          <Sparkles className="w-3.5 h-3.5 text-blue-600" />
          <span>Prebuilt Pan-India Destinations:</span>
        </div>
        <div className="flex flex-wrap items-center gap-1.5">
          {POPULAR_DESTINATION_PILLS.map((pill) => {
            const isSelected = value.toLowerCase().includes(pill.state.toLowerCase()) || value === pill.value;
            return (
              <button
                key={pill.label}
                type="button"
                onClick={() => handleSelect(pill.value)}
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
