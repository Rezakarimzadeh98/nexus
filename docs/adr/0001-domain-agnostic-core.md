# ADR 0001 — Domain-agnostic core concepts

## Status

Accepted

## Context

NEXUS must serve multiple domains without rewriting the engine. Early demos tempt domain-specific schemas (e.g. only “tickers” or only “units”).

## Decision

All pipelines persist and compute against a fixed core vocabulary: Observation, Entity, Event, Relationship, State, Signal, Pattern, Forecast, Evidence, Outcome. Domains plug in via adapters that map vocabulary and source configs.

## Consequences

- Slower first demo than a hard-coded news app, but one evaluation story for all domains
- Adapters own ontologies; core stays stable across semver minor versions
- Defense/finance/cyber modules cannot bypass evidence and evaluation contracts
