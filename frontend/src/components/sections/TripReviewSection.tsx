import React, { useState } from 'react';
import { useTravel } from '../../context/TravelContext';
import { 
  CheckCircle2, 
  Plane, 
  Train,
  Hotel, 
  Car, 
  MapPin, 
  CalendarDays, 
  IndianRupee, 
  ShieldCheck, 
  AlertCircle, 
  ArrowRight, 
  ArrowLeft,
  FileText,
  UserCheck,
  CreditCard,
  Lock,
  ExternalLink
} from 'lucide-react';

export const TripReviewSection: React.FC = () => {
  const {
    requirements,
    selectedFlight,
    selectedTrain,
    selectedHotel,
    selectedAttractions,
    transfers,
    itinerary,
    budget,
    confirmBooking,
    setCurrentStep
  } = useTravel();

  const [confirmationModalOpen, setConfirmationModalOpen] = useState(false);
  const [agreedToTerms, setAgreedToTerms] = useState(false);
  const [bookingInProgress, setBookingInProgress] = useState(false);

  const selectedTransfers = transfers.filter(t => t.selected);

  const handleExecuteBooking = () => {
    setBookingInProgress(true);
    setTimeout(() => {
      confirmBooking('ALL');
      setBookingInProgress(false);
      setConfirmationModalOpen(false);
      setCurrentStep('my-trips');
    }, 1500);
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      
      {/* Header */}
      <div className="bg-white rounded-3xl border border-slate-200 p-6 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2 text-xs font-bold uppercase tracking-wider text-slate-400">
            <span>Pre-Booking Verification & Summary</span>
            <span>•</span>
            <span className="text-blue-600">Unified Travel Order</span>
          </div>
          <h2 className="text-2xl font-extrabold text-slate-900 mt-1">
            Review Your Complete Travel Plan
          </h2>
          <p className="text-xs text-slate-500 mt-0.5">
            Carefully verify your traveller details, selected airlines, hotel check-ins, transfers, and daily itinerary before confirming.
          </p>
        </div>

        <button
          onClick={() => setConfirmationModalOpen(true)}
          className="px-6 py-3 rounded-2xl bg-blue-600 hover:bg-blue-700 text-white font-extrabold text-sm shadow-lg shadow-blue-500/25 transition flex items-center space-x-2 self-start md:self-auto"
        >
          <Lock className="h-4 w-4" />
          <span>Confirm & Proceed to Booking</span>
        </button>
      </div>

      {/* Review Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        
        {/* Left Column: Line Items (2 Cols) */}
        <div className="lg:col-span-2 space-y-6">
          
          {/* Traveller Summary Card */}
          <div className="bg-white rounded-3xl border border-slate-200 p-6 shadow-sm space-y-3">
            <h3 className="font-heading font-extrabold text-base text-slate-900 flex items-center space-x-2">
              <UserCheck className="h-5 w-5 text-blue-600" />
              <span>Primary Traveller & Guest Information</span>
            </h3>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs pt-1">
              <div className="p-3 bg-slate-50 rounded-xl border border-slate-200">
                <span className="text-slate-400 font-bold block uppercase text-[10px]">Lead Traveller</span>
                <span className="font-bold text-slate-900 mt-0.5 block">Vijay Kumar & Family</span>
                <span className="text-slate-500 text-[11px]">Indian National</span>
              </div>

              <div className="p-3 bg-slate-50 rounded-xl border border-slate-200">
                <span className="text-slate-400 font-bold block uppercase text-[10px]">Passengers</span>
                <span className="font-bold text-slate-900 mt-0.5 block">{requirements.travellers.adults} Adults, {requirements.travellers.children} Child</span>
                <span className="text-slate-500 text-[11px]">{requirements.tripType} configuration</span>
              </div>

              <div className="p-3 bg-slate-50 rounded-xl border border-slate-200">
                <span className="text-slate-400 font-bold block uppercase text-[10px]">Special Requests</span>
                <span className="font-bold text-slate-900 mt-0.5 block">
                  {requirements.specialRequirements?.slice(0, 2).join(', ') || 'Standard preferences'}
                </span>
                <span className="text-slate-500 text-[11px]">Noted in booking file</span>
              </div>
            </div>
          </div>

          {/* Transport Reservation Card (Flight or Indian Railways Train) */}
          <div className="bg-white rounded-3xl border border-slate-200 p-6 shadow-sm space-y-4">
            <div className="flex justify-between items-center">
              <h3 className="font-heading font-extrabold text-base text-slate-900 flex items-center space-x-2">
                {requirements.transportMode === 'TRAIN' || selectedTrain ? (
                  <>
                    <Train className="h-5 w-5 text-indigo-600" />
                    <span>Selected Train Reservation (Indian Railways)</span>
                  </>
                ) : (
                  <>
                    <Plane className="h-5 w-5 text-blue-600" />
                    <span>Selected Flight Reservation</span>
                  </>
                )}
              </h3>
              <button
                onClick={() => setCurrentStep('flights')}
                className="text-xs font-bold text-blue-600 hover:text-blue-700"
              >
                Modify
              </button>
            </div>

            {selectedTrain ? (
              <div className="p-4 bg-slate-50 rounded-2xl border border-slate-200 space-y-3">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                  <div className="flex items-center space-x-3">
                    <div className="h-10 w-10 rounded-xl bg-indigo-900 text-white font-extrabold text-xs flex items-center justify-center">
                      IR
                    </div>
                    <div>
                      <span className="font-bold text-sm text-slate-900 block">{selectedTrain.trainNumber} - {selectedTrain.trainName}</span>
                      <span className="text-xs text-slate-500">Class {selectedTrain.selectedClass} • Indian Railways Express</span>
                    </div>
                  </div>
                  <div className="sm:text-right">
                    <span className="text-base font-extrabold text-indigo-700 block">₹{selectedTrain.totalPrice.toLocaleString('en-IN')}</span>
                    <span className="text-[11px] text-slate-400">Total for all travellers</span>
                  </div>
                </div>

                <div className="pt-2 border-t border-slate-200 flex justify-between text-xs text-slate-600">
                  <div>
                    <strong>Departure:</strong> {requirements.startDate} at {selectedTrain.departureTime} ({selectedTrain.originStationCode})
                  </div>
                  <div>
                    <strong>Arrival:</strong> {selectedTrain.arrivalTime} ({selectedTrain.destinationStationCode}) • {selectedTrain.duration}
                  </div>
                </div>

                <div className="text-[11px] text-indigo-700 font-semibold flex items-center justify-between pt-1">
                  <span className="flex items-center space-x-1">
                    <CheckCircle2 className="h-3.5 w-3.5" />
                    <span>Booking Partner: IRCTC Official Booking Link</span>
                  </span>
                  <a
                    href={selectedTrain.bookingUrl || 'https://www.irctc.co.in/nget/'}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center space-x-1 font-bold text-blue-600 hover:underline"
                  >
                    <span>IRCTC Portal</span>
                    <ExternalLink className="h-3 w-3" />
                  </a>
                </div>
              </div>
            ) : selectedFlight ? (
              <div className="p-4 bg-slate-50 rounded-2xl border border-slate-200 space-y-3">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                  <div className="flex items-center space-x-3">
                    <div className="h-10 w-10 rounded-xl bg-blue-900 text-white font-extrabold text-xs flex items-center justify-center">
                      {selectedFlight.airlineCode}
                    </div>
                    <div>
                      <span className="font-bold text-sm text-slate-900 block">{selectedFlight.airline} {selectedFlight.flightNumber}</span>
                      <span className="text-xs text-slate-500">{selectedFlight.cabinClass} Class • {selectedFlight.stops === 0 ? 'Non-stop Direct' : selectedFlight.stopDetails}</span>
                    </div>
                  </div>
                  <div className="sm:text-right">
                    <span className="text-base font-extrabold text-blue-700 block">₹{selectedFlight.totalPrice.toLocaleString('en-IN')}</span>
                    <span className="text-[11px] text-slate-400">Total for all travellers</span>
                  </div>
                </div>

                <div className="pt-2 border-t border-slate-200 flex justify-between text-xs text-slate-600">
                  <div>
                    <strong>Departure:</strong> {requirements.startDate} at {selectedFlight.departureTime} ({selectedFlight.originCode})
                  </div>
                  <div>
                    <strong>Arrival:</strong> {selectedFlight.arrivalTime} ({selectedFlight.destinationCode})
                  </div>
                </div>

                <div className="text-[11px] text-emerald-700 font-semibold flex items-center space-x-1">
                  <CheckCircle2 className="h-3.5 w-3.5" />
                  <span>Baggage Included: {selectedFlight.baggage.checkIn} Check-in, {selectedFlight.baggage.cabin} Cabin</span>
                </div>
              </div>
            ) : (
              <div className="p-4 bg-amber-50 rounded-2xl border border-amber-200 text-xs text-amber-900 flex justify-between items-center">
                <span>No transport option selected yet. You can proceed or select an option now.</span>
                <button
                  onClick={() => setCurrentStep('flights')}
                  className="font-bold underline"
                >
                  Browse Transport ➔
                </button>
              </div>
            )}
          </div>

          {/* Hotel Details Card */}
          <div className="bg-white rounded-3xl border border-slate-200 p-6 shadow-sm space-y-4">
            <div className="flex justify-between items-center">
              <h3 className="font-heading font-extrabold text-base text-slate-900 flex items-center space-x-2">
                <Hotel className="h-5 w-5 text-indigo-600" />
                <span>Selected Hotel Accommodation</span>
              </h3>
              <button
                onClick={() => setCurrentStep('hotels')}
                className="text-xs font-bold text-indigo-600 hover:text-indigo-700"
              >
                Modify
              </button>
            </div>

            {selectedHotel ? (
              <div className="p-4 bg-slate-50 rounded-2xl border border-slate-200 flex flex-col sm:flex-row gap-4">
                <img
                  src={selectedHotel.image}
                  alt={selectedHotel.name}
                  className="h-28 w-full sm:w-36 rounded-xl object-cover"
                  onError={(e) => {
                    (e.target as HTMLImageElement).src = 'https://images.unsplash.com/photo-1566073771259-6a8506099945?auto=format&fit=crop&w=400&q=80';
                  }}
                />
                <div className="flex-1 space-y-1.5 text-xs">
                  <div className="flex justify-between items-start">
                    <div>
                      <h4 className="font-bold text-sm text-slate-900">{selectedHotel.name}</h4>
                      <p className="text-indigo-700 font-semibold">{selectedHotel.roomType}</p>
                    </div>
                    <div className="text-right">
                      <span className="text-base font-extrabold text-indigo-700 block">₹{selectedHotel.totalCost.toLocaleString('en-IN')}</span>
                      <span className="text-[10px] text-slate-400">{requirements.durationDays} Nights</span>
                    </div>
                  </div>

                  <p className="text-slate-500">{selectedHotel.location}</p>
                  <p className="text-[11px] text-emerald-700 font-medium">✓ {selectedHotel.cancellationPolicy}</p>
                </div>
              </div>
            ) : (
              <div className="p-4 bg-amber-50 rounded-2xl border border-amber-200 text-xs text-amber-900 flex justify-between items-center">
                <span>No hotel selected yet.</span>
                <button
                  onClick={() => setCurrentStep('hotels')}
                  className="font-bold underline"
                >
                  Browse Hotels ➔
                </button>
              </div>
            )}
          </div>

          {/* Transfers & Sightseeing Summary */}
          <div className="bg-white rounded-3xl border border-slate-200 p-6 shadow-sm space-y-3">
            <h3 className="font-heading font-extrabold text-base text-slate-900 flex items-center space-x-2">
              <Car className="h-5 w-5 text-cyan-600" />
              <span>Transfers & Sightseeing Overview</span>
            </h3>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
              <div className="p-3 bg-slate-50 rounded-xl border border-slate-200 space-y-1">
                <span className="font-bold text-slate-800 block">Transportation & Transfers:</span>
                {selectedTransfers.length > 0 ? (
                  selectedTransfers.map(t => (
                    <div key={t.id} className="text-slate-600 flex justify-between">
                      <span>• {t.title}</span>
                      <span className="font-semibold">₹{t.price.toLocaleString('en-IN')}</span>
                    </div>
                  ))
                ) : (
                  <span className="text-slate-400 italic">Self arrangement / Local cabs</span>
                )}
              </div>

              <div className="p-3 bg-slate-50 rounded-xl border border-slate-200 space-y-1">
                <span className="font-bold text-slate-800 block">Sightseeing Places ({selectedAttractions.length}):</span>
                <p className="text-slate-600 line-clamp-2">
                  {selectedAttractions.map(a => a.name).join(', ') || 'No specific attractions chosen'}
                </p>
              </div>
            </div>
          </div>

        </div>

        {/* Right Column: Order Total & Checkout (1 Col) */}
        <div className="space-y-6">
          
          {/* Order Total Card */}
          <div className="bg-white rounded-3xl border border-slate-200 p-6 shadow-sm space-y-4">
            <h3 className="font-heading font-extrabold text-base text-slate-900">
              Trip Cost Summary
            </h3>

            <div className="space-y-2 text-xs text-slate-600">
              <div className="flex justify-between">
                <span>Flights Cost:</span>
                <span className="font-bold text-slate-900">₹{budget.flightCost.toLocaleString('en-IN')}</span>
              </div>
              <div className="flex justify-between">
                <span>Hotel Stay ({requirements.durationDays}N):</span>
                <span className="font-bold text-slate-900">₹{budget.hotelCost.toLocaleString('en-IN')}</span>
              </div>
              <div className="flex justify-between">
                <span>Transfers & Sightseeing:</span>
                <span className="font-bold text-slate-900">₹{(budget.transportCost + budget.sightseeingCost).toLocaleString('en-IN')}</span>
              </div>
              <div className="flex justify-between">
                <span>Meals & Experience Reserve:</span>
                <span className="font-bold text-slate-900">₹{(budget.foodEstimate + budget.activitiesCost).toLocaleString('en-IN')}</span>
              </div>
              <div className="flex justify-between">
                <span>GST, Fuel & Misc Surcharges:</span>
                <span className="font-bold text-slate-900">₹{budget.miscCost.toLocaleString('en-IN')}</span>
              </div>

              <div className="pt-3 border-t border-slate-200 flex justify-between items-center text-sm">
                <div>
                  <span className="font-extrabold text-slate-900 block">Total Payable:</span>
                  <span className="text-[11px] text-slate-400">All taxes included</span>
                </div>
                <div className="text-right">
                  <span className="text-2xl font-extrabold text-blue-700">
                    ₹{budget.totalEstimatedCost.toLocaleString('en-IN')}
                  </span>
                  <div className="text-[11px] text-slate-500 font-semibold">
                    ₹{budget.perPersonCost.toLocaleString('en-IN')} / person
                  </div>
                </div>
              </div>
            </div>

            <button
              onClick={() => setConfirmationModalOpen(true)}
              className="w-full py-3 rounded-2xl bg-blue-600 hover:bg-blue-700 text-white font-extrabold text-sm shadow-lg shadow-blue-500/25 transition flex items-center justify-center space-x-2"
            >
              <CreditCard className="h-4 w-4" />
              <span>Confirm & Book Complete Trip</span>
            </button>

            <div className="p-3 bg-slate-50 rounded-xl border border-slate-200 text-[11px] text-slate-500 space-y-1">
              <div className="flex items-center space-x-1 font-bold text-slate-700">
                <ShieldCheck className="h-4 w-4 text-emerald-600" />
                <span>Verified Hybrid Booking Architecture</span>
              </div>
              <p>
                Hotels book directly via LiteAPI Sandbox. Flights link directly to airline portals (External Booking – Not Confirmed). No fake PNRs or charges.
              </p>
            </div>
          </div>

        </div>

      </div>

      {/* Navigation Footer */}
      <div className="pt-6 border-t border-slate-200 flex justify-between items-center">
        <button
          onClick={() => setCurrentStep('budget')}
          className="px-4 py-2.5 rounded-xl border border-slate-300 hover:bg-slate-100 text-slate-700 text-xs font-bold transition flex items-center space-x-1.5"
        >
          <ArrowLeft className="h-4 w-4" />
          <span>Back to Budget</span>
        </button>
      </div>

      {/* Consequential Booking Confirmation Modal */}
      {confirmationModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm">
          <div className="bg-white rounded-3xl max-w-lg w-full p-6 shadow-2xl border border-slate-200 space-y-5">
            <div className="flex justify-between items-center border-b border-slate-100 pb-3">
              <div className="flex items-center space-x-2">
                <ShieldCheck className="h-6 w-6 text-blue-600" />
                <h3 className="font-heading font-extrabold text-lg text-slate-900">
                  Confirm Travel Booking
                </h3>
              </div>
              <button
                onClick={() => setConfirmationModalOpen(false)}
                className="text-slate-400 hover:text-slate-600"
              >
                ✕
              </button>
            </div>

            <div className="space-y-3 text-xs text-slate-600 leading-relaxed">
              <div className="p-3.5 bg-blue-50 border border-blue-200 rounded-xl space-y-1 text-blue-950">
                <div className="font-bold">Trip: {requirements.durationDays}-Day {requirements.tripType} in {requirements.destination}</div>
                <div>Dates: {requirements.startDate} to {requirements.endDate}</div>
                <div className="font-extrabold text-blue-700 text-sm pt-1">
                  Total Order Amount: ₹{budget.totalEstimatedCost.toLocaleString('en-IN')}
                </div>
              </div>

              {/* Over Budget Notice */}
              {budget.status === 'OVER_BUDGET' && (
                <div className="p-3 bg-rose-50 rounded-xl border border-rose-200 text-rose-900 text-[11px] space-y-1">
                  <span className="font-bold flex items-center space-x-1 text-rose-700">
                    <AlertCircle className="h-3.5 w-3.5 text-rose-600" />
                    <span>Budget Advisory: Over Configured Limit</span>
                  </span>
                  <p>
                    Your estimated total (₹{budget.totalEstimatedCost.toLocaleString('en-IN')}) exceeds your total budget of ₹{budget.totalBudget.toLocaleString('en-IN')} by ₹{Math.abs(budget.remainingBudget).toLocaleString('en-IN')}. You may proceed with saving the itinerary or adjust options in the Budget step.
                  </p>
                </div>
              )}

              <div className="p-3 bg-amber-50 rounded-xl border border-amber-200 text-amber-900 text-[11px] space-y-1">
                <span className="font-bold flex items-center space-x-1">
                  <AlertCircle className="h-3.5 w-3.5 text-amber-600" />
                  <span>Important Provider Terms & Transparency:</span>
                </span>
                <p className="font-semibold text-amber-950">
                  ⚠️ Confirming your WanderAI trip plan does NOT purchase tickets or hotel rooms. Please use the verified external booking links to complete bookings.
                </p>
                <p className="text-amber-800 text-[10px]">
                  Hotel reservations are submitted through LiteAPI sandbox mode, and flight & train selections are recorded with external booking links (IRCTC / Airlines). No fake PNRs or real financial charges occur. Vouchers are saved in your <strong>My Trips</strong> portal.
                </p>
              </div>

              <label className="flex items-start space-x-2.5 pt-1 cursor-pointer select-none">
                <input
                  type="checkbox"
                  checked={agreedToTerms}
                  onChange={(e) => setAgreedToTerms(e.target.checked)}
                  className="rounded text-blue-600 focus:ring-blue-500 accent-blue-600 h-4 w-4 mt-0.5"
                />
                <span className="text-[11px] text-slate-700 font-medium">
                  I have reviewed all itinerary times, flight luggage rules, and hotel cancellation guidelines.
                </span>
              </label>
            </div>

            <div className="flex justify-end space-x-3 pt-3 border-t border-slate-100">
              <button
                onClick={() => setConfirmationModalOpen(false)}
                disabled={bookingInProgress}
                className="px-4 py-2.5 rounded-xl border border-slate-300 text-slate-700 text-xs font-semibold hover:bg-slate-100 disabled:opacity-50"
              >
                Cancel
              </button>

              <button
                onClick={handleExecuteBooking}
                disabled={!agreedToTerms || bookingInProgress}
                className="px-6 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-700 text-white text-xs font-bold shadow-md shadow-blue-500/20 disabled:opacity-40 disabled:cursor-not-allowed flex items-center space-x-2"
              >
                {bookingInProgress ? (
                  <span>Generating Booking Vouchers...</span>
                ) : (
                  <>
                    <CheckCircle2 className="h-4 w-4" />
                    <span>Authorize & Confirm Booking</span>
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}

    </div>
  );
};

