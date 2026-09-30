"""Minimal candidate-preservation guard for ordinary transitions (Python 3.10+).

Evidence validity and compatibility are supplied by the caller. No model API,
action execution, authorization policy, or persistent storage is included.
"""

from dataclasses import dataclass
from typing import Iterable


def _ids(values: Iterable[str]) -> frozenset[str]:
    if isinstance(values, (str, bytes)):
        raise ValueError("Use a collection of IDs, not a single string.")
    result = frozenset(values)
    if any(not isinstance(x, str) or not x.strip() for x in result):
        raise ValueError("IDs must be non-empty strings.")
    return result


@dataclass(frozen=True)
class MAnchor:
    omega: frozenset[str]
    candidates: frozenset[str] | None = None

    def __post_init__(self):
        omega = _ids(self.omega)
        candidates = omega if self.candidates is None else _ids(self.candidates)
        if not omega or not candidates <= omega:
            raise ValueError("Need non-empty omega and candidates within omega.")
        object.__setattr__(self, "omega", omega)
        object.__setattr__(self, "candidates", candidates)

    def step(
        self, action: str, reason: str, *,
        evidence: Iterable[str] = (),
        compatible: Iterable[str] | None = None,
        map_version: str | None = None,
        proposed: Iterable[str] | None = None,
    ) -> tuple["MAnchor", dict]:
        """Return (new state, JSON-ready record); raise before any state change.

        evidence: IDs of accepted, currently valid records applied at this step.
        compatible: M(D), supplied by the test harness or evidence interpreter.
        proposed: optional candidate set to check; default is full incorporation.
        """
        if not all(isinstance(x, str) and x.strip() for x in (action, reason)):
            raise ValueError("Action and its reason must be non-empty strings.")
        basis = _ids(evidence)
        if not basis:
            if compatible is not None or map_version is not None:
                raise ValueError("A compatibility interpretation needs an evidence basis.")
            allowed, version = self.omega, "empty-basis-identity/v1"
        else:
            if compatible is None or not isinstance(map_version, str) or not map_version.strip():
                raise ValueError("Applied evidence needs compatible and map_version.")
            allowed, version = _ids(compatible), map_version
            if not allowed <= self.omega:
                raise ValueError("Compatibility result is outside omega.")
        before = self.candidates
        after = before & allowed if proposed is None else _ids(proposed)
        if not after <= before:
            raise ValueError("Ordinary transitions cannot add or restore candidates.")
        removed = before - after
        unsupported = removed & allowed
        if unsupported:
            raise ValueError(f"Unsupported removal: {sorted(unsupported)}")
        record = {
            "action": {
                "candidates": sorted(before), "value": action, "reason": reason,
            },
            "audit": {
                "before": sorted(before), "after": sorted(after),
                "removed": sorted(removed), "evidence": sorted(basis),
                "map_version": version, "compatible": sorted(allowed),
            },
        }
        return MAnchor(self.omega, after), record
