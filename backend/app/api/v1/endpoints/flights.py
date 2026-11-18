import logging
from typing import Any, Dict
from fastapi import APIRouter, Depends, HTTPException, status

from backend.app.schemas.flight import FlightSearchRequest
from backend.app.services.ignav_service import (
    IgnavService,
    IgnavError,
    IgnavConfigurationError,
    IgnavAuthenticationError,
    IgnavNetworkError,
    IgnavResponseError,
    get_ignav_service,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/flights", tags=["Flights"])


@router.post(
    "/search",
    summary="Search one-way flights",
    response_model=Dict[str, Any],
    status_code=status.HTTP_200_OK,
    responses={
        200: {"description": "Flight search completed successfully"},
        422: {"description": "Invalid search parameters"},
        502: {"description": "Upstream flight provider error or authentication failure"},
        503: {"description": "Flight search service unconfigured or unavailable"},
        504: {"description": "Upstream flight provider timeout or network failure"},
    },
)
def search_flights(
    request: FlightSearchRequest,
    ignav_service: IgnavService = Depends(get_ignav_service),
) -> Dict[str, Any]:
    """Search for one-way flight fares between origin and destination using Ignav API."""
    try:
        results = ignav_service.search_one_way_flights(
            origin=request.origin,
            destination=request.destination,
            departure_date=request.departure_date,
            adults=request.adults,
            cabin_class=request.cabin_class,
            market="IN",
        )
        return results

    except IgnavConfigurationError:
        logger.error("Ignav service configuration error: IGNAV_API_KEY is not configured.")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Flight search service is currently unconfigured or unavailable.",
        )

    except IgnavAuthenticationError as exc:
        err_msg = str(exc).lower()
        if "not configured" in err_msg or "missing" in err_msg:
            logger.error("Ignav service configuration error: API key missing")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Flight search service is currently unconfigured or unavailable.",
            )
        logger.error(f"Ignav upstream authentication failure: {exc}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Upstream flight provider authentication failed.",
        )

    except IgnavNetworkError as exc:
        logger.error(f"Ignav network/timeout failure: {exc}")
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Upstream flight provider request timed out or connection failed.",
        )

    except (IgnavResponseError, IgnavError) as exc:
        logger.error(f"Ignav provider response error: {exc}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Upstream flight provider returned an invalid response.",
        )

    except ValueError as exc:
        logger.warning(f"Validation error in flight search: {exc}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        )

    except HTTPException:
        raise

    except Exception as exc:
        logger.error(f"Unexpected error in flight search endpoint: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while processing the flight search request.",
        )

