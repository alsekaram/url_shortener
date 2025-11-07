"""Pydantic models for data validation."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, HttpUrl


class LinkCreate(BaseModel):
    """Model for creating a new link."""

    short_code: str
    target_url: str
    title: Optional[str] = None


class LinkUpdate(BaseModel):
    """Model for updating a link."""

    target_url: str


class Link(BaseModel):
    """Model representing a link."""

    id: int
    short_code: str
    target_url: str
    title: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class Click(BaseModel):
    """Model representing a click event."""

    id: int
    link_id: int
    clicked_at: datetime
    user_agent: Optional[str] = None
    ip_address: Optional[str] = None
    referer: Optional[str] = None


class LinkStats(BaseModel):
    """Model for link statistics."""

    short_code: str
    title: Optional[str] = None
    clicks_period: int
    total_clicks: int
    avg_per_day: float
    change_percent: Optional[float] = None


class DailyReport(BaseModel):
    """Model for daily report data."""

    date: str
    total_clicks: int
    links: list[LinkStats]


class WeeklyReport(BaseModel):
    """Model for weekly report data."""

    start_date: str
    end_date: str
    total_clicks: int
    top_links: list[LinkStats]


