"""SonarQube API client with authentication and retry logic.

This module provides a client for interacting with SonarQube REST API,
including token authentication, timeout handling, and exponential backoff retry.
"""

import requests
from typing import Dict, Any, Optional
from time import sleep

from backend.src.utils.config import settings
from backend.src.utils.errors import (
    ConnectionError,
    AuthenticationError,
    TokenExpiredError,
    RateLimitError,
    InvalidAPIResponseError
)
from backend.src.utils.logger import get_logger

logger = get_logger(__name__)


class SonarQubeClient:
    """Client for SonarQube REST API."""
    
    def __init__(self, server_url: str, token: str):
        """Initialize SonarQube API client.
        
        Args:
            server_url: SonarQube server URL
            token: Authentication token
        """
        self.server_url = server_url.rstrip('/')
        self.token = token
        self.timeout = settings.sonarqube_timeout
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {token}'
        })
    
    def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        retry_count: int = 0
    ) -> Dict[str, Any]:
        """Make HTTP request to SonarQube API with retry logic.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint path
            params: Optional query parameters
            json_data: Optional JSON request body
            retry_count: Current retry attempt
            
        Returns:
            Dict[str, Any]: Parsed JSON response
            
        Raises:
            ConnectionError: If server is unreachable
            AuthenticationError: If authentication fails
            TokenExpiredError: If token has expired
            RateLimitError: If rate limit is exceeded
            InvalidAPIResponseError: If response is malformed
        """
        url = f"{self.server_url}{endpoint}"
        
        try:
            response = self.session.request(
                method=method,
                url=url,
                params=params,
                json=json_data,
                timeout=self.timeout
            )
            
            # Handle authentication errors
            if response.status_code == 401:
                logger.error(f"Authentication failed for {url}")
                raise TokenExpiredError(
                    "Authentication token has expired or is invalid",
                    {"url": url}
                )
            
            # Handle rate limiting
            if response.status_code == 429:
                retry_after = int(response.headers.get('Retry-After', 60))
                
                if retry_count < settings.sonarqube_retry_max_attempts:
                    delay = settings.sonarqube_retry_delays[min(retry_count, len(settings.sonarqube_retry_delays) - 1)]
                    logger.warning(f"Rate limited. Retrying after {delay}s (attempt {retry_count + 1})")
                    sleep(delay)
                    return self._make_request(method, endpoint, params, json_data, retry_count + 1)
                
                raise RateLimitError(
                    "SonarQube API rate limit exceeded",
                    retry_after_seconds=retry_after,
                    details={"url": url}
                )
            
            # Handle server errors with retry
            if response.status_code >= 500:
                if retry_count < settings.sonarqube_retry_max_attempts:
                    delay = settings.sonarqube_retry_delays[min(retry_count, len(settings.sonarqube_retry_delays) - 1)]
                    logger.warning(f"Server error {response.status_code}. Retrying after {delay}s")
                    sleep(delay)
                    return self._make_request(method, endpoint, params, json_data, retry_count + 1)
                
                raise ConnectionError(
                    f"SonarQube server error: {response.status_code}",
                    {"url": url, "status_code": response.status_code}
                )
            
            # Raise for other 4xx errors
            response.raise_for_status()
            
            # Parse JSON response
            try:
                return response.json()
            except ValueError as e:
                raise InvalidAPIResponseError(
                    f"Invalid JSON response from SonarQube API: {e}",
                    {"url": url}
                )
                
        except requests.exceptions.Timeout:
            logger.error(f"Request timeout for {url}")
            raise ConnectionError(
                f"Request timeout after {self.timeout} seconds",
                {"url": url, "timeout": self.timeout}
            )
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Connection failed for {url}: {e}")
            raise ConnectionError(
                f"Failed to connect to SonarQube server: {e}",
                {"url": url}
            )
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed for {url}: {e}")
            raise ConnectionError(
                f"SonarQube API request failed: {e}",
                {"url": url}
            )
    
    def validate_connection(self) -> Dict[str, Any]:
        """Validate connection by fetching system status.
        
        Returns:
            Dict[str, Any]: System status including version and status
            
        Raises:
            ConnectionError: If validation fails
            AuthenticationError: If token is invalid
        """
        logger.info(f"Validating connection to {self.server_url}")
        
        try:
            response = self._make_request('GET', '/api/system/status')
            
            return {
                'status': response.get('status'),
                'version': response.get('version'),
                'id': response.get('id')
            }
        except Exception as e:
            logger.error(f"Connection validation failed: {e}")
            raise
    
    def get_system_info(self) -> Dict[str, Any]:
        """Get system information.
        
        Returns:
            Dict[str, Any]: System information
        """
        return self._make_request('GET', '/api/system/info')
    
    def close(self) -> None:
        """Close the HTTP session."""
        self.session.close()


def validate_connection_url(url: str) -> bool:
    """Helper function to validate connection URL format.
    
    Args:
        url: URL to validate
        
    Returns:
        bool: True if URL is valid
        
    Raises:
        ValueError: If URL is invalid
    """
    import re
    
    if not url:
        raise ValueError("URL cannot be empty")
    
    url_pattern = re.compile(
        r'^https?://'
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'
        r'localhost|'
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'
        r'(?::\d+)?'
        r'(?:/?|[/?]\S+)$', re.IGNORECASE
    )
    
    if not url_pattern.match(url):
        raise ValueError("Invalid URL format")
    
    return True
