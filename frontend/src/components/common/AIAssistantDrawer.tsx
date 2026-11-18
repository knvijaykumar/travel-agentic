import React, { useState } from 'react';
import { useTravel } from '../../context/TravelContext';
import { BrandLogo } from './BrandLogo';
import { 
  X, 
  Send, 
  User, 
  ArrowRight, 
  Compass, 
  RefreshCw
} from 'lucide-react';

const QUICK_PROMPTS = [
  { label: 'Find cheaper hotels', prompt: 'Find cheaper hotels in our destination and show how much we can save.' },
  { label: 'Reduce trip budget', prompt: 'Reduce my trip budget by optimizing flight and accommodation selections.' },
  { label: 'Add adventure activities', prompt: 'Add exciting outdoor and adventure activities to my itinerary.' },
  { label: 'Regenerate Day 2 Route', prompt: 'Regenerate Day 2 itinerary to optimize travel times and avoid traffic.' },
  { label: 'Travel from Bangalore to Kerala for 4 days within ₹35,000', prompt: 'I want to travel from Bengaluru to Kerala for 4 days with family, budget ₹35,000.' }
];

export const AIAssistantDrawer: React.FC = () => {
  const { 
    aiDrawerOpen, 
    setAIDrawerOpen, 
    aiMessages, 
    sendAIMessage, 
    isAILoading, 
    setCurrentStep, 
    requirements, 
    budget 
  } = useTravel();

  const [inputVal, setInputVal] = useState('');

  if (!aiDrawerOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputVal.trim() || isAILoading) return;
    const msg = inputVal;
    setInputVal('');
    await sendAIMessage(msg);
  };

  const handleQuickPrompt = async (prompt: string) => {
    if (isAILoading) return;
    await sendAIMessage(prompt);
  };

  return (
    <div className="fixed inset-0 z-50 overflow-hidden">
      {/* Backdrop */}
      <div 
        className="absolute inset-0 bg-slate-900/60 backdrop-blur-sm transition-opacity" 
        onClick={() => setAIDrawerOpen(false)}
      />

      <div className="fixed inset-y-0 right-0 max-w-full flex pl-10">
        <div className="w-screen max-w-lg bg-white shadow-2xl flex flex-col border-l border-slate-200">
          
          {/* Header */}
          <div className="p-4 bg-gradient-to-r from-slate-900 to-indigo-950 text-white flex items-center justify-between border-b border-indigo-900/50">
            <div className="flex items-center space-x-3">
              <BrandLogo
                variant="icon"
                surface="dark"
                imgClassName="h-8 w-8 object-contain"
                containerClassName="p-1 rounded-xl shrink-0"
              />
              <div>
                <div className="flex items-center space-x-2">
                  <span className="font-heading font-bold text-base text-white">Pravasa AI Agent</span>
                  <span className="text-[10px] bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 px-2 py-0.5 rounded-full font-semibold">Autonomous Copilot</span>
                </div>
                <p className="text-[11px] text-slate-300">Context-Aware Travel Replanning & Dynamic Optimization</p>
              </div>
            </div>
            <button
              onClick={() => setAIDrawerOpen(false)}
              className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition"
            >
              <X className="h-5 w-5" />
            </button>
          </div>

          {/* Quick Context Bar */}
          <div className="bg-slate-100 px-4 py-2 border-b border-slate-200 flex items-center justify-between text-xs text-slate-600">
            <div className="flex items-center space-x-2">
              <Compass className="h-3.5 w-3.5 text-blue-600" />
              <span className="font-semibold text-slate-900">{requirements.destination}</span>
              <span className="text-slate-400">•</span>
              <span>{requirements.durationDays}D / {requirements.travellers.adults}A</span>
            </div>
            <div className="font-semibold text-slate-900">
              Budget: ₹{budget.totalEstimatedCost.toLocaleString('en-IN')}
            </div>
          </div>

          {/* Messages Flow */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {aiMessages.map(msg => (
              <div 
                key={msg.id} 
                className={`flex space-x-3 ${msg.sender === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                {msg.sender === 'assistant' && (
                  <div className="h-8 w-8 rounded-lg bg-white border border-slate-200 flex items-center justify-center p-1 shadow-xs flex-shrink-0">
                    <BrandLogo variant="icon" surface="light" imgClassName="h-6 w-6 object-contain" />
                  </div>
                )}
                
                <div className={`max-w-[85%] rounded-2xl p-3.5 text-xs shadow-sm ${
                  msg.sender === 'user' 
                    ? 'bg-blue-600 text-white rounded-br-none' 
                    : 'bg-slate-50 border border-slate-200 text-slate-800 rounded-bl-none'
                }`}>
                  <div className="whitespace-pre-line leading-relaxed">{msg.content}</div>
                  
                  {/* Action buttons inside response */}
                  {msg.suggestedActions && msg.suggestedActions.length > 0 && (
                    <div className="mt-3 pt-2.5 border-t border-slate-200/60 flex flex-wrap gap-1.5">
                      {msg.suggestedActions.map((act, i) => (
                        <button
                          key={i}
                          onClick={() => {
                            if (act.actionType === 'NAVIGATE' && act.payload) {
                              setCurrentStep(act.payload);
                              setAIDrawerOpen(false);
                            } else if (act.actionType === 'OPTIMIZE_BUDGET') {
                              handleQuickPrompt('Suggest cheaper hotels');
                            }
                          }}
                          className="px-2.5 py-1 rounded-md bg-white border border-blue-200 hover:border-blue-400 text-blue-700 font-semibold text-[11px] transition shadow-xs flex items-center space-x-1"
                        >
                          <span>{act.label}</span>
                          <ArrowRight className="h-3 w-3" />
                        </button>
                      ))}
                    </div>
                  )}

                  <div className={`text-[10px] mt-1.5 ${msg.sender === 'user' ? 'text-blue-200' : 'text-slate-400'} text-right`}>
                    {msg.timestamp}
                  </div>
                </div>

                {msg.sender === 'user' && (
                  <div className="h-8 w-8 rounded-lg bg-slate-800 text-white flex items-center justify-center flex-shrink-0">
                    <User className="h-4 w-4" />
                  </div>
                )}
              </div>
            ))}

            {isAILoading && (
              <div className="flex space-x-3 items-center text-xs text-slate-500 bg-slate-50 p-3 rounded-xl border border-slate-200 w-max">
                <RefreshCw className="h-4 w-4 text-blue-600 animate-spin" />
                <span>AI Virtual Agent is analyzing requirements and recalculating live travel options...</span>
              </div>
            )}
          </div>

          {/* Quick Contextual Prompts Chips */}
          <div className="px-4 py-2.5 bg-slate-50 border-t border-slate-200">
            <span className="text-[11px] font-bold text-slate-500 uppercase tracking-wider block mb-1.5">Quick Context Actions:</span>
            <div className="flex flex-wrap gap-1.5">
              {QUICK_PROMPTS.map((qp, idx) => (
                <button
                  key={idx}
                  onClick={() => handleQuickPrompt(qp.prompt)}
                  disabled={isAILoading}
                  className="px-2.5 py-1 rounded-lg bg-white border border-slate-200 hover:border-blue-400 hover:bg-blue-50/50 text-[11px] text-slate-700 font-medium transition active:scale-95 disabled:opacity-50"
                >
                  {qp.label}
                </button>
              ))}
            </div>
          </div>

          {/* Input Form */}
          <form onSubmit={handleSubmit} className="p-3 bg-white border-t border-slate-200 flex items-center space-x-2">
            <input
              type="text"
              value={inputVal}
              onChange={(e) => setInputVal(e.target.value)}
              placeholder="Ask anything (e.g. 'Find cheaper stay', 'Trip to Goa for ₹30k')..."
              className="flex-1 text-xs px-3.5 py-2.5 rounded-xl border border-slate-300 focus:outline-hidden focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-slate-50"
              disabled={isAILoading}
            />
            <button
              type="submit"
              disabled={!inputVal.trim() || isAILoading}
              className="p-2.5 rounded-xl bg-blue-600 hover:bg-blue-700 text-white font-semibold transition disabled:opacity-40 disabled:cursor-not-allowed"
            >
              <Send className="h-4 w-4" />
            </button>
          </form>

        </div>
      </div>
    </div>
  );
};

