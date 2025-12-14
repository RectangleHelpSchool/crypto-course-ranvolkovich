"""Retry decorator utilities using tenacity."""

import logging
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
)
from web3.exceptions import Web3Exception
import asyncio

from .config import get_settings

logger = logging.getLogger(__name__)


def get_retry_decorator():
    """
    Get a configured retry decorator for async functions.

    Returns a tenacity retry decorator configured with settings from config.
    """
    settings = get_settings()

    return retry(
        stop=stop_after_attempt(settings.max_retry_attempts),
        wait=wait_exponential(
            multiplier=settings.retry_multiplier,
            min=settings.retry_min_wait,
            max=settings.retry_max_wait,
        ),
        retry=retry_if_exception_type((
            Web3Exception,
            asyncio.TimeoutError,
            ConnectionError,
            TimeoutError,
        )),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        reraise=True,
    )


# Pre-configured retry decorator
retry_on_failure = get_retry_decorator()
