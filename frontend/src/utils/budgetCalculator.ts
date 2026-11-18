import { FlightOption, TrainOption, HotelOption, ItineraryDay, TransferOption, TripBudgetBreakdown, TripRequirements } from '../types/travel';

export function calculateTripBudget(
  requirements: TripRequirements,
  flight?: FlightOption,
  hotel?: HotelOption,
  transfers: TransferOption[] = [],
  itinerary: ItineraryDay[] = [],
  train?: TrainOption
): TripBudgetBreakdown {
  const totalTravellers = Math.max(1, (requirements.travellers.adults || 1) + (requirements.travellers.children || 0));
  const days = Math.max(1, requirements.durationDays || 4);

  // Flight cost or Train cost based on user selection
  const isTrainMode = requirements.transportPreference === 'Train' || requirements.transportMode === 'TRAIN';
  const flightCost = (!isTrainMode && flight) ? flight.totalPrice : 0;
  const trainCost = (isTrainMode && train) ? train.totalPrice : (train ? train.totalPrice : 0);

  // Hotel cost
  const hotelCost = hotel ? hotel.totalCost : 0;

  // Selected transfers
  const transportCost = transfers
    .filter(t => t.selected)
    .reduce((sum, t) => sum + t.price, 0);

  // Sightseeing and Activities from Itinerary
  let sightseeingCost = 0;
  let activitiesCost = 0;

  itinerary.forEach(day => {
    day.activities.forEach(act => {
      if (act.attractionId) {
        sightseeingCost += act.costEstimate;
      } else if (act.timeSlot === 'Evening' || act.timeSlot === 'Afternoon') {
        activitiesCost += act.costEstimate;
      }
    });
  });

  // Food Estimate: ~₹750 per person per day
  const foodEstimate = Math.round(750 * totalTravellers * days);

  // Misc & contingency: ~3% of transport + stays + 300 * days
  const miscCost = Math.round((flightCost + trainCost + hotelCost + sightseeingCost + activitiesCost) * 0.03) + (300 * days);

  const totalEstimatedCost = flightCost + trainCost + hotelCost + transportCost + sightseeingCost + activitiesCost + foodEstimate + miscCost;

  const userBudget = requirements.totalBudget || 40000;
  const remainingBudget = userBudget - totalEstimatedCost;
  const perPersonCost = Math.round(totalEstimatedCost / totalTravellers);
  const budgetUtilizationPct = Math.round((totalEstimatedCost / userBudget) * 100);

  let status: 'OPTIMAL' | 'APPROACHING_LIMIT' | 'OVER_BUDGET' = 'OPTIMAL';
  if (budgetUtilizationPct > 100) {
    status = 'OVER_BUDGET';
  } else if (budgetUtilizationPct >= 88) {
    status = 'APPROACHING_LIMIT';
  }

  return {
    totalBudget: userBudget,
    flightCost,
    trainCost,
    hotelCost,
    transportCost,
    sightseeingCost,
    foodEstimate,
    activitiesCost,
    miscCost,
    totalEstimatedCost,
    perPersonCost,
    remainingBudget,
    budgetUtilizationPct,
    status
  };
}

