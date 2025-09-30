"""
Real LLM Adapter with concurrent API calls.
Replaces mock LLM with actual API integration.
"""

import asyncio
import aiohttp
import json
import uuid
from typing import Dict, List, Any, Optional
from datetime import datetime
from dataclasses import dataclass, field


@dataclass
class LLMConfig:
    """Configuration for LLM adapter."""

    api_url: str
    api_key: str
    model: str = "gpt-4"
    max_tokens: int = 2048
    temperature: float = 0.1
    timeout: float = 30.0
    max_retries: int = 3
    retry_delay: float = 1.0
    concurrent_requests: int = 5
    rate_limit: float = 60.0  # requests per minute


@dataclass
class LLMResponse:
    """Response from LLM."""

    content: str
    model: str
    usage: Dict[str, int]
    finish_reason: str
    response_time: float
    request_id: str
    metadata: Dict[str, Any] = field(default_factory=dict)


class LLMAdapter:
    """Real LLM adapter with concurrent API calls."""

    def __init__(self, config: LLMConfig):
        self.config = config
        self.session: Optional[aiohttp.ClientSession] = None
        self.request_semaphore = asyncio.Semaphore(config.concurrent_requests)
        self.rate_limiter = asyncio.Semaphore(int(config.rate_limit))
        self.initialized = False

        # Statistics
        self.total_requests = 0
        self.successful_requests = 0
        self.failed_requests = 0
        self.average_response_time = 0.0

    async def initialize(self, domain_spec: Dict[str, Any]) -> None:
        """Initialize the LLM adapter."""
        self.domain_spec = domain_spec
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.config.timeout)
        )
        self.initialized = True

    async def generate(
        self,
        prompt: str,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        **kwargs,
    ) -> str:
        """Generate text using LLM."""
        if not self.initialized:
            raise RuntimeError("LLM adapter not initialized")

        response = await self.generate_with_metadata(
            prompt=prompt, max_tokens=max_tokens, temperature=temperature, **kwargs
        )

        return response.content

    async def generate_with_metadata(
        self,
        prompt: str,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        **kwargs,
    ) -> LLMResponse:
        """Generate text with full metadata."""
        if not self.initialized:
            raise RuntimeError("LLM adapter not initialized")

        async with self.request_semaphore:
            async with self.rate_limiter:
                return await self._make_request(
                    prompt=prompt,
                    max_tokens=max_tokens or self.config.max_tokens,
                    temperature=temperature or self.config.temperature,
                    **kwargs,
                )

    async def generate_implementation(
        self,
        specification: Dict[str, Any],
        context: Any,
        constraints: List[Dict[str, Any]],
        previous_implementation: Optional[Dict[str, Any]] = None,
        counterexample: Optional[Any] = None,
    ) -> Dict[str, Any]:
        """Generate implementation from specification."""
        # Build prompt for implementation generation
        prompt = self._build_implementation_prompt(
            specification=specification,
            context=context,
            constraints=constraints,
            previous_implementation=previous_implementation,
            counterexample=counterexample,
        )

        # Generate implementation
        response = await self.generate_with_metadata(prompt)

        # Parse response into implementation
        return self._parse_implementation_response(response)

    async def generate_multiple(
        self,
        prompts: List[str],
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
    ) -> List[LLMResponse]:
        """Generate multiple responses concurrently."""
        if not self.initialized:
            raise RuntimeError("LLM adapter not initialized")

        tasks = [
            self.generate_with_metadata(
                prompt=prompt, max_tokens=max_tokens, temperature=temperature
            )
            for prompt in prompts
        ]

        return await asyncio.gather(*tasks, return_exceptions=True)

    async def _make_request(
        self, prompt: str, max_tokens: int, temperature: float, **kwargs
    ) -> LLMResponse:
        """Make actual API request to LLM."""
        start_time = datetime.now()
        request_id = str(uuid.uuid4())

        payload = {
            "model": self.config.model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": temperature,
            **kwargs,
        }

        headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json",
        }

        retry_count = 0
        last_exception = None

        while retry_count < self.config.max_retries:
            try:
                async with self.session.post(
                    self.config.api_url, json=payload, headers=headers
                ) as response:
                    if response.status == 200:
                        data = await response.json()

                        # Update statistics
                        self.total_requests += 1
                        self.successful_requests += 1

                        response_time = (datetime.now() - start_time).total_seconds()
                        self._update_average_response_time(response_time)

                        return LLMResponse(
                            content=data["choices"][0]["message"]["content"],
                            model=data["model"],
                            usage=data.get("usage", {}),
                            finish_reason=data["choices"][0].get("finish_reason", "stop"),
                            response_time=response_time,
                            request_id=request_id,
                            metadata={
                                "prompt_length": len(prompt),
                                "retry_count": retry_count,
                                "status_code": response.status,
                            },
                        )
                    else:
                        # Handle API errors
                        error_data = await response.json()
                        raise Exception(f"API error: {error_data}")

            except Exception as e:
                last_exception = e
                retry_count += 1

                if retry_count < self.config.max_retries:
                    await asyncio.sleep(self.config.retry_delay * retry_count)
                else:
                    # Update statistics
                    self.total_requests += 1
                    self.failed_requests += 1

                    raise Exception(
                        f"LLM request failed after {retry_count} retries: {last_exception}"
                    )

        raise last_exception

    def _build_implementation_prompt(
        self,
        specification: Dict[str, Any],
        context: Any,
        constraints: List[Dict[str, Any]],
        previous_implementation: Optional[Dict[str, Any]] = None,
        counterexample: Optional[Any] = None,
    ) -> str:
        """Build prompt for implementation generation."""
        prompt_parts = [
            "Generate a code implementation based on the following specification:",
            "",
            f"Specification: {json.dumps(specification, indent=2)}",
            "",
            f"Constraints: {json.dumps(constraints, indent=2)}",
            "",
        ]

        if previous_implementation:
            prompt_parts.extend(
                [
                    "Previous implementation (for reference):",
                    json.dumps(previous_implementation, indent=2),
                    "",
                ]
            )

        if counterexample:
            prompt_parts.extend(
                [
                    "Counterexample to address:",
                    f"Failing property: {counterexample.failing_property}",
                    f"Evidence: {json.dumps(counterexample.evidence, indent=2)}",
                    f"Suggestions: {', '.join(counterexample.suggestions)}",
                    "",
                ]
            )

        prompt_parts.extend(
            [
                "Generate a complete, working implementation that satisfies all requirements.",
                "Return the result as a JSON object with fields:",
                "- code: The implementation code",
                "- language: Programming language used",
                "- dependencies: List of required dependencies",
                "- tests: List of test cases",
                "- documentation: Brief documentation",
            ]
        )

        return "\n".join(prompt_parts)

    def _parse_implementation_response(self, response: LLMResponse) -> Dict[str, Any]:
        """Parse LLM response into implementation."""
        try:
            # Try to parse as JSON
            return json.loads(response.content)
        except json.JSONDecodeError:
            # Fallback to text parsing
            return {
                "code": response.content,
                "language": "python",
                "dependencies": [],
                "tests": [],
                "documentation": "Generated implementation",
                "metadata": {
                    "parsed_from": "text",
                    "response_time": response.response_time,
                    "model": response.model,
                },
            }

    def _update_average_response_time(self, response_time: float) -> None:
        """Update average response time."""
        if self.successful_requests == 1:
            self.average_response_time = response_time
        else:
            self.average_response_time = (
                self.average_response_time * (self.successful_requests - 1) + response_time
            ) / self.successful_requests

    async def get_statistics(self) -> Dict[str, Any]:
        """Get LLM adapter statistics."""
        return {
            "total_requests": self.total_requests,
            "successful_requests": self.successful_requests,
            "failed_requests": self.failed_requests,
            "success_rate": self.successful_requests / max(self.total_requests, 1),
            "average_response_time": self.average_response_time,
            "config": {
                "model": self.config.model,
                "max_tokens": self.config.max_tokens,
                "temperature": self.config.temperature,
                "timeout": self.config.timeout,
                "concurrent_requests": self.config.concurrent_requests,
            },
        }

    async def cleanup(self) -> None:
        """Cleanup resources."""
        if self.session:
            await self.session.close()
        self.initialized = False
