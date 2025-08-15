"""
Data models for rubot
"""

from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from datetime import datetime
import json


@dataclass
class Announcement:
    """Municipal announcement data model"""

    title: str
    description: str
    category: str
    date: Optional[str] = None
    location: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "description": self.description,
            "category": self.category,
            "date": self.date,
            "location": self.location,
        }


@dataclass
class Event:
    """Municipal event data model"""

    title: str
    date: Optional[str] = None
    time: Optional[str] = None
    location: Optional[str] = None
    description: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "date": self.date,
            "time": self.time,
            "location": self.location,
            "description": self.description,
        }


@dataclass
class ImportantDate:
    """Important deadline data model"""

    description: str
    date: str
    details: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "description": self.description,
            "date": self.date,
            "details": self.details,
        }


@dataclass
class RathausUmschauAnalysis:
    """Complete analysis result data model"""

    summary: str
    announcements: List[Announcement]
    events: List[Event]
    important_dates: List[ImportantDate]
    processing_date: str
    source_date: str
    model_used: str

    def __post_init__(self) -> None:
        if not self.processing_date:
            self.processing_date = datetime.now().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "summary": self.summary,
            "announcements": [a.to_dict() for a in self.announcements],
            "events": [e.to_dict() for e in self.events],
            "important_dates": [d.to_dict() for d in self.important_dates],
            "processing_date": self.processing_date,
            "source_date": self.source_date,
            "model_used": self.model_used,
        }

    def to_json(self, indent: int = 2) -> str:
        """Convert to JSON string"""
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)

    @classmethod
    def from_llm_response(
        cls, response_text: str, source_date: str, model: str
    ) -> "RathausUmschauAnalysis":
        """
        Create analysis from LLM response.

        Args:
            response_text: JSON response from LLM (OpenRouter format)
            source_date: Date of source document
            model: Model used for analysis

        Returns:
            RathausUmschauAnalysis instance
        """
        try:
            # Parse OpenRouter response format
            openrouter_response = json.loads(response_text)

            # Extract the actual content from OpenRouter response
            if (
                "choices" in openrouter_response
                and openrouter_response["choices"]
            ):
                actual_content = openrouter_response["choices"][0]["message"][
                    "content"
                ]

                # Try to parse the content as JSON
                try:
                    data = json.loads(actual_content)
                    # Ensure data is a dictionary
                    if not isinstance(data, dict):
                        raise json.JSONDecodeError(
                            "Content is not a JSON object", actual_content, 0
                        )

                    # Parse announcements
                    announcements = []
                    for ann_data in data.get("announcements", []):
                        announcements.append(
                            Announcement(
                                title=ann_data.get("title", ""),
                                description=ann_data.get("description", ""),
                                category=ann_data.get("category", ""),
                                date=ann_data.get("date"),
                                location=ann_data.get("location"),
                            )
                        )

                    # Parse events
                    events = []
                    for event_data in data.get("events", []):
                        events.append(
                            Event(
                                title=event_data.get("title", ""),
                                date=event_data.get("date"),
                                time=event_data.get("time"),
                                location=event_data.get("location"),
                                description=event_data.get("description"),
                            )
                        )

                    # Parse important dates
                    important_dates = []
                    for date_data in data.get("important_dates", []):
                        important_dates.append(
                            ImportantDate(
                                description=date_data.get("description", ""),
                                date=date_data.get("date", ""),
                                details=date_data.get("details"),
                            )
                        )

                    return cls(
                        summary=data.get("summary", ""),
                        announcements=announcements,
                        events=events,
                        important_dates=important_dates,
                        processing_date=datetime.now().isoformat(),
                        source_date=source_date,
                        model_used=model,
                    )

                except json.JSONDecodeError:
                    # Content is not JSON, treat as summary
                    return cls(
                        summary=(
                            actual_content[:500] + "..."
                            if len(actual_content) > 500
                            else actual_content
                        ),
                        announcements=[],
                        events=[],
                        important_dates=[],
                        processing_date=datetime.now().isoformat(),
                        source_date=source_date,
                        model_used=model,
                    )
            else:
                # No choices in response, use raw response as summary
                return cls(
                    summary=(
                        response_text[:500] + "..."
                        if len(response_text) > 500
                        else response_text
                    ),
                    announcements=[],
                    events=[],
                    important_dates=[],
                    processing_date=datetime.now().isoformat(),
                    source_date=source_date,
                    model_used=model,
                )

        except json.JSONDecodeError:
            # Fallback for non-JSON responses
            return cls(
                summary=(
                    response_text[:500] + "..."
                    if len(response_text) > 500
                    else response_text
                ),
                announcements=[],
                events=[],
                important_dates=[],
                processing_date=datetime.now().isoformat(),
                source_date=source_date,
                model_used=model,
            )
