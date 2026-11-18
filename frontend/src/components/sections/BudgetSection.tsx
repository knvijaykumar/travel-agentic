import React, { useState } from 'react';
import { useTravel } from '../../context/TravelContext';
import { 
  IndianRupee, 
  Wallet, 
  TrendingUp, 
  TrendingDown, 
  PieChart, 
  ShieldCheck, 
  Plane, 
  Train,
  Hotel, 
  Car, 
  Ticket, 
  Utensils, 
  Sparkles, 
  CheckCircle2, 
  AlertTriangle, 
  ArrowRight, 
  ArrowLeft,
  Sliders,
  DollarSign
} from 'lucide-react';

export const BudgetSection: React.FC = () => {
  const {
    budget,
    updateBudget,
    requirements,
    selectedFlight,
    selectedHotel,
    transfers,
    toggleTransfer,
    itinerary,
    setCurrentStep,
    sendAIMessage
  } = useTravel();

  const [tempBudget, setTempBudget] = useState(requirements.totalBudget);

  const isTrain = requirements.transportMode === 'TRAIN' || requirements.transportPreference === 'Train' || (Boolean(budget.trainCost) && (budget.trainCost || 0) > 0);
  const transportAmount = isTrain ? (budget.trainCost || 0) : budget.flightCost;
  const transportLabel = isTrain ? 'Indian Railways Train' : 'Flights';
  const transportIcon = isTrain ? Train : Plane;

  const categories = [
    { label: transportLabel, amount: transportAmount, icon: transportIcon, color: isTrain ? 'bg-indigo-600' : 'bg-blue-600', text: isTrain ? 'text-indigo-600' : 'text-blue-600', border: 'border-blue-200', bg: 'bg-blue-50' },
    { label: 'Hotel Accommodation', amount: budget.hotelCost, icon: Hotel, color: 'bg-indigo-600', text: 'text-indigo-600', border: 'border-indigo-200', bg: 'bg-indigo-50' },
    { label: 'Transfers & Cabs', amount: budget.transportCost, icon: Car, color: 'bg-cyan-600', text: 'text-cyan-600', border: 'border-cyan-200', bg: 'bg-cyan-50' },
    { label: 'Sightseeing & Tickets', amount: budget.sightseeingCost, icon: Ticket, color: 'bg-emerald-600', text: 'text-emerald-600', border: 'border-emerald-200', bg: 'bg-emerald-50' },
    { label: 'Food & Dining (Est.)', amount: budget.foodEstimate, icon: Utensils, color: 'bg-amber-600', text: 'text-amber-600', border: 'border-amber-200', bg: 'bg-amber-50' },
    { label: 'Taxes & Contingency', amount: budget.miscCost, icon: ShieldCheck, color: 'bg-slate-600', text: 'text-slate-600', border: 'border-slate-200', bg: 'bg-slate-50' }
  ];

  const totalCalculated = Math.max(1, budget.totalEstimatedCost);

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      
      {/* Header */}
      <div className="bg-white rounded-3xl border border-slate-200 p-6 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2 text-xs font-bold uppercase tracking-wider text-slate-400">
            <span>Trip Budget & Expense Intelligence</span>
            <span>•</span>
            <span className="text-blue-600">No Double Counting</span>
          </div>
          <h2 className="text-2xl font-extrabold text-slate-900 mt-1">
            Complete Financial Breakdown
          </h2>
          <p className="text-xs text-slate-500 mt-0.5">
            Transparent breakdown across Flights, Hotel Stays, Transfers, Sightseeing, and Daily Meal Allocations.
          </p>
        </div>

        {/* Budget Status Badge */}
        <div className={`px-4 py-2.5 rounded-2xl border text-xs font-bold flex items-center space-x-2 ${
          budget.status === 'OVER_BUDGET' 
            ? 'bg-rose-50 border-rose-300 text-rose-800' 
            : budget.status === 'APPROACHING_LIMIT'
            ? 'bg-amber-50 border-amber-300 text-amber-800'
            : 'bg-emerald-50 border-emerald-300 text-emerald-800'
        }`}>
          {budget.status === 'OVER_BUDGET' ? (
            <AlertTriangle className="h-4 w-4 text-rose-600" />
          ) : (
            <CheckCircle2 className="h-4 w-4 text-emerald-600" />
          )}
          <span>
            {budget.status === 'OVER_BUDGET' 
              ? `Over Target by ₹${Math.abs(budget.remainingBudget).toLocaleString('en-IN')}` 
              : `Within Budget: ₹${budget.remainingBudget.toLocaleString('en-IN')} remaining`}
          </span>
        </div>
      </div>

      {/* Strict Over-Budget Guidance Panel */}
      {budget.status === 'OVER_BUDGET' && (
        <div className="bg-rose-50 border-2 border-rose-300 rounded-3xl p-6 shadow-sm space-y-4">
          <div className="flex items-center space-x-2 text-rose-700 font-extrabold text-sm uppercase tracking-wider">
            <AlertTriangle className="h-5 w-5 text-rose-600" />
            <span>Strict Budget Control Alert: Over Target by ₹{Math.abs(budget.remainingBudget).toLocaleString('en-IN')}</span>
          </div>
          <p className="text-xs text-rose-900 leading-relaxed">
            Your combined trip expenses (₹{budget.totalEstimatedCost.toLocaleString('en-IN')}) exceed the total trip budget of <strong>₹{budget.totalBudget.toLocaleString('en-IN')}</strong> for all {Math.max(1, requirements.travellers.adults + requirements.travellers.children)} travellers. To maintain strict financial control, please consider these actionable cost-saving substitutions:
          </p>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3 pt-1">
            <div className="p-3 bg-white rounded-xl border border-rose-200 space-y-1">
              <span className="text-[10px] font-bold uppercase text-rose-500">1. Transport Shift</span>
              <p className="text-xs font-bold text-slate-800">
                {!isTrain ? 'Switch from Flights to Indian Railways (Vande Bharat / Express)' : 'Select Sleeper or 3A Class'}
              </p>
              <p className="text-[11px] text-slate-500">Saves up to ₹6,000–₹12,000 for all travellers.</p>
              <button
                onClick={() => setCurrentStep('flights')}
                className="mt-2 text-xs font-bold text-blue-600 hover:underline"
              >
                Change Transport ➔
              </button>
            </div>

            <div className="p-3 bg-white rounded-xl border border-rose-200 space-y-1">
              <span className="text-[10px] font-bold uppercase text-rose-500">2. Hotel Accommodation</span>
              <p className="text-xs font-bold text-slate-800">Switch to Budget / Standard Tier</p>
              <p className="text-[11px] text-slate-500">Reduces nightly stay expense to match budget.</p>
              <button
                onClick={() => setCurrentStep('hotels')}
                className="mt-2 text-xs font-bold text-blue-600 hover:underline"
              >
                Browse Hotels ➔
              </button>
            </div>

            <div className="p-3 bg-white rounded-xl border border-rose-200 space-y-1">
              <span className="text-[10px] font-bold uppercase text-rose-500">3. Local Transfers</span>
              <p className="text-xs font-bold text-slate-800">Optimize Cab Transfers</p>
              <p className="text-[11px] text-slate-500">Use on-demand autos or public transport.</p>
              <button
                onClick={() => {
                  transfers.forEach(t => {
                    if (t.selected) toggleTransfer(t.id);
                  });
                }}
                className="mt-2 text-xs font-bold text-rose-600 hover:underline"
              >
                Deselect Extra Cabs ➔
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Top 4 Metrics Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        
        {/* Total Estimated Cost */}
        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-xs">
          <span className="text-xs font-bold text-slate-400 uppercase tracking-wider block">Estimated Total</span>
          <div className="mt-2 flex items-center text-2xl font-extrabold text-slate-900">
            <IndianRupee className="h-6 w-6 text-blue-600" />
            <span>₹{budget.totalEstimatedCost.toLocaleString('en-IN')}</span>
          </div>
          <span className="text-[11px] text-slate-500 mt-1 block">
            Target: ₹{budget.totalBudget.toLocaleString('en-IN')}
          </span>
        </div>

        {/* Remaining Budget */}
        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-xs">
          <span className="text-xs font-bold text-slate-400 uppercase tracking-wider block">Remaining Balance</span>
          <div className={`mt-2 flex items-center text-2xl font-extrabold ${
            budget.remainingBudget >= 0 ? 'text-emerald-600' : 'text-rose-600'
          }`}>
            <IndianRupee className="h-6 w-6" />
            <span>₹{Math.abs(budget.remainingBudget).toLocaleString('en-IN')}</span>
          </div>
          <span className="text-[11px] text-slate-500 mt-1 block">
            {budget.remainingBudget >= 0 ? 'Surplus buffer available' : 'Budget limit exceeded'}
          </span>
        </div>

        {/* Per-Person Cost */}
        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-xs">
          <span className="text-xs font-bold text-slate-400 uppercase tracking-wider block">Per-Person Cost</span>
          <div className="mt-2 flex items-center text-2xl font-extrabold text-indigo-700">
            <IndianRupee className="h-6 w-6" />
            <span>₹{budget.perPersonCost.toLocaleString('en-IN')}</span>
          </div>
          <span className="text-[11px] text-slate-500 mt-1 block">
            Split across {requirements.travellers.adults + requirements.travellers.children} travellers
          </span>
        </div>

        {/* Budget Utilization Rate */}
        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-xs">
          <span className="text-xs font-bold text-slate-400 uppercase tracking-wider block">Budget Utilisation</span>
          <div className="mt-2 flex items-center text-2xl font-extrabold text-slate-900">
            <span>{budget.budgetUtilizationPct}%</span>
          </div>
          <div className="w-full bg-slate-100 rounded-full h-2 mt-2 overflow-hidden">
            <div 
              className={`h-full rounded-full transition-all ${
                budget.budgetUtilizationPct > 100 ? 'bg-rose-500' :
                budget.budgetUtilizationPct > 85 ? 'bg-amber-500' : 'bg-emerald-500'
              }`}
              style={{ width: `${Math.min(100, budget.budgetUtilizationPct)}%` }}
            />
          </div>
        </div>

      </div>

      {/* Visual Category Breakdown & Transfer Options */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        
        {/* Category Expense Distribution (2 Cols) */}
        <div className="lg:col-span-2 space-y-6">
          <div className="bg-white rounded-3xl border border-slate-200 p-6 shadow-sm space-y-5">
            <h3 className="font-heading font-extrabold text-base text-slate-900 flex items-center space-x-2">
              <PieChart className="h-5 w-5 text-blue-600" />
              <span>Category Expense Breakdown</span>
            </h3>

            {/* Visual Horizontal Segmented Bar */}
            <div className="space-y-2">
              <div className="w-full h-4 rounded-full bg-slate-100 flex overflow-hidden shadow-inner">
                {categories.map((cat, i) => {
                  const pct = Math.round((cat.amount / totalCalculated) * 100);
                  if (pct <= 0) return null;
                  return (
                    <div
                      key={i}
                      className={`${cat.color} h-full transition-all`}
                      style={{ width: `${pct}%` }}
                      title={`${cat.label}: ₹${cat.amount.toLocaleString('en-IN')} (${pct}%)`}
                    />
                  );
                })}
              </div>

              <div className="flex flex-wrap gap-3 pt-1 text-[11px] text-slate-600 font-medium">
                {categories.map((cat, i) => (
                  <div key={i} className="flex items-center space-x-1.5">
                    <span className={`h-2.5 w-2.5 rounded-full ${cat.color}`} />
                    <span>{cat.label} ({Math.round((cat.amount / totalCalculated) * 100)}%)</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Category Cards Grid */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-3">
              {categories.map((cat, idx) => {
                const Icon = cat.icon;
                return (
                  <div key={idx} className={`p-4 rounded-2xl border ${cat.border} ${cat.bg} flex items-center justify-between`}>
                    <div className="flex items-center space-x-3">
                      <div className={`p-2 rounded-xl bg-white shadow-2xs ${cat.text}`}>
                        <Icon className="h-4 w-4" />
                      </div>
                      <div>
                        <span className="text-xs font-bold text-slate-800 block">{cat.label}</span>
                        <span className="text-[11px] text-slate-500">
                          {Math.round((cat.amount / totalCalculated) * 100)}% of total
                        </span>
                      </div>
                    </div>
                    <div className="font-extrabold text-sm text-slate-900">
                      ₹{cat.amount.toLocaleString('en-IN')}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Transfers & Local Transport Selection */}
          <div className="bg-white rounded-3xl border border-slate-200 p-6 shadow-sm space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="font-heading font-extrabold text-base text-slate-900 flex items-center space-x-2">
                  <Car className="h-5 w-5 text-cyan-600" />
                  <span>Transfers & Local Transportation</span>
                </h3>
                <p className="text-xs text-slate-500 mt-0.5">Toggle optional dedicated transfer and cab services</p>
              </div>
            </div>

            <div className="space-y-3">
              {transfers.map(tr => (
                <div
                  key={tr.id}
                  className={`p-4 rounded-2xl border transition-all flex flex-col sm:flex-row sm:items-center justify-between gap-3 ${
                    tr.selected 
                      ? 'bg-cyan-50/60 border-cyan-400 ring-2 ring-cyan-400/20 shadow-xs' 
                      : 'bg-white border-slate-200 hover:border-slate-300'
                  }`}
                >
                  <div className="space-y-1">
                    <div className="flex items-center space-x-2">
                      <span className="font-bold text-xs text-slate-900">{tr.title}</span>
                      <span className="text-[10px] bg-slate-100 text-slate-600 px-2 py-0.5 rounded font-medium">
                        {tr.vehicle}
                      </span>
                    </div>
                    <p className="text-xs text-slate-500">{tr.capacity}</p>
                    <div className="flex flex-wrap gap-1.5 pt-0.5">
                      {tr.features.map((f, i) => (
                        <span key={i} className="text-[10px] text-cyan-800 bg-cyan-100/60 px-2 py-0.5 rounded font-medium">
                          ✓ {f}
                        </span>
                      ))}
                    </div>
                  </div>

                  <div className="flex sm:flex-col items-center sm:items-end justify-between sm:justify-center gap-2">
                    <div className="font-extrabold text-sm text-slate-900">
                      ₹{tr.price.toLocaleString('en-IN')}
                    </div>
                    <button
                      onClick={() => toggleTransfer(tr.id)}
                      className={`px-3.5 py-1.5 rounded-xl text-xs font-bold transition ${
                        tr.selected 
                          ? 'bg-cyan-700 hover:bg-cyan-800 text-white shadow-2xs' 
                          : 'bg-slate-100 hover:bg-slate-200 text-slate-700'
                      }`}
                    >
                      {tr.selected ? 'Selected' : 'Add to Trip'}
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Daily Expense Breakdown Table */}
          <div className="bg-white rounded-3xl border border-slate-200 p-6 shadow-sm space-y-4">
            <h3 className="font-heading font-extrabold text-base text-slate-900">
              Daily Itinerary Expense Schedule
            </h3>

            <div className="overflow-x-auto">
              <table className="w-full text-xs text-left">
                <thead className="bg-slate-50 text-slate-500 font-bold uppercase border-b border-slate-200">
                  <tr>
                    <th className="px-4 py-3">Day / Date</th>
                    <th className="px-4 py-3">Theme</th>
                    <th className="px-4 py-3">Activities Included</th>
                    <th className="px-4 py-3 text-right">Day Total</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 font-medium text-slate-700">
                  {itinerary.map(day => (
                    <tr key={day.dayNumber} className="hover:bg-slate-50/50">
                      <td className="px-4 py-3 font-bold text-slate-900">
                        Day {day.dayNumber}
                        <div className="text-[10px] text-slate-400 font-normal">{day.date.split(',')[0]}</div>
                      </td>
                      <td className="px-4 py-3">{day.theme}</td>
                      <td className="px-4 py-3 text-slate-500">
                        {day.activities.length} scheduled stops
                      </td>
                      <td className="px-4 py-3 text-right font-extrabold text-slate-900">
                        ₹{day.totalDayExpense.toLocaleString('en-IN')}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

        </div>

        {/* Right Column: AI Budget Optimizer (1 Col) */}
        <div className="space-y-6">
          
          {/* Target Budget Modifier Card */}
          <div className="bg-white rounded-3xl border border-slate-200 p-6 shadow-sm space-y-4">
            <div className="flex items-center space-x-2 text-slate-800 font-bold text-xs uppercase tracking-wider">
              <Sliders className="h-4 w-4 text-blue-600" />
              <span>Modify Target Budget</span>
            </div>

            <div className="flex items-center text-2xl font-extrabold text-slate-900">
              <IndianRupee className="h-6 w-6 text-blue-600" />
              <span>₹{tempBudget.toLocaleString('en-IN')}</span>
            </div>

            <input
              type="range"
              min={20000}
              max={150000}
              step={2500}
              value={tempBudget}
              onChange={(e) => {
                const val = parseInt(e.target.value, 10);
                setTempBudget(val);
                updateBudget(val);
              }}
              className="w-full accent-blue-600 cursor-pointer"
            />

            <div className="flex justify-between text-[11px] text-slate-400 font-semibold">
              <span>₹20,000</span>
              <span>₹75,000</span>
              <span>₹1,50,000</span>
            </div>

            <div className="pt-2 border-t border-slate-100 text-xs text-slate-600 space-y-2">
              <p>
                Adjusting the slider dynamically triggers AI recommendations to keep all flights and hotels in sync with your spending preference.
              </p>
            </div>
          </div>

          {/* AI Optimizer Recommendations Card */}
          <div className="bg-gradient-to-br from-indigo-900 to-slate-900 text-white rounded-3xl p-6 shadow-md border border-indigo-800 space-y-4">
            <div className="flex items-center space-x-2 text-amber-300 text-xs font-bold uppercase tracking-wider">
              <Sparkles className="h-4 w-4" />
              <span>AI Budget Recommendations</span>
            </div>

            <h4 className="font-heading font-extrabold text-lg text-white">
              Smart Ways to Save ₹3,500+
            </h4>

            <div className="space-y-2.5 text-xs text-slate-200">
              <div className="p-3 bg-white/10 rounded-xl border border-white/10 space-y-1">
                <span className="font-bold text-white block">1. Flight Timing Shift</span>
                <p className="text-slate-300 text-[11px]">
                  Opting for early morning IndiGo (6E-512) saves ₹1,200 per passenger compared to peak afternoon departures.
                </p>
              </div>

              <div className="p-3 bg-white/10 rounded-xl border border-white/10 space-y-1">
                <span className="font-bold text-white block">2. Group Entry Combo</span>
                <p className="text-slate-300 text-[11px]">
                  Composite heritage tickets at monuments in {requirements.destinationState} save up to 25% on gate fares.
                </p>
              </div>
            </div>

            <button
              onClick={() => sendAIMessage('Reduce my trip budget by optimizing flight and accommodation selections.')}
              className="w-full py-2.5 px-4 rounded-xl bg-blue-600 hover:bg-blue-500 text-white font-bold text-xs shadow-md transition"
            >
              Apply AI Auto-Optimization
            </button>
          </div>

        </div>

      </div>

      {/* Navigation Footer */}
      <div className="pt-6 border-t border-slate-200 flex justify-between items-center">
        <button
          onClick={() => setCurrentStep('itinerary')}
          className="px-4 py-2.5 rounded-xl border border-slate-300 hover:bg-slate-100 text-slate-700 text-xs font-bold transition flex items-center space-x-1.5"
        >
          <ArrowLeft className="h-4 w-4" />
          <span>Back to Itinerary</span>
        </button>

        <button
          onClick={() => setCurrentStep('review')}
          className="px-6 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-700 text-white text-xs font-bold transition shadow-md shadow-blue-500/20 flex items-center space-x-1.5"
        >
          <span>Final Trip Review</span>
          <ArrowRight className="h-4 w-4" />
        </button>
      </div>

    </div>
  );
};

