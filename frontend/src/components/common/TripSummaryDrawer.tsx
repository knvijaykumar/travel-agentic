import React from 'react';
import { useTravel } from '../../context/TravelContext';
import { BrandLogo } from './BrandLogo';
import { X, Plane, Hotel, MapPin, IndianRupee, ArrowRight, ShieldCheck, Trash2, CheckCircle2 } from 'lucide-react';

export const TripSummaryDrawer: React.FC = () => {
  const {
    tripSummaryDrawerOpen,
    setTripSummaryDrawerOpen,
    requirements,
    selectedFlight,
    selectedHotel,
    selectedAttractions,
    transfers,
    budget,
    setCurrentStep,
    currentStep
  } = useTravel();

  if (!tripSummaryDrawerOpen) return null;

  return (
    <div className="fixed inset-0 z-50 overflow-hidden">
      {/* Backdrop */}
      <div 
        className="absolute inset-0 bg-slate-900/60 backdrop-blur-sm transition-opacity" 
        onClick={() => setTripSummaryDrawerOpen(false)}
      />

      <div className="fixed inset-y-0 right-0 max-w-full flex pl-10">
        <div className="w-screen max-w-md bg-white shadow-2xl flex flex-col border-l border-slate-200">
          
          {/* Header */}
          <div className="p-4 bg-slate-900 text-white flex items-center justify-between border-b border-slate-800">
            <div className="flex items-center space-x-3">
              <BrandLogo variant="icon" surface="dark" imgClassName="h-7 w-7 object-contain" containerClassName="p-1 rounded-lg shrink-0" />
              <div>
                <div className="flex items-center space-x-2">
                  <span className="font-heading font-bold text-lg text-white">Live Trip Summary</span>
                  <span className="text-[10px] bg-blue-500/20 text-blue-300 border border-blue-500/30 px-2 py-0.5 rounded-full font-semibold">Active State</span>
                </div>
                <p className="text-xs text-slate-400 mt-0.5">{requirements.destination} • {requirements.durationDays} Days</p>
              </div>
            </div>
            <button
              onClick={() => setTripSummaryDrawerOpen(false)}
              className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition"
            >
              <X className="h-5 w-5" />
            </button>
          </div>

          {/* Body Content */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            
            {/* Trip Specs Card */}
            <div className="bg-slate-50 border border-slate-200 rounded-xl p-3.5 space-y-2">
              <div className="flex justify-between items-center text-xs">
                <span className="text-slate-500 font-medium">Route:</span>
                <span className="font-bold text-slate-900">{requirements.origin} ➔ {requirements.destination}</span>
              </div>
              <div className="flex justify-between items-center text-xs">
                <span className="text-slate-500 font-medium">Dates:</span>
                <span className="font-semibold text-slate-800">{requirements.startDate} to {requirements.endDate}</span>
              </div>
              <div className="flex justify-between items-center text-xs">
                <span className="text-slate-500 font-medium">Travellers:</span>
                <span className="font-semibold text-slate-800">{requirements.travellers.adults} Adults, {requirements.travellers.children} Children</span>
              </div>
              <div className="flex justify-between items-center text-xs">
                <span className="text-slate-500 font-medium">Travel Style:</span>
                <span className="font-semibold text-blue-700 bg-blue-50 px-2 py-0.5 rounded border border-blue-200">{requirements.tripType}</span>
              </div>
            </div>

            {/* Flight Selection */}
            <div className="border border-slate-200 rounded-xl p-3.5 bg-white">
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center space-x-2">
                  <Plane className="h-4 w-4 text-blue-600" />
                  <span className="text-xs font-bold text-slate-900 uppercase tracking-wider">Flight Selection</span>
                </div>
                <button
                  onClick={() => { setTripSummaryDrawerOpen(false); setCurrentStep('flights'); }}
                  className="text-xs text-blue-600 hover:text-blue-700 font-semibold"
                >
                  {selectedFlight ? 'Change' : 'Select Flight'}
                </button>
              </div>

              {selectedFlight ? (
                <div className="bg-slate-50 p-2.5 rounded-lg border border-slate-200 text-xs space-y-1">
                  <div className="flex justify-between items-center">
                    <span className="font-bold text-slate-900">{selectedFlight.airline} ({selectedFlight.flightNumber})</span>
                    <span className="font-extrabold text-blue-700">₹{selectedFlight.totalPrice.toLocaleString('en-IN')}</span>
                  </div>
                  <div className="text-slate-500 flex justify-between">
                    <span>{selectedFlight.originCode} ({selectedFlight.departureTime}) ➔ {selectedFlight.destinationCode} ({selectedFlight.arrivalTime})</span>
                    <span>{selectedFlight.duration}</span>
                  </div>
                  <div className="text-[11px] text-emerald-700 font-medium pt-1 flex items-center space-x-1">
                    <CheckCircle2 className="h-3 w-3" />
                    <span>Retained across all planning steps</span>
                  </div>
                </div>
              ) : (
                <div className="p-3 bg-amber-50/60 border border-amber-200/80 rounded-lg text-xs text-amber-800 flex items-center justify-between">
                  <span>No flight selected yet</span>
                  <button
                    onClick={() => { setTripSummaryDrawerOpen(false); setCurrentStep('flights'); }}
                    className="font-bold underline text-amber-900"
                  >
                    Browse Flights ➔
                  </button>
                </div>
              )}
            </div>

            {/* Hotel Selection */}
            <div className="border border-slate-200 rounded-xl p-3.5 bg-white">
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center space-x-2">
                  <Hotel className="h-4 w-4 text-indigo-600" />
                  <span className="text-xs font-bold text-slate-900 uppercase tracking-wider">Hotel Stay</span>
                </div>
                <button
                  onClick={() => { setTripSummaryDrawerOpen(false); setCurrentStep('hotels'); }}
                  className="text-xs text-indigo-600 hover:text-indigo-700 font-semibold"
                >
                  {selectedHotel ? 'Change' : 'Select Hotel'}
                </button>
              </div>

              {selectedHotel ? (
                <div className="bg-slate-50 p-2.5 rounded-lg border border-slate-200 text-xs space-y-1">
                  <div className="flex justify-between items-center">
                    <span className="font-bold text-slate-900 line-clamp-1">{selectedHotel.name}</span>
                    <span className="font-extrabold text-indigo-700 whitespace-nowrap ml-2">₹{selectedHotel.totalCost.toLocaleString('en-IN')}</span>
                  </div>
                  <div className="text-slate-500">
                    {selectedHotel.roomType} • {requirements.durationDays} Nights
                  </div>
                  <div className="text-[11px] text-slate-400">
                    {selectedHotel.location}
                  </div>
                </div>
              ) : (
                <div className="p-3 bg-amber-50/60 border border-amber-200/80 rounded-lg text-xs text-amber-800 flex items-center justify-between">
                  <span>No hotel selected yet</span>
                  <button
                    onClick={() => { setTripSummaryDrawerOpen(false); setCurrentStep('hotels'); }}
                    className="font-bold underline text-amber-900"
                  >
                    Browse Hotels ➔
                  </button>
                </div>
              )}
            </div>

            {/* Attractions */}
            <div className="border border-slate-200 rounded-xl p-3.5 bg-white">
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center space-x-2">
                  <MapPin className="h-4 w-4 text-emerald-600" />
                  <span className="text-xs font-bold text-slate-900 uppercase tracking-wider">Sightseeing Places ({selectedAttractions.length})</span>
                </div>
                <button
                  onClick={() => { setTripSummaryDrawerOpen(false); setCurrentStep('sightseeing'); }}
                  className="text-xs text-emerald-600 hover:text-emerald-700 font-semibold"
                >
                  Manage
                </button>
              </div>

              {selectedAttractions.length > 0 ? (
                <div className="flex flex-wrap gap-1.5 pt-1">
                  {selectedAttractions.map(a => (
                    <span key={a.id} className="text-[11px] bg-slate-100 border border-slate-200 px-2 py-0.5 rounded-md text-slate-800 font-medium">
                      {a.name}
                    </span>
                  ))}
                </div>
              ) : (
                <p className="text-xs text-slate-400 italic">No sightseeing places selected</p>
              )}
            </div>

            {/* Financial Summary */}
            <div className="border border-slate-200 rounded-xl p-4 bg-slate-50 space-y-2">
              <span className="text-xs font-bold text-slate-900 uppercase tracking-wider block mb-1">Expense Breakdown</span>
              
              <div className="flex justify-between text-xs text-slate-600">
                <span>Flights ({requirements.travellers.adults + requirements.travellers.children} pax):</span>
                <span className="font-semibold text-slate-900">₹{budget.flightCost.toLocaleString('en-IN')}</span>
              </div>
              <div className="flex justify-between text-xs text-slate-600">
                <span>Hotel ({requirements.durationDays} nights):</span>
                <span className="font-semibold text-slate-900">₹{budget.hotelCost.toLocaleString('en-IN')}</span>
              </div>
              <div className="flex justify-between text-xs text-slate-600">
                <span>Transfers & Sightseeing:</span>
                <span className="font-semibold text-slate-900">₹{(budget.transportCost + budget.sightseeingCost).toLocaleString('en-IN')}</span>
              </div>
              <div className="flex justify-between text-xs text-slate-600">
                <span>Meals & Experiences (Est):</span>
                <span className="font-semibold text-slate-900">₹{(budget.foodEstimate + budget.activitiesCost).toLocaleString('en-IN')}</span>
              </div>
              <div className="flex justify-between text-xs text-slate-600">
                <span>Taxes & Misc Reserve:</span>
                <span className="font-semibold text-slate-900">₹{budget.miscCost.toLocaleString('en-IN')}</span>
              </div>

              <div className="border-t border-slate-200 pt-2 flex justify-between items-center text-sm">
                <div>
                  <span className="font-extrabold text-slate-900">Estimated Total:</span>
                  <div className="text-[11px] text-slate-500 font-medium">Target: ₹{budget.totalBudget.toLocaleString('en-IN')}</div>
                </div>
                <div className="text-right">
                  <span className="font-extrabold text-base text-blue-700">₹{budget.totalEstimatedCost.toLocaleString('en-IN')}</span>
                  <div className={`text-[11px] font-bold ${budget.remainingBudget >= 0 ? 'text-emerald-600' : 'text-rose-600'}`}>
                    {budget.remainingBudget >= 0 ? `₹${budget.remainingBudget.toLocaleString('en-IN')} left` : `₹${Math.abs(budget.remainingBudget).toLocaleString('en-IN')} over budget`}
                  </div>
                </div>
              </div>
            </div>

          </div>

          {/* Footer Jump Button */}
          <div className="p-4 bg-white border-t border-slate-200">
            <button
              onClick={() => {
                setTripSummaryDrawerOpen(false);
                if (currentStep === 'requirements') setCurrentStep('flights');
                else if (currentStep === 'flights') setCurrentStep('hotels');
                else if (currentStep === 'hotels') setCurrentStep('sightseeing');
                else if (currentStep === 'sightseeing') setCurrentStep('itinerary');
                else if (currentStep === 'itinerary') setCurrentStep('budget');
                else if (currentStep === 'budget') setCurrentStep('review');
                else setCurrentStep('review');
              }}
              className="w-full py-2.5 px-4 rounded-xl bg-blue-600 hover:bg-blue-700 text-white font-bold text-sm shadow-md shadow-blue-500/20 transition flex items-center justify-center space-x-2"
            >
              <span>Continue Planning</span>
              <ArrowRight className="h-4 w-4" />
            </button>
          </div>

        </div>
      </div>
    </div>
  );
};

