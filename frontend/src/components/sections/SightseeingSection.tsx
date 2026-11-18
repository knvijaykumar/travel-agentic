import React, { useState } from 'react';
import { useTravel } from '../../context/TravelContext';
import { PAN_INDIA_DESTINATIONS, StateDestination } from '../../data/panIndiaData';
import { Attraction } from '../../types/travel';
import { 
  MapPin, 
  Sparkles, 
  Clock, 
  IndianRupee, 
  CheckCircle2, 
  Plus, 
  Star, 
  Search, 
  Filter, 
  ArrowRight, 
  ArrowLeft,
  Compass,
  Check
} from 'lucide-react';

const REGIONS: { key: string; label: string; filter: (d: StateDestination) => boolean }[] = [
  { key: 'ALL', label: 'All 36 States & UTs', filter: () => true },
  { 
    key: 'NORTH', 
    label: 'North India', 
    filter: (d) => ['Delhi', 'Himachal Pradesh', 'Jammu and Kashmir', 'Ladakh', 'Punjab', 'Rajasthan', 'Uttar Pradesh', 'Uttarakhand', 'Haryana', 'Chandigarh'].includes(d.name) 
  },
  { 
    key: 'SOUTH', 
    label: 'South India', 
    filter: (d) => ['Andhra Pradesh', 'Karnataka', 'Kerala', 'Tamil Nadu', 'Telangana', 'Puducherry', 'Lakshadweep', 'Andaman and Nicobar Islands'].includes(d.name) 
  },
  { 
    key: 'WEST', 
    label: 'West India', 
    filter: (d) => ['Goa', 'Gujarat', 'Maharashtra', 'Dadra & Nagar Haveli and Daman & Diu'].includes(d.name) 
  },
  { 
    key: 'EAST_CENTRAL', 
    label: 'East & Central India', 
    filter: (d) => ['Bihar', 'Chhattisgarh', 'Jharkhand', 'Madhya Pradesh', 'Odisha', 'West Bengal'].includes(d.name) 
  },
  { 
    key: 'NORTHEAST', 
    label: 'North-East India', 
    filter: (d) => ['Arunachal Pradesh', 'Assam', 'Manipur', 'Meghalaya', 'Mizoram', 'Nagaland', 'Sikkim', 'Tripura'].includes(d.name) 
  },
  { 
    key: 'UT', 
    label: '8 Union Territories', 
    filter: (d) => d.type === 'Union Territory' 
  }
];

