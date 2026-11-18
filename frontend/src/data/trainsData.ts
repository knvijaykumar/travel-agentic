import { TrainOption, TrainClassInfo, DataSource } from '../types/travel';
import { ALL_INDIAN_CITIES } from './citiesData';

export function generateTrainsForRoute(
  origin: string,
  destination: string,
  travelDate: string,
  totalPax: number = 1
): TrainOption[] {
  const origClean = (origin || 'Bengaluru').replace(/\([A-Z]{3}\)/g, '').trim();
  const destClean = (destination || 'Goa').replace(/\([A-Z]{3}\)/g, '').trim();

  // Find railway station codes
  const origCity = ALL_INDIAN_CITIES.find(c => origClean.toLowerCase().includes(c.city.toLowerCase()) || origClean.toLowerCase().includes(c.state.toLowerCase()));
  const destCity = ALL_INDIAN_CITIES.find(c => destClean.toLowerCase().includes(c.city.toLowerCase()) || destClean.toLowerCase().includes(c.state.toLowerCase()));

  const origStation = origCity ? `${origCity.city} Junction (${origCity.railwayCode})` : `${origClean} Station`;
  const origCode = origCity?.railwayCode || 'NDLS';
  const destStation = destCity ? `${destCity.city} Junction (${destCity.railwayCode})` : `${destClean} Station`;
  const destCode = destCity?.railwayCode || 'JP';

  // Base fare per passenger based on route distance
  const baseSleeperFare = 480;
  const base3AFare = 1250;
  const base2AFare = 1850;
  const base1AFare = 3100;
  const baseCCFare = 950;

  return [
    {
      id: `tr-vb-${Date.now()}-1`,
      trainName: 'Vande Bharat Express',
      trainNumber: '20641',
      originStation: origStation,
      originStationCode: origCode,
      destinationStation: destStation,
      destinationStationCode: destCode,
      departureTime: '06:00 AM',
      arrivalTime: '01:45 PM',
      duration: '7h 45m',
      classes: [
        { code: 'CC', name: 'AC Chair Car', farePerPerson: baseCCFare, availability: 'AVAILABLE-64' },
        { code: 'EC', name: 'Executive Chair Car', farePerPerson: baseCCFare * 1.8, availability: 'AVAILABLE-18' }
      ],
      selectedClass: 'CC',
      pricePerPerson: baseCCFare,
      totalPrice: baseCCFare * totalPax,
      status: 'AVAILABLE',
      irctcNotice: 'High-speed modern train with catering included',
      bookingUrl: 'https://www.irctc.co.in/nget/train-search',
      dataSource: 'Frontend Reference Data' as DataSource,
      recommended: true,
      cheapest: false
    },
    {
      id: `tr-raj-${Date.now()}-2`,
      trainName: 'Superfast Rajdhani Express',
      trainNumber: '12431',
      originStation: origStation,
      originStationCode: origCode,
      destinationStation: destStation,
      destinationStationCode: destCode,
      departureTime: '07:15 PM',
      arrivalTime: '07:30 AM',
      duration: '12h 15m',
      classes: [
        { code: '3A', name: 'AC 3 Tier', farePerPerson: base3AFare, availability: 'AVAILABLE-32' },
        { code: '2A', name: 'AC 2 Tier', farePerPerson: base2AFare, availability: 'AVAILABLE-12' },
        { code: '1A', name: 'AC 1st Class', farePerPerson: base1AFare, availability: 'AVAILABLE-4' }
      ],
      selectedClass: '3A',
      pricePerPerson: base3AFare,
      totalPrice: base3AFare * totalPax,
      status: 'AVAILABLE',
      irctcNotice: 'Overnight premium express with full berths & complimentary dinner',
      bookingUrl: 'https://www.irctc.co.in/nget/train-search',
      dataSource: 'Frontend Reference Data' as DataSource,
      recommended: false,
      cheapest: false
    },
    {
      id: `tr-exp-${Date.now()}-3`,
      trainName: 'Indian Railways Express Mail',
      trainNumber: '12625',
      originStation: origStation,
      originStationCode: origCode,
      destinationStation: destStation,
      destinationStationCode: destCode,
      departureTime: '10:30 AM',
      arrivalTime: '11:45 PM',
      duration: '13h 15m',
      classes: [
        { code: 'SL', name: 'Sleeper Class', farePerPerson: baseSleeperFare, availability: 'AVAILABLE-110' },
        { code: '3A', name: 'AC 3 Tier', farePerPerson: base3AFare - 150, availability: 'AVAILABLE-45' },
        { code: '2A', name: 'AC 2 Tier', farePerPerson: base2AFare - 200, availability: 'AVAILABLE-14' }
      ],
      selectedClass: 'SL',
      pricePerPerson: baseSleeperFare,
      totalPrice: baseSleeperFare * totalPax,
      status: 'AVAILABLE',
      irctcNotice: 'Daily scheduled superfast express – most affordable route option',
      bookingUrl: 'https://www.irctc.co.in/nget/train-search',
      dataSource: 'Frontend Reference Data' as DataSource,
      recommended: false,
      cheapest: true
    },
    {
      id: `tr-dur-${Date.now()}-4`,
      trainName: 'AC Duronto Non-Stop Express',
      trainNumber: '12213',
      originStation: origStation,
      originStationCode: origCode,
      destinationStation: destStation,
      destinationStationCode: destCode,
      departureTime: '11:40 PM',
      arrivalTime: '10:15 AM',
      duration: '10h 35m',
      classes: [
        { code: '3A', name: 'AC 3 Tier', farePerPerson: base3AFare + 100, availability: 'AVAILABLE-28' },
        { code: '2A', name: 'AC 2 Tier', farePerPerson: base2AFare + 150, availability: 'AVAILABLE-10' }
      ],
      selectedClass: '3A',
      pricePerPerson: base3AFare + 100,
      totalPrice: (base3AFare + 100) * totalPax,
      status: 'AVAILABLE',
      irctcNotice: 'Point-to-point point non-stop transit with minimal technical halts',
      bookingUrl: 'https://www.irctc.co.in/nget/train-search',
      dataSource: 'Frontend Reference Data' as DataSource,
      recommended: false,
      cheapest: false
    }
  ];
}
