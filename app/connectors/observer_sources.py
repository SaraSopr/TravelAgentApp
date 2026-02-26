from datetime import UTC, datetime, timedelta

import httpx

from app.core.config import Settings
from app.domain.models import ThreatEvent


class ObserverSources:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    async def collect(self, city: str) -> list[ThreatEvent]:
        async with httpx.AsyncClient(timeout=5.0) as client:
            news = await self._fetch_news(client, city)
            transit = await self._fetch_transit(client, city)
            social = await self._fetch_social(client, city)
        events = news + transit + social
        return events[: self._settings.observer_max_events_per_cycle]

    async def _fetch_news(self, client: httpx.AsyncClient, city: str) -> list[ThreatEvent]:
        if not self._settings.news_api_key:
            return []
        params = {
            "q": f"{city} strike protest incident transport",
            "language": "en",
            "pageSize": 5,
            "apiKey": self._settings.news_api_key,
        }
        response = await client.get(self._settings.news_api_url, params=params)
        if response.status_code >= 400:
            return []
        data = response.json()
        now = datetime.now(UTC)
        normalized: list[ThreatEvent] = []
        for article in data.get("articles", [])[:5]:
            text = f"{article.get('title', '')} {article.get('description', '')}".lower()
            if not _is_relevant(text):
                continue
            normalized.append(
                ThreatEvent(
                    city=city,
                    category="news_alert",
                    severity=0.55,
                    confidence=0.65,
                    description=article.get("title", "News alert"),
                    location={"lat": 45.4642, "lon": 9.1900},
                    starts_at=now + timedelta(minutes=20),
                    ends_at=now + timedelta(hours=4),
                    source="official_news",
                )
            )
        return normalized

    async def _fetch_transit(self, client: httpx.AsyncClient, city: str) -> list[ThreatEvent]:
        if not self._settings.transit_alerts_url:
            return []
        response = await client.get(self._settings.transit_alerts_url, params={"city": city})
        if response.status_code >= 400:
            return []
        data = response.json()
        now = datetime.now(UTC)
        normalized: list[ThreatEvent] = []
        for item in data.get("alerts", [])[:5]:
            normalized.append(
                ThreatEvent(
                    city=city,
                    category=item.get("category", "transit_disruption"),
                    severity=float(item.get("severity", 0.8)),
                    confidence=float(item.get("confidence", 0.9)),
                    description=item.get("description", "Transit disruption"),
                    location={"lat": float(item.get("lat", 45.4642)), "lon": float(item.get("lon", 9.1900))},
                    starts_at=now + timedelta(minutes=10),
                    ends_at=now + timedelta(hours=2),
                    source="transit",
                )
            )
        return normalized

    async def _fetch_social(self, client: httpx.AsyncClient, city: str) -> list[ThreatEvent]:
        if not self._settings.social_signals_url:
            return []
        response = await client.get(self._settings.social_signals_url, params={"city": city})
        if response.status_code >= 400:
            return []
        data = response.json()
        now = datetime.now(UTC)
        normalized: list[ThreatEvent] = []
        for post in data.get("signals", [])[:10]:
            text = str(post.get("text", "")).lower()
            if not _is_relevant(text):
                continue
            normalized.append(
                ThreatEvent(
                    city=city,
                    category="social_signal",
                    severity=float(post.get("severity", 0.45)),
                    confidence=float(post.get("confidence", 0.5)),
                    description=post.get("text", "Potential disruption"),
                    location={"lat": float(post.get("lat", 45.4642)), "lon": float(post.get("lon", 9.1900))},
                    starts_at=now + timedelta(minutes=30),
                    ends_at=now + timedelta(hours=2),
                    source="social",
                )
            )
        return normalized


def _is_relevant(text: str) -> bool:
    keywords = ("strike", "protest", "incident", "accident", "closed", "disruption", "blocked")
    return any(keyword in text for keyword in keywords)
