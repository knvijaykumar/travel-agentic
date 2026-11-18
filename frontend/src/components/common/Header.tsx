import React from 'react';
import { useTravel } from '../../context/TravelContext';
import { WorkflowStep } from '../../types/travel';
import { BrandLogo } from './BrandLogo';
import { 
  Compass, 
  Plane, 
  Hotel, 
  MapPin, 
  CalendarDays, 
  Wallet, 
  CheckCircle2, 
  Luggage, 
  Sparkles
} from 'lucide-react';

const steps: { key: WorkflowStep; label: string; icon: React.FC<{ className?: string }> }[] = [
  { key: 'requirements', label: '1. Travel Details', icon: Compass },
  { key: 'flights', label: '2. Transport (Air/Rail)', icon: Plane },
  { key: 'hotels', label: '3. Hotels', icon: Hotel },
  { key: 'itinerary', label: '4. AI Itinerary', icon: CalendarDays },
  { key: 'budget', label: '5. Budget', icon: Wallet },
  { key: 'review', label: '6. Trip Review', icon: CheckCircle2 },
  { key: 'my-trips', label: '7. My Trips', icon: Luggage }
];

export const Header: React.FC = () => {
  const { 
    currentStep, 
    setCurrentStep, 
    setAIDrawerOpen,
    backendOnline
  } = useTravel();

  return (
    <header className="sticky top-0 z-40 bg-slate-900 border-b border-slate-800 text-white shadow-xl">
      {/* Top Banner Bar */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between py-2.5 sm:py-3">
          {/* Brand Logo */}
          <div className="flex items-center space-x-3 cursor-pointer group" onClick={() => setCurrentStep('requirements')}>
            <BrandLogo
              variant="full"
              surface="dark"
              imgClassName="h-9 sm:h-11 w-auto object-contain transition-transform group-hover:scale-[1.02]"
            />
            <span className="hidden md:inline-flex items-center text-[10px] uppercase font-bold tracking-widest bg-blue-500/20 text-blue-300 border border-blue-500/30 px-2.5 py-1 rounded-full">
              Virtual Agent
            </span>
          </div>

          {/* Action Trigger */}
          <div className="flex items-center space-x-2.5">
            {/* Backend Connectivity Status Pill */}
            <div className={`hidden sm:flex items-center space-x-1.5 px-2.5 py-1 rounded-full text-[10px] font-bold border ${
              backendOnline 
                ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30' 
                : 'bg-amber-500/10 text-amber-400 border-amber-500/30'
            }`}>
              <span className={`h-2 w-2 rounded-full ${backendOnline ? 'bg-emerald-400 animate-pulse' : 'bg-amber-400'}`} />
              <span>{backendOnline ? 'FastAPI Backend Online' : 'Client Intelligence Engine'}</span>
            </div>

            {/* AI Assistant Button */}
            <button
              onClick={() => setAIDrawerOpen(true)}
              className="px-3.5 py-2 text-xs font-bold rounded-lg bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white shadow-md shadow-blue-600/30 transition flex items-center space-x-1.5 active:scale-95"
            >
              <Sparkles className="h-4 w-4 text-amber-300 animate-pulse" />
              <span>AI Assistant</span>
            </button>
          </div>
        </div>
      </div>

      {/* Workflow Navigation Steps */}
      <div className="bg-slate-950/90 border-t border-slate-800/80 overflow-x-auto scrollbar-none py-2 px-4 sm:px-6 lg:px-8">
        <nav className="max-w-7xl mx-auto flex items-center space-x-1 min-w-max">
          {steps.map((step, idx) => {
            const Icon = step.icon;
            const isActive = currentStep === step.key;
            return (
              <button
                key={step.key}
                onClick={() => setCurrentStep(step.key)}
                className={`flex items-center space-x-2 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                  isActive
                    ? 'bg-blue-600 text-white shadow-sm shadow-blue-500/40 ring-1 ring-blue-400'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/70'
                }`}
              >
                <Icon className={`h-3.5 w-3.5 ${isActive ? 'text-white' : 'text-slate-400'}`} />
                <span>{step.label}</span>
                {idx < steps.length - 1 && (
                  <span className="ml-1 text-slate-600 text-[10px]">➔</span>
                )}
              </button>
            );
          })}
        </nav>
      </div>
    </header>
  );
};

