import React, { useState, useRef, useEffect } from 'react';
import { ALL_INDIAN_CITIES, IndianCityRecord, searchIndianCities } from '../../data/citiesData';
import { MapPin, Search, Plane, Train, Check, X } from 'lucide-react';

interface CityAutocompleteInputProps {
  label: string;
  value: string;
  onChange: (city: string, state: string, fullFormatted: string) => void;
  placeholder?: string;
  error?: string | null;
  required?: boolean;
}

export const CityAutocompleteInput: React.FC<CityAutocompleteInputProps> = ({
  label,
  value,
  onChange,
  placeholder = 'Type city, state or airport (e.g. Bengaluru, Jaipur)',
  error,
  required = false
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [searchTerm, setSearchTerm] = useState(value);
  const wrapperRef = useRef<HTMLDivElement>(null);

  // Sync internal search term when external value changes
  useEffect(() => {
    setSearchTerm(value);
  }, [value]);

  // Handle outside click to close dropdown
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (wrapperRef.current && !wrapperRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const suggestions = searchIndianCities(searchTerm);

  const handleSelectCity = (record: IndianCityRecord) => {
    const formatted = `${record.city}, ${record.state} (${record.airportCode})`;
    setSearchTerm(formatted);
    onChange(record.city, record.state, formatted);
    setIsOpen(false);
  };

  const handleClear = () => {
    setSearchTerm('');
    onChange('', '', '');
    setIsOpen(true);
  };

  return (
    <div ref={wrapperRef} className="relative w-full">
      <label className="block text-xs font-bold text-slate-700 uppercase mb-1.5 flex items-center justify-between">
        <span>
          {label} {required && <span className="text-rose-500">*</span>}
        </span>
        <span className="text-[10px] text-blue-600 font-semibold lowercase tracking-normal">
          Pan-India: 28 States & 8 UTs
        </span>
      </label>

      <div className="relative">
        <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-400">
          <MapPin className="h-4 w-4 text-blue-600" />
        </div>

        <input
          type="text"
          value={searchTerm}
          onChange={(e) => {
            setSearchTerm(e.target.value);
            setIsOpen(true);
          }}
          onFocus={() => setIsOpen(true)}
          placeholder={placeholder}
          className={`w-full pl-9 pr-9 py-2.5 rounded-xl border text-xs font-semibold bg-slate-50 focus:bg-white focus:outline-hidden transition-all ${
            error 
              ? 'border-rose-400 focus:ring-2 focus:ring-rose-400 focus:border-rose-400 bg-rose-50/20' 
              : 'border-slate-300 focus:ring-2 focus:ring-blue-500 focus:border-blue-500'
          }`}
        />

        {searchTerm && (
          <button
            type="button"
            onClick={handleClear}
            className="absolute inset-y-0 right-0 pr-3 flex items-center text-slate-400 hover:text-slate-600"
          >
            <X className="h-3.5 w-3.5" />
          </button>
        )}
      </div>

      {error && (
        <p className="mt-1 text-[11px] text-rose-600 font-medium flex items-center space-x-1">
          <span>⚠</span>
          <span>{error}</span>
        </p>
      )}

      {/* Autocomplete Dropdown */}
      {isOpen && (
        <div className="absolute z-50 mt-1.5 w-full bg-white rounded-2xl border border-slate-200 shadow-xl overflow-hidden max-h-72 flex flex-col">
          <div className="px-3.5 py-2 bg-slate-50 border-b border-slate-100 flex items-center justify-between text-[11px] font-bold text-slate-500">
            <span>
              {!searchTerm ? 'Prebuilt Popular Hubs' : `Suggestions (${suggestions.length})`}
            </span>
            <span className="text-slate-400 font-normal">Click to select city</span>
          </div>

          <div className="overflow-y-auto divide-y divide-slate-100">
            {suggestions.length === 0 ? (
              <div className="p-4 text-center text-xs text-slate-500">
                No matching Indian city found for "{searchTerm}". Please select an authorized city in India.
              </div>
            ) : (
              suggestions.map((item, idx) => {
                const isCurrent = value.includes(item.city);
                return (
                  <button
                    key={`${item.city}-${item.state}-${idx}`}
                    type="button"
                    onClick={() => handleSelectCity(item)}
                    className={`w-full px-3.5 py-2.5 text-left text-xs transition flex items-center justify-between ${
                      isCurrent 
                        ? 'bg-blue-50/80 text-blue-900 font-bold' 
                        : 'hover:bg-slate-50 text-slate-800'
                    }`}
                  >
                    <div className="flex items-center space-x-2.5">
                      <div className="h-7 w-7 rounded-lg bg-blue-100 text-blue-700 flex items-center justify-center font-bold text-[10px] flex-shrink-0">
                        {item.airportCode !== 'N/A' ? item.airportCode : 'IN'}
                      </div>
                      <div>
                        <div className="font-bold text-slate-900 flex items-center space-x-1">
                          <span>{item.city}</span>
                          <span className="text-[10px] font-normal text-slate-500">({item.state})</span>
                        </div>
                        <div className="text-[10px] text-slate-400 flex items-center space-x-2 mt-0.5">
                          {item.airportCode !== 'N/A' && (
                            <span className="flex items-center space-x-0.5">
                              <Plane className="h-2.5 w-2.5 text-blue-500" />
                              <span>{item.airportCode}</span>
                            </span>
                          )}
                          {item.railwayCode !== 'N/A' && (
                            <span className="flex items-center space-x-0.5">
                              <Train className="h-2.5 w-2.5 text-emerald-500" />
                              <span>{item.railwayCode} Rly</span>
                            </span>
                          )}
                        </div>
                      </div>
                    </div>

                    {isCurrent && (
                      <Check className="h-4 w-4 text-blue-600 flex-shrink-0" />
                    )}
                  </button>
                );
              })
            )}
          </div>
        </div>
      )}
    </div>
  );
};

