from __future__ import annotations

import json
from dataclasses import asdict
from decimal import Decimal
from typing import Any, Protocol

from arbcore.models import Opportunity


class DecimalEncoder(json.JSONEncoder):
    """Custom JSON encoder for Decimal types."""

    def default(self, obj: Any) -> Any:
        if isinstance(obj, Decimal):
            return float(obj)
        return super().default(obj)


class Reporter(Protocol):
    """Extension point for rendering analysis results."""

    def render(self, opportunities: list[Opportunity]) -> str:
        """Return a complete string representation of opportunities."""


class JsonReporter:
    """Machine-readable JSON output."""

    def render(self, opportunities: list[Opportunity]) -> str:
        return json.dumps([asdict(item) for item in opportunities], indent=2, cls=DecimalEncoder)


class TextReporter:
    """Human-readable command-line output."""

    def render(self, opportunities: list[Opportunity]) -> str:
        if not opportunities:
            return "No opportunities passed the configured policy."
        lines = []
        for item in opportunities:
            route = " -> ".join(item.path)
            venues = ", ".join(item.venues)
            lines.append(
                f"[{item.network}] {route} | {float(item.profit_bps):.2f} bps | "
                f"capacity: {float(item.estimated_capacity):.4g} | venues: {venues}"
            )
        return "\n".join(lines)
