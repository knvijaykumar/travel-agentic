from fastapi import APIRouter
from backend.app.api.v1.endpoints import health, chat, places, flights, hotels, itinerary, bookings

api_router = APIRouter()

# Include routes
api_router.include_router(health.router, tags=["Health"])
api_router.include_router(chat.router, tags=["Chat"])
api_router.include_router(places.router)
api_router.include_router(flights.router)
api_router.include_router(hotels.router)
api_router.include_router(itinerary.router)
api_router.include_router(bookings.router)




