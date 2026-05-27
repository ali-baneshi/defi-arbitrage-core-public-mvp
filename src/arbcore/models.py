from __future__ import annotations

import math
import re
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any, Mapping

from arbcore.errors import PolicyError, SnapshotError

BPS_DENOMINATOR = Decimal("10000")
MAX_REASONABLE_HOPS = 8
MAX_REASONABLE_RESULTS = 1_000
MAX_ASSET_SYMBOL_LENGTH = 32
MAX_VENUE_LENGTH = 80
MAX_SOURCE_LENGTH = 120
MAX_NETWORK_LENGTH = 64
RFC3339_UTC_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")


@dataclass(frozen=True)
class Edge:
    """A directed exchange quote from one asset to another.

    `rate` means units of `target` received for one unit of `source` before fees.
    `liquidity` is expressed in source-asset units and is used as a conservative
    route capacity estimate.
    """

    source: str
    target: str
    rate: Decimal
    venue: str = "unknown"
    fee_bps: Decimal = Decimal("0")
    liquidity: Decimal | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def normalized(self) -> Edge:
        if not isinstance(self.metadata, dict):
            raise SnapshotError("edge metadata must be an object")
        # Convert numeric fields to Decimal for type safety
        rate_val = self.rate if isinstance(self.rate, Decimal) else Decimal(str(self.rate))
        fee_val = self.fee_bps if isinstance(self.fee_bps, Decimal) else Decimal(str(self.fee_bps))
        liq_val = None if self.liquidity is None else (
            self.liquidity if isinstance(self.liquidity, Decimal) else Decimal(str(self.liquidity))
        )
        return Edge(
            source=str(self.source).strip().upper(),
            target=str(self.target).strip().upper(),
            rate=rate_val,
            venue=str(self.venue).strip() or "unknown",
            fee_bps=fee_val,
            liquidity=liq_val,
            metadata=dict(self.metadata),
        )

    def effective_rate(self) -> Decimal:
        fee_multiplier = Decimal("1") - (self.fee_bps / BPS_DENOMINATOR)
        return self.rate * fee_multiplier

    def validate(self) -> None:
        edge = self.normalized()
        if not edge.source or not edge.target:
            raise SnapshotError("edge source and target are required")
        if len(edge.source) > MAX_ASSET_SYMBOL_LENGTH or len(edge.target) > MAX_ASSET_SYMBOL_LENGTH:
            raise SnapshotError("edge source and target must be 32 characters or fewer")
        if edge.source == edge.target:
            raise SnapshotError("edge source and target must differ")
        if len(edge.venue) > MAX_VENUE_LENGTH:
            raise SnapshotError("edge venue must be 80 characters or fewer")
        if not edge.rate.is_finite() or edge.rate <= 0:
            raise SnapshotError("edge rate must be a finite positive number")
        if not edge.fee_bps.is_finite() or edge.fee_bps < 0 or edge.fee_bps >= BPS_DENOMINATOR:
            raise SnapshotError("edge fee_bps must be a finite number in [0, 10000)")
        if edge.liquidity is not None and (not edge.liquidity.is_finite() or edge.liquidity < 0):
            raise SnapshotError("edge liquidity must be a finite non-negative number")


@dataclass(frozen=True)
class MarketSnapshot:
    """A point-in-time collection of exchange edges."""

    edges: tuple[Edge, ...]
    source: str = "local"
    network: str = "polygon"
    timestamp: str | None = None

    def normalized(self) -> MarketSnapshot:
        return MarketSnapshot(
            edges=tuple(edge.normalized() for edge in self.edges),
            source=(self.source or "local").strip(),
            network=(self.network or "polygon").strip().lower(),
            timestamp=self.timestamp,
        )

    def validate(self) -> None:
        if not self.edges:
            raise SnapshotError("market snapshot must contain at least one edge")
        if not isinstance(self.source, str) or not self.source.strip():
            raise SnapshotError("market snapshot source must be a non-empty string")
        if len(self.source.strip()) > MAX_SOURCE_LENGTH:
            raise SnapshotError(
                f"market snapshot source must be {MAX_SOURCE_LENGTH} characters or fewer"
            )
        if not isinstance(self.network, str) or not self.network.strip():
            raise SnapshotError("market snapshot network must be a non-empty string")
        if len(self.network.strip()) > MAX_NETWORK_LENGTH:
            raise SnapshotError(
                f"market snapshot network must be {MAX_NETWORK_LENGTH} characters or fewer"
            )
        if self.timestamp is not None:
            if not isinstance(self.timestamp, str):
                raise SnapshotError("market snapshot timestamp must be a string when provided")
            if not RFC3339_UTC_RE.fullmatch(self.timestamp):
                raise SnapshotError(
                    "market snapshot timestamp must use UTC RFC3339 form YYYY-MM-DDTHH:MM:SSZ"
                )
        for edge in self.edges:
            edge.validate()


@dataclass(frozen=True)
class RiskPolicy:
    """Conservative filters applied before an opportunity is reported.

    `max_notional` is a route capacity ceiling, not a trade recommendation.
    """

    min_profit_bps: Decimal = Decimal("5")
    max_hops: int = 4
    min_liquidity: Decimal = Decimal("0")
    max_notional: Decimal = Decimal("10000")
    max_results: int = 25

    def __post_init__(self) -> None:
        # Ensure Decimal fields are actually Decimal instances for type safety
        object.__setattr__(self, 'min_profit_bps', 
            self.min_profit_bps if isinstance(self.min_profit_bps, Decimal) else Decimal(str(self.min_profit_bps)))
        object.__setattr__(self, 'min_liquidity',
            self.min_liquidity if isinstance(self.min_liquidity, Decimal) else Decimal(str(self.min_liquidity)))
        object.__setattr__(self, 'max_notional',
            self.max_notional if isinstance(self.max_notional, Decimal) else Decimal(str(self.max_notional)))

    def validate(self) -> None:
        if not self.min_profit_bps.is_finite() or self.min_profit_bps < 0:
            raise PolicyError("min_profit_bps must be a finite non-negative number")
        if self.max_hops < 2:
            raise PolicyError("max_hops must be at least 2")
        if self.max_hops > MAX_REASONABLE_HOPS:
            raise PolicyError(f"max_hops must be at most {MAX_REASONABLE_HOPS}")
        if not self.min_liquidity.is_finite() or self.min_liquidity < 0:
            raise PolicyError("min_liquidity must be a finite non-negative number")
        if not self.max_notional.is_finite() or self.max_notional <= 0:
            raise PolicyError("max_notional must be a finite positive number")
        if self.max_results < 1:
            raise PolicyError("max_results must be at least 1")
        if self.max_results > MAX_REASONABLE_RESULTS:
            raise PolicyError(f"max_results must be at most {MAX_REASONABLE_RESULTS}")


@dataclass(frozen=True)
class Opportunity:
    """A discovered cycle after policy checks."""

    network: str
    path: tuple[str, ...]
    venues: tuple[str, ...]
    gross_return: Decimal
    profit_bps: Decimal
    limiting_liquidity: Decimal | None
    estimated_capacity: Decimal

    @property
    def is_profitable(self) -> bool:
        return self.profit_bps > 0
