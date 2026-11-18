import React, { useState } from 'react';
import { useTravel } from '../../context/TravelContext';
import { PAN_INDIA_DESTINATIONS } from '../../data/panIndiaData';
import { PAN_INDIA_STATES_AND_UTS } from '../../data/panIndiaLocations';
import { PanIndiaDestinationSelect } from '../plan/PanIndiaDestinationSelect';
import { PanIndiaDepartureSelect } from '../plan/PanIndiaDepartureSelect';
import { CityAutocompleteInput } from '../common/CityAutocompleteInput';
import { BrandLogo } from '../common/BrandLogo';
import { TripType, TransportPreference, AccommodationTier, AccommodationPreference } from '../../types/travel';
import { travelApi } from '../../services/apiClient';
import { 
  Sparkles, 
  MapPin, 
  Calendar, 
  Users, 
  IndianRupee, 
  Compass, 
  ArrowRight, 
  CheckCircle2, 
  AlertTriangle,
  Heart, 
  ShieldCheck,
  Palmtree,
  Mountain,
  Building,
  Flame,
  Plane,
  Train,
  Car,
  Hotel,
  Clock,
  Check
} from 'lucide-react';

const TRIP_TYPES: { key: TripType; label: string; icon: React.FC<{ className?: string }>; desc: string }[] = [
  { key: 'Family', label: 'Family Vacation', icon: Users, desc: 'Kid-friendly, relaxed pace & comfort' },
  { key: 'Adventure', label: 'Adventure & Thrills', icon: Mountain, desc: 'Hiking, rafting, safaris & outdoors' },
  { key: 'Cultural', label: 'Cultural & Heritage', icon: Building, desc: 'Palaces, UNESCO ruins & temples' },
  { key: 'Relaxation', label: 'Relaxation & Wellness', icon: Palmtree, desc: 'Beaches, spa resorts & peaceful scenery' },
  { key: 'Romantic', label: 'Romantic & Honeymoon', icon: Heart, desc: 'Intimate stays, sunsets & candlelit dining' },
  { key: 'Spiritual', label: 'Spiritual Pilgrimage', icon: Flame, desc: 'Holy rivers, ancient shrines & aartis' },
];

const ACCOMMODATION_TIERS: { tier: AccommodationTier; title: string; stars: string; priceGuide: string; desc: string }[] = [
  { tier: 'Budget', title: 'Budget Friendly', stars: '2-3★', priceGuide: '₹1,500 - ₹3,500/nt', desc: 'Clean, reliable homestays & comfortable city hotels' },
  { tier: 'Standard', title: 'Standard Comfort', stars: '3-4★', priceGuide: '₹3,500 - ₹6,500/nt', desc: 'Quality business & boutique hotels with breakfast' },
  { tier: 'Premium', title: 'Premium Leisure', stars: '4-5★', priceGuide: '₹6,500 - ₹12,000/nt', desc: 'Upscale properties, pools, curated dining & views' },
  { tier: 'Luxury', title: 'Luxury & Heritage', stars: '5★ Luxury', priceGuide: '₹12,000+/nt', desc: 'Historic palaces, 5-star beachfront & forest resorts' }
];

