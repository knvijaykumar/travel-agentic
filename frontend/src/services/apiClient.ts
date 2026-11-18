import { TripRequirements, FlightOption, HotelOption, ItineraryDay, BookingRecord, SavedTrip, Attraction, DataSource } from '../types/travel';
import { generateFlightsForRoute, getHotelsForDestination } from '../data/flightsAndHotels';
import { PAN_INDIA_DESTINATIONS, findDestinationByName } from '../data/panIndiaData';
import { generateSmartItinerary } from '../utils/itineraryEngine';

// Default backend API base URL pointing to FastAPI v1 routes
const RAW_ENV_URL = (import.meta.env.VITE_API_URL ?? '').trim();
const RAW_URL = (RAW_ENV_URL || 'http://localhost:8000').replace(/\/+$/, '');
export const API_BASE_URL = RAW_URL.endsWith('/api/v1')
  ? RAW_URL
  : RAW_URL.endsWith('/api')
    ? `${RAW_URL}/v1`
    : `${RAW_URL}/api/v1`;

const ROOT_BASE_URL = RAW_URL.replace(/\/api(\/v1)?$/, '');

export interface BackendStatus {
  isAvailable: boolean;
  message: string;
  version?: string;
  geminiReady?: boolean;
}

export interface ChatApiRequest {
  message: string;
  session_id?: string;
}

export interface ChatApiResponse {
  session_id: string;
  assistant_message: string;
  planning_status: 'ask_user' | 'ready_for_planning' | 'error' | string;
  missing_fields: string[];
  skipped_fields?: string[];
  extracted_details?: {
    destination?: string;
    origin?: string;
    start_date?: string;
    end_date?: string;
    duration_days?: number;
    budget?: number;
    adults?: number;
    children?: number;
    trip_type?: string;
    interests?: string[];
    [key: string]: any;
  };
}

export interface BackendPlace {
  place_id: string;
  name: string;
  category: string;
  latitude: float;
  longitude: float;
  address?: string;
  city?: string;
  country?: string;
  image_url?: string;
  image_attribution?: string;
  source_provider: string;
}

export interface BackendFlightSearchRequest {
  origin: string; // 3-letter IATA
  destination: string; // 3-letter IATA
  departure_date: string; // YYYY-MM-DD
  adults?: number;
  cabin_class?: string;
}

export interface BackendHotelSearchRequest {
  city_name?: string;
  country_code?: string;
  checkin: string; // YYYY-MM-DD
  checkout: string; // YYYY-MM-DD
  adults?: number;
  currency?: string;
  hotel_ids?: string[];
}

export interface HotelGuestHolder {
  first_name: string;
  last_name: string;
  email: string;
  phone?: string;
}

export interface HotelPrebookRequest {
  offer_id: string;
  use_payment_sdk?: boolean;
}

export interface HotelPrebookResponse {
  prebook_id: string;
  offer_id: string;
  price_amount: number;
  currency: string;
  cancellation_policy?: string;
  room_name?: string;
  is_sandbox: boolean;
  raw_data?: any;
}

export interface HotelBookingConfirmationRequest {
  prebook_id: string;
  holder: HotelGuestHolder;
  client_reference?: string;
  payment_method?: string;
}

export interface HotelBookingConfirmationResponse {
  booking_id: string;
  status: string;
  booking_reference: string;
  hotel_name: string;
  price_amount: number;
  currency: string;
  checkin_date: string;
  checkout_date: string;
  holder: HotelGuestHolder;
  is_sandbox: boolean;
  cancellation_policy?: string;
  confirmed_at: string;
}

export interface ItineraryGenerationRequest {
  destination: string;
  departure_city?: string;
  start_date: string;
  end_date: string;
  adults?: number;
  budget?: number;
  currency?: string;
  pace?: string;
  interests?: string[];
}

type float = number;

export class TravelApiService {
  private static instance: TravelApiService;
  private currentSessionId: string | null = null;

  public static getInstance(): TravelApiService {
    if (!TravelApiService.instance) {
      TravelApiService.instance = new TravelApiService();
    }
    return TravelApiService.instance;
  }

  // 1. Health check
  async checkBackendHealth(): Promise<BackendStatus> {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 3000);

