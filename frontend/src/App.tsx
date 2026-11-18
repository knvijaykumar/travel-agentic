import React from 'react';
import { TravelProvider, useTravel } from './context/TravelContext';
import { Header } from './components/common/Header';
import { TripSummaryDrawer } from './components/common/TripSummaryDrawer';
import { AIAssistantDrawer } from './components/common/AIAssistantDrawer';
import { RequirementsSection } from './components/sections/RequirementsSection';
import { FlightsSection } from './components/sections/FlightsSection';
import { HotelsSection } from './components/sections/HotelsSection';
import { SightseeingSection } from './components/sections/SightseeingSection';
import { ItinerarySection } from './components/sections/ItinerarySection';
import { BudgetSection } from './components/sections/BudgetSection';
import { TripReviewSection } from './components/sections/TripReviewSection';
import { MyTripsSection } from './components/sections/MyTripsSection';
import { BrandLogo } from './components/common/BrandLogo';
import { ShieldCheck } from 'lucide-react';

const MainLayout: React.FC = () => {
  const { currentStep } = useTravel();

  return (
    <div className="min-h-screen flex flex-col bg-slate-50 text-slate-900 font-sans">
      <Header />

      {/* Main Active Section */}
      <main className="flex-1 pb-16">
        {currentStep === 'requirements' && <RequirementsSection />}
        {currentStep === 'flights' && <FlightsSection />}
        {currentStep === 'hotels' && <HotelsSection />}
        {currentStep === 'sightseeing' && <SightseeingSection />}
        {currentStep === 'itinerary' && <ItinerarySection />}
        {currentStep === 'budget' && <BudgetSection />}
        {currentStep === 'review' && <TripReviewSection />}
        {currentStep === 'my-trips' && <MyTripsSection />}
      </main>

      {/* Drawers */}
      <TripSummaryDrawer />
      <AIAssistantDrawer />

      {/* Global Footer */}
      <footer className="bg-slate-900 text-slate-400 py-10 border-t border-slate-800 text-xs">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex items-center space-x-3">
            <BrandLogo variant="full" surface="dark" imgClassName="h-8 w-auto object-contain" containerClassName="px-2.5 py-1" />
            <span className="text-slate-600">•</span>
            <span>AI Travel Planning Platform</span>
          </div>

          <div className="flex items-center space-x-4 text-[11px]">
            <span className="flex items-center space-x-1 text-slate-300">
              <ShieldCheck className="h-3.5 w-3.5 text-blue-400" />
              <span>Pan-India Coverage (28 States & 8 UTs)</span>
            </span>
            <span className="text-slate-600">•</span>
            <span>FastAPI & Gemini AI Architecture</span>
          </div>

          <div className="text-[11px] text-slate-500">
            © 2026 Pravasa Platform. All rights reserved.
          </div>
        </div>
      </footer>
    </div>
  );
};

export const App: React.FC = () => {
  return (
    <TravelProvider>
      <MainLayout />
    </TravelProvider>
  );
};

export default App;