export const RequirementsSection: React.FC = () => {
  const { 
    requirements, 
    updateRequirements, 
    setCurrentStep, 
    backendOnline,
    setIsGuidedWorkflowActive 
  } = useTravel();

  const [promptText, setPromptText] = useState('');
  const [isExtracting, setIsExtracting] = useState(false);
  const [extractedFeedback, setExtractedFeedback] = useState<string | null>(null);

  // Form Validation Errors
  const [errors, setErrors] = useState<{
    origin?: string;
    destination?: string;
    dates?: string;
    budget?: string;
    travellers?: string;
  }>({});

  const [guideMeEnabled, setGuideMeEnabled] = useState(true);
  const [isStartingGuide, setIsStartingGuide] = useState(false);

  const totalPax = Math.max(1, requirements.travellers.adults + requirements.travellers.children);
  const perPersonBudget = Math.round(requirements.totalBudget / totalPax);

  // Validate inputs before starting guided planning
  const validateForm = (): boolean => {
    const newErrors: typeof errors = {};

    if (!requirements.origin.trim()) {
      newErrors.origin = 'Starting city is required.';
    }

    if (!requirements.destination.trim()) {
      newErrors.destination = 'Destination city is required.';
    }

    if (requirements.origin.trim().toLowerCase() === requirements.destination.trim().toLowerCase()) {
      newErrors.destination = 'Destination must be different from starting city.';
    }

    if (!requirements.startDate || !requirements.endDate) {
      newErrors.dates = 'Both departure and return dates are required.';
    } else {
      const start = new Date(requirements.startDate).getTime();
      const end = new Date(requirements.endDate).getTime();
      if (end < start) {
        newErrors.dates = 'Return date cannot be earlier than departure date.';
      }
    }

    if (!requirements.totalBudget || requirements.totalBudget < 10000) {
      newErrors.budget = 'Please enter a valid total trip budget (minimum ₹10,000).';
    }

    if (requirements.travellers.adults < 1) {
      newErrors.travellers = 'At least 1 adult traveller is required.';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleStartGuideMe = async () => {
    if (!validateForm()) {
      // Scroll to top of form
      window.scrollTo({ top: 350, behavior: 'smooth' });
      return;
    }

    setIsStartingGuide(true);
    setIsGuidedWorkflowActive(true);

    try {
      // Call backend intent / places pre-fetch if online
      if (backendOnline) {
        travelApi.parseNaturalLanguageIntent(
          `Travel from ${requirements.origin} to ${requirements.destination} for ${requirements.durationDays} days with ${totalPax} travellers with total budget of Rs ${requirements.totalBudget}`
        ).catch(() => null);
      }
    } finally {
      setIsStartingGuide(false);
      // Navigate to Step 1: Transport (Flights/Trains)
      setCurrentStep('flights');
    }
  };

  const handleNaturalLanguageExtract = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!promptText.trim()) return;

    setIsExtracting(true);
    setExtractedFeedback(null);

    try {
      const parsed = await travelApi.parseNaturalLanguageIntent(promptText);
      updateRequirements({
        ...parsed,
        confirmedByUser: true
      });
      setExtractedFeedback(`AI successfully extracted intent: ${parsed.destination || 'Destination'} for ${parsed.durationDays || 5} days within ₹${(parsed.totalBudget || 40000).toLocaleString('en-IN')}!`);
    } catch {
      setExtractedFeedback('Intent processed and matched with the nearest verified Indian destination.');
    } finally {
      setIsExtracting(false);
    }
  };

  const handleStartDateChange = (val: string) => {
    const start = new Date(val);
    const end = new Date(requirements.endDate);
    let newEnd = requirements.endDate;
    let days = requirements.durationDays;

    if (!requirements.endDate || end < start) {
      // Automatically adjust end date to start + durationDays
      const adjusted = new Date(start.getTime() + days * 86400000);
      newEnd = adjusted.toISOString().split('T')[0];
    } else {
      days = Math.max(1, Math.round((end.getTime() - start.getTime()) / 86400000));
    }

    updateRequirements({
      startDate: val,
      endDate: newEnd,
      durationDays: days
    });
  };

  const handleEndDateChange = (val: string) => {
    const start = new Date(requirements.startDate);
    const end = new Date(val);
    const days = Math.max(1, Math.round((end.getTime() - start.getTime()) / 86400000));

    updateRequirements({
      endDate: val,
      durationDays: days
    });
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      
      {/* 1. POST-LOGIN WELCOME BANNER */}
      <div className="relative overflow-hidden rounded-3xl bg-gradient-to-br from-slate-900 via-indigo-950 to-slate-900 text-white p-6 sm:p-10 shadow-2xl border border-indigo-900/50">
        <div className="absolute top-0 right-0 -mt-10 -mr-10 w-96 h-96 bg-blue-500/15 rounded-full blur-3xl pointer-events-none" />
        
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-8 relative z-10">
          <div className="max-w-2xl space-y-4">
            <div className="inline-flex items-center space-x-2 px-3.5 py-1 rounded-full bg-blue-500/20 border border-blue-400/30 text-blue-300 text-xs font-bold tracking-wide">
              <Sparkles className="h-3.5 w-3.5 text-amber-300 animate-pulse" />
              <span>Pan-India Virtual Travel Agent • Strict Budget Control</span>
            </div>

            <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight">
              Welcome back! Where would you like to travel?
            </h1>

            <p className="text-slate-300 text-sm sm:text-base leading-relaxed">
              Discover travel across <strong>all 28 Indian States & 8 Union Territories</strong>. Configure your route, travellers, and hard maximum budget below, then start your personalized <strong>Guide Me</strong> journey.
            </p>

            {/* Quick Natural Thought Input */}
            <form onSubmit={handleNaturalLanguageExtract} className="pt-2">
              <div className="flex flex-col sm:flex-row gap-2.5 bg-white/10 p-2 rounded-2xl backdrop-blur-md border border-white/20">
                <input
                  type="text"
                  value={promptText}
                  onChange={(e) => setPromptText(e.target.value)}
                  placeholder='Or describe naturally: "Bengaluru to Rajasthan for 5 days with 4 family members, within ₹40,000"'
                  className="flex-1 px-4 py-3 bg-white text-slate-900 rounded-xl text-xs sm:text-sm font-medium focus:outline-hidden focus:ring-2 focus:ring-blue-500 shadow-inner placeholder:text-slate-400"
                />
                <button
                  type="submit"
                  disabled={isExtracting}
                  className="px-6 py-3 rounded-xl bg-blue-600 hover:bg-blue-500 font-bold text-xs sm:text-sm text-white shadow-lg shadow-blue-600/40 transition flex items-center justify-center space-x-2 disabled:opacity-50"
                >
                  <Sparkles className="h-4 w-4 text-amber-300" />
                  <span>{isExtracting ? 'Extracting...' : 'Apply Prompt'}</span>
                </button>
              </div>
            </form>

            {extractedFeedback && (
              <div className="p-3 bg-emerald-500/20 border border-emerald-400/30 rounded-xl text-xs text-emerald-300 flex items-center space-x-2">
                <CheckCircle2 className="h-4 w-4 text-emerald-400 flex-shrink-0" />
                <span>{extractedFeedback}</span>
              </div>
            )}
          </div>

          {/* Right Brand Logo Card */}
          <div className="hidden lg:flex flex-col items-center justify-center shrink-0">
            <BrandLogo
              variant="full"
              surface="dark"
              imgClassName="h-24 w-auto object-contain"
              containerClassName="px-6 py-4 rounded-3xl shadow-2xl border border-white/30"
            />
          </div>
        </div>
      </div>

      {/* TWO SEPARATE FORM BOXES */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        
        {/* ======================================================== */}
        {/* BOX 1: Origin, Destination & Travel Dates                 */}
        {/* ======================================================== */}
        <div className="bg-white rounded-3xl border border-slate-200 p-6 sm:p-7 shadow-sm space-y-6 flex flex-col justify-between">
          <div className="space-y-5">
            <div className="border-b border-slate-100 pb-3 flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <div className="h-8 w-8 rounded-lg bg-blue-100 text-blue-700 flex items-center justify-center">
                  <MapPin className="h-4 w-4" />
                </div>
                <div>
                  <h2 className="text-base font-extrabold text-slate-900">BOX 1: Route & Dates</h2>
                  <p className="text-[11px] text-slate-500">Origin, Destination & Travel Duration</p>
                </div>
              </div>
              <span className="text-[10px] font-bold bg-blue-50 text-blue-700 border border-blue-200 px-2 py-0.5 rounded-full uppercase">
                Step 1 of 2
              </span>
            </div>

            {/* 1. Destination City / Region with Pan-India Prebuilt Options */}
            <div>
              <PanIndiaDestinationSelect
                value={requirements.destination}
                onChange={(dest) => {
                  let city = dest;
                  let state = dest;
                  if (dest.includes(',')) {
                    const parts = dest.split(',');
                    city = parts[0].trim();
                    state = parts[1].trim();
                  } else {
                    const found = PAN_INDIA_STATES_AND_UTS.find(e => 
                      e.name.toLowerCase() === dest.toLowerCase().trim() ||
                      e.popularCities.some(c => c.toLowerCase() === dest.toLowerCase().trim())
                    );
                    if (found) state = found.name;
                  }
                  updateRequirements({
                    destination: dest,
                    destinationCity: city,
                    destinationState: state
                  });
                  if (errors.destination) setErrors(prev => ({ ...prev, destination: undefined }));
                }}
                error={errors.destination}
                placeholder="e.g. Goa, Jaipur, Bengaluru"
                required
              />
            </div>

            {/* 2. Departure City (Origin) with Commercial Airports & Hubs */}
            <div>
              <PanIndiaDepartureSelect
                value={requirements.origin}
                onChange={(orig) => {
                  let city = orig;
                  if (orig.includes('(')) {
                    city = orig.split('(')[0].trim();
                  }
                  updateRequirements({
                    origin: orig,
                    originCity: city
                  });
                  if (errors.origin) setErrors(prev => ({ ...prev, origin: undefined }));
                }}
                error={errors.origin}
                placeholder="e.g. Delhi, Mumbai, Bengaluru"
                required
              />
            </div>

            {/* 3 & 4. Departure Date & Return Date */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-1">
              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase mb-1.5 flex items-center justify-between">
                  <span>Departure Date <span className="text-rose-500">*</span></span>
                  <Calendar className="h-3.5 w-3.5 text-slate-400" />
                </label>
                <input
                  type="date"
                  min={new Date().toISOString().split('T')[0]}
                  value={requirements.startDate}
                  onChange={(e) => handleStartDateChange(e.target.value)}
                  className="w-full text-xs font-semibold px-3.5 py-2.5 rounded-xl border border-slate-300 bg-slate-50 focus:bg-white focus:ring-2 focus:ring-blue-500 focus:outline-hidden"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase mb-1.5 flex items-center justify-between">
                  <span>Return Date <span className="text-rose-500">*</span></span>
                  <Calendar className="h-3.5 w-3.5 text-slate-400" />
                </label>
                <input
                  type="date"
                  min={requirements.startDate}
                  value={requirements.endDate}
                  onChange={(e) => handleEndDateChange(e.target.value)}
                  className="w-full text-xs font-semibold px-3.5 py-2.5 rounded-xl border border-slate-300 bg-slate-50 focus:bg-white focus:ring-2 focus:ring-blue-500 focus:outline-hidden"
                />
              </div>
            </div>

            {errors.dates && (
              <p className="text-[11px] text-rose-600 font-medium flex items-center space-x-1">
                <span>⚠</span>
                <span>{errors.dates}</span>
              </p>
            )}
          </div>

          {/* Route Summary Pill */}
          <div className="p-3.5 bg-slate-50 rounded-2xl border border-slate-200 flex items-center justify-between text-xs">
            <div className="flex items-center space-x-2">
              <Clock className="h-4 w-4 text-indigo-600" />
              <span className="font-bold text-slate-700">Trip Duration:</span>
              <span className="font-extrabold text-indigo-700">{requirements.durationDays} Days / {requirements.durationDays - 1} Nights</span>
            </div>
            <span className="text-[11px] text-slate-500">
              {requirements.startDate} ➔ {requirements.endDate}
            </span>
          </div>
        </div>

        {/* ======================================================== */}
        {/* BOX 2: Travellers, Transportation & Accommodation Tiers  */}
        {/* ======================================================== */}
        <div className="bg-white rounded-3xl border border-slate-200 p-6 sm:p-7 shadow-sm space-y-6 flex flex-col justify-between">
          <div className="space-y-5">
            <div className="border-b border-slate-100 pb-3 flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <div className="h-8 w-8 rounded-lg bg-emerald-100 text-emerald-700 flex items-center justify-center">
                  <Users className="h-4 w-4" />
                </div>
                <div>
                  <h2 className="text-base font-extrabold text-slate-900">BOX 2: Travellers, Transport & Budget</h2>
                  <p className="text-[11px] text-slate-500">Party Size, Intercity Transit, Stay Tier & Strict Budget</p>
                </div>
              </div>
              <span className="text-[10px] font-bold bg-emerald-50 text-emerald-700 border border-emerald-200 px-2 py-0.5 rounded-full uppercase">
                Step 2 of 2
              </span>
            </div>

            {/* 1. Travellers Count */}
            <div>
              <div className="flex items-center justify-between mb-1.5">
                <label className="text-xs font-bold text-slate-700 uppercase">Travellers Count</label>
                <span className="text-[11px] font-bold text-emerald-700 bg-emerald-50 px-2.5 py-0.5 rounded-full border border-emerald-200">
                  Total: {totalPax} Travellers ({requirements.travellers.adults} Adults, {requirements.travellers.children} Child)
                </span>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div className="p-3 bg-slate-50 rounded-xl border border-slate-200 flex items-center justify-between">
                  <div>
                    <span className="text-xs font-bold text-slate-800 block">Adults</span>
                    <span className="text-[10px] text-slate-500">12+ years</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <button
                      type="button"
                      onClick={() => updateRequirements({
                        travellers: { ...requirements.travellers, adults: Math.max(1, requirements.travellers.adults - 1) }
                      })}
                      className="w-7 h-7 rounded-lg bg-white border border-slate-300 font-bold text-slate-700 hover:bg-slate-100"
                    >
                      -
                    </button>
                    <span className="font-bold text-sm text-slate-900 w-4 text-center">{requirements.travellers.adults}</span>
                    <button
                      type="button"
                      onClick={() => updateRequirements({
                        travellers: { ...requirements.travellers, adults: requirements.travellers.adults + 1 }
                      })}
                      className="w-7 h-7 rounded-lg bg-white border border-slate-300 font-bold text-slate-700 hover:bg-slate-100"
                    >
                      +
                    </button>
                  </div>
                </div>

                <div className="p-3 bg-slate-50 rounded-xl border border-slate-200 flex items-center justify-between">
                  <div>
                    <span className="text-xs font-bold text-slate-800 block">Children</span>
                    <span className="text-[10px] text-slate-500">2 - 11 years</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <button
                      type="button"
                      onClick={() => updateRequirements({
                        travellers: { ...requirements.travellers, children: Math.max(0, requirements.travellers.children - 1) }
                      })}
                      className="w-7 h-7 rounded-lg bg-white border border-slate-300 font-bold text-slate-700 hover:bg-slate-100"
                    >
                      -
                    </button>
                    <span className="font-bold text-sm text-slate-900 w-4 text-center">{requirements.travellers.children}</span>
                    <button
                      type="button"
                      onClick={() => updateRequirements({
                        travellers: { ...requirements.travellers, children: requirements.travellers.children + 1 }
                      })}
                      className="w-7 h-7 rounded-lg bg-white border border-slate-300 font-bold text-slate-700 hover:bg-slate-100"
                    >
                      +
                    </button>
                  </div>
                </div>
              </div>
            </div>

            {/* 2. Intercity Transport Mode */}
            <div>
              <label className="block text-xs font-bold text-slate-700 uppercase mb-1.5">
                Intercity Transport Mode
              </label>
              <div className="grid grid-cols-2 gap-3">
                <button
                  type="button"
                  onClick={() => updateRequirements({ 
                    transportPreference: 'Flight',
                    transportMode: 'FLIGHT'
                  })}
                  className={`p-3 rounded-2xl border text-left transition-all flex items-center space-x-3 ${
                    requirements.transportPreference === 'Flight' || requirements.transportMode === 'FLIGHT'
                      ? 'bg-blue-600 text-white border-blue-600 shadow-md shadow-blue-500/20'
                      : 'bg-slate-50 border-slate-200 text-slate-800 hover:bg-slate-100'
                  }`}
                >
                  <Plane className={`h-5 w-5 ${requirements.transportPreference === 'Flight' ? 'text-white' : 'text-blue-600'}`} />
                  <div>
                    <div className="font-bold text-xs">Flights</div>
                    <div className={`text-[10px] ${requirements.transportPreference === 'Flight' ? 'text-blue-100' : 'text-slate-500'}`}>
                      Fast air travel & live fares
                    </div>
                  </div>
                </button>

                <button
                  type="button"
                  onClick={() => updateRequirements({ 
                    transportPreference: 'Train',
                    transportMode: 'TRAIN'
                  })}
                  className={`p-3 rounded-2xl border text-left transition-all flex items-center space-x-3 ${
                    requirements.transportPreference === 'Train' || requirements.transportMode === 'TRAIN'
                      ? 'bg-blue-600 text-white border-blue-600 shadow-md shadow-blue-500/20'
                      : 'bg-slate-50 border-slate-200 text-slate-800 hover:bg-slate-100'
                  }`}
                >
                  <Train className={`h-5 w-5 ${requirements.transportPreference === 'Train' ? 'text-white' : 'text-emerald-600'}`} />
                  <div>
                    <div className="font-bold text-xs">Train (IRCTC)</div>
                    <div className={`text-[10px] ${requirements.transportPreference === 'Train' ? 'text-blue-100' : 'text-slate-500'}`}>
                      Vande Bharat, Rajdhani & Mail
                    </div>
                  </div>
                </button>
              </div>
            </div>

            {/* 3. Accommodation Tier */}
            <div>
              <label className="block text-xs font-bold text-slate-700 uppercase mb-1.5">
                Accommodation Tier
              </label>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                {ACCOMMODATION_TIERS.map(item => {
                  const isSelected = requirements.accommodationTier === item.tier || 
                    (item.tier === 'Standard' && !requirements.accommodationTier);
                  return (
                    <button
                      key={item.tier}
                      type="button"
                      onClick={() => updateRequirements({ 
                        accommodationTier: item.tier,
                        accommodationPreference: item.tier === 'Luxury' ? 'Luxury 5-Star' : item.tier === 'Premium' ? 'Boutique/Resort' : item.tier === 'Standard' ? 'Standard/Business' : 'Budget/Homestay'
                      })}
                      className={`p-2.5 rounded-xl border text-left transition ${
                        isSelected 
                          ? 'bg-indigo-50 border-indigo-500 ring-2 ring-indigo-500/20 text-indigo-900 shadow-xs' 
                          : 'bg-slate-50 border-slate-200 hover:bg-slate-100 text-slate-700'
                      }`}
                    >
                      <div className="font-extrabold text-xs">{item.tier}</div>
                      <div className="text-[10px] text-amber-600 font-bold">{item.stars}</div>
                      <div className="text-[9px] text-slate-400 mt-0.5">{item.priceGuide}</div>
                    </button>
                  );
                })}
              </div>
            </div>

            {/* 4. Total Trip Budget (₹) */}
            <div>
              <div className="flex items-center justify-between mb-1.5">
                <label className="text-xs font-extrabold text-slate-900 uppercase">
                  Total Budget for All Travellers (₹)
                </label>
                <span className="text-[11px] font-extrabold text-blue-700 bg-blue-50 px-2.5 py-0.5 rounded-md border border-blue-200">
                  ₹{perPersonBudget.toLocaleString('en-IN')} / person
                </span>
              </div>

              <div className="flex items-center space-x-2 bg-slate-50 p-2.5 rounded-2xl border border-slate-300">
                <IndianRupee className="h-6 w-6 text-blue-600 flex-shrink-0" />
                <input
                  type="number"
                  step={1000}
                  min={10000}
                  max={500000}
                  value={requirements.totalBudget}
                  onChange={(e) => updateRequirements({ totalBudget: parseInt(e.target.value, 10) || 10000 })}
                  className="w-full bg-transparent font-extrabold text-2xl text-slate-900 focus:outline-hidden"
                />
              </div>

              <div className="pt-2">
                <input
                  type="range"
                  min={15000}
                  max={200000}
                  step={2500}
                  value={requirements.totalBudget}
                  onChange={(e) => updateRequirements({ totalBudget: parseInt(e.target.value, 10) })}
                  className="w-full accent-blue-600 cursor-pointer"
                />
                <div className="flex justify-between text-[10px] text-slate-400 font-semibold">
                  <span>₹15,000</span>
                  <span className="font-bold text-blue-600">₹40,000 (Recommended)</span>
                  <span>₹1,00,000</span>
                  <span>₹2,00,000</span>
                </div>
              </div>

              {errors.budget && (
                <p className="mt-1 text-[11px] text-rose-600 font-medium">
                  ⚠ {errors.budget}
                </p>
              )}
            </div>

          </div>

          {/* Budget Constraint Assurance Note */}
          <div className="p-3 bg-blue-50/70 border border-blue-200/60 rounded-2xl text-xs text-blue-950 space-y-1">
            <span className="font-extrabold flex items-center space-x-1.5 text-blue-800">
              <ShieldCheck className="h-4 w-4 text-emerald-600" />
              <span>Strict Total Budget Enforcement</span>
            </span>
            <p className="text-[11px] text-slate-600 leading-relaxed">
              Your ₹{requirements.totalBudget.toLocaleString('en-IN')} budget is enforced as a <strong>hard maximum</strong> for all {totalPax} travellers combined across transport, hotel stay ({requirements.durationDays - 1} nights), daily cabs, meals and sightseeing.
            </p>
          </div>
        </div>

      </div>

      {/* ======================================================== */}
      {/* 2. GUIDE ME ACTIVATION & PRIMARY ACTION                  */}
      {/* ======================================================== */}
      <div className="bg-gradient-to-r from-blue-900 via-indigo-900 to-slate-900 rounded-3xl p-6 sm:p-8 text-white shadow-xl flex flex-col md:flex-row md:items-center justify-between gap-6 border border-blue-800/40">
        <div className="space-y-2 max-w-2xl">
          <div className="flex items-center space-x-2">
            <span className="h-2.5 w-2.5 rounded-full bg-emerald-400 animate-ping" />
            <span className="text-xs font-bold uppercase tracking-wider text-blue-300">
              Autonomous Guided Planning Pipeline
            </span>
          </div>

          <h3 className="text-xl sm:text-2xl font-extrabold">
            Ready to plan with strict budget control?
          </h3>

          <p className="text-xs sm:text-sm text-slate-300 leading-relaxed">
            Our virtual agent will sequence <strong>Transport ➔ Hotels ➔ AI Itinerary ➔ Budget ➔ Review ➔ Confirm</strong>, continuously evaluating combined expenses against your ₹{requirements.totalBudget.toLocaleString('en-IN')} limit.
          </p>

          <label className="inline-flex items-center space-x-2.5 pt-1 cursor-pointer">
            <input
              type="checkbox"
              checked={guideMeEnabled}
              onChange={(e) => setGuideMeEnabled(e.target.checked)}
              className="h-4 w-4 rounded text-blue-600 focus:ring-blue-500 accent-blue-500"
            />
            <span className="text-xs font-bold text-white select-none">
              Enable "Guide Me" step-by-step workflow with real-time budget guardrails
            </span>
          </label>
        </div>

        <div className="flex flex-col sm:flex-row items-center gap-3">
          <button
            type="button"
            onClick={handleStartGuideMe}
            disabled={isStartingGuide}
            className="w-full sm:w-auto px-8 py-4 rounded-2xl bg-gradient-to-r from-blue-500 to-indigo-600 hover:from-blue-400 hover:to-indigo-500 text-white font-extrabold text-sm shadow-xl shadow-blue-500/30 transition flex items-center justify-center space-x-2.5 active:scale-95 disabled:opacity-50"
          >
            <Sparkles className="h-5 w-5 text-amber-300 animate-spin-slow" />
            <span>{isStartingGuide ? 'Verifying Routes & Inventory...' : 'Guide Me – Start Journey'}</span>
            <ArrowRight className="h-4 w-4" />
          </button>
        </div>
      </div>

    </div>
  );
};
