"""
Tests for models module
"""

import pytest
import json
from datetime import datetime

from rubot.models import Announcement, Event, ImportantDate, RathausUmschauAnalysis


class TestModels:
    
    def test_announcement_creation(self):
        """Test Announcement model creation"""
        ann = Announcement(
            title="Test Announcement",
            description="Test description",
            category="test",
            date="2024-01-15",
            location="Munich"
        )
        
        assert ann.title == "Test Announcement"
        assert ann.description == "Test description"
        assert ann.category == "test"
        assert ann.date == "2024-01-15"
        assert ann.location == "Munich"
    
    def test_announcement_to_dict(self):
        """Test Announcement to_dict method"""
        ann = Announcement(
            title="Test",
            description="Desc",
            category="cat"
        )
        
        result = ann.to_dict()
        expected = {
            'title': 'Test',
            'description': 'Desc',
            'category': 'cat',
            'date': None,
            'location': None
        }
        
        assert result == expected
    
    def test_event_creation(self):
        """Test Event model creation"""
        event = Event(
            title="Test Event",
            date="2024-01-15",
            time="14:00",
            location="City Hall",
            description="Test event description"
        )
        
        assert event.title == "Test Event"
        assert event.date == "2024-01-15"
        assert event.time == "14:00"
        assert event.location == "City Hall"
        assert event.description == "Test event description"
    
    def test_important_date_creation(self):
        """Test ImportantDate model creation"""
        imp_date = ImportantDate(
            description="Application deadline",
            date="2024-01-31",
            details="Submit by 5 PM"
        )
        
        assert imp_date.description == "Application deadline"
        assert imp_date.date == "2024-01-31"
        assert imp_date.details == "Submit by 5 PM"
    
    def test_rathaus_umschau_analysis_creation(self):
        """Test RathausUmschauAnalysis model creation"""
        announcements = [
            Announcement("Ann 1", "Desc 1", "cat1"),
            Announcement("Ann 2", "Desc 2", "cat2")
        ]
        events = [
            Event("Event 1", "2024-01-15")
        ]
        important_dates = [
            ImportantDate("Deadline", "2024-01-31")
        ]
        
        analysis = RathausUmschauAnalysis(
            summary="Test summary",
            announcements=announcements,
            events=events,
            important_dates=important_dates,
            processing_date="2024-01-15T10:00:00",
            source_date="2024-01-15",
            model_used="test-model"
        )
        
        assert analysis.summary == "Test summary"
        assert len(analysis.announcements) == 2
        assert len(analysis.events) == 1
        assert len(analysis.important_dates) == 1
        assert analysis.source_date == "2024-01-15"
        assert analysis.model_used == "test-model"
    
    def test_rathaus_umschau_analysis_to_json(self):
        """Test RathausUmschauAnalysis to_json method"""
        analysis = RathausUmschauAnalysis(
            summary="Test",
            announcements=[],
            events=[],
            important_dates=[],
            processing_date="2024-01-15T10:00:00",
            source_date="2024-01-15",
            model_used="test-model"
        )
        
        json_str = analysis.to_json()
        parsed = json.loads(json_str)
        
        assert parsed['summary'] == "Test"
        assert parsed['announcements'] == []
        assert parsed['source_date'] == "2024-01-15"
        assert parsed['model_used'] == "test-model"
    
    def test_from_llm_response_valid_json(self):
        """Test creating analysis from valid LLM JSON response"""
        llm_response = json.dumps({
            "summary": "Test summary",
            "announcements": [
                {
                    "title": "Test Ann",
                    "description": "Test desc",
                    "category": "test",
                    "date": "2024-01-15"
                }
            ],
            "events": [
                {
                    "title": "Test Event",
                    "date": "2024-01-16",
                    "location": "Munich"
                }
            ],
            "important_dates": [
                {
                    "description": "Test deadline",
                    "date": "2024-01-31"
                }
            ]
        })
        
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