    try {
      // Try /api/v1/health first, then /health only when server responded with non-200
      let res = await fetch(`${API_BASE_URL}/health`, { signal: controller.signal }).catch(() => null);
      if (res && !res.ok) {
        res = await fetch(`${ROOT_BASE_URL}/health`, { signal: controller.signal }).catch(() => null);
      }

      if (res && res.ok) {
        const data = await res.json();
        return {
          isAvailable: true,
          message: 'FastAPI Backend Online & Connected',
          version: data.version || 'v0.1.0',
          geminiReady: true
        };
      }
      return {
        isAvailable: false,
        message: 'Backend unavailable. Operating in High-Fidelity Client Engine Mode.'
      };
    } catch {
      return {
        isAvailable: false,
        message: 'FastAPI Backend Offline. Running on Embedded Pan-India Client Intelligence Engine.'
      };
    } finally {
      clearTimeout(timeoutId);
    }
  }

  // 2. Chat & NLP Intent (POST /api/v1/chat)
  async sendChatMessage(message: string, sessionId?: string): Promise<ChatApiResponse> {
    const sid = sessionId || this.currentSessionId || undefined;
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 10000);

    try {
      const res = await fetch(`${API_BASE_URL}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message, session_id: sid }),
        signal: controller.signal
      });
      clearTimeout(timeoutId);

      if (!res.ok) {
        throw new Error(`Chat API responded with status ${res.status}`);
      }

      const data: ChatApiResponse = await res.json();
      if (data.session_id) {
        this.currentSessionId = data.session_id;
      }
      return data;
    } catch (err) {
      clearTimeout(timeoutId);
      throw err;
    }
  }

  // Parse natural language requirements (with fallback to regex parser)
  async parseNaturalLanguageIntent(text: string): Promise<Partial<TripRequirements>> {
    try {
      const chatRes = await this.sendChatMessage(text);
      if (chatRes && chatRes.extracted_details) {
        const d = chatRes.extracted_details;
        const mapped: Partial<TripRequirements> = {
          rawPrompt: text
        };

        if (d.destination) {
          mapped.destination = d.destination;
          const destLower = d.destination.toLowerCase();
          // deduce state
          for (const s of PAN_INDIA_DESTINATIONS) {
            if (s.name.toLowerCase().includes(destLower) || 
                destLower.includes(s.name.toLowerCase()) ||
                s.capital.toLowerCase().includes(destLower) ||
                s.attractions.some(a => a.name.toLowerCase().includes(destLower) || a.city.toLowerCase().includes(destLower))) {
              mapped.destinationState = s.name;
              break;
            }
          }
        }

        if (d.origin) mapped.origin = d.origin;
        if (d.start_date) mapped.startDate = d.start_date;
        if (d.end_date) mapped.endDate = d.end_date;
        if (d.duration_days) mapped.durationDays = d.duration_days;
        if (d.budget) mapped.totalBudget = d.budget;
        if (d.adults) {
          mapped.travellers = {
            adults: d.adults,
            children: d.children || 0,
            infants: 0
          };
        }
        return mapped;
      }
    } catch {
      // Graceful fallback to client-side rule & regex parsing
    }

    return this.clientSideParseIntent(text);
  }

  // 3. Tourist places discovery (GET /api/v1/places/search)
  async searchPlaces(destination: string, categories?: string, limit = 8): Promise<BackendPlace[]> {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 8000);

    try {
      const params = new URLSearchParams({
        destination,
        limit: limit.toString()
      });
      if (categories) params.append('categories', categories);

      const res = await fetch(`${API_BASE_URL}/places/search?${params.toString()}`, {
        method: 'GET',
        headers: { 'Accept': 'application/json' },
        signal: controller.signal
      });
      clearTimeout(timeoutId);

      if (!res.ok) {
        throw new Error(`Places search responded with status ${res.status}`);
      }

      return await res.json();
    } catch (err) {
      clearTimeout(timeoutId);
      throw err;
    }
  }

  // 4. Flight search (POST /api/v1/flights/search)
  async searchFlights(request: BackendFlightSearchRequest): Promise<any> {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 12000);

    try {
      const res = await fetch(`${API_BASE_URL}/flights/search`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(request),
        signal: controller.signal
      });
      clearTimeout(timeoutId);

      if (!res.ok) {
        const errorText = await res.text().catch(() => '');
        throw new Error(`Flight search failed (${res.status}): ${errorText}`);
      }

      return await res.json();
    } catch (err) {
      clearTimeout(timeoutId);
      throw err;
    }
  }

  // 5. Hotel search (POST /api/v1/hotels/search)
  async searchHotels(request: BackendHotelSearchRequest): Promise<any> {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 15000);

    try {
      const res = await fetch(`${API_BASE_URL}/hotels/search`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(request),
        signal: controller.signal
      });
      clearTimeout(timeoutId);

      if (!res.ok) {
        const errorText = await res.text().catch(() => '');
        throw new Error(`Hotel search failed (${res.status}): ${errorText}`);
      }

      return await res.json();
    } catch (err) {
      clearTimeout(timeoutId);
      throw err;
    }
  }

  // 6. Hotel Pre-book (POST /api/v1/bookings/hotels/prebook)
  async prebookHotel(offerId: string, usePaymentSdk = false): Promise<HotelPrebookResponse> {
    const res = await fetch(`${API_BASE_URL}/bookings/hotels/prebook`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ offer_id: offerId, use_payment_sdk: usePaymentSdk })
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Failed to prebook rate' }));
      throw new Error(err.detail || 'Hotel prebook failed');
    }

    return await res.json();
  }

  // 7. Hotel Confirm Booking (POST /api/v1/bookings/hotels/book)
  async confirmHotelBooking(payload: HotelBookingConfirmationRequest): Promise<HotelBookingConfirmationResponse> {
    const res = await fetch(`${API_BASE_URL}/bookings/hotels/book`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Failed to confirm booking' }));
      throw new Error(err.detail || 'Hotel confirmation failed');
    }

    return await res.json();
  }

  // 8. Hotel Booking Details (GET /api/v1/bookings/hotels/{booking_id})
  async getHotelBooking(bookingId: string): Promise<any> {
    const res = await fetch(`${API_BASE_URL}/bookings/hotels/${encodeURIComponent(bookingId)}`);
    if (!res.ok) {
      throw new Error(`Failed to retrieve booking ${bookingId}`);
    }
    return await res.json();
  }

  // 9. Hotel Cancel Booking (POST /api/v1/bookings/hotels/{booking_id}/cancel)
  async cancelHotelBooking(bookingId: string): Promise<any> {
    const res = await fetch(`${API_BASE_URL}/bookings/hotels/${encodeURIComponent(bookingId)}/cancel`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' }
    });
    if (!res.ok) {
      throw new Error(`Failed to cancel booking ${bookingId}`);
    }
    return await res.json();
  }

  // 10. AI Itinerary Generation (POST /api/v1/itinerary/generate)
  async generateItinerary(request: ItineraryGenerationRequest): Promise<any> {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 20000);

    try {
      const res = await fetch(`${API_BASE_URL}/itinerary/generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(request),
        signal: controller.signal
      });
      clearTimeout(timeoutId);

      if (!res.ok) {
        throw new Error(`Itinerary generation failed with status ${res.status}`);
      }

      return await res.json();
    } catch (err) {
      clearTimeout(timeoutId);
      throw err;
    }
  }

  // 11. AI Itinerary Replanning (POST /api/v1/itinerary/replan)
  async replanItinerary(payload: any): Promise<any> {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 20000);

    try {
      const res = await fetch(`${API_BASE_URL}/itinerary/replan`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
        signal: controller.signal
      });
      clearTimeout(timeoutId);

      if (!res.ok) {
        throw new Error(`Itinerary replan failed with status ${res.status}`);
      }

      return await res.json();
    } catch (err) {
      clearTimeout(timeoutId);
      throw err;
    }
  }

  // Embedded Client Fallback Intent Parser
  private clientSideParseIntent(text: string): Partial<TripRequirements> {
    const lower = text.toLowerCase();
    const result: Partial<TripRequirements> = {
      rawPrompt: text
    };

    // Extract Origin
    const originMatch = lower.match(/(?:from|departing from|leaving)\s+([a-zA-Z\s]+?)(?=\s+(?:to|for|with|in|within|on|around)|\s*$)/);
    if (originMatch && originMatch[1]) {
      result.origin = capitalizeWords(originMatch[1].trim());
    } else if (lower.includes('bengaluru') || lower.includes('bangalore')) {
      result.origin = 'Bengaluru';
    } else if (lower.includes('delhi')) {
      result.origin = 'New Delhi';
    } else if (lower.includes('mumbai')) {
      result.origin = 'Mumbai';
    }

    // Extract Destination from PAN-INDIA list
    for (const state of PAN_INDIA_DESTINATIONS) {
      if (lower.includes(state.name.toLowerCase()) || lower.includes(state.capital.toLowerCase())) {
        result.destination = state.capital + ', ' + state.name;
        result.destinationState = state.name;
        break;
      }
      const matchedAttr = state.attractions.find(a => lower.includes(a.name.toLowerCase()) || lower.includes(a.city.toLowerCase()));
      if (matchedAttr) {
        result.destination = matchedAttr.city + ', ' + state.name;
        result.destinationState = state.name;
        break;
      }
    }

    if (!result.destination) {
      if (lower.includes('rajasthan')) {
        result.destination = 'Jaipur, Rajasthan';
        result.destinationState = 'Rajasthan';
      } else if (lower.includes('goa')) {
        result.destination = 'Panaji, Goa';
        result.destinationState = 'Goa';
      } else if (lower.includes('kerala')) {
        result.destination = 'Kochi, Kerala';
        result.destinationState = 'Kerala';
      } else if (lower.includes('kashmir') || lower.includes('srinagar')) {
        result.destination = 'Srinagar, Jammu & Kashmir';
        result.destinationState = 'Jammu and Kashmir';
      } else if (lower.includes('ladakh') || lower.includes('leh')) {
        result.destination = 'Leh, Ladakh';
        result.destinationState = 'Ladakh';
      }
    }

    // Extract Duration in days
    const daysMatch = lower.match(/(\d+)\s*(?:days|day|d)/);
    if (daysMatch) {
      result.durationDays = parseInt(daysMatch[1], 10);
    } else {
      result.durationDays = 5;
    }

    // Extract Budget
    const rawNumberMatch = lower.match(/(?:budget|within|under|around|approx)\s*(?:of)?\s*(?:₹|rs\.?|inr)?\s*(\d+)(?:k)?/i);
    if (lower.includes('40,000') || lower.includes('40000') || lower.includes('40k')) {
      result.totalBudget = 40000;
    } else if (lower.includes('50,000') || lower.includes('50000') || lower.includes('50k')) {
      result.totalBudget = 50000;
    } else if (lower.includes('30,000') || lower.includes('30000') || lower.includes('30k')) {
      result.totalBudget = 30000;
    } else if (rawNumberMatch && rawNumberMatch[1]) {
      let val = parseInt(rawNumberMatch[1], 10);
      if (rawNumberMatch[0].toLowerCase().includes('k')) val *= 1000;
      if (val < 1000) val *= 1000;
      result.totalBudget = val;
    }

    // Extract Travellers
    if (lower.includes('family')) {
      result.tripType = 'Family';
      result.travellers = { adults: 2, children: 1, infants: 0 };
    } else if (lower.includes('couple') || lower.includes('honeymoon') || lower.includes('romantic')) {
      result.tripType = 'Romantic';
      result.travellers = { adults: 2, children: 0, infants: 0 };
    } else if (lower.includes('solo')) {
      result.tripType = 'Adventure';
      result.travellers = { adults: 1, children: 0, infants: 0 };
    } else if (lower.includes('friends') || lower.includes('group')) {
      result.tripType = 'Adventure';
      result.travellers = { adults: 4, children: 0, infants: 0 };
    } else {
      result.travellers = { adults: 2, children: 0, infants: 0 };
    }

    // Dates default
    const today = new Date();
    const start = new Date(today.getTime() + 14 * 24 * 60 * 60 * 1000);
    const end = new Date(start.getTime() + (result.durationDays || 5) * 24 * 60 * 60 * 1000);

    result.startDate = start.toISOString().split('T')[0];
    result.endDate = end.toISOString().split('T')[0];

    return result;
  }
}

function capitalizeWords(str: string): string {
  return str.replace(/\b\w/g, l => l.toUpperCase());
}

export const travelApi = TravelApiService.getInstance();
