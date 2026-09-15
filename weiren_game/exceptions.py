"""Shared exception types for the rules engine."""


class RuleViolation(ValueError):
    """Raised when a requested player action is not legal."""
