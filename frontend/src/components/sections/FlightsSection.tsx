import React, { useState } from 'react';
import { useTravel } from '../../context/TravelContext';
import { FlightOption, TrainOption } from '../../types/travel';
import { 
  Plane, 
  Train,
  Clock, 
  ArrowRight, 
  CheckCircle2, 
  Luggage, 
  ShieldCheck, 
  ExternalLink, 
  SlidersHorizontal, 
  IndianRupee, 
  AlertCircle,
  AlertTriangle,
  Sparkles,
  ChevronRight,
  ArrowLeft,
  Info
} from 'lucide-react';

export const FlightsSection: React.FC = () => {
  const {
    requirements,
    updateRequirements,
    availableFlights,
    selectedFlight,
    selectFlight,
    availableTrains,
    selectedTrain,
    selectTrain,
    setCurrentStep
  } = useTravel();

  const [activeTab, setActiveTab] = useState<'FLIGHT' | 'TRAIN'>(
    requirements.transportPreference === 'Train' || requirements.transportMode === 'TRAIN' ? 'TRAIN' : 'FLIGHT'
  );

  const [sortBy, setSortBy] = useState<'recommended' | 'cheapest' | 'fastest' | 'departure'>('recommended');
  const [selectedAirline, setSelectedAirline] = useState<string>('ALL');
  const [nonStopOnly, setNonStopOnly] = useState<boolean>(false);
  const [redirectModalFlight, setRedirectModalFlight] = useState<FlightOption | null>(null);
  const [redirectModalTrain, setRedirectModalTrain] = useState<TrainOption | null>(null);

  const totalPax = Math.max(1, requirements.travellers.adults + requirements.travellers.children);
  const totalTripBudget = requirements.totalBudget || 40000;

  // Compute selected transport cost
  const activeTransportCost = activeTab === 'FLIGHT'
    ? (selectedFlight ? selectedFlight.totalPrice : 0)
    : (selectedTrain ? selectedTrain.totalPrice : 0);

  const remainingForStayAndFood = totalTripBudget - activeTransportCost;
  const transportPct = Math.round((activeTransportCost / totalTripBudget) * 100);

  const handleOpenAirlinePortal = (flight: FlightOption) => {
    let url = flight.bookingUrl;
    if (!url || (!url.startsWith('http://') && !url.startsWith('https://'))) {
      url = `https://www.google.com/travel/flights?q=flights+from+${flight.originCode}+to+${flight.destinationCode}`;
    }
    try {
      const parsed = new URL(url);
      if (parsed.protocol === 'http:' || parsed.protocol === 'https:') {
        window.open(url, '_blank', 'noopener,noreferrer');
      }
    } catch {
      window.open(`https://www.google.com/travel/flights?q=flights+from+${flight.originCode}+to+${flight.destinationCode}`, '_blank', 'noopener,noreferrer');
    }
  };

  const handleOpenIrctcPortal = () => {
    window.open('https://www.irctc.co.in/nget/train-search', '_blank', 'noopener,noreferrer');
  };

  // Filter & sort flights
  const filteredFlights = availableFlights
    .filter(f => {
      if (selectedAirline !== 'ALL' && f.airline !== selectedAirline) return false;
      if (nonStopOnly && f.stops > 0) return false;
      return true;
    })
    .sort((a, b) => {
      if (sortBy === 'cheapest') return a.totalPrice - b.totalPrice;
      if (sortBy === 'fastest') return a.duration.localeCompare(b.duration);
      if (sortBy === 'departure') return a.departureTime.localeCompare(b.departureTime);
      return (b.recommended ? 1 : 0) - (a.recommended ? 1 : 0);
    });

  // Filter & sort trains
  const filteredTrains = [...availableTrains].sort((a, b) => {
    if (sortBy === 'cheapest') return a.totalPrice - b.totalPrice;
    if (sortBy === 'fastest') return a.duration.localeCompare(b.duration);
    return (b.recommended ? 1 : 0) - (a.recommended ? 1 : 0);
  });

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
      
      {/* 1. Header & Transport Mode Switcher */}
      <div className="bg-white rounded-3xl border border-slate-200 p-6 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2 text-xs font-bold uppercase tracking-wider text-slate-400">
            <span>Step 1: Intercity Transportation</span>
            <span>•</span>
            <span className="text-blue-600">Strict Total Budget Evaluation</span>
          </div>
          <div className="mt-1 flex items-center space-x-3 text-xl font-extrabold text-slate-900">
            <span>{requirements.origin}</span>
            <span className="text-blue-600">➔</span>
            <span>{requirements.destination}</span>
          </div>
          <div className="mt-1 text-xs text-slate-500 font-medium">
            Departure: <strong className="text-slate-800">{requirements.startDate}</strong> | Travellers: <strong className="text-slate-800">{totalPax} Passengers</strong> ({requirements.travellers.adults}A, {requirements.travellers.children}C)
          </div>
        </div>

        {/* Mode Switcher Tabs */}
        <div className="flex items-center space-x-2 bg-slate-100 p-1.5 rounded-2xl border border-slate-200">
          <button
            type="button"
            onClick={() => {
              setActiveTab('FLIGHT');
              updateRequirements({ transportPreference: 'Flight', transportMode: 'FLIGHT' });
            }}
            className={`px-4 py-2 rounded-xl text-xs font-bold transition flex items-center space-x-1.5 ${
              activeTab === 'FLIGHT'
                ? 'bg-white text-blue-700 shadow-sm'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            <Plane className="h-4 w-4 text-blue-600" />
            <span>Flights</span>
          </button>

          <button
            type="button"
            onClick={() => {
              setActiveTab('TRAIN');
              updateRequirements({ transportPreference: 'Train', transportMode: 'TRAIN' });
            }}
            className={`px-4 py-2 rounded-xl text-xs font-bold transition flex items-center space-x-1.5 ${
              activeTab === 'TRAIN'
                ? 'bg-white text-emerald-700 shadow-sm'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            <Train className="h-4 w-4 text-emerald-600" />
            <span>Train (IRCTC)</span>
          </button>
        </div>
      </div>

      {/* 2. STRICT BUDGET WATCH BAR */}
      <div className={`p-4 rounded-2xl border text-xs flex flex-col md:flex-row md:items-center justify-between gap-3 ${
        remainingForStayAndFood < (totalTripBudget * 0.4)
          ? 'bg-amber-50/90 border-amber-300 text-amber-950'
          : 'bg-blue-50/90 border-blue-200 text-blue-950'
      }`}>
        <div className="flex items-center space-x-3">
          <div className="h-9 w-9 rounded-xl bg-white shadow-xs flex items-center justify-center font-extrabold text-blue-600">
            <IndianRupee className="h-4 w-4" />
          </div>
          <div>
            <span className="font-extrabold block text-sm">
              Strict Budget Watch: ₹{activeTransportCost.toLocaleString('en-IN')} allocated for transport ({transportPct}% of ₹{totalTripBudget.toLocaleString('en-IN')})
            </span>
            <span className="text-slate-600 text-[11px]">
              Leaves <strong className="text-emerald-700 font-extrabold">₹{remainingForStayAndFood.toLocaleString('en-IN')}</strong> remaining for Hotels, Local Cabs, Dining & Sightseeing.
            </span>
          </div>
        </div>

        {activeTransportCost > 0 && (
          <button
            onClick={() => setCurrentStep('hotels')}
            className="px-4 py-2 rounded-xl bg-blue-600 hover:bg-blue-700 text-white font-bold text-xs shadow-md shadow-blue-500/20 flex items-center space-x-1 self-start md:self-auto"
          >
            <span>Proceed to Hotels (₹{remainingForStayAndFood.toLocaleString('en-IN')} avail)</span>
            <ArrowRight className="h-3.5 w-3.5" />
          </button>
        )}
      </div>

      {/* 3. FLIGHTS VIEW */}
      {activeTab === 'FLIGHT' && (
        <div className="space-y-4">
          <div className="flex flex-wrap items-center justify-between gap-3 bg-white p-3 rounded-xl border border-slate-200 text-xs font-medium">
            <div className="flex items-center space-x-2">
              <span className="text-slate-500 font-bold">Filter Airline:</span>
              <select
                value={selectedAirline}
                onChange={(e) => setSelectedAirline(e.target.value)}
                className="px-2.5 py-1 rounded-lg border border-slate-300 bg-slate-50 text-xs font-semibold"
              >
                <option value="ALL">All Airlines ({availableFlights.length})</option>
                {Array.from(new Set(availableFlights.map(f => f.airline))).map(a => (
                  <option key={a} value={a}>{a}</option>
                ))}
              </select>
            </div>

            <div className="flex items-center space-x-2">
              <span className="text-slate-500 font-bold">Sort By:</span>
              {(['recommended', 'cheapest', 'fastest'] as const).map(s => (
                <button
                  key={s}
                  onClick={() => setSortBy(s)}
                  className={`px-2.5 py-1 rounded-lg capitalize transition ${
                    sortBy === s ? 'bg-blue-600 text-white font-bold' : 'bg-slate-100 hover:bg-slate-200 text-slate-700'
                  }`}
                >
                  {s}
                </button>
              ))}
            </div>
          </div>

          <div className="space-y-4">
            {filteredFlights.map(flight => {
              const isSelected = selectedFlight?.id === flight.id;
              const consumesPct = Math.round((flight.totalPrice / totalTripBudget) * 100);
              const isHeavyOnBudget = consumesPct > 45;

              return (
                <div
                  key={flight.id}
                  className={`bg-white rounded-2xl border p-5 transition-all ${
                    isSelected 
                      ? 'border-blue-600 ring-2 ring-blue-500/30 shadow-md' 
                      : 'border-slate-200 hover:border-slate-300 hover:shadow-xs'
                  }`}
                >
                  <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
                    
                    {/* Airline & Number */}
                    <div className="flex items-center space-x-3.5">
                      <div className="h-11 w-11 rounded-xl bg-blue-900 text-white font-extrabold text-sm flex items-center justify-center">
                        {flight.airlineCode}
                      </div>
                      <div>
                        <div className="flex items-center space-x-2">
                          <h3 className="font-extrabold text-slate-900 text-sm">{flight.airline}</h3>
                          <span className="text-xs text-slate-500 font-mono font-medium">({flight.flightNumber})</span>
                          {flight.cheapest && (
                            <span className="text-[10px] bg-emerald-100 text-emerald-800 font-bold px-2 py-0.5 rounded-full">
                              Best Fare
                            </span>
                          )}
                        </div>
                        <p className="text-[11px] text-slate-400 mt-0.5">{flight.providerNotice}</p>
                      </div>
                    </div>

                    {/* Schedule */}
                    <div className="flex items-center space-x-6 text-center">
                      <div>
                        <div className="text-base font-extrabold text-slate-900">{flight.departureTime}</div>
                        <div className="text-xs font-bold text-slate-600">{flight.originCode}</div>
                      </div>

                      <div className="flex flex-col items-center">
                        <span className="text-[10px] text-slate-400 font-semibold">{flight.duration}</span>
                        <div className="w-20 sm:w-28 h-0.5 bg-slate-200 my-1 relative">
                          <Plane className="h-3 w-3 text-blue-600 absolute right-1/2 translate-x-1/2 -top-1" />
                        </div>
                        <span className="text-[10px] text-emerald-600 font-bold">
                          {flight.stops === 0 ? 'Direct Non-stop' : `${flight.stops} Stop`}
                        </span>
                      </div>

                      <div>
                        <div className="text-base font-extrabold text-slate-900">{flight.arrivalTime}</div>
                        <div className="text-xs font-bold text-slate-600">{flight.destinationCode}</div>
                      </div>
                    </div>

                    {/* Budget Impact Indicator */}
                    <div className="text-xs space-y-0.5 lg:text-right">
                      <div className="text-lg font-extrabold text-slate-900 flex items-center lg:justify-end">
                        <IndianRupee className="h-4 w-4 text-blue-600" />
                        <span>₹{flight.totalPrice.toLocaleString('en-IN')}</span>
                      </div>
                      <div className="text-[10px] text-slate-400">
                        ₹{flight.pricePerPerson.toLocaleString('en-IN')}/person • for {totalPax} pax
                      </div>
                      <div className={`text-[10px] font-bold ${
                        isHeavyOnBudget ? 'text-amber-700' : 'text-emerald-700'
                      }`}>
                        {isHeavyOnBudget 
                          ? `Consumes ${consumesPct}% of budget` 
                          : `Budget Friendly (${consumesPct}%)`}
                      </div>
                    </div>

                    {/* Actions */}
                    <div className="flex items-center space-x-2 pt-2 lg:pt-0 border-t lg:border-t-0 border-slate-100 justify-end">
                      <button
                        type="button"
                        onClick={() => setRedirectModalFlight(flight)}
                        className="p-2 rounded-xl border border-slate-200 hover:bg-slate-50 text-slate-600 text-xs font-bold"
                        title="View External Redirect Details"
                      >
                        <ExternalLink className="h-4 w-4" />
                      </button>

                      <button
                        type="button"
                        onClick={() => selectFlight(flight)}
                        className={`px-4 py-2 rounded-xl text-xs font-bold transition flex items-center space-x-1.5 ${
                          isSelected
                            ? 'bg-emerald-600 text-white'
                            : 'bg-blue-600 hover:bg-blue-700 text-white shadow-sm'
                        }`}
                      >
                        {isSelected ? (
                          <>
                            <CheckCircle2 className="h-4 w-4" />
                            <span>Selected</span>
                          </>
                        ) : (
                          <span>Select Flight</span>
                        )}
                      </button>
                    </div>

                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* 4. TRAINS VIEW (IRCTC AUTHENTIC SCHEDULES) */}
      {activeTab === 'TRAIN' && (
        <div className="space-y-4">
          <div className="p-3 bg-emerald-50 border border-emerald-200 rounded-2xl flex items-center justify-between text-xs text-emerald-900">
            <div className="flex items-center space-x-2">
              <Train className="h-4 w-4 text-emerald-700 flex-shrink-0" />
              <span>
                <strong>Indian Railways (IRCTC) Schedules:</strong> High-speed Vande Bharat, Rajdhani & Superfast Express routes.
              </span>
            </div>
            <span className="text-[10px] font-bold bg-white px-2 py-0.5 rounded border border-emerald-300">
              Frontend Reference Data
            </span>
          </div>

          <div className="space-y-4">
            {filteredTrains.map(train => {
              const isSelected = selectedTrain?.id === train.id;
              const consumesPct = Math.round((train.totalPrice / totalTripBudget) * 100);

              return (
                <div
                  key={train.id}
                  className={`bg-white rounded-2xl border p-5 transition-all ${
                    isSelected 
                      ? 'border-emerald-600 ring-2 ring-emerald-500/30 shadow-md' 
                      : 'border-slate-200 hover:border-slate-300 hover:shadow-xs'
                  }`}
                >
                  <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
                    
                    {/* Train Info */}
                    <div className="flex items-center space-x-3.5">
                      <div className="h-11 w-11 rounded-xl bg-emerald-800 text-white font-extrabold text-xs flex items-center justify-center">
                        <Train className="h-5 w-5" />
                      </div>
                      <div>
                        <div className="flex items-center space-x-2">
                          <h3 className="font-extrabold text-slate-900 text-sm">{train.trainName}</h3>
                          <span className="text-xs text-slate-500 font-mono font-bold">#{train.trainNumber}</span>
                          {train.cheapest && (
                            <span className="text-[10px] bg-emerald-100 text-emerald-800 font-bold px-2 py-0.5 rounded-full">
                              Most Affordable
                            </span>
                          )}
                        </div>
                        <p className="text-[11px] text-slate-500 mt-0.5">{train.irctcNotice}</p>
                      </div>
                    </div>

                    {/* Schedule */}
                    <div className="flex items-center space-x-6 text-center">
                      <div>
                        <div className="text-base font-extrabold text-slate-900">{train.departureTime}</div>
                        <div className="text-xs font-bold text-slate-600">{train.originStationCode}</div>
                      </div>

                      <div className="flex flex-col items-center">
                        <span className="text-[10px] text-slate-400 font-semibold">{train.duration}</span>
                        <div className="w-20 sm:w-28 h-0.5 bg-slate-200 my-1 relative">
                          <Train className="h-3 w-3 text-emerald-600 absolute right-1/2 translate-x-1/2 -top-1" />
                        </div>
                        <span className="text-[10px] text-emerald-700 font-bold">Express Rail</span>
                      </div>

                      <div>
                        <div className="text-base font-extrabold text-slate-900">{train.arrivalTime}</div>
                        <div className="text-xs font-bold text-slate-600">{train.destinationStationCode}</div>
                      </div>
                    </div>

                    {/* Class Selection & Fare */}
                    <div className="text-xs space-y-1 lg:text-right">
                      <div className="flex items-center space-x-1.5 lg:justify-end">
                        <span className="text-[11px] text-slate-500 font-semibold">Class:</span>
                        <select
                          value={train.selectedClass}
                          onChange={(e) => {
                            const newClass = train.classes.find(c => c.code === e.target.value);
                            if (newClass) {
                              selectTrain({
                                ...train,
                                selectedClass: newClass.code,
                                pricePerPerson: newClass.farePerPerson,
                                totalPrice: newClass.farePerPerson * totalPax
                              });
                            }
                          }}
                          className="text-xs font-bold px-2 py-0.5 rounded border border-slate-300 bg-slate-50"
                        >
                          {train.classes.map(c => (
                            <option key={c.code} value={c.code}>
                              {c.code} – {c.name} (₹{c.farePerPerson})
                            </option>
                          ))}
                        </select>
                      </div>

                      <div className="text-lg font-extrabold text-slate-900 flex items-center lg:justify-end">
                        <IndianRupee className="h-4 w-4 text-emerald-600" />
                        <span>₹{train.totalPrice.toLocaleString('en-IN')}</span>
                      </div>
                      <div className="text-[10px] text-emerald-700 font-bold">
                        Only {consumesPct}% of budget (Saves ₹{(totalTripBudget - train.totalPrice).toLocaleString('en-IN')} for stay)
                      </div>
                    </div>

                    {/* Action */}
                    <div className="flex items-center space-x-2 pt-2 lg:pt-0 border-t lg:border-t-0 border-slate-100 justify-end">
                      <button
                        type="button"
                        onClick={handleOpenIrctcPortal}
                        className="p-2 rounded-xl border border-slate-200 hover:bg-slate-50 text-slate-600 text-xs font-bold"
                        title="Book on Official IRCTC Portal"
                      >
                        <ExternalLink className="h-4 w-4" />
                      </button>

                      <button
                        type="button"
                        onClick={() => selectTrain(train)}
                        className={`px-4 py-2 rounded-xl text-xs font-bold transition flex items-center space-x-1.5 ${
                          isSelected
                            ? 'bg-emerald-600 text-white'
                            : 'bg-emerald-700 hover:bg-emerald-800 text-white shadow-sm'
                        }`}
                      >
                        {isSelected ? (
                          <>
                            <CheckCircle2 className="h-4 w-4" />
                            <span>Train Selected</span>
                          </>
                        ) : (
                          <span>Select Train</span>
                        )}
                      </button>
                    </div>

                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* 5. Navigation Bar */}
      <div className="pt-6 border-t border-slate-200 flex justify-between items-center">
        <button
          type="button"
          onClick={() => setCurrentStep('requirements')}
          className="px-4 py-2.5 rounded-xl border border-slate-300 hover:bg-slate-100 text-slate-700 text-xs font-bold transition flex items-center space-x-1.5"
        >
          <ArrowLeft className="h-4 w-4" />
          <span>Back: Travel Details</span>
        </button>

        <button
          type="button"
          onClick={() => setCurrentStep('hotels')}
          className="px-6 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-700 text-white text-xs font-bold transition shadow-md shadow-blue-500/20 flex items-center space-x-1.5"
        >
          <span>Continue to Hotels</span>
          <ArrowRight className="h-4 w-4" />
        </button>
      </div>

      {/* Redirect Info Modal */}
      {redirectModalFlight && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm">
          <div className="bg-white rounded-2xl max-w-lg w-full p-6 shadow-2xl border border-slate-200 space-y-4">
            <div className="flex justify-between items-center border-b border-slate-100 pb-3">
              <div className="flex items-center space-x-2">
                <Plane className="h-5 w-5 text-blue-600" />
                <h3 className="font-heading font-bold text-base text-slate-900">
                  External Airline Redirect Notice
                </h3>
              </div>
              <button
                onClick={() => setRedirectModalFlight(null)}
                className="text-slate-400 hover:text-slate-600 p-1 rounded-lg"
              >
                ✕
              </button>
            </div>

            <div className="text-xs text-slate-600 space-y-3 leading-relaxed">
              <p>
                WanderAI uses a <strong>verified external booking model</strong> for airline reservations.
              </p>
              <div className="p-3 bg-amber-50 border border-amber-200 rounded-xl space-y-1 text-amber-900">
                <span className="font-bold flex items-center space-x-1">
                  <Info className="h-3.5 w-3.5 text-amber-600" />
                  <span>External Booking – Not Confirmed</span>
                </span>
                <p className="text-[11px] text-amber-800">
                  Selecting this flight retains it in your WanderAI itinerary. You will be redirected to the official carrier ({redirectModalFlight.airline}) to enter passenger names and complete payment safely. WanderAI never stores card data or issues fake PNRs.
                </p>
              </div>
            </div>

            <div className="flex justify-end space-x-2 pt-2 border-t border-slate-100">
              <button
                onClick={() => setRedirectModalFlight(null)}
                className="px-4 py-2 rounded-xl border border-slate-300 text-slate-700 text-xs font-semibold hover:bg-slate-100"
              >
                Close
              </button>
              <button
                onClick={() => {
                  handleOpenAirlinePortal(redirectModalFlight);
                  setRedirectModalFlight(null);
                }}
                className="px-5 py-2 rounded-xl bg-blue-600 hover:bg-blue-700 text-white text-xs font-bold flex items-center space-x-1.5"
              >
                <span>Continue to Airline</span>
                <ExternalLink className="h-3.5 w-3.5" />
              </button>
            </div>
          </div>
        </div>
      )}

    </div>
  );
};
