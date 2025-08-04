"""
Tests for models module
"""

import pytest
import json
from datetime import datetime
from unittest.mock import patch

from rubot.models import Announcement, Event, ImportantDate, RathausUmschauAnalysis


class TestModels:

    def test_announcement_creation(self):
        """Test Announcement model creation"""
        ann = Announcement(
            title="Test Announcement",
            description="Test description",
            category="test",
            date="2024-01-15",
            location="Munich",
        )

        assert ann.title == "Test Announcement"
        assert ann.description == "Test description"
        assert ann.category == "test"
        assert ann.date == "2024-01-15"
        assert ann.location == "Munich"

    def test_announcement_to_dict(self):
        """Test Announcement to_dict method"""
        ann = Announcement(title="Test", description="Desc", category="cat")

        result = ann.to_dict()
        expected = {
            "title": "Test",
            "description": "Desc",
            "category": "cat",
            "date": None,
            "location": None,
        }

        assert result == expected

    def test_event_creation(self):
        """Test Event model creation"""
        event = Event(
            title="Test Event",
            date="2024-01-15",
            time="14:00",
            location="City Hall",
            description="Test event description",
        )

        assert event.title == "Test Event"
        assert event.date == "2024-01-15"
        assert event.time == "14:00"
        assert event.location == "City Hall"
        assert event.description == "Test event description"
        
    def test_event_to_dict(self):
        """Test Event to_dict method"""
        event = Event(
            title="Test Event",
            date="2024-01-15",
            time="14:00",
            location="City Hall",
            description="Test event description",
        )
        
        result = event.to_dict()
        expected = {
            "title": "Test Event",
            "date": "2024-01-15",
            "time": "14:00",
            "location": "City Hall",
            "description": "Test event description",
        }
        
        assert result == expected
        
    def test_event_with_minimal_fields(self):
        """Test Event with only required fields"""
        event = Event(title="Minimal Event")
        
        assert event.title == "Minimal Event"
        assert event.date is None
        assert event.time is None
        assert event.location is None
        assert event.description is None

    def test_important_date_creation(self):
        """Test ImportantDate model creation"""
        imp_date = ImportantDate(
            description="Application deadline",
            date="2024-01-31",
            details="Submit by 5 PM",
        )

        assert imp_date.description == "Application deadline"
        assert imp_date.date == "2024-01-31"
        assert imp_date.details == "Submit by 5 PM"
        
    def test_important_date_to_dict(self):
        """Test ImportantDate to_dict method"""
        imp_date = ImportantDate(
            description="Application deadline",
            date="2024-01-31",
            details="Submit by 5 PM",
        )
        
        result = imp_date.to_dict()
        expected = {
            "description": "Application deadline",
            "date": "2024-01-31",
            "details": "Submit by 5 PM",
        }
        
        assert result == expected
        
    def test_important_date_without_details(self):
        """Test ImportantDate without optional details"""
        imp_date = ImportantDate(description="Deadline", date="2024-02-01")
        
        assert imp_date.description == "Deadline"
        assert imp_date.date == "2024-02-01"
        assert imp_date.details is None

    def test_rathaus_umschau_analysis_creation(self):
        """Test RathausUmschauAnalysis model creation"""
        announcements = [
            Announcement("Ann 1", "Desc 1", "cat1"),
            Announcement("Ann 2", "Desc 2", "cat2"),
        ]
        events = [Event("Event 1", "2024-01-15")]
        important_dates = [ImportantDate("Deadline", "2024-01-31")]

        analysis = RathausUmschauAnalysis(
            summary="Test summary",
            announcements=announcements,
            events=events,
            important_dates=important_dates,
            processing_date="2024-01-15T10:00:00",
            source_date="2024-01-15",
            model_used="test-model",
        )

        assert analysis.summary == "Test summary"
        assert len(analysis.announcements) == 2
        assert len(analysis.events) == 1
        assert len(analysis.important_dates) == 1
        assert analysis.source_date == "2024-01-15"
        assert analysis.model_used == "test-model"
        
    def test_rathaus_umschau_analysis_post_init(self):
        """Test RathausUmschauAnalysis __post_init__ method"""
        with patch('rubot.models.datetime') as mock_datetime:
            mock_datetime.now.return_value = datetime(2024, 1, 15, 12, 0, 0)
            mock_datetime.isoformat = datetime.isoformat
            
            # Create analysis without processing_date
            analysis = RathausUmschauAnalysis(
                summary="Test",
                announcements=[],
                events=[],
                important_dates=[],
                processing_date="",  # Empty processing_date
                source_date="2024-01-15",
                model_used="test-model",
            )
            
            # Should be set by __post_init__
            assert analysis.processing_date == "2024-01-15T12:00:00"

    def test_rathaus_umschau_analysis_to_dict(self):
        """Test RathausUmschauAnalysis to_dict method"""
        announcements = [
            Announcement("Ann 1", "Desc 1", "cat1"),
            Announcement("Ann 2", "Desc 2", "cat2"),
        ]
        events = [Event("Event 1", "2024-01-15")]
        important_dates = [ImportantDate("Deadline", "2024-01-31")]
        
        analysis = RathausUmschauAnalysis(
            summary="Test summary",
            announcements=announcements,
            events=events,
            important_dates=important_dates,
            processing_date="2024-01-15T10:00:00",
            source_date="2024-01-15",
            model_used="test-model",
        )
        
        result = analysis.to_dict()
        
        assert result["summary"] == "Test summary"
        assert len(result["announcements"]) == 2
        assert result["announcements"][0]["title"] == "Ann 1"
        assert result["announcements"][1]["title"] == "Ann 2"
        assert len(result["events"]) == 1
        assert result["events"][0]["title"] == "Event 1"
        assert len(result["important_dates"]) == 1
        assert result["important_dates"][0]["description"] == "Deadline"
        assert result["source_date"] == "2024-01-15"
        assert result["model_used"] == "test-model"

    def test_rathaus_umschau_analysis_to_json(self):
        """Test RathausUmschauAnalysis to_json method"""
        analysis = RathausUmschauAnalysis(
            summary="Test",
            announcements=[],
            events=[],
            important_dates=[],
            processing_date="2024-01-15T10:00:00",
            source_date="2024-01-15",
            model_used="test-model",
        )

        json_str = analysis.to_json()
        parsed = json.loads(json_str)

        assert parsed["summary"] == "Test"
        assert parsed["announcements"] == []
        assert parsed["source_date"] == "2024-01-15"
        assert parsed["model_used"] == "test-model"
        
    def test_rathaus_umschau_analysis_to_json_with_indent(self):
        """Test RathausUmschauAnalysis to_json method with custom indent"""
        analysis = RathausUmschauAnalysis(
            summary="Test",
            announcements=[],
            events=[],
            important_dates=[],
            processing_date="2024-01-15T10:00:00",
            source_date="2024-01-15",
            model_used="test-model",
        )
        
        # Test with custom indent
        json_str = analysis.to_json(indent=4)
        
        # Ensure it's valid JSON
        parsed = json.loads(json_str)
        assert parsed["summary"] == "Test"
        
        # Check indentation (basic check)
        lines = json_str.split("\n")
        if len(lines) > 1:  # Has newlines with indentation
            assert lines[1].startswith("    ")  # 4 spaces

    def test_from_llm_response_valid_json(self):
        """Test creating analysis from valid LLM JSON response"""
        # Create OpenRouter format response
        content_data = {
            "summary": "Test summary",
            "announcements": [
                {
                    "title": "Test Ann",
                    "description": "Test desc",
                    "category": "test",
                    "date": "2024-01-15",
                }
            ],
            "events": [
                {"title": "Test Event", "date": "2024-01-16", "location": "Munich"}
            ],
            "important_dates": [{"description": "Test deadline", "date": "2024-01-31"}],
        }

        openrouter_response = {
            "choices": [{"message": {"content": json.dumps(content_data)}}]
        }
        llm_response = json.dumps(openrouter_response)

        analysis = RathausUmschauAnalysis.from_llm_response(
            llm_response, "2024-01-15", "test-model"
        )

        assert analysis.summary == "Test summary"
        assert len(analysis.announcements) == 1
        assert analysis.announcements[0].title == "Test Ann"
        assert len(analysis.events) == 1
        assert analysis.events[0].title == "Test Event"
        assert len(analysis.important_dates) == 1
        assert analysis.important_dates[0].description == "Test deadline"

    def test_from_llm_response_invalid_json(self):
        """Test creating analysis from invalid JSON response"""
        llm_response = "This is not valid JSON"

        analysis = RathausUmschauAnalysis.from_llm_response(
            llm_response, "2024-01-15", "test-model"
        )

        assert "This is not valid JSON" in analysis.summary
        assert len(analysis.announcements) == 0
        assert len(analysis.events) == 0
        assert len(analysis.important_dates) == 0
        assert analysis.source_date == "2024-01-15"
        assert analysis.model_used == "test-model"
        
    def test_from_llm_response_content_not_json(self):
        """Test creating analysis from LLM response where content is not JSON"""
        # Create OpenRouter format response where content is not JSON
        openrouter_response = {
            "choices": [{"message": {"content": "This is not JSON content"}}]
        }
        llm_response = json.dumps(openrouter_response)
        
        analysis = RathausUmschauAnalysis.from_llm_response(
            llm_response, "2024-01-15", "test-model"
        )
        
        assert "This is not JSON content" in analysis.summary
        assert len(analysis.announcements) == 0
        assert len(analysis.events) == 0
        assert len(analysis.important_dates) == 0
        
    def test_from_llm_response_content_not_dict(self):
        """Test creating analysis from LLM response where JSON content is not a dict"""
        # Create OpenRouter format response where content is JSON array, not object
        openrouter_response = {
            "choices": [{"message": {"content": json.dumps(["item1", "item2"])}}]
        }
        llm_response = json.dumps(openrouter_response)
        
        analysis = RathausUmschauAnalysis.from_llm_response(
            llm_response, "2024-01-15", "test-model"
        )
        
        # Should handle this gracefully
        assert len(analysis.announcements) == 0
        assert len(analysis.events) == 0
        assert len(analysis.important_dates) == 0
        
    def test_from_llm_response_no_choices(self):
        """Test creating analysis from LLM response with no choices"""
        # Create OpenRouter format response with no choices
        openrouter_response = {"id": "test", "object": "chat.completion"}
        llm_response = json.dumps(openrouter_response)
        
        analysis = RathausUmschauAnalysis.from_llm_response(
            llm_response, "2024-01-15", "test-model"
        )
        
        # Should use raw response as summary
        assert json.dumps(openrouter_response) in analysis.summary
        assert len(analysis.announcements) == 0
        assert len(analysis.events) == 0
        assert len(analysis.important_dates) == 0
        
    def test_from_llm_response_missing_fields(self):
        """Test creating analysis from LLM response with missing fields"""
        # Create content with missing fields
        content_data = {
            "summary": "Test summary",
            # Missing announcements
            "events": [{"title": "Test Event"}],  # Minimal event data
            # Missing important_dates
        }
        
        openrouter_response = {
            "choices": [{"message": {"content": json.dumps(content_data)}}]
        }
        llm_response = json.dumps(openrouter_response)
        
        analysis = RathausUmschauAnalysis.from_llm_response(
            llm_response, "2024-01-15", "test-model"
        )
        
        assert analysis.summary == "Test summary"
        assert len(analysis.announcements) == 0  # Missing in input
        assert len(analysis.events) == 1
        assert analysis.events[0].title == "Test Event"
        assert len(analysis.important_dates) == 0  # Missing in input
        
    def test_from_llm_response_truncate_long_summary(self):
        """Test summary truncation for non-JSON responses"""
        # Create a very long text response
        long_text = "A" * 1000  # 1000 characters
        
        analysis = RathausUmschauAnalysis.from_llm_response(
            long_text, "2024-01-15", "test-model"
        )
        
        # Summary should be truncated to 500 chars + "..."
        assert len(analysis.summary) == 503
        assert analysis.summary.endswith("...")
