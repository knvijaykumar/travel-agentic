import React, { useState } from 'react';
import { useTravel } from '../../context/TravelContext';
import { HotelOption } from '../../types/travel';
import { travelApi } from '../../services/apiClient';
import { 
  Hotel, 
  Star, 
  MapPin, 
  CheckCircle2, 
  IndianRupee, 
  Sparkles, 
  Wifi, 
  Utensils, 
  ArrowRight, 
  ArrowLeft, 
  Scale, 
  X, 
  ShieldCheck, 
  Award,
  ChevronRight,
  AlertCircle,
  Calendar,
  Lock
} from 'lucide-react';

export const HotelsSection: React.FC = () => {
  const {
    requirements,
    availableHotels,
    selectedHotel,
    selectHotel,
    selectedFlight,
    selectedTrain,
    setCurrentStep,
    confirmBooking
  } = useTravel();

  const [compareModalOpen, setCompareModalOpen] = useState(false);
  const [filterRating, setFilterRating] = useState<number>(0);
  const [filterBadge, setFilterBadge] = useState<string>('ALL');
  const [selectedTier, setSelectedTier] = useState<string>(requirements.accommodationTier || 'ALL');

  // Booking Modal State
  const [bookingModalHotel, setBookingModalHotel] = useState<HotelOption | null>(null);
  const [guestFirstName, setGuestFirstName] = useState('');
  const [guestLastName, setGuestLastName] = useState('');
  const [guestEmail, setGuestEmail] = useState('');
  const [guestPhone, setGuestPhone] = useState('');
  const [bookingError, setBookingError] = useState<string | null>(null);
  const [bookingSuccess, setBookingSuccess] = useState<string | null>(null);
  const [isSubmittingBooking, setIsSubmittingBooking] = useState(false);

  const nights = Math.max(1, requirements.durationDays);
  const totalPax = requirements.travellers.adults + requirements.travellers.children;
  const totalTripBudget = requirements.totalBudget || 40000;
  const transportCost = (selectedFlight ? selectedFlight.totalPrice : 0) + (selectedTrain ? selectedTrain.totalPrice : 0);
  const remainingBudgetForHotels = Math.max(0, totalTripBudget - transportCost);

  const filteredHotels = availableHotels.filter(h => {
    if (filterRating > 0 && h.rating < filterRating) return false;
    if (filterBadge !== 'ALL' && h.badge !== filterBadge) return false;
    if (selectedTier !== 'ALL') {
      if (selectedTier === 'Budget' && (h.stars > 3 || h.pricePerNight > 4000)) return false;
      if (selectedTier === 'Standard' && (h.stars < 3 || h.pricePerNight > 7500)) return false;
      if (selectedTier === 'Premium' && (h.stars < 4)) return false;
      if (selectedTier === 'Luxury' && (h.stars < 5 && h.badge !== 'Luxury Pick')) return false;
    }
    return true;
  });

  const handleStartBooking = (hotel: HotelOption) => {
    setBookingModalHotel(hotel);
    setBookingError(null);
    setBookingSuccess(null);
  };

  const handleConfirmBookingModal = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!guestFirstName.trim() || !guestLastName.trim() || !guestEmail.trim()) {
      setBookingError('First name, last name, and a valid email address are required.');
      return;
    }

    if (!guestEmail.includes('@') || !guestEmail.includes('.')) {
      setBookingError('Please enter a valid email address.');
      return;
    }

    setIsSubmittingBooking(true);
    setBookingError(null);

    try {
      if (bookingModalHotel?.offerId) {
        // Step 1: Prebook
        const prebookRes = await travelApi.prebookHotel(bookingModalHotel.offerId);
        // Step 2: Confirm
        const bookRes = await travelApi.confirmHotelBooking({
          prebook_id: prebookRes.prebook_id,
          holder: {
            first_name: guestFirstName.trim(),
            last_name: guestLastName.trim(),
            email: guestEmail.trim(),
            phone: guestPhone.trim() || undefined
          },
          client_reference: `VTA-TRIP-${Date.now()}`
        });

        selectHotel(bookingModalHotel);
        confirmBooking('HOTEL');
        setBookingSuccess(`Booking Confirmed! LiteAPI Reference: ${bookRes.booking_reference || bookRes.booking_id}. Check your email for voucher.`);
      } else {
        // Fallback / reference hotel booking
        if (bookingModalHotel) {
          selectHotel(bookingModalHotel);
          confirmBooking('HOTEL');
          setBookingSuccess(`Reservation Confirmed in Sandbox! Reference: HTL-CONF-${Math.floor(100000 + Math.random() * 900000)}.`);
        }
      }
    } catch (err: any) {
      setBookingError(err.message || 'Hotel booking failed. Operating in fallback demonstration mode.');
      // Still allow selecting stay for trip
      if (bookingModalHotel) {
        selectHotel(bookingModalHotel);
      }
    } finally {
      setIsSubmittingBooking(false);
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
      
      {/* Search Header Summary */}
      <div className="bg-white rounded-2xl border border-slate-200 p-5 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2 text-xs font-bold uppercase tracking-wider text-slate-400">
            <span>Verified Accommodation Discovery</span>
            <span>•</span>
            <span className="text-indigo-600">Property-Specific Image Directory</span>
          </div>
          <div className="mt-1 flex items-center space-x-3 text-xl font-extrabold text-slate-900">
            <Hotel className="h-6 w-6 text-indigo-600" />
            <span>Hotels in {requirements.destination}</span>
          </div>
          <div className="mt-1 text-xs text-slate-500 font-medium">
            Stay: <strong className="text-slate-800">{requirements.startDate} to {requirements.endDate}</strong> ({nights} Nights) | Guests: <strong className="text-slate-800">{requirements.travellers.adults + requirements.travellers.children} Guests</strong>
          </div>
        </div>

        {/* Selected Hotel Quick Banner */}
        {selectedHotel ? (
          <div className="bg-indigo-50 border border-indigo-200 rounded-xl p-3 flex items-center space-x-3">
            <img
              src={selectedHotel.image}
              alt={selectedHotel.name}
              className="h-12 w-12 rounded-lg object-cover shadow-xs"
              onError={(e) => {
                (e.target as HTMLImageElement).src = 'https://images.unsplash.com/photo-1566073771259-6a8506099945?auto=format&fit=crop&w=400&q=80';
              }}
            />
            <div className="text-xs">
              <span className="font-bold text-slate-900 line-clamp-1">{selectedHotel.name}</span>
              <span className="text-indigo-700 font-extrabold">₹{selectedHotel.totalCost.toLocaleString('en-IN')} total</span>
              <span className="text-slate-500 block">Selected for trip</span>
            </div>
            <button
              onClick={() => setCurrentStep('sightseeing')}
              className="ml-auto px-3.5 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-bold flex items-center space-x-1"
            >
              <span>Next: Sightseeing</span>
              <ChevronRight className="h-4 w-4" />
            </button>
          </div>
        ) : (
          <div className="flex items-center space-x-3">
            <button
              onClick={() => setCompareModalOpen(true)}
              className="px-4 py-2.5 rounded-xl border border-slate-300 hover:bg-slate-50 text-slate-700 text-xs font-bold transition flex items-center space-x-1.5"
            >
              <Scale className="h-4 w-4 text-slate-500" />
              <span>Compare All Stays</span>
            </button>
          </div>
        )}
      </div>

      {/* Strict Stay Budget Bar */}
      <div className={`p-4 rounded-2xl border text-xs flex flex-col md:flex-row md:items-center justify-between gap-3 ${
        selectedHotel && selectedHotel.totalCost > remainingBudgetForHotels
          ? 'bg-rose-50/90 border-rose-300 text-rose-950'
          : 'bg-indigo-50/90 border-indigo-200 text-indigo-950'
      }`}>
        <div className="flex items-center space-x-3">
          <div className="h-9 w-9 rounded-xl bg-white shadow-xs flex items-center justify-center font-extrabold text-indigo-600">
            <IndianRupee className="h-4 w-4" />
          </div>
          <div>
            <span className="font-extrabold block text-sm">
              Strict Stay Budget: ₹{remainingBudgetForHotels.toLocaleString('en-IN')} available for hotel accommodation
            </span>
            <span className="text-slate-600 text-[11px]">
              Calculated from ₹{totalTripBudget.toLocaleString('en-IN')} total trip budget minus ₹{transportCost.toLocaleString('en-IN')} transport for {totalPax} travellers.
            </span>
          </div>
        </div>

        {selectedHotel && (
          <div className="md:text-right text-xs">
            <span className="font-bold text-slate-800 block">
              Selected: ₹{selectedHotel.totalCost.toLocaleString('en-IN')} ({nights} nights)
            </span>
            <span className={`text-[11px] font-extrabold ${
              selectedHotel.totalCost <= remainingBudgetForHotels ? 'text-emerald-700' : 'text-rose-700'
            }`}>
              {selectedHotel.totalCost <= remainingBudgetForHotels 
                ? `Leaves ₹${(remainingBudgetForHotels - selectedHotel.totalCost).toLocaleString('en-IN')} for food & local transit`
                : `Exceeds stay target by ₹${(selectedHotel.totalCost - remainingBudgetForHotels).toLocaleString('en-IN')}`}
            </span>
          </div>
        )}
      </div>

      {/* Filter Chips */}
      <div className="flex flex-wrap items-center justify-between gap-3 bg-slate-50 p-3.5 rounded-xl border border-slate-200 text-xs">
        <div className="flex flex-wrap items-center gap-2">
          <span className="font-bold text-slate-500 uppercase">Tier:</span>
          {['ALL', 'Budget', 'Standard', 'Premium', 'Luxury'].map(tier => (
            <button
              key={tier}
              onClick={() => setSelectedTier(tier)}
              className={`px-3 py-1 rounded-lg font-semibold transition ${
                selectedTier === tier 
                  ? 'bg-indigo-600 text-white shadow-xs' 
                  : 'bg-white border border-slate-200 text-slate-700 hover:bg-slate-100'
              }`}
            >
              {tier}
            </button>
          ))}

          <span className="font-bold text-slate-400 mx-1">•</span>

          <span className="font-bold text-slate-500 uppercase">Category:</span>
          {['ALL', 'Luxury Pick', 'Best Value', 'Top Rated'].map(badge => (
            <button
              key={badge}
              onClick={() => setFilterBadge(badge)}
              className={`px-3 py-1 rounded-lg font-semibold transition ${
                filterBadge === badge 
                  ? 'bg-indigo-600 text-white shadow-xs' 
                  : 'bg-white border border-slate-200 text-slate-700 hover:bg-slate-100'
              }`}
            >
              {badge}
            </button>
          ))}
        </div>

        <div className="flex items-center space-x-2">
          <span className="font-bold text-slate-500 uppercase">Min Rating:</span>
          {[0, 4.5, 4.8].map(r => (
            <button
              key={r}
              onClick={() => setFilterRating(r)}
              className={`px-2.5 py-1 rounded-lg font-semibold transition ${
                filterRating === r 
                  ? 'bg-amber-600 text-white shadow-xs' 
                  : 'bg-white border border-slate-200 text-slate-700 hover:bg-slate-100'
              }`}
            >
              {r === 0 ? 'All' : `${r}★+`}
            </button>
          ))}
        </div>
      </div>

      {/* Hotel Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {filteredHotels.map(hotel => {
          const isSelected = selectedHotel?.id === hotel.id;
          return (
            <div
              key={hotel.id}
              className={`rounded-2xl border overflow-hidden bg-white flex flex-col transition-all ${
                isSelected 
                  ? 'border-indigo-600 ring-2 ring-indigo-500/30 shadow-lg' 
                  : 'border-slate-200 hover:border-slate-300 hover:shadow-md'
              }`}
            >
              {/* Hotel Property Image */}
              <div className="relative h-52 bg-slate-100">
                <img
                  src={hotel.image}
                  alt={hotel.name}
                  className="w-full h-full object-cover transition-transform duration-500 hover:scale-105"
                  onError={(e) => {
                    (e.target as HTMLImageElement).src = 'https://images.unsplash.com/photo-1566073771259-6a8506099945?auto=format&fit=crop&w=800&q=80';
                  }}
                />
                
                {/* Badge */}
                {hotel.badge && (
                  <div className="absolute top-3 left-3 bg-slate-900/80 backdrop-blur-md text-amber-300 text-[10px] font-extrabold uppercase tracking-wider px-2.5 py-1 rounded-md border border-amber-400/30 flex items-center space-x-1">
                    <Award className="h-3 w-3" />
                    <span>{hotel.badge}</span>
                  </div>
                )}

                {/* Star Rating Badge */}
                <div className="absolute top-3 right-3 bg-white/95 backdrop-blur-md px-2.5 py-1 rounded-lg shadow-sm text-xs font-bold text-slate-900 flex items-center space-x-1">
                  <Star className="h-3.5 w-3.5 text-amber-500 fill-amber-500" />
                  <span>{hotel.rating}</span>
                  <span className="text-[10px] text-slate-400">({hotel.reviewCount})</span>
                </div>

                <div className="absolute bottom-3 left-3 text-white text-xs drop-shadow-md flex items-center space-x-1">
                  <MapPin className="h-3.5 w-3.5 text-indigo-400" />
                  <span>{hotel.distanceFromCenter}</span>
                </div>
              </div>

              {/* Card Body */}
              <div className="p-5 flex-1 flex flex-col justify-between space-y-4">
                <div className="space-y-1.5">
                  <div className="flex items-center space-x-1 text-amber-500">
                    {Array.from({ length: hotel.stars }).map((_, i) => (
                      <Star key={i} className="h-3 w-3 fill-amber-500" />
                    ))}
                    <span className="text-[11px] text-slate-500 ml-1 font-medium">{hotel.stars}-Star Property</span>
                    <span className={`ml-auto text-[10px] font-bold px-2 py-0.5 rounded-full ${
                      hotel.dataSource === 'Sandbox Data'
                        ? 'bg-amber-100 text-amber-800 border border-amber-200'
                        : hotel.dataSource === 'Live Provider Data'
                          ? 'bg-emerald-100 text-emerald-800 border border-emerald-200'
                          : 'bg-slate-100 text-slate-700 border border-slate-200'
                    }`}>
                      {hotel.dataSource || 'Frontend Reference Data'}
                    </span>
                  </div>

                  <h3 className="font-heading font-extrabold text-base text-slate-900 line-clamp-1">{hotel.name}</h3>
                  <p className="text-xs text-indigo-700 font-semibold">{hotel.roomType}</p>
                  <p className="text-xs text-slate-500 line-clamp-1">{hotel.location}</p>

                  {/* Amenities */}
                  <div className="pt-2 flex flex-wrap gap-1.5">
                    {hotel.amenities.slice(0, 4).map((amenity, i) => (
                      <span key={i} className="text-[11px] bg-slate-100 text-slate-700 px-2 py-0.5 rounded-md font-medium">
                        {amenity}
                      </span>
                    ))}
                  </div>

                  <p className="text-[11px] text-emerald-700 font-medium pt-1">
                    ✓ {hotel.cancellationPolicy}
                  </p>

                  {/* Strict Budget Fit Badge */}
                  <div className={`p-2 rounded-xl text-[10px] font-bold flex items-center justify-between ${
                    hotel.totalCost <= remainingBudgetForHotels
                      ? 'bg-emerald-50 text-emerald-800 border border-emerald-200'
                      : 'bg-rose-50 text-rose-800 border border-rose-200'
                  }`}>
                    <span>
                      {hotel.totalCost <= remainingBudgetForHotels 
                        ? `✓ Fits inside stay allocation (Leaves ₹${(remainingBudgetForHotels - hotel.totalCost).toLocaleString('en-IN')})`
                        : `⚠ Exceeds stay budget by ₹${(hotel.totalCost - remainingBudgetForHotels).toLocaleString('en-IN')}`}
                    </span>
                    <span>{Math.round((hotel.totalCost / totalTripBudget) * 100)}% of budget</span>
                  </div>
                </div>

                {/* Card Footer Price & Select */}
                <div className="pt-3 border-t border-slate-100 flex items-center justify-between">
                  <div>
                    <div className="flex items-center text-lg font-extrabold text-slate-900">
                      <IndianRupee className="h-4 w-4 text-indigo-600" />
                      <span>₹{hotel.pricePerNight.toLocaleString('en-IN')}</span>
                      <span className="text-xs text-slate-400 font-normal ml-1">/ night</span>
                    </div>
                    <div className="text-[11px] text-slate-500 font-semibold">
                      Total: ₹{hotel.totalCost.toLocaleString('en-IN')} ({nights} nights)
                    </div>
                  </div>

                  <div className="flex items-center space-x-2">
                    <button
                      type="button"
                      onClick={() => handleStartBooking(hotel)}
                      className="px-3 py-2 rounded-xl border border-indigo-200 bg-indigo-50 hover:bg-indigo-100 text-indigo-700 text-xs font-bold transition flex items-center space-x-1"
                      title="LiteAPI Sandbox Hotel Booking Workflow"
                    >
                      <Lock className="h-3 w-3" />
                      <span>Book (Sandbox)</span>
                    </button>
                    <button
                      onClick={() => selectHotel(hotel)}
                      className={`px-4 py-2 rounded-xl text-xs font-bold transition flex items-center space-x-1.5 ${
                        isSelected 
                          ? 'bg-emerald-600 hover:bg-emerald-700 text-white shadow-xs' 
                          : 'bg-indigo-600 hover:bg-indigo-700 text-white shadow-md shadow-indigo-500/20'
                      }`}
                    >
                      {isSelected ? (
                        <>
                          <CheckCircle2 className="h-4 w-4" />
                          <span>Selected</span>
                        </>
                      ) : (
                        <span>Select Stay</span>
                      )}
                    </button>
                  </div>
                </div>

              </div>
            </div>
          );
        })}
      </div>

      {/* Navigation Footer */}
      <div className="pt-6 border-t border-slate-200 flex justify-between items-center">
        <button
          onClick={() => setCurrentStep('flights')}
          className="px-4 py-2.5 rounded-xl border border-slate-300 hover:bg-slate-100 text-slate-700 text-xs font-bold transition flex items-center space-x-1.5"
        >
          <ArrowLeft className="h-4 w-4" />
          <span>Back to Transport</span>
        </button>

        <button
          onClick={() => setCurrentStep('itinerary')}
          className="px-6 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-bold transition shadow-md shadow-indigo-500/20 flex items-center space-x-1.5"
        >
          <span>Continue to AI Itinerary</span>
          <ArrowRight className="h-4 w-4" />
        </button>
      </div>

      {/* Comparison Modal */}
      {compareModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm">
          <div className="bg-white rounded-2xl max-w-4xl w-full max-h-[85vh] flex flex-col shadow-2xl border border-slate-200">
            <div className="p-4 bg-slate-900 text-white flex justify-between items-center rounded-t-2xl">
              <div className="flex items-center space-x-2">
                <Scale className="h-5 w-5 text-indigo-400" />
                <h3 className="font-heading font-bold text-base">Hotel Side-by-Side Comparison</h3>
              </div>
              <button
                onClick={() => setCompareModalOpen(false)}
                className="text-slate-400 hover:text-white"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            <div className="p-6 overflow-x-auto flex-1">
              <div className="grid grid-cols-3 gap-4 min-w-[600px]">
                {availableHotels.slice(0, 3).map(hotel => (
                  <div key={hotel.id} className="border border-slate-200 rounded-xl p-4 bg-slate-50 space-y-3">
                    <img
                      src={hotel.image}
                      alt={hotel.name}
                      className="h-32 w-full object-cover rounded-lg"
                      onError={(e) => {
                        (e.target as HTMLImageElement).src = 'https://images.unsplash.com/photo-1566073771259-6a8506099945?auto=format&fit=crop&w=400&q=80';
                      }}
                    />
                    <div>
                      <h4 className="font-bold text-xs text-slate-900">{hotel.name}</h4>
                      <div className="text-[11px] text-amber-600 font-bold flex items-center space-x-1 mt-0.5">
                        <Star className="h-3 w-3 fill-amber-500" />
                        <span>{hotel.rating} / 5 ({hotel.reviewCount} reviews)</span>
                      </div>
                    </div>
                    <div className="text-xs space-y-1 text-slate-600">
                      <div><strong>Rate:</strong> ₹{hotel.pricePerNight.toLocaleString('en-IN')}/night</div>
                      <div><strong>Total:</strong> ₹{hotel.totalCost.toLocaleString('en-IN')}</div>
                      <div><strong>Location:</strong> {hotel.distanceFromCenter}</div>
                      <div><strong>Policy:</strong> {hotel.cancellationPolicy}</div>
                    </div>
                    <button
                      onClick={() => {
                        selectHotel(hotel);
                        setCompareModalOpen(false);
                      }}
                      className="w-full py-2 bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-bold rounded-lg transition"
                    >
                      Choose This Stay
                    </button>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* LiteAPI Sandbox Booking Modal */}
      {bookingModalHotel && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm">
          <div className="bg-white rounded-2xl max-w-lg w-full max-h-[90vh] flex flex-col shadow-2xl border border-slate-200">
            <div className="p-4 bg-indigo-900 text-white flex justify-between items-center rounded-t-2xl">
              <div className="flex items-center space-x-2">
                <Hotel className="h-5 w-5 text-indigo-300" />
                <h3 className="font-heading font-bold text-base">Book Stay (LiteAPI Sandbox)</h3>
              </div>
              <button
                onClick={() => setBookingModalHotel(null)}
                className="text-slate-300 hover:text-white"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            <div className="p-5 overflow-y-auto space-y-4 text-xs">
              {/* Hotel Summary */}
              <div className="p-3 bg-indigo-50 border border-indigo-200 rounded-xl space-y-1">
                <div className="font-bold text-indigo-950 text-sm">{bookingModalHotel.name}</div>
                <div className="text-slate-600">{bookingModalHotel.roomType} • {bookingModalHotel.location}</div>
                <div className="text-indigo-700 font-extrabold">
                  ₹{bookingModalHotel.totalCost.toLocaleString('en-IN')} total ({nights} nights)
                </div>
                <div className="text-[11px] text-emerald-700 font-semibold pt-0.5">
                  ✓ {bookingModalHotel.cancellationPolicy}
                </div>
              </div>

              {/* Data provenance notice */}
              <div className="p-3 bg-amber-50 border border-amber-200 rounded-xl text-amber-900 flex items-start space-x-2">
                <AlertCircle className="h-4 w-4 text-amber-600 flex-shrink-0 mt-0.5" />
                <span>
                  <strong>Sandbox Integration Notice:</strong> This reservation executes through the LiteAPI / Nuitee sandbox connector. No real payment charge occurs.
                </span>
              </div>

              {bookingSuccess ? (
                <div className="p-4 bg-emerald-50 border border-emerald-200 rounded-xl text-emerald-900 space-y-2">
                  <div className="flex items-center space-x-2 font-bold text-sm text-emerald-800">
                    <CheckCircle2 className="h-5 w-5 text-emerald-600" />
                    <span>Hotel Reservation Completed!</span>
                  </div>
                  <p className="text-xs">{bookingSuccess}</p>
                  <button
                    type="button"
                    onClick={() => {
                      setBookingModalHotel(null);
                      setCurrentStep('sightseeing');
                    }}
                    className="w-full mt-2 py-2.5 bg-emerald-600 hover:bg-emerald-700 text-white font-bold rounded-xl transition"
                  >
                    Continue to Sightseeing
                  </button>
                </div>
              ) : (
                <form onSubmit={handleConfirmBookingModal} className="space-y-3">
                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <label className="block text-[11px] font-bold text-slate-700 uppercase mb-1">
                        First Name *
                      </label>
                      <input
                        type="text"
                        value={guestFirstName}
                        onChange={(e) => setGuestFirstName(e.target.value)}
                        placeholder="e.g. Ramesh"
                        required
                        className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 font-medium"
                      />
                    </div>
                    <div>
                      <label className="block text-[11px] font-bold text-slate-700 uppercase mb-1">
                        Last Name *
                      </label>
                      <input
                        type="text"
                        value={guestLastName}
                        onChange={(e) => setGuestLastName(e.target.value)}
                        placeholder="e.g. Kumar"
                        required
                        className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 font-medium"
                      />
                    </div>
                  </div>

                  <div>
                    <label className="block text-[11px] font-bold text-slate-700 uppercase mb-1">
                      Email Address *
                    </label>
                    <input
                      type="email"
                      value={guestEmail}
                      onChange={(e) => setGuestEmail(e.target.value)}
                      placeholder="e.g. ramesh.kumar@example.com"
                      required
                      className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 font-medium"
                    />
                  </div>

                  <div>
                    <label className="block text-[11px] font-bold text-slate-700 uppercase mb-1">
                      Phone Number (Optional)
                    </label>
                    <input
                      type="tel"
                      value={guestPhone}
                      onChange={(e) => setGuestPhone(e.target.value)}
                      placeholder="e.g. +91 98765 43210"
                      className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 font-medium"
                    />
                  </div>

                  {bookingError && (
                    <div className="p-2.5 bg-red-50 border border-red-200 text-red-700 rounded-lg flex items-center space-x-1.5">
                      <AlertCircle className="h-4 w-4 text-red-600 flex-shrink-0" />
                      <span>{bookingError}</span>
                    </div>
                  )}

                  <div className="flex justify-end space-x-2 pt-2 border-t border-slate-100">
                    <button
                      type="button"
                      onClick={() => setBookingModalHotel(null)}
                      className="px-4 py-2 border border-slate-300 text-slate-700 rounded-xl hover:bg-slate-100 font-semibold"
                    >
                      Cancel
                    </button>
                    <button
                      type="submit"
                      disabled={isSubmittingBooking}
                      className="px-5 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl font-bold flex items-center space-x-1.5 disabled:opacity-50"
                    >
                      <Lock className="h-3.5 w-3.5" />
                      <span>{isSubmittingBooking ? 'Reserving...' : 'Confirm Sandbox Reservation'}</span>
                    </button>
                  </div>
                </form>
              )}
            </div>
          </div>
        </div>
      )}

    </div>
  );
};

