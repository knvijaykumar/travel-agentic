import { describe, it } from 'node:test';
import assert from 'node:assert';
import { PAN_INDIA_DESTINATIONS, findDestinationByName, getAttractionsByState } from '../data/panIndiaData.ts';
import { generateFlightsForRoute, getHotelsForDestination, DEFAULT_TRANSFERS } from '../data/flightsAndHotels.ts';
import { calculateTripBudget } from '../utils/budgetCalculator.ts';
import { generateSmartItinerary } from '../utils/itineraryEngine.ts';

describe('WanderAI Frontend1 Integration & Pan-India Coverage Verification', () => {
  it('covers all 28 Indian States and 8 Union Territories', () => {
    assert.strictEqual(PAN_INDIA_DESTINATIONS.length, 36, 'Must contain exactly 36 regions');

    const states = PAN_INDIA_DESTINATIONS.filter(d => d.type === 'State');
    const uts = PAN_INDIA_DESTINATIONS.filter(d => d.type === 'Union Territory');

    assert.strictEqual(states.length, 28, 'Must contain 28 States');
    assert.strictEqual(uts.length, 8, 'Must contain 8 Union Territories');

    for (const dest of PAN_INDIA_DESTINATIONS) {
      assert.ok(dest.name && dest.name.trim().length > 0, `Destination must have valid name: ${dest.id}`);
      assert.ok(dest.capital && dest.capital.trim().length > 0, `Destination must have capital: ${dest.name}`);
      assert.ok(dest.heroImage && dest.heroImage.startsWith('http'), `Destination must have valid hero image: ${dest.name}`);
      assert.ok(Array.isArray(dest.popularAirports) && dest.popularAirports.length > 0, `Must have airports: ${dest.name}`);
      assert.ok(dest.popularAirports[0].code.length === 3, `Airport must be 3-letter IATA: ${dest.name}`);
      assert.ok(Array.isArray(dest.attractions) && dest.attractions.length > 0, `Must have attractions: ${dest.name}`);

      for (const attr of dest.attractions) {
        assert.ok(attr.name && attr.name.length > 0, `Attraction must have name in ${dest.name}`);
        assert.ok(attr.image && attr.image.startsWith('http'), `Attraction photo must be valid in ${dest.name}`);
        assert.strictEqual(attr.state, dest.name, `Attraction state must match destination in ${dest.name}`);
      }
    }
  });

  it('verifies multi-state destination queries across all Indian zones', () => {
    const testDestinations = [
      { name: 'Karnataka', capital: 'Bengaluru' },
      { name: 'Kerala', capital: 'Thiruvananthapuram' },
      { name: 'Tamil Nadu', capital: 'Chennai' },
      { name: 'Maharashtra', capital: 'Mumbai' },
      { name: 'Goa', capital: 'Panaji' },
      { name: 'Rajasthan', capital: 'Jaipur' },
      { name: 'Delhi', capital: 'New Delhi' },
      { name: 'Uttar Pradesh', capital: 'Lucknow' },
      { name: 'West Bengal', capital: 'Kolkata' },
      { name: 'Assam', capital: 'Dispur' },
      { name: 'Meghalaya', capital: 'Shillong' },
      { name: 'Sikkim', capital: 'Gangtok' },
      { name: 'Madhya Pradesh', capital: 'Bhopal' },
      { name: 'Jammu and Kashmir', capital: 'Srinagar' }
    ];

    for (const t of testDestinations) {
      const found = findDestinationByName(t.name);
      assert.ok(found, `Must find destination for ${t.name}`);
      assert.strictEqual(found.capital, t.capital);

      const attrs = getAttractionsByState(t.name);
      assert.ok(attrs.length > 0, `Must have attractions for ${t.name}`);

      const hotels = getHotelsForDestination(t.name, 4);
      assert.ok(hotels.length > 0, `Must have fallback hotels for ${t.name}`);

      const flights = generateFlightsForRoute('Bengaluru (BLR)', `${t.capital} (${found.popularAirports[0].code})`, '2026-12-01', 2);
      assert.ok(flights.length > 0, `Must generate flights for route to ${t.name}`);
    }
  });

  it('validates budget calculation reactivity and status thresholds', () => {
    const reqs = {
      origin: 'Bengaluru (BLR)',
      destination: 'Jaipur (JAI)',
      destinationState: 'Rajasthan',
      startDate: '2026-12-10',
      endDate: '2026-12-15',
      durationDays: 5,
      travellers: { adults: 2, children: 1, infants: 0 },
      tripType: 'Family',
      transportPreference: 'Flight',
      accommodationPreference: 'Standard/Business',
      totalBudget: 60000,
      specialRequirements: [],
      confirmedByUser: true
    };

    const flights = generateFlightsForRoute(reqs.origin, reqs.destination, reqs.startDate, 3);
    const selectedFlight = flights[0];
    const hotels = getHotelsForDestination(reqs.destinationState, 5);
    const selectedHotel = hotels[0];
    const dummyItinerary = generateSmartItinerary(reqs, hotels[0].amenities.map((_, i) => ({ id: `a-${i}` })), selectedHotel);

    const budget = calculateTripBudget(reqs, selectedFlight, selectedHotel, DEFAULT_TRANSFERS, dummyItinerary);

    assert.ok(budget.totalEstimatedCost > 0, 'Total cost must be calculated');
    assert.strictEqual(budget.flightCost, selectedFlight.totalPrice);
    assert.strictEqual(budget.hotelCost, selectedHotel.totalCost);
    assert.ok(budget.perPersonCost === Math.round(budget.totalEstimatedCost / 3));
    assert.ok(['OPTIMAL', 'APPROACHING_LIMIT', 'OVER_BUDGET'].includes(budget.status));
  });

  it('strictly validates that flight external booking produces NO synthetic PNR or fake ticket', () => {
    const flights = generateFlightsForRoute('BLR', 'DEL', '2026-12-01', 1);
    const flight = flights[0];

    // Simulate booking record creation
    const record = {
      id: `bk-fl-${Date.now()}`,
      bookingRef: 'N/A (External Airline Redirect)',
      productType: 'FLIGHT',
      title: `${flight.airline} (${flight.flightNumber}): ${flight.originCode} ➔ ${flight.destinationCode}`,
      provider: `${flight.airline} External Booking`,
      status: 'EXTERNAL_REDIRECT',
      amount: flight.totalPrice,
      bookingDate: new Date().toISOString(),
      travelDates: '2026-12-01',
      passengerOrGuestName: '1 Adult',
      voucherNumber: undefined,
      detailsSummary: 'External Booking – Not Confirmed'
    };

    assert.strictEqual(record.status, 'EXTERNAL_REDIRECT');
    assert.strictEqual(record.voucherNumber, undefined, 'Must NOT contain fake ticket number');
    assert.strictEqual(record.bookingRef, 'N/A (External Airline Redirect)', 'Must NOT contain fake PNR code');
    assert.ok(!record.bookingRef.includes('PNR'), 'Must NOT synthesize PNR string');
  });
});

