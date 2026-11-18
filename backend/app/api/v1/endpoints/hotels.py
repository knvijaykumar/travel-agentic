import logging
from typing import Any, Dict
from fastapi import APIRouter, Depends, HTTPException, status

from backend.app.schemas.hotel import HotelSearchRequest
from backend.app.services.nuitee_service import (
    NuiteeService,
    NuiteeError,
    NuiteeConfigurationError,
    NuiteeAuthenticationError,
    NuiteeNetworkError,
    NuiteeResponseError,
    get_nuitee_service,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/hotels", tags=["Hotels"])


@router.post(
    "/search",
    summary="Search hotel rates",
    response_model=Dict[str, Any],
    status_code=status.HTTP_200_OK,
    responses={
        200: {"description": "Hotel search completed successfully"},
        422: {"description": "Invalid search parameters"},
        502: {"description": "Upstream hotel provider error or authentication failure"},
        503: {"description": "Hotel search service unconfigured or unavailable"},
        504: {"description": "Upstream hotel provider timeout or network failure"},
    },
)
def search_hotels(
    request: HotelSearchRequest,
    nuitee_service: NuiteeService = Depends(get_nuitee_service),
) -> Dict[str, Any]:
    """Search for hotel rates and availability using Nuitee Connect (LiteAPI)."""
    try:
        occupancies = request.to_occupancies()
        results = nuitee_service.search_hotel_rates(
            checkin=request.checkin,
            checkout=request.checkout,
            occupancies=occupancies,
            adults=request.adults,
            currency=request.currency,
            guest_nationality=request.guest_nationality,
            city_name=request.city_name,
            country_code=request.country_code,
            latitude=request.latitude,
            longitude=request.longitude,
            radius=request.radius,
            hotel_ids=request.hotel_ids,
            include_hotel_data=True,
        )
        return results

    except NuiteeConfigurationError:
        logger.error("Nuitee service configuration error: NUITEE_API_KEY is not configured.")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Hotel search service is currently unconfigured or unavailable.",
        )

    except NuiteeAuthenticationError as exc:
        err_msg = str(exc).lower()
        if "not configured" in err_msg or "missing" in err_msg:
            logger.error("Nuitee service configuration error: API key missing")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Hotel search service is currently unconfigured or unavailable.",
            )
        logger.error(f"Nuitee upstream authentication failure: {exc}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Upstream hotel provider authentication failed.",
        )

    except NuiteeNetworkError as exc:
        logger.error(f"Nuitee network/timeout failure: {exc}")
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Upstream hotel provider request timed out or connection failed.",
        )

    except (NuiteeResponseError, NuiteeError) as exc:
        logger.error(f"Nuitee provider response error: {exc}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Upstream hotel provider returned an invalid response.",
        )

    except ValueError as exc:
        logger.warning(f"Validation error in hotel search: {exc}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        )

    except HTTPException:
        raise

    except Exception as exc:
        logger.error(f"Unexpected error in hotel search endpoint: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while processing the hotel search request.",
        )

