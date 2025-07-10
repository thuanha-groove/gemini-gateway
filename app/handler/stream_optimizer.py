import asyncio
import math
from typing import Any, AsyncGenerator, Callable, List

from app.config.config import settings
from app.core.constants import (
    DEFAULT_STREAM_CHUNK_SIZE,
    DEFAULT_STREAM_LONG_TEXT_THRESHOLD,
    DEFAULT_STREAM_MAX_DELAY,
    DEFAULT_STREAM_MIN_DELAY,
    DEFAULT_STREAM_SHORT_TEXT_THRESHOLD,
)
from app.log.logger import get_gemini_logger, get_openai_logger

logger_openai = get_openai_logger()
logger_gemini = get_gemini_logger()


class StreamOptimizer:
    """Stream Output Optimizer

    Provides stream output optimization features, including intelligent delay adjustment and long text chunking.
    """

    def __init__(
        self,
        logger=None,
        min_delay: float = DEFAULT_STREAM_MIN_DELAY,
        max_delay: float = DEFAULT_STREAM_MAX_DELAY,
        short_text_threshold: int = DEFAULT_STREAM_SHORT_TEXT_THRESHOLD,
        long_text_threshold: int = DEFAULT_STREAM_LONG_TEXT_THRESHOLD,
        chunk_size: int = DEFAULT_STREAM_CHUNK_SIZE,
    ):
        """Initializes the Stream Output Optimizer

        Args:
            logger: The logger instance.
            min_delay: Minimum delay time (seconds).
            max_delay: Maximum delay time (seconds).
            short_text_threshold: Short text threshold (number of characters).
            long_text_threshold: Long text threshold (number of characters).
            chunk_size: Long text chunk size (number of characters).
        """
        self.logger = logger
        self.min_delay = min_delay
        self.max_delay = max_delay
        self.short_text_threshold = short_text_threshold
        self.long_text_threshold = long_text_threshold
        self.chunk_size = chunk_size

    def calculate_delay(self, text_length: int) -> float:
        """Calculates delay time based on text length

        Args:
            text_length: The length of the text.

        Returns:
            Delay time (seconds).
        """
        if text_length <= self.short_text_threshold:
            # Use larger delay for short text
            return self.max_delay
        elif text_length >= self.long_text_threshold:
            # Use smaller delay for long text
            return self.min_delay
        else:
            # Use linear interpolation for medium-length text
            # Use a logarithmic function for smoother delay changes
            ratio = math.log(text_length / self.short_text_threshold) / math.log(
                self.long_text_threshold / self.short_text_threshold
            )
            return self.max_delay - ratio * (self.max_delay - self.min_delay)

    def split_text_into_chunks(self, text: str) -> List[str]:
        """Splits text into small chunks

        Args:
            text: The text to be split.

        Returns:
            A list of text chunks.
        """
        return [
            text[i : i + self.chunk_size] for i in range(0, len(text), self.chunk_size)
        ]

    async def optimize_stream_output(
        self,
        text: str,
        create_response_chunk: Callable[[str], Any],
        format_chunk: Callable[[Any], str],
    ) -> AsyncGenerator[str, None]:
        """Optimizes stream output

        Args:
            text: The text to be output.
            create_response_chunk: Function to create a response chunk, takes text and returns a response chunk.
            format_chunk: Function to format a response chunk, takes a response chunk and returns a formatted string.

        Returns:
            An async generator that yields formatted response chunks.
        """
        if not text:
            return

        # Calculate intelligent delay time
        delay = self.calculate_delay(len(text))

        # Decide output method based on text length
        if len(text) >= self.long_text_threshold:
            # Long text: output in chunks
            chunks = self.split_text_into_chunks(text)
            for chunk_text in chunks:
                chunk_response = create_response_chunk(chunk_text)
                yield format_chunk(chunk_response)
                await asyncio.sleep(delay)
        else:
            # Short text: output character by character
            for char in text:
                char_chunk = create_response_chunk(char)
                yield format_chunk(char_chunk)
                await asyncio.sleep(delay)


# Create default optimizer instances that can be imported directly
openai_optimizer = StreamOptimizer(
    logger=logger_openai,
    min_delay=settings.STREAM_MIN_DELAY,
    max_delay=settings.STREAM_MAX_DELAY,
    short_text_threshold=settings.STREAM_SHORT_TEXT_THRESHOLD,
    long_text_threshold=settings.STREAM_LONG_TEXT_THRESHOLD,
    chunk_size=settings.STREAM_CHUNK_SIZE,
)

gemini_optimizer = StreamOptimizer(
    logger=logger_gemini,
    min_delay=settings.STREAM_MIN_DELAY,
    max_delay=settings.STREAM_MAX_DELAY,
    short_text_threshold=settings.STREAM_SHORT_TEXT_THRESHOLD,
    long_text_threshold=settings.STREAM_LONG_TEXT_THRESHOLD,
    chunk_size=settings.STREAM_CHUNK_SIZE,
)