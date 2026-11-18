import asyncio
from typing import Any, Dict, Optional
import httpx
from backend.app.core.logger import logger
from integrations.base_models import DataSourceType, IntegrationMetadata, IntegrationResponse


class BaseIntegrationClient:
    """Base HTTP client for external service integrations with retry, timeout, and provenance tracking."""

    def __init__(
        self,
        source_name: str,
        base_url: str = "",
        timeout_seconds: float = 8.0,
        max_retries: int = 1,
    ):
        self.source_name = source_name
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout_seconds
        self.max_retries = max_retries

    def create_metadata(
        self,
        is_mock: bool = False,
        data_source_type: DataSourceType = DataSourceType.LIVE_API,
        status_code: int = 200,
        error_message: Optional[str] = None,
        cached: bool = False,
    ) -> IntegrationMetadata:
        """Create standardized data provenance metadata."""
        return IntegrationMetadata(
            source_name=self.source_name,
            data_source_type=data_source_type,
            is_mock=is_mock,
            status_code=status_code,
            error_message=error_message,
            cached=cached,
        )

    async def get(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """Perform an async GET request with retry logic."""
        url = f"{self.base_url}/{endpoint.lstrip('/')}" if self.base_url else endpoint
        attempt = 0
        last_error = None

        while attempt <= self.max_retries:
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.get(url, params=params, headers=headers)
                    response.raise_for_status()
                    return response.json()
            except Exception as exc:
                attempt += 1
                last_error = exc
                logger.warning(
                    f"[{self.source_name}] GET to {url} failed (attempt {attempt}/{self.max_retries + 1}): {exc}"
                )
                if attempt <= self.max_retries:
                    await asyncio.sleep(0.3 * attempt)

        raise RuntimeError(f"[{self.source_name}] Request failed after {self.max_retries + 1} attempts: {last_error}")

    async def post(
        self,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """Perform an async POST request with retry logic."""
        url = f"{self.base_url}/{endpoint.lstrip('/')}" if self.base_url else endpoint
        attempt = 0
        last_error = None

        while attempt <= self.max_retries:
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.post(url, data=data, json=json_data, headers=headers)
                    response.raise_for_status()
                    return response.json()
            except Exception as exc:
                attempt += 1
                last_error = exc
                logger.warning(
                    f"[{self.source_name}] POST to {url} failed (attempt {attempt}/{self.max_retries + 1}): {exc}"
                )
                if attempt <= self.max_retries:
                    await asyncio.sleep(0.3 * attempt)

        raise RuntimeError(f"[{self.source_name}] POST failed after {self.max_retries + 1} attempts: {last_error}")
