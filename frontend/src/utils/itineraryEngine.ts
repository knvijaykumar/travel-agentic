import { Attraction, HotelOption, ItineraryDay, ItineraryActivity, TripRequirements } from '../types/travel';

export function generateSmartItinerary(
  requirements: TripRequirements,
  selectedAttractions: Attraction[],
  hotel?: HotelOption
): ItineraryDay[] {
  const daysCount = Math.max(1, Math.min(requirements.durationDays || 4, 10));
  const hotelName = hotel?.name || 'Selected City Hotel';
  const hotelLocation = hotel?.location || requirements.destination;

  // Clone attractions to distribute
  const attractionsPool = [...selectedAttractions];
  
  const itinerary: ItineraryDay[] = [];
  const startD = new Date(requirements.startDate || Date.now());

  for (let i = 1; i <= daysCount; i++) {
    const curDate = new Date(startD);
    curDate.setDate(startD.getDate() + (i - 1));
    const dateStr = curDate.toLocaleDateString('en-IN', { weekday: 'short', month: 'short', day: 'numeric', year: 'numeric' });

    let theme = '';
    let summary = '';
    const activities: ItineraryActivity[] = [];

    if (i === 1) {
      theme = 'Arrival, Check-in & Cultural Immersion';
      summary = `Touch down at ${requirements.destination}, check in at ${hotelName}, relax and begin with local sunset sights.`;

      activities.push({
        id: `act-${i}-1`,
        timeSlot: 'Morning',
        time: '09:30 AM',
        title: `Arrival at ${requirements.destination} Airport / Station`,
        description: `Baggage collection, greeting by dedicated private transfer driver, and scenic transit through city outskirts.`,
        location: `${requirements.destination} Terminal`,
        transportMode: 'Private Transfer',
        travelDurationFromPrevious: '35 mins from arrival lounge',
        costEstimate: 450,
        tips: 'Keep digital booking IDs and ID proofs ready for verification.'
      });

      activities.push({
        id: `act-${i}-2`,
        timeSlot: 'Morning',
        time: '11:45 AM',
        title: `Hotel Check-in & Freshen Up at ${hotelName}`,
        description: `Welcome drink reception, briefing with local concierge, settling into rooms, and short rest.`,
        location: hotelLocation,
        transportMode: 'Walking',
        travelDurationFromPrevious: 'At property',
        costEstimate: 0,
        tips: 'Inquire with reception about local walking maps and authentic lunch spots.'
      });

      const day1Attraction = attractionsPool.shift();
      if (day1Attraction) {
        activities.push({
          id: `act-${i}-3`,
          timeSlot: 'Afternoon',
          time: '03:15 PM',
          title: `Discover ${day1Attraction.name}`,
          description: day1Attraction.description,
          attractionId: day1Attraction.id,
          image: day1Attraction.image,
          location: day1Attraction.location,
          transportMode: 'Cab',
          travelDurationFromPrevious: '20 mins drive from hotel',
          costEstimate: day1Attraction.entryFee * (requirements.travellers.adults || 1),
          tips: `Optimal lighting for photography. Operating hours: ${day1Attraction.openingHours}`
        });
      }

      activities.push({
        id: `act-${i}-4`,
        timeSlot: 'Evening',
        time: '07:00 PM',
        title: `Local Heritage Promenade & Authentic Dining`,
        description: `Stroll through the old bazaar, discover local handicraft emporiums, and enjoy a traditional regional feast.`,
        location: `${requirements.destination} Old Market`,
        transportMode: 'Walking',
        travelDurationFromPrevious: '15 mins leisurely stroll',
        costEstimate: 850 * (requirements.travellers.adults || 1),
        tips: 'Bargaining is customary at roadside bazaars. Try the signature regional dessert!'
      });
    } else if (i === daysCount) {
      theme = 'Souvenir Shopping & Farewell Departure';
      summary = `Final moments enjoying local delicacies, packing treasures, hotel check-out, and transfer to airport.`;

      const lastAttraction = attractionsPool.shift();
      if (lastAttraction) {
        activities.push({
          id: `act-${i}-1`,
          timeSlot: 'Morning',
          time: '09:00 AM',
          title: `Morning Exploration: ${lastAttraction.name}`,
          description: lastAttraction.description,
          attractionId: lastAttraction.id,
          image: lastAttraction.image,
          location: lastAttraction.location,
          transportMode: 'Cab',
          travelDurationFromPrevious: '18 mins drive',
          costEstimate: lastAttraction.entryFee * (requirements.travellers.adults || 1),
          tips: 'Arrive early before peak midday crowds gather.'
        });
      }

      activities.push({
        id: `act-${i}-2`,
        timeSlot: 'Afternoon',
        time: '12:00 PM',
        title: `Hotel Check-out & Traditional Farewell Lunch`,
        description: `Complete luggage handover, express check-out, and enjoy a relaxed lunch savoring signature culinary recipes.`,
        location: hotelName,
        transportMode: 'Walking',
        travelDurationFromPrevious: '15 mins',
        costEstimate: 650 * (requirements.travellers.adults || 1),
        tips: 'Request the hotel concierge to hold bags if your flight is in the evening.'
      });

      activities.push({
        id: `act-${i}-3`,
        timeSlot: 'Evening',
        time: '04:30 PM',
        title: `Private Transfer to Airport & Boarding`,
        description: `Smooth drop-off at departure gates, web check-in baggage drop, and comfortable flight boarding.`,
        location: `${requirements.destination} Departure Gates`,
        transportMode: 'Private Transfer',
        travelDurationFromPrevious: '45 mins highway route',
        costEstimate: 500,
        tips: 'Reach airport at least 2 hours prior to scheduled departure.'
      });
    } else {
      // Intermediate days
      const attr1 = attractionsPool.shift();
      const attr2 = attractionsPool.shift();

      if (i % 2 === 0) {
        theme = 'Architectural Wonders & Heritage Highlights';
        summary = `A deep dive into monumental palaces, ancient shrines, and rich historical legends of ${requirements.destination}.`;
      } else {
        theme = 'Scenic Landscapes, Nature & Experiential Trails';
        summary = `Immerse in breathtaking viewpoints, serene lakes, artisan quarters, and active exploration.`;
      }

      if (attr1) {
        activities.push({
          id: `act-${i}-1`,
          timeSlot: 'Morning',
          time: '09:15 AM',
          title: `Visit ${attr1.name}`,
          description: attr1.description,
          attractionId: attr1.id,
          image: attr1.image,
          location: attr1.location,
          transportMode: 'Cab',
          travelDurationFromPrevious: '25 mins from hotel',
          costEstimate: attr1.entryFee * (requirements.travellers.adults || 1),
          tips: `Estimated duration: ${attr1.estimatedDuration}. Dress modestly for heritage sites.`
        });
      } else {
        activities.push({
          id: `act-${i}-1`,
          timeSlot: 'Morning',
          time: '09:30 AM',
          title: `Panoramic City Viewpoint & Heritage Walk`,
          description: `Breathtaking valley vistas, sunrise vantage points, and a guided historic trail uncovering architectural relics.`,
          location: `${requirements.destination} Hilltop`,
          transportMode: 'Cab',
          travelDurationFromPrevious: '20 mins drive',
          costEstimate: 150,
          tips: 'Wear comfortable walking shoes.'
        });
      }

      activities.push({
        id: `act-${i}-2`,
        timeSlot: 'Afternoon',
        time: '01:00 PM',
        title: `Authentic Regional Lunch & Leisure Rest`,
        description: `Taste organic local specialties at a garden courtyard bistro followed by a brief break during peak afternoon sun.`,
        location: `Central ${requirements.destination}`,
        transportMode: 'Walking',
        travelDurationFromPrevious: '10 mins walk',
        costEstimate: 700 * (requirements.travellers.adults || 1),
        tips: 'Stay well hydrated with fresh coconut water or regional cooler.'
      });

      if (attr2) {
        activities.push({
          id: `act-${i}-3`,
          timeSlot: 'Afternoon',
          time: '03:45 PM',
          title: `Experience ${attr2.name}`,
          description: attr2.description,
          attractionId: attr2.id,
          image: attr2.image,
          location: attr2.location,
          transportMode: 'Cab',
          travelDurationFromPrevious: '15 mins drive',
          costEstimate: attr2.entryFee * (requirements.travellers.adults || 1),
          tips: `Highlights: ${attr2.highlights.slice(0, 2).join(', ')}.`
        });
      } else {
        activities.push({
          id: `act-${i}-3`,
          timeSlot: 'Afternoon',
          time: '04:00 PM',
          title: `Cultural Artisan Village & Live Workshop`,
          description: `Watch master craftsmen create traditional tapestries, block printing, or wood pottery with hands-on trials.`,
          location: `Artisans Guild, ${requirements.destination}`,
          transportMode: 'Cab',
          travelDurationFromPrevious: '15 mins drive',
          costEstimate: 200,
          tips: 'Great place to buy authentic souvenirs directly from local artists.'
        });
      }

      activities.push({
        id: `act-${i}-4`,
        timeSlot: 'Evening',
        time: '07:30 PM',
        title: `Evening Cultural Sound, Light & Dinner Gala`,
        description: `Witness a vibrant open-air folk music or classical dance showcase accompanied by a candlelit dinner.`,
        location: `Heritage Courtyard, ${requirements.destination}`,
        transportMode: 'Cab',
        travelDurationFromPrevious: '12 mins drive',
        costEstimate: 1100 * (requirements.travellers.adults || 1),
        tips: 'Pre-reserved prime seating included in VIP tour desk access.'
      });
    }

    const totalDayExpense = activities.reduce((sum, a) => sum + a.costEstimate, 0);

    itinerary.push({
      dayNumber: i,
      date: dateStr,
      theme,
      summary,
      activities,
      totalDayExpense
    });
  }

  return itinerary;
}

