import React, { useState } from 'react';
import { useTravel } from '../../context/TravelContext';
import { ItineraryActivity } from '../../types/travel';
import { 
  CalendarDays, 
  Clock, 
  MapPin, 
  Car, 
  Footprints, 
  Plane, 
  IndianRupee, 
  Sparkles, 
  RefreshCw, 
  ArrowUp, 
  ArrowDown, 
  Trash2, 
  Plus, 
  ArrowRight, 
  ArrowLeft,
  Navigation,
  Compass,
  CheckCircle2,
  Lightbulb,
  Route
} from 'lucide-react';

export const ItinerarySection: React.FC = () => {
  const {
    itinerary,
    regenerateItinerary,
    regenerateDay,
    reorderActivity,
    removeActivity,
    addActivity,
    requirements,
    selectedHotel,
    setCurrentStep
  } = useTravel();

  const [activeDayIndex, setActiveDayIndex] = useState(0);
  const [showAddActivityModal, setShowAddActivityModal] = useState(false);
  const [newActivity, setNewActivity] = useState<Partial<ItineraryActivity>>({
    timeSlot: 'Afternoon',
    time: '02:30 PM',
    title: '',
    description: '',
    location: requirements.destination,
    transportMode: 'Cab',
    travelDurationFromPrevious: '15 mins drive',
    costEstimate: 250,
    tips: 'Recommended regional leisure stop.'
  });

  const activeDay = itinerary[activeDayIndex] || itinerary[0];

  const handleAddSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newActivity.title || !activeDay) return;

    addActivity(activeDay.dayNumber, {
      id: `custom-act-${Date.now()}`,
      timeSlot: newActivity.timeSlot as any,
      time: newActivity.time || '03:00 PM',
      title: newActivity.title,
      description: newActivity.description || 'Custom added itinerary activity.',
      location: newActivity.location || requirements.destination,
      transportMode: newActivity.transportMode as any,
      travelDurationFromPrevious: newActivity.travelDurationFromPrevious || '15 mins',
      costEstimate: Number(newActivity.costEstimate) || 0,
      tips: newActivity.tips || 'Enjoy at your own pace.'
    });

    setShowAddActivityModal(false);
    setNewActivity({
      timeSlot: 'Afternoon',
      time: '02:30 PM',
      title: '',
      description: '',
      location: requirements.destination,
      transportMode: 'Cab',
      travelDurationFromPrevious: '15 mins drive',
      costEstimate: 250,
      tips: 'Recommended regional leisure stop.'
    });
  };

  if (!activeDay) {
    return (
      <div className="max-w-7xl mx-auto px-4 py-12 text-center">
        <p className="text-slate-500">Generating initial itinerary schedule...</p>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      
      {/* Header & AI Controls */}
      <div className="bg-white rounded-3xl border border-slate-200 p-6 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2 text-xs font-bold uppercase tracking-wider text-slate-400">
            <span>AI Dynamic Day-by-Day Scheduler</span>
            <span>•</span>
            <span className="text-blue-600">Geographically Clustered</span>
          </div>
          <h2 className="text-2xl font-extrabold text-slate-900 mt-1">
            {requirements.durationDays}-Day Daily Timeline for {requirements.destination}
          </h2>
          <p className="text-xs text-slate-500 mt-0.5">
            Optimized for {requirements.tripType} pace • Centered from <strong>{selectedHotel?.name || 'Selected Stay'}</strong>
          </p>
        </div>

        {/* Global AI Regenerate Actions */}
        <div className="flex flex-wrap items-center gap-2">
          <button
            onClick={() => regenerateDay(activeDay.dayNumber)}
            className="px-3.5 py-2 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-bold transition flex items-center space-x-1.5"
          >
            <RefreshCw className="h-3.5 w-3.5 text-blue-600" />
            <span>Regenerate Day {activeDay.dayNumber}</span>
          </button>

          <button
            onClick={regenerateItinerary}
            className="px-4 py-2 rounded-xl bg-blue-600 hover:bg-blue-700 text-white text-xs font-bold transition shadow-md shadow-blue-500/20 flex items-center space-x-1.5"
          >
            <Sparkles className="h-4 w-4 text-amber-300" />
            <span>Regenerate Full Trip</span>
          </button>
        </div>
      </div>

      {/* Day Selector Tabs */}
      <div className="flex space-x-2 overflow-x-auto pb-2 scrollbar-thin">
        {itinerary.map((day, idx) => {
          const isActive = idx === activeDayIndex;
          return (
            <button
              key={day.dayNumber}
              onClick={() => setActiveDayIndex(idx)}
              className={`flex-shrink-0 px-5 py-3 rounded-2xl text-left transition-all border ${
                isActive 
                  ? 'bg-blue-600 text-white border-blue-600 shadow-md ring-2 ring-blue-500/20' 
                  : 'bg-white text-slate-700 border-slate-200 hover:border-slate-300 hover:bg-slate-50'
              }`}
            >
              <div className="flex items-center space-x-2">
                <CalendarDays className={`h-4 w-4 ${isActive ? 'text-white' : 'text-blue-600'}`} />
                <span className="font-extrabold text-sm">DAY {day.dayNumber}</span>
              </div>
              <div className={`text-[11px] mt-0.5 ${isActive ? 'text-blue-100' : 'text-slate-400'}`}>
                {day.date.split(',')[0]}
              </div>
            </button>
          );
        })}
      </div>

      {/* Active Day Theme Card */}
      <div className="bg-gradient-to-r from-blue-900 to-indigo-900 text-white rounded-2xl p-5 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2 text-xs text-blue-300 font-bold uppercase tracking-wider">
            <span>Day {activeDay.dayNumber} Theme & Highlights</span>
            <span>•</span>
            <span>{activeDay.date}</span>
            <span>•</span>
            <span className="bg-white/20 text-white px-2 py-0.5 rounded-full text-[10px] lowercase first-letter:uppercase font-semibold">
              {activeDay.dataSource || 'AI Generated Information'}
            </span>
          </div>
          <h3 className="text-xl font-bold mt-1 text-white">{activeDay.theme}</h3>
          <p className="text-xs text-slate-200 mt-1 max-w-2xl leading-relaxed">{activeDay.summary}</p>
        </div>

        <div className="bg-white/10 backdrop-blur-md rounded-xl p-3 border border-white/20 text-right min-w-[150px]">
          <span className="text-[11px] font-bold text-slate-300 uppercase block">Daily Activity Budget</span>
          <span className="text-lg font-extrabold text-amber-300">₹{activeDay.totalDayExpense.toLocaleString('en-IN')}</span>
          <span className="text-[10px] text-slate-300 block">Tickets & transfers</span>
        </div>
      </div>

      {/* Interactive Route Waypoint Visualizer (SVG Graphical Map) */}
      <div className="bg-white rounded-2xl border border-slate-200 p-5 shadow-sm space-y-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2 text-xs font-bold text-slate-700 uppercase tracking-wider">
            <Route className="h-4 w-4 text-blue-600" />
            <span>Interactive Day Route Visualisation</span>
          </div>
          <span className="text-xs text-emerald-700 font-semibold bg-emerald-50 px-2.5 py-0.5 rounded-full border border-emerald-200">
            ✓ Linear path without backtracking
          </span>
        </div>

        {/* Visual Waypoint Route Ribbon */}
        <div className="p-4 bg-slate-50 rounded-xl border border-slate-200 overflow-x-auto">
          <div className="flex items-center space-x-3 min-w-[650px]">
            {activeDay.activities.map((act, idx) => (
              <React.Fragment key={act.id}>
                <div className="flex flex-col items-center flex-shrink-0 text-center max-w-[120px]">
                  <div className={`h-8 w-8 rounded-full flex items-center justify-center font-bold text-xs text-white shadow-xs ${
                    idx === 0 ? 'bg-blue-600' :
                    idx === activeDay.activities.length - 1 ? 'bg-indigo-600' : 'bg-slate-800'
                  }`}>
                    {idx + 1}
                  </div>
                  <span className="text-[11px] font-bold text-slate-800 mt-1 line-clamp-1">{act.title}</span>
                  <span className="text-[10px] text-slate-400 font-medium">{act.time}</span>
                </div>

                {idx < activeDay.activities.length - 1 && (
                  <div className="flex-1 flex flex-col items-center px-1">
                    <span className="text-[10px] font-bold text-slate-500 whitespace-nowrap mb-0.5">
                      {activeDay.activities[idx + 1].travelDurationFromPrevious}
                    </span>
                    <div className="w-full flex items-center">
                      <div className="h-0.5 bg-blue-300 w-full dashed" />
                      <Navigation className="h-3 w-3 text-blue-600 rotate-90 transform -ml-1" />
                    </div>
                    <span className="text-[9px] text-slate-400 font-medium">
                      {activeDay.activities[idx + 1].transportMode}
                    </span>
                  </div>
                )}
              </React.Fragment>
            ))}
          </div>
        </div>
      </div>

      {/* Day Timeline Activities Flow */}
      <div className="space-y-4">
        <div className="flex justify-between items-center">
          <h3 className="font-heading font-extrabold text-base text-slate-900">
            Detailed Hourly Schedule ({activeDay.activities.length} Activities)
          </h3>
          <button
            onClick={() => setShowAddActivityModal(true)}
            className="px-3 py-1.5 bg-slate-900 hover:bg-slate-800 text-white rounded-xl text-xs font-bold flex items-center space-x-1.5 transition"
          >
            <Plus className="h-3.5 w-3.5" />
            <span>Add Custom Activity</span>
          </button>
        </div>

        {activeDay.activities.map((activity, idx) => (
          <div
            key={activity.id}
            className="bg-white rounded-2xl border border-slate-200 p-5 shadow-xs hover:border-slate-300 transition-all flex flex-col md:flex-row md:items-start justify-between gap-5"
          >
            {/* Left: Time & Transport Info */}
            <div className="md:w-48 flex-shrink-0 space-y-1">
              <div className="inline-flex items-center space-x-1.5 px-2.5 py-1 rounded-lg bg-blue-50 border border-blue-100 text-blue-800 font-bold text-xs">
                <Clock className="h-3.5 w-3.5 text-blue-600" />
                <span>{activity.time}</span>
              </div>
              <div className="text-xs font-semibold text-slate-500">{activity.timeSlot}</div>

              <div className="pt-2 text-xs space-y-1 text-slate-600">
                <div className="flex items-center space-x-1">
                  {activity.transportMode === 'Walking' ? (
                    <Footprints className="h-3.5 w-3.5 text-slate-400" />
                  ) : activity.transportMode === 'Flight' ? (
                    <Plane className="h-3.5 w-3.5 text-slate-400" />
                  ) : (
                    <Car className="h-3.5 w-3.5 text-slate-400" />
                  )}
                  <span className="font-medium">{activity.transportMode}</span>
                </div>
                <div className="text-[11px] text-slate-400">
                  {activity.travelDurationFromPrevious}
                </div>
              </div>
            </div>

            {/* Middle: Details & Photo */}
            <div className="flex-1 space-y-2">
              <div className="flex items-start justify-between gap-2">
                <div>
                  <h4 className="font-heading font-extrabold text-base text-slate-900">{activity.title}</h4>
                  <div className="flex items-center space-x-1 text-xs text-slate-500 mt-0.5">
                    <MapPin className="h-3 w-3 text-slate-400" />
                    <span>{activity.location}</span>
                  </div>
                </div>

                {/* Expense Tag */}
                {activity.costEstimate > 0 && (
                  <div className="text-xs font-extrabold text-slate-800 bg-slate-100 px-2.5 py-1 rounded-lg border border-slate-200 whitespace-nowrap">
                    ₹{activity.costEstimate.toLocaleString('en-IN')}
                  </div>
                )}
              </div>

              <p className="text-xs text-slate-600 leading-relaxed">{activity.description}</p>

              {/* Photo if present */}
              {activity.image && (
                <div className="h-36 w-full max-w-sm rounded-xl overflow-hidden mt-2 bg-slate-100 border border-slate-200">
                  <img
                    src={activity.image}
                    alt={activity.title}
                    className="w-full h-full object-cover"
                    onError={(e) => {
                      (e.target as HTMLImageElement).src = 'https://images.unsplash.com/photo-1599661046289-e31897846e41?auto=format&fit=crop&w=600&q=80';
                    }}
                  />
                </div>
              )}

              {/* Insider Tips */}
              {activity.tips && (
                <div className="p-2.5 bg-amber-50/70 border border-amber-200/60 rounded-xl text-[11px] text-amber-900 flex items-start space-x-1.5 mt-2">
                  <Lightbulb className="h-3.5 w-3.5 text-amber-600 flex-shrink-0 mt-0.5" />
                  <span><strong>Travel Tip:</strong> {activity.tips}</span>
                </div>
              )}
            </div>

            {/* Right: Reorder & Remove Controls */}
            <div className="flex md:flex-col items-center justify-end space-x-1 md:space-x-0 md:space-y-1.5 pt-3 md:pt-0 border-t md:border-t-0 border-slate-100">
              <button
                disabled={idx === 0}
                onClick={() => reorderActivity(activeDay.dayNumber, idx, idx - 1)}
                className="p-1.5 rounded-lg border border-slate-200 text-slate-600 hover:bg-slate-100 disabled:opacity-30 disabled:cursor-not-allowed"
                title="Move earlier"
              >
                <ArrowUp className="h-3.5 w-3.5" />
              </button>

              <button
                disabled={idx === activeDay.activities.length - 1}
                onClick={() => reorderActivity(activeDay.dayNumber, idx, idx + 1)}
                className="p-1.5 rounded-lg border border-slate-200 text-slate-600 hover:bg-slate-100 disabled:opacity-30 disabled:cursor-not-allowed"
                title="Move later"
              >
                <ArrowDown className="h-3.5 w-3.5" />
              </button>

              <button
                onClick={() => removeActivity(activeDay.dayNumber, activity.id)}
                className="p-1.5 rounded-lg border border-red-200 text-red-600 hover:bg-red-50"
                title="Remove activity"
              >
                <Trash2 className="h-3.5 w-3.5" />
              </button>
            </div>

          </div>
        ))}
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
          onClick={() => setCurrentStep('budget')}
          className="px-6 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-700 text-white text-xs font-bold transition shadow-md shadow-blue-500/20 flex items-center space-x-1.5"
        >
          <span>Continue to Budget</span>
          <ArrowRight className="h-4 w-4" />
        </button>
      </div>

      {/* Add Custom Activity Modal */}
      {showAddActivityModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm">
          <form onSubmit={handleAddSubmit} className="bg-white rounded-2xl max-w-lg w-full p-6 shadow-2xl border border-slate-200 space-y-4">
            <div className="flex justify-between items-center border-b border-slate-100 pb-3">
              <h3 className="font-heading font-bold text-base text-slate-900">
                Add Custom Activity to Day {activeDay.dayNumber}
              </h3>
              <button
                type="button"
                onClick={() => setShowAddActivityModal(false)}
                className="text-slate-400 hover:text-slate-600"
              >
                ✕
              </button>
            </div>

            <div className="space-y-3 text-xs">
              <div>
                <label className="block font-bold text-slate-700 mb-1">Activity Title</label>
                <input
                  type="text"
                  required
                  value={newActivity.title || ''}
                  onChange={(e) => setNewActivity({ ...newActivity, title: e.target.value })}
                  placeholder="e.g. Sunset High Tea at Nahargarh Fort"
                  className="w-full px-3 py-2 rounded-xl border border-slate-300 focus:outline-hidden focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block font-bold text-slate-700 mb-1">Time Slot</label>
                  <select
                    value={newActivity.timeSlot}
                    onChange={(e) => setNewActivity({ ...newActivity, timeSlot: e.target.value as any })}
                    className="w-full px-3 py-2 rounded-xl border border-slate-300"
                  >
                    <option value="Morning">Morning</option>
                    <option value="Afternoon">Afternoon</option>
                    <option value="Evening">Evening</option>
                    <option value="Night">Night</option>
                  </select>
                </div>
                <div>
                  <label className="block font-bold text-slate-700 mb-1">Time</label>
                  <input
                    type="text"
                    value={newActivity.time || ''}
                    onChange={(e) => setNewActivity({ ...newActivity, time: e.target.value })}
                    placeholder="e.g. 05:30 PM"
                    className="w-full px-3 py-2 rounded-xl border border-slate-300"
                  />
                </div>
              </div>

              <div>
                <label className="block font-bold text-slate-700 mb-1">Description</label>
                <textarea
                  value={newActivity.description || ''}
                  onChange={(e) => setNewActivity({ ...newActivity, description: e.target.value })}
                  rows={2}
                  placeholder="Details about what to see and experience..."
                  className="w-full px-3 py-2 rounded-xl border border-slate-300"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block font-bold text-slate-700 mb-1">Location</label>
                  <input
                    type="text"
                    value={newActivity.location || ''}
                    onChange={(e) => setNewActivity({ ...newActivity, location: e.target.value })}
                    className="w-full px-3 py-2 rounded-xl border border-slate-300"
                  />
                </div>
                <div>
                  <label className="block font-bold text-slate-700 mb-1">Est. Cost (₹)</label>
                  <input
                    type="number"
                    value={newActivity.costEstimate || 0}
                    onChange={(e) => setNewActivity({ ...newActivity, costEstimate: parseInt(e.target.value, 10) })}
                    className="w-full px-3 py-2 rounded-xl border border-slate-300"
                  />
                </div>
              </div>
            </div>

            <div className="flex justify-end space-x-2 pt-2 border-t border-slate-100">
              <button
                type="button"
                onClick={() => setShowAddActivityModal(false)}
                className="px-4 py-2 rounded-xl border border-slate-300 text-slate-700 text-xs font-semibold hover:bg-slate-100"
              >
                Cancel
              </button>
              <button
                type="submit"
                className="px-5 py-2 rounded-xl bg-blue-600 hover:bg-blue-700 text-white text-xs font-bold shadow-md shadow-blue-500/20"
              >
                Add Activity
              </button>
            </div>
          </form>
        </div>
      )}

    </div>
  );
};