export const SightseeingSection: React.FC = () => {
  const {
    requirements,
    updateRequirements,
    selectedAttractions,
    toggleAttraction,
    setCurrentStep
  } = useTravel();

  const [activeRegion, setActiveRegion] = useState<string>('ALL');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [activeCategory, setActiveCategory] = useState<string>('ALL');

  // Currently viewed destination state (defaults to requirements.destinationState)
  const [viewedState, setViewedState] = useState<string>(requirements.destinationState || 'Rajasthan');

  const currentDestination = PAN_INDIA_DESTINATIONS.find(d => d.name === viewedState) || PAN_INDIA_DESTINATIONS[0];

  // Filter states based on region and search query
  const displayedStates = PAN_INDIA_DESTINATIONS.filter(d => {
    const regionMatch = REGIONS.find(r => r.key === activeRegion)?.filter(d) ?? true;
    const searchMatch = !searchQuery || d.name.toLowerCase().includes(searchQuery.toLowerCase()) || d.capital.toLowerCase().includes(searchQuery.toLowerCase());
    return regionMatch && searchMatch;
  });

  // Filter attractions in the currently selected destination state
  const displayedAttractions = currentDestination.attractions.filter(attr => {
    if (activeCategory !== 'ALL' && attr.category !== activeCategory) return false;
    return true;
  });

  const categories = ['ALL', 'Historical', 'Natural', 'Religious', 'Cultural', 'Adventure', 'Wildlife', 'Architectural'];

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      
      {/* Title & Pan-India Coverage Banner */}
      <div className="bg-gradient-to-r from-slate-900 via-indigo-950 to-slate-900 text-white rounded-3xl p-6 sm:p-8 shadow-xl border border-indigo-900/50">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="space-y-1.5">
            <div className="flex items-center space-x-2">
              <span className="text-[11px] font-extrabold uppercase tracking-widest bg-emerald-500/20 text-emerald-300 border border-emerald-400/30 px-3 py-1 rounded-full">
                PAN-INDIA 100% COVERAGE GUARANTEED
              </span>
              <span className="text-xs text-slate-300">All 28 States & 8 Union Territories</span>
            </div>
            <h2 className="text-2xl sm:text-3xl font-extrabold tracking-tight">
              Famous Attractions & Travel Experiences
            </h2>
            <p className="text-xs sm:text-sm text-slate-300 max-w-2xl">
              Explore authentic monuments, natural wonders, wildlife sanctuaries, and sacred shrines across the entire Indian subcontinent with verified timings and entry fees.
            </p>
          </div>

          {/* Quick Counter */}
          <div className="bg-white/10 backdrop-blur-md rounded-2xl p-4 border border-white/20 text-center min-w-[180px]">
            <span className="text-xs font-bold text-slate-300 uppercase tracking-wider block">Selected Places</span>
            <span className="text-3xl font-extrabold text-amber-300">{selectedAttractions.length}</span>
            <span className="text-[11px] text-slate-300 block mt-0.5">Clustered into itinerary</span>
          </div>
        </div>

        {/* Region Filter Chips */}
        <div className="pt-6 border-t border-slate-800/80 mt-6 flex flex-wrap gap-2">
          {REGIONS.map(reg => (
            <button
              key={reg.key}
              onClick={() => setActiveRegion(reg.key)}
              className={`px-3 py-1.5 rounded-xl text-xs font-semibold transition ${
                activeRegion === reg.key 
                  ? 'bg-blue-600 text-white shadow-sm' 
                  : 'bg-white/10 hover:bg-white/20 text-slate-300 border border-white/10'
              }`}
            >
              {reg.label}
            </button>
          ))}
        </div>
      </div>

      {/* State / UT Selector Carousel Bar */}
      <div className="space-y-3">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div className="flex items-center space-x-2">
            <Compass className="h-4 w-4 text-blue-600" />
            <h3 className="font-heading font-bold text-sm text-slate-900 uppercase tracking-wider">
              Select State / Union Territory ({displayedStates.length} Available)
            </h3>
          </div>

          {/* Search Box */}
          <div className="relative w-full sm:w-64">
            <Search className="h-4 w-4 text-slate-400 absolute left-3 top-2.5" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search state or capital..."
              className="w-full text-xs pl-9 pr-3 py-2 rounded-xl border border-slate-300 bg-white focus:outline-hidden focus:ring-2 focus:ring-blue-500 shadow-xs"
            />
          </div>
        </div>

        {/* Horizontal scroll of all 36 States & UTs */}
        <div className="flex space-x-2.5 overflow-x-auto pb-2 scrollbar-thin">
          {displayedStates.map(state => {
            const isCurrent = state.name === viewedState;
            return (
              <button
                key={state.id}
                onClick={() => {
                  setViewedState(state.name);
                  // Update requirements destination state if changed
                  updateRequirements({
                    destinationState: state.name,
                    destination: `${state.capital}, ${state.name}`
                  });
                }}
                className={`flex-shrink-0 px-4 py-2.5 rounded-xl text-xs font-bold transition flex items-center space-x-2 border ${
                  isCurrent 
                    ? 'bg-blue-600 text-white border-blue-600 shadow-md ring-2 ring-blue-400/30' 
                    : 'bg-white text-slate-700 border-slate-200 hover:border-slate-300 hover:bg-slate-50'
                }`}
              >
                <span>{state.name}</span>
                <span className={`text-[10px] px-1.5 py-0.5 rounded font-medium ${isCurrent ? 'bg-blue-700 text-white' : 'bg-slate-100 text-slate-500'}`}>
                  {state.type === 'Union Territory' ? 'UT' : 'State'}
                </span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Destination Overview Hero Banner */}
      <div className="bg-white rounded-3xl border border-slate-200 overflow-hidden shadow-sm">
        <div className="relative h-64 sm:h-80">
          <img
            src={currentDestination.heroImage}
            alt={currentDestination.name}
            className="w-full h-full object-cover"
            onError={(e) => {
              (e.target as HTMLImageElement).src = 'https://images.unsplash.com/photo-1599661046289-e31897846e41?auto=format&fit=crop&w=1200&q=80';
            }}
          />
          <div className="absolute inset-0 bg-gradient-to-t from-slate-950 via-slate-950/40 to-transparent" />
          
          <div className="absolute bottom-6 left-6 right-6 text-white space-y-2">
            <div className="flex flex-wrap items-center gap-2">
              <span className="text-[11px] font-bold uppercase tracking-wider bg-blue-600 px-3 py-1 rounded-full text-white shadow-sm">
                {currentDestination.type}
              </span>
              <span className="text-xs bg-black/40 backdrop-blur-md px-3 py-1 rounded-full text-slate-200 border border-white/20">
                Capital: <strong>{currentDestination.capital}</strong>
              </span>
              <span className="text-xs bg-black/40 backdrop-blur-md px-3 py-1 rounded-full text-slate-200 border border-white/20">
                Best Season: <strong>{currentDestination.bestSeason}</strong>
              </span>
            </div>

            <h2 className="text-2xl sm:text-4xl font-extrabold tracking-tight">
              {currentDestination.name}
            </h2>

            <p className="text-xs sm:text-sm text-slate-200 max-w-3xl leading-relaxed">
              {currentDestination.overview}
            </p>
          </div>
        </div>

        {/* Popular Activities & Cultural Tags */}
        <div className="p-5 bg-slate-50 border-t border-slate-200 flex flex-col md:flex-row items-start md:items-center justify-between gap-4 text-xs">
          <div>
            <span className="font-bold text-slate-700 uppercase tracking-wider block mb-1">Signature Experiences:</span>
            <div className="flex flex-wrap gap-2">
              {currentDestination.popularActivities.map((act, i) => (
                <span key={i} className="bg-white border border-slate-200 px-2.5 py-1 rounded-lg text-slate-800 font-medium shadow-2xs">
                  ✨ {act}
                </span>
              ))}
            </div>
          </div>

          <div className="flex flex-wrap gap-1.5 self-start md:self-auto">
            {currentDestination.culturalTags.map((tag, i) => (
              <span key={i} className="bg-blue-100 text-blue-800 border border-blue-200 px-2.5 py-0.5 rounded-full font-semibold text-[11px]">
                #{tag}
              </span>
            ))}
          </div>
        </div>
      </div>

      {/* Category Tabs */}
      <div className="flex items-center space-x-2 overflow-x-auto pb-1">
        <Filter className="h-4 w-4 text-slate-400 flex-shrink-0" />
        {categories.map(cat => (
          <button
            key={cat}
            onClick={() => setActiveCategory(cat)}
            className={`px-3 py-1.5 rounded-xl text-xs font-semibold whitespace-nowrap transition ${
              activeCategory === cat 
                ? 'bg-slate-900 text-white shadow-xs' 
                : 'bg-white border border-slate-200 text-slate-700 hover:bg-slate-50'
            }`}
          >
            {cat}
          </button>
        ))}
      </div>

      {/* Attraction Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {displayedAttractions.map(attr => {
          const isSelected = selectedAttractions.some(a => a.id === attr.id);
          return (
            <div
              key={attr.id}
              className={`rounded-2xl border overflow-hidden bg-white flex flex-col transition-all ${
                isSelected 
                  ? 'border-emerald-600 ring-2 ring-emerald-500/30 shadow-md' 
                  : 'border-slate-200 hover:border-slate-300 hover:shadow-sm'
              }`}
            >
              {/* Attraction Photo */}
              <div className="relative h-48 bg-slate-100">
                <img
                  src={attr.image}
                  alt={attr.name}
                  className="w-full h-full object-cover transition-transform duration-500 hover:scale-105"
                  onError={(e) => {
                    (e.target as HTMLImageElement).src = 'https://images.unsplash.com/photo-1599661046289-e31897846e41?auto=format&fit=crop&w=600&q=80';
                  }}
                />
                
                {/* Category Pill */}
                <span className="absolute top-3 left-3 bg-slate-900/80 backdrop-blur-md text-white text-[10px] font-bold uppercase tracking-wider px-2.5 py-1 rounded-md">
                  {attr.category}
                </span>

                {/* Provenance Badge */}
                <div className="absolute top-3 right-3 bg-white/95 backdrop-blur-md px-2 py-0.5 rounded-lg text-[10px] font-bold text-slate-900 flex items-center space-x-1 shadow-xs">
                  <span className={`h-1.5 w-1.5 rounded-full ${attr.dataSource === 'Live Provider Data' ? 'bg-emerald-500' : 'bg-blue-500'}`} />
                  <span>{attr.dataSource || 'Frontend Reference Data'}</span>
                </div>

                <div className="absolute bottom-2.5 left-3 text-white text-xs drop-shadow-md flex items-center space-x-1">
                  <MapPin className="h-3.5 w-3.5 text-emerald-400" />
                  <span className="font-medium">{attr.city}</span>
                </div>
              </div>

              {/* Card Details */}
              <div className="p-5 flex-1 flex flex-col justify-between space-y-4">
                <div className="space-y-2">
                  <h4 className="font-heading font-extrabold text-base text-slate-900 line-clamp-1">{attr.name}</h4>
                  <p className="text-xs text-slate-600 leading-relaxed line-clamp-3">{attr.description}</p>

                  {/* Highlights */}
                  {attr.highlights && attr.highlights.length > 0 && (
                    <div className="pt-1 flex flex-wrap gap-1">
                      {attr.highlights.map((h, i) => (
                        <span key={i} className="text-[10px] bg-slate-100 text-slate-700 px-2 py-0.5 rounded font-medium">
                          • {h}
                        </span>
                      ))}
                    </div>
                  )}

                  {/* Metadata: Hours & Fee */}
                  <div className="pt-2 border-t border-slate-100 grid grid-cols-2 gap-2 text-xs text-slate-500">
                    <div className="flex items-center space-x-1">
                      <Clock className="h-3.5 w-3.5 text-slate-400 flex-shrink-0" />
                      <span className="truncate">{attr.estimatedDuration}</span>
                    </div>
                    <div className="flex items-center space-x-1">
                      <IndianRupee className="h-3.5 w-3.5 text-slate-400 flex-shrink-0" />
                      <span>{attr.entryFee === 0 ? 'Free Entry' : `₹${attr.entryFee} entry`}</span>
                    </div>
                  </div>
                </div>

                {/* Add to Trip Action */}
                <button
                  onClick={() => toggleAttraction(attr)}
                  className={`w-full py-2.5 rounded-xl text-xs font-bold transition flex items-center justify-center space-x-1.5 ${
                    isSelected 
                      ? 'bg-emerald-600 hover:bg-emerald-700 text-white shadow-xs' 
                      : 'bg-slate-900 hover:bg-blue-600 text-white shadow-md'
                  }`}
                >
                  {isSelected ? (
                    <>
                      <Check className="h-4 w-4" />
                      <span>Added to Day-wise Itinerary</span>
                    </>
                  ) : (
                    <>
                      <Plus className="h-4 w-4" />
                      <span>Add to Trip Plan</span>
                    </>
                  )}
                </button>
              </div>

            </div>
          );
        })}
      </div>

      {/* Navigation Footer */}
      <div className="pt-6 border-t border-slate-200 flex justify-between items-center">
        <button
          onClick={() => setCurrentStep('hotels')}
          className="px-4 py-2.5 rounded-xl border border-slate-300 hover:bg-slate-100 text-slate-700 text-xs font-bold transition flex items-center space-x-1.5"
        >
          <ArrowLeft className="h-4 w-4" />
          <span>Back to Hotels</span>
        </button>

        <button
          onClick={() => setCurrentStep('itinerary')}
          className="px-6 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-700 text-white text-xs font-bold transition shadow-md shadow-blue-500/20 flex items-center space-x-1.5"
        >
          <span>Generate AI Day-wise Itinerary</span>
          <ArrowRight className="h-4 w-4" />
        </button>
      </div>

    </div>
  );
};

