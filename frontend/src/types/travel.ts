export type WorkflowStep = 
  | 'requirements'
  | 'flights'
  | 'hotels'
  | 'sightseeing'
  | 'itinerary'
  | 'budget'
  | 'review'
  | 'my-trips';

export type TripType = 
  | 'Adventure' 
  | 'Relaxation' 
  | 'Family' 
  | 'Business' 
  | 'Romantic' 
  | 'Cultural' 
  | 'Wildlife' 
  | 'Spiritual';

export type TransportPreference = 'Flight' | 'Train' | 'Cab/Road' | 'Any';

export type AccommodationTier = 'Budget' | 'Standard' | 'Premium' | 'Luxury';

export type AccommodationPreference = 'Luxury 5-Star' | 'Boutique/Resort' | 'Standard/Business' | 'Budget/Homestay';

export type DataSource = 
  | 'Live Provider Data' 
  | 'Sandbox Data' 
  | 'Frontend Reference Data' 
  | 'AI Generated Information' 
  | 'AI Generated Information (Client Engine)' 
  | 'Temporarily Unavailable';

export interface TripRequirements {
  origin: string;
  destination: string;
  destinationState: string;
  originCity?: string;
  destinationCity?: string;
  startDate: string;
  endDate: string;
  durationDays: number;
  travellers: {
    adults: number;
    children: number;
    infants: number;
  };
  tripType: TripType;
  transportPreference: TransportPreference;
  transportMode?: 'FLIGHT' | 'TRAIN';
  accommodationPreference: AccommodationPreference;
  accommodationTier?: AccommodationTier;
  totalBudget: number; // Combined hard maximum budget for ALL travellers
  specialRequirements: string[];
  rawPrompt?: string;
  confirmedByUser: boolean;
  guideMeEnabled?: boolean;
}

export interface TrainClassInfo {
  code: string;
  name: string;
  farePerPerson: number;
  availability: string;
}

export interface TrainOption {
  id: string;
  trainName: string;
  trainNumber: string;
  originStation: string;
  originStationCode: string;
  destinationStation: string;
  destinationStationCode: string;
  departureTime: string;
  arrivalTime: string;
  duration: string;
  classes: TrainClassInfo[];
  selectedClass: string;
  pricePerPerson: number;
  totalPrice: number;
  status: 'AVAILABLE' | 'SELECTED' | 'CONFIRMED';
  irctcNotice: string;
  bookingUrl?: string;
  dataSource?: DataSource;
  recommended?: boolean;
  cheapest?: boolean;
}

export interface FlightOption {
  id: string;
  airline: string;
  airlineCode: string;
  flightNumber: string;
  origin: string;
  originCode: string;
  destination: string;
  destinationCode: string;
  departureTime: string;
  arrivalTime: string;
  duration: string;
  stops: number;
  stopDetails?: string;
  pricePerPerson: number;
  totalPrice: number;
  cabinClass: 'Economy' | 'Premium Economy' | 'Business';
  baggage: {
    cabin: string;
    checkIn: string;
  };
  recommended?: boolean;
  cheapest?: boolean;
  refundable: boolean;
  status: 'AVAILABLE' | 'SELECTED' | 'REDIRECT_PENDING' | 'CONFIRMED';
  providerNotice: string;
  bookingUrl?: string;
  dataSource?: DataSource;
}

export interface HotelOption {
  id: string;
  name: string;
  state: string;
  city: string;
  rating: number;
  reviewCount: number;
  stars: number;
  image: string;
  additionalImages: string[];
  pricePerNight: number;
  totalCost: number;
  roomType: string;
  availableRoomTypes?: { name: string; pricePerNight: number; perks: string }[];
  amenities: string[];
  location: string;
  distanceFromCenter: string;
  status: 'AVAILABLE' | 'SELECTED' | 'CONFIRMED';
  cancellationPolicy: string;
  badge?: 'Best Value' | 'Top Rated' | 'Luxury Pick' | 'Eco Friendly';
  offerId?: string;
  isSandbox?: boolean;
  dataSource?: DataSource;
}

export interface Attraction {
  id: string;
  name: string;
  state: string;
  city: string;
  category: 'Historical' | 'Natural' | 'Religious' | 'Cultural' | 'Adventure' | 'Wildlife' | 'Architectural';
  image: string;
  description: string;
  location: string;
  openingHours: string;
  entryFee: number;
  estimatedDuration: string;
  rating: number;
  isSelected?: boolean;
  highlights: string[];
  dataSource?: DataSource;
}

export interface ItineraryActivity {
  id: string;
  timeSlot: 'Morning' | 'Afternoon' | 'Evening' | 'Night';
  time: string;
  title: string;
  description: string;
  attractionId?: string;
  image?: string;
  location: string;
  transportMode: 'Walking' | 'Cab' | 'Metro/Auto' | 'Private Transfer' | 'Flight';
  travelDurationFromPrevious: string;
  costEstimate: number;
  tips: string;
}

export interface ItineraryDay {
  dayNumber: number;
  date: string;
  theme: string;
  summary: string;
  activities: ItineraryActivity[];
  totalDayExpense: number;
  dataSource?: DataSource;
}

export interface TransferOption {
  id: string;
  title: string;
  vehicle: string;
  capacity: string;
  type: 'Airport Transfer' | 'Full Day Private Cab' | 'Self Drive Car' | 'Intercity Express';
  price: number;
  features: string[];
  selected: boolean;
}

export interface TripBudgetBreakdown {
  totalBudget: number;
  flightCost: number;
  trainCost?: number;
  hotelCost: number;
  transportCost: number;
  sightseeingCost: number;
  foodEstimate: number;
  activitiesCost: number;
  miscCost: number;
  totalEstimatedCost: number;
  perPersonCost: number;
  remainingBudget: number;
  budgetUtilizationPct: number;
  status: 'OPTIMAL' | 'APPROACHING_LIMIT' | 'OVER_BUDGET';
}

export interface BookingRecord {
  id: string;
  bookingRef: string;
  productType: 'FLIGHT' | 'HOTEL' | 'TRANSFER' | 'ACTIVITIES_PASS';
  title: string;
  provider: string;
  status: 'CONFIRMED' | 'INTEGRATION_PENDING' | 'EXTERNAL_REDIRECT' | 'CANCELLED';
  amount: number;
  bookingDate: string;
  travelDates: string;
  passengerOrGuestName: string;
  voucherNumber?: string;
  detailsSummary: string;
}

export interface SavedTrip {
  id: string;
  tripTitle: string;
  destination: string;
  state: string;
  startDate: string;
  endDate: string;
  status: 'UPCOMING' | 'ONGOING' | 'COMPLETED';
  requirements: TripRequirements;
  flight?: FlightOption;
  train?: TrainOption;
  hotel?: HotelOption;
  attractions: Attraction[];
  itinerary: ItineraryDay[];
  transfers: TransferOption[];
  budget: TripBudgetBreakdown;
  bookings: BookingRecord[];
  disruptionAlerts?: {
    type: 'WEATHER' | 'FLIGHT_DELAY' | 'SCHEDULE_CHANGE';
    title: string;
    description: string;
    severity: 'LOW' | 'MEDIUM' | 'HIGH';
  }[];
}

export interface AIMessage {
  id: string;
  sender: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: string;
  suggestedActions?: {
    label: string;
    actionType: 'APPLY_FILTER' | 'SELECT_FLIGHT' | 'SELECT_HOTEL' | 'REGENERATE_DAY' | 'OPTIMIZE_BUDGET' | 'NAVIGATE';
    payload?: any;
  }[];
  extractedRequirements?: Partial<TripRequirements>;
}

