import React, { useState } from 'react';
import { useTravel } from '../../context/TravelContext';
import { SavedTrip, BookingRecord } from '../../types/travel';
import { BrandLogo } from '../common/BrandLogo';
import { 
  Luggage, 
  Calendar, 
  MapPin, 
  FileText, 
  AlertTriangle, 
  CheckCircle2, 
  X, 
  Download, 
  Printer, 
  RefreshCw, 
  Plane, 
  Hotel, 
  Car, 
  IndianRupee, 
  Clock, 
  ShieldAlert,
  ArrowRight
} from 'lucide-react';

export const MyTripsSection: React.FC = () => {
  const { myTrips, cancelBooking, setCurrentStep } = useTravel();

  const [activeTab, setActiveTab] = useState<'UPCOMING' | 'ONGOING' | 'COMPLETED'>('UPCOMING');
  const [selectedVoucherTrip, setSelectedVoucherTrip] = useState<SavedTrip | null>(null);
  const [cancelModalItem, setCancelModalItem] = useState<{ tripId: string; booking: BookingRecord } | null>(null);

  const filteredTrips = myTrips.filter(t => t.status === activeTab);

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      
      {/* Header */}
      <div className="bg-white rounded-3xl border border-slate-200 p-6 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2 text-xs font-bold uppercase tracking-wider text-slate-400">
            <span>Post-Booking Management & Travel Hub</span>
            <span>•</span>
            <span className="text-blue-600">Verified Vouchers & Disruption Support</span>
          </div>
          <h2 className="text-2xl font-extrabold text-slate-900 mt-1">
            My Trips & Booking Passes
          </h2>
          <p className="text-xs text-slate-500 mt-0.5">
            Access your e-tickets, hotel check-in vouchers, real-time travel disruption advisories, and modification policies.
          </p>
        </div>

        {/* Tab Switcher */}
        <div className="flex items-center space-x-1.5 bg-slate-100 p-1.5 rounded-2xl border border-slate-200 text-xs">
          {(['UPCOMING', 'ONGOING', 'COMPLETED'] as const).map(tab => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`px-4 py-2 rounded-xl font-bold transition ${
                activeTab === tab 
                  ? 'bg-white text-slate-900 shadow-xs' 
                  : 'text-slate-500 hover:text-slate-800'
              }`}
            >
              {tab.charAt(0) + tab.slice(1).toLowerCase()} ({myTrips.filter(t => t.status === tab).length})
            </button>
          ))}
        </div>
      </div>

      {/* Trips Content */}
      {filteredTrips.length === 0 ? (
        <div className="bg-white rounded-3xl border border-slate-200 p-12 text-center space-y-4">
          <div className="h-16 w-16 rounded-3xl bg-blue-50 text-blue-600 flex items-center justify-center mx-auto">
            <Luggage className="h-8 w-8" />
          </div>
          <div>
            <h3 className="font-heading font-extrabold text-lg text-slate-900">
              No {activeTab.toLowerCase()} trips right now
            </h3>
            <p className="text-xs text-slate-500 mt-1 max-w-sm mx-auto">
              Plan your next getaway across all 28 Indian states & 8 Union Territories with our AI-powered travel assistant.
            </p>
          </div>
          <button
            onClick={() => setCurrentStep('requirements')}
            className="px-6 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-700 text-white text-xs font-bold transition shadow-md shadow-blue-500/20"
          >
            Start Planning a New Trip ➔
          </button>
        </div>
      ) : (
        <div className="space-y-6">
          {filteredTrips.map(trip => (
            <div
              key={trip.id}
              className="bg-white rounded-3xl border border-slate-200 overflow-hidden shadow-sm space-y-5 p-6"
            >
              {/* Trip Header Banner */}
              <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-100 pb-4">
                <div>
                  <div className="flex items-center space-x-2">
                    <span className="text-[10px] font-bold uppercase tracking-wider bg-emerald-100 text-emerald-800 border border-emerald-200 px-2.5 py-0.5 rounded-full">
                      ✓ Confirmed Reservation
                    </span>
                    <span className="text-xs text-slate-400 font-mono">ID: {trip.id}</span>
                  </div>
                  <h3 className="text-xl font-extrabold text-slate-900 mt-1">{trip.tripTitle}</h3>
                  <div className="flex items-center space-x-2 text-xs text-slate-500 mt-0.5">
                    <Calendar className="h-3.5 w-3.5 text-blue-600" />
                    <span>{trip.startDate} to {trip.endDate} ({trip.requirements.durationDays} Days)</span>
                    <span>•</span>
                    <MapPin className="h-3.5 w-3.5 text-blue-600" />
                    <span>{trip.destination}</span>
                  </div>
                </div>

                <div className="flex items-center space-x-2">
                  <button
                    onClick={() => setSelectedVoucherTrip(trip)}
                    className="px-4 py-2 rounded-xl bg-slate-900 hover:bg-slate-800 text-white text-xs font-bold transition flex items-center space-x-1.5 shadow-sm"
                  >
                    <FileText className="h-4 w-4" />
                    <span>View E-Vouchers</span>
                  </button>
                </div>
              </div>

              {/* Travel Disruption Advisory */}
              {trip.disruptionAlerts && trip.disruptionAlerts.length > 0 && (
                <div className="p-3.5 bg-blue-50 border border-blue-200 rounded-2xl flex items-start space-x-3 text-xs">
                  <ShieldAlert className="h-4 w-4 text-blue-600 flex-shrink-0 mt-0.5" />
                  <div>
                    <span className="font-bold text-blue-900">{trip.disruptionAlerts[0].title}</span>
                    <p className="text-blue-800 text-[11px] mt-0.5">{trip.disruptionAlerts[0].description}</p>
                  </div>
                </div>
              )}

              {/* Bookings Table / Cards */}
              <div className="space-y-3">
                <span className="text-xs font-bold text-slate-700 uppercase tracking-wider block">
                  Booked Travel Products ({trip.bookings.length})
                </span>

                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                  {trip.bookings.map(booking => {
                    const isCancelled = booking.status === 'CANCELLED';
                    return (
                      <div
                        key={booking.id}
                        className={`p-4 rounded-2xl border text-xs space-y-2 ${
                          isCancelled ? 'bg-slate-50 border-slate-200 opacity-60' : 'bg-slate-50 border-slate-200'
                        }`}
                      >
                        <div className="flex justify-between items-start">
                          <span className={`text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded ${
                            booking.productType === 'FLIGHT' ? 'bg-blue-100 text-blue-800' :
                            booking.productType === 'HOTEL' ? 'bg-indigo-100 text-indigo-800' :
                            'bg-cyan-100 text-cyan-800'
                          }`}>
                            {booking.productType}
                          </span>

                          <span className={`text-[10px] font-bold px-2 py-0.5 rounded ${
                            isCancelled 
                              ? 'bg-rose-100 text-rose-700' 
                              : booking.status === 'EXTERNAL_REDIRECT'
                                ? 'bg-amber-100 text-amber-800 border border-amber-200'
                                : 'bg-emerald-100 text-emerald-800'
                          }`}>
                            {isCancelled 
                              ? 'CANCELLED' 
                              : booking.status === 'EXTERNAL_REDIRECT'
                                ? 'External Booking – Not Confirmed'
                                : 'CONFIRMED'}
                          </span>
                        </div>

                        <div>
                          <h4 className="font-bold text-slate-900 line-clamp-1">{booking.title}</h4>
                          <span className="text-slate-400 font-mono text-[11px]">Ref: {booking.bookingRef}</span>
                        </div>

                        <div className="pt-1 border-t border-slate-200 flex justify-between items-center text-slate-600">
                          <span>Amount:</span>
                          <span className="font-extrabold text-slate-900">₹{booking.amount.toLocaleString('en-IN')}</span>
                        </div>

                        {!isCancelled && (
                          <div className="pt-1 flex justify-end">
                            <button
                              onClick={() => setCancelModalItem({ tripId: trip.id, booking })}
                              className="text-[11px] text-rose-600 hover:text-rose-700 font-semibold underline"
                            >
                              Cancel Booking
                            </button>
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>

            </div>
          ))}
        </div>
      )}

      {/* E-Voucher & Travel Passes Modal */}
      {selectedVoucherTrip && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm">
          <div className="bg-white rounded-3xl max-w-2xl w-full max-h-[90vh] flex flex-col shadow-2xl border border-slate-200">
            <div className="p-5 bg-slate-900 text-white flex justify-between items-center rounded-t-3xl">
              <div className="flex items-center space-x-2">
                <FileText className="h-5 w-5 text-blue-400" />
                <h3 className="font-heading font-bold text-base">
                  Official Travel Vouchers & Boarding Passes
                </h3>
              </div>
              <button
                onClick={() => setSelectedVoucherTrip(null)}
                className="text-slate-400 hover:text-white"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            <div className="p-6 overflow-y-auto space-y-5 text-xs">
              <div className="text-center pb-4 border-b border-slate-100">
                <div className="flex justify-center mb-2">
                  <BrandLogo variant="full" surface="light" imgClassName="h-12 w-auto object-contain" />
                </div>
                <span className="text-[10px] uppercase font-bold text-blue-600 tracking-widest block">
                  Pravasa Digital Travel Pass
                </span>
                <h2 className="text-lg font-extrabold text-slate-900 mt-0.5">
                  {selectedVoucherTrip.tripTitle}
                </h2>
                <p className="text-slate-500 text-[11px]">
                  Issued to: <strong>Vijay Kumar & Party</strong> ({selectedVoucherTrip.requirements.travellers.adults} Adults, {selectedVoucherTrip.requirements.travellers.children} Child)
                </p>
              </div>

              {/* Vouchers list */}
              {selectedVoucherTrip.bookings.map(b => (
                <div key={b.id} className="p-4 bg-slate-50 rounded-2xl border border-slate-200 space-y-2">
                  <div className="flex justify-between items-center">
                    <span className="font-bold text-sm text-slate-900">{b.title}</span>
                    <span className="font-mono text-xs font-bold bg-white border border-slate-300 px-2 py-0.5 rounded">
                      {b.bookingRef}
                    </span>
                  </div>
                  <div className="text-slate-600 text-[11px]">
                    Provider: <strong>{b.provider}</strong> | Travel: {b.travelDates}
                  </div>
                  {b.voucherNumber && (
                    <div className="text-slate-500 font-mono text-[10px]">
                      Ticket / Voucher Code: {b.voucherNumber}
                    </div>
                  )}
                </div>
              ))}

              {/* Barcode Graphic Simulation */}
              <div className="p-4 bg-slate-100 rounded-xl text-center space-y-1">
                <div className="h-10 w-48 bg-slate-800 mx-auto rounded flex items-center justify-center text-white font-mono text-[10px] tracking-widest">
                  |||||| |||| |||||||| |||
                </div>
                <span className="text-[10px] text-slate-500 font-mono">PNR AUTH: YA-2026-IND-7789</span>
              </div>
            </div>

            <div className="p-4 bg-slate-50 border-t border-slate-100 flex justify-end space-x-2 rounded-b-3xl">
              <button
                onClick={() => alert('Voucher PDF successfully downloaded to your device!')}
                className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-xl text-xs font-bold flex items-center space-x-1.5"
              >
                <Download className="h-3.5 w-3.5" />
                <span>Download PDF Passes</span>
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Cancellation Confirmation Modal */}
      {cancelModalItem && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm">
          <div className="bg-white rounded-3xl max-w-md w-full p-6 shadow-2xl border border-slate-200 space-y-4">
            <div className="flex items-center space-x-2 text-rose-600">
              <AlertTriangle className="h-6 w-6" />
              <h3 className="font-heading font-extrabold text-base text-slate-900">
                Cancel Booking Reservation?
              </h3>
            </div>

            <div className="text-xs text-slate-600 space-y-2 leading-relaxed">
              <p>
                Are you sure you wish to cancel <strong>{cancelModalItem.booking.title}</strong> (Ref: {cancelModalItem.booking.bookingRef})?
              </p>
              <div className="p-3 bg-slate-50 rounded-xl border border-slate-200 text-[11px] space-y-1">
                <div>Original Booking Fare: <strong>₹{cancelModalItem.booking.amount.toLocaleString('en-IN')}</strong></div>
                <div>Cancellation Processing Fee: <strong>₹500</strong></div>
                <div className="text-emerald-700 font-bold">
                  Estimated Refund Amount: ₹{(cancelModalItem.booking.amount - 500).toLocaleString('en-IN')}
                </div>
              </div>
            </div>

            <div className="flex justify-end space-x-2 pt-2">
              <button
                onClick={() => setCancelModalItem(null)}
                className="px-4 py-2 rounded-xl border border-slate-300 text-slate-700 text-xs font-semibold hover:bg-slate-100"
              >
                Keep Booking
              </button>
              <button
                onClick={() => {
                  cancelBooking(cancelModalItem.tripId, cancelModalItem.booking.bookingRef);
                  setCancelModalItem(null);
                }}
                className="px-5 py-2 rounded-xl bg-rose-600 hover:bg-rose-700 text-white text-xs font-bold shadow-md shadow-rose-600/20"
              >
                Confirm Cancellation
              </button>
            </div>
          </div>
        </div>
      )}

    </div>
  );
};

