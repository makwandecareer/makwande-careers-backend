from __future__ import annotations

from collections import defaultdict
from dataclasses import asdict, dataclass
from typing import Iterable

from fastapi import FastAPI
from fastapi.routing import APIRoute


@dataclass(frozen=True)
class RouteCollision:
    method: str
    path: str
    endpoint_names: tuple[str, ...]


def find_route_collisions(app: FastAPI) -> list[RouteCollision]:
    """Return duplicate HTTP method/path registrations without removing routes."""
    registered: dict[tuple[str, str], list[str]] = defaultdict(list)

    for route in app.routes:
        if not isinstance(route, APIRoute):
            continue

        endpoint_name = getattr(route.endpoint, "__qualname__", route.name)
        module_name = getattr(route.endpoint, "__module__", "unknown")
        endpoint_label = f"{module_name}.{endpoint_name}"

        for method in sorted(route.methods or set()):
            if method in {"HEAD", "OPTIONS"}:
                continue
            registered[(method, route.path)].append(endpoint_label)

    collisions: list[RouteCollision] = []
    for (method, path), endpoint_names in sorted(registered.items()):
        unique_names = tuple(dict.fromkeys(endpoint_names))
        if len(unique_names) > 1:
            collisions.append(
                RouteCollision(
                    method=method,
                    path=path,
                    endpoint_names=unique_names,
                )
            )

    return collisions


def collision_payload(collisions: Iterable[RouteCollision]) -> list[dict[str, object]]:
    return [asdict(collision) for collision in collisions]
