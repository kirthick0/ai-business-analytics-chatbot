"""OpenAI Responses API integration for business analytics explanations."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import pandas as pd
from dotenv import load_dotenv
from openai import (
    APIConnectionError,
    APIStatusError,
    APITimeoutError,
    AuthenticationError,
    OpenAI,
    OpenAIError,
    RateLimitError,
)


DEFAULT_MODEL = "gpt-4.1-mini"
PROJECT_ROOT = Path(__file__).resolve().parents[1]


class AssistantConfigurationError(RuntimeError):
    """Raised when the API key is missing or rejected."""


class AssistantRequestError(RuntimeError):
    """Raised when an OpenAI request cannot be completed."""


def configured_api_key() -> str | None:
    """Read the API key from the process environment or the local .env file."""
    load_dotenv(PROJECT_ROOT / ".env", override=False)
    key = os.getenv("OPENAI_API_KEY", "").strip()
    return key or None


def configured_model() -> str:
    """Return the configured model, defaulting to GPT-4.1 mini."""
    load_dotenv(PROJECT_ROOT / ".env", override=False)
    return os.getenv("OPENAI_MODEL", "").strip() or DEFAULT_MODEL


def _request_error(exc: OpenAIError) -> AssistantRequestError:
    if isinstance(exc, AuthenticationError):
        return AssistantConfigurationError(
            "OpenAI rejected the API key. Check OPENAI_API_KEY and confirm the key is active."
        )
    if isinstance(exc, RateLimitError):
        body = getattr(exc, "body", None)
        details = body.get("error") if isinstance(body, dict) else None
        code = details.get("code") if isinstance(details, dict) else None
        if code in {"insufficient_quota", "billing_hard_limit_reached"}:
            return AssistantRequestError(
                "The OpenAI API account has insufficient quota or credits. Check billing and usage limits."
            )
        return AssistantRequestError(
            "OpenAI rate limit reached. Wait briefly and try again."
        )
    if isinstance(exc, APITimeoutError):
        return AssistantRequestError("The OpenAI request timed out. Please try again.")
    if isinstance(exc, APIConnectionError):
        return AssistantRequestError(
            "Could not connect to OpenAI. Check the network connection and try again."
        )
    if isinstance(exc, APIStatusError):
        if exc.status_code == 401:
            return AssistantConfigurationError(
                "OpenAI rejected the API key. Check OPENAI_API_KEY and confirm the key is active."
            )
        if exc.status_code == 429:
            return AssistantRequestError(
                "OpenAI rate limit or quota reached. Check usage and billing, then try again."
            )
        if exc.status_code in {400, 404}:
            return AssistantRequestError(
                "OpenAI rejected this request or model. Check OPENAI_MODEL and confirm it is available to your API account."
            )
        if exc.status_code >= 500:
            return AssistantRequestError(
                "The OpenAI service is temporarily unavailable. Please try again shortly."
            )
        return AssistantRequestError(
            f"OpenAI returned an API error (HTTP {exc.status_code})."
        )
    return AssistantRequestError("The OpenAI request failed. Please try again.")


def generate_assistant_response(
    message: str,
    *,
    api_key: str | None,
    model: str = DEFAULT_MODEL,
    history: list[dict[str, str]] | None = None,
    dataset_context: str | None = None,
    verified_result: str | None = None,
    client: OpenAI | None = None,
) -> str:
    """Generate an answer, treating any supplied dataset result as verified input."""
    if not message or not message.strip():
        raise ValueError("Enter a question before sending it.")
    if client is None and not api_key:
        raise AssistantConfigurationError(
            "No OpenAI API key is configured. Add OPENAI_API_KEY to .env or Streamlit Secrets."
        )

    instructions = (
        "You are a clear, practical business and data analytics assistant. Help with business "
        "analytics, Python, SQL, Excel, Power BI, data cleaning, EDA, statistics, machine "
        "learning, forecasting, sales, finance, marketing, KPIs, reporting, visualization, "
        "and dashboards. Be transparent about assumptions and limitations. Never claim to "
        "have executed code or inspected source rows. Do not invent dataset facts, values, "
        "statistics, or trends. When verified analysis context is supplied, use it only to "
        "explain the method and implications qualitatively; do not repeat or derive numerical "
        "claims. The UI displays the exact Pandas-calculated result separately. If a data "
        "question cannot be answered from the supplied context, say what additional analysis "
        "or column information is needed. Use Markdown, concise headings, and fenced code "
        "blocks when useful."
    )
    if dataset_context:
        instructions += f"\n\nDataset schema and quality facts (not raw records):\n{dataset_context}"
    if verified_result:
        instructions += f"\n\nPandas-calculated result for the current question:\n{verified_result}"

    input_messages: list[dict[str, str]] = []
    for item in (history or [])[-12:]:
        role = item.get("role")
        content = item.get("content", "")
        if role in {"user", "assistant"} and content.strip():
            input_messages.append({"role": role, "content": content[:4000]})
    input_messages.append({"role": "user", "content": message.strip()[:4000]})

    active_client = client or OpenAI(api_key=api_key, timeout=30.0, max_retries=1)
    try:
        response: Any = active_client.responses.create(
            model=model or DEFAULT_MODEL,
            instructions=instructions,
            input=input_messages,
            max_output_tokens=900,
            store=False,
        )
    except OpenAIError as exc:
        raise _request_error(exc) from exc

    answer = getattr(response, "output_text", None)
    if not isinstance(answer, str) or not answer.strip():
        raise AssistantRequestError(
            "OpenAI returned an empty response. Please rephrase your question and try again."
        )
    return answer.strip()


def build_dataset_context(frame: pd.DataFrame) -> str:
    """Create a compact dataset profile without sending source rows."""
    details = [
        f"Rows: {len(frame)}",
        f"Columns: {len(frame.columns)}",
        f"Missing cells: {int(frame.isna().sum().sum())}",
        f"Duplicate rows: {int(frame.duplicated().sum())}",
        "Columns (name and dtype): "
        + ", ".join(f"{column} ({dtype})" for column, dtype in frame.dtypes.items()),
    ]
    return "\n".join(details)


def build_verified_result(answer: str, table: pd.DataFrame | None) -> str:
    """Serialize a bounded calculated answer for optional GPT explanation."""
    result = answer[:2000]
    if table is not None and not table.empty:
        result += "\nCalculated result table (first 10 rows):\n"
        result += table.head(10).to_json(orient="records", date_format="iso")
    return result
