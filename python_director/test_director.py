import os
import json
import pytest
from unittest.mock import patch, MagicMock
from director import generate_story, upload_to_firestore

# Sample structured output mock response
mock_story_data = {
    "story_title": "Test Story Title",
    "journals": [
        {"title": "Day 1", "body": "It begins.", "time_offset_minutes": 10}
    ],
    "chats": [
        {"senderId": "Unknown", "text": "Are you alone?", "isProtagonist": False, "time_offset_minutes": 15}
    ],
    "emails": [
        {"sender": "boss@firm.com", "subject": "Meeting", "body": "See me.", "time_offset_minutes": 20}
    ],
    "receipts": [
        {"merchantName": "Cafe", "amount": 4.5, "description": "Coffee", "time_offset_minutes": 30}
    ]
}

class MockResponse:
    def __init__(self, text):
        self.text = text

@patch('director.client')
def test_generate_story_success(mock_client):
    # Setup mock to return valid JSON matching our schema
    mock_generate = MagicMock()
    mock_generate.return_value = MockResponse(json.dumps(mock_story_data))
    mock_client.models.generate_content = mock_generate

    story = generate_story()

    assert story is not None
    assert story['story_title'] == "Test Story Title"
    assert len(story['journals']) == 1
    assert story['journals'][0]['title'] == "Day 1"
    assert len(story['chats']) == 1
    assert story['chats'][0]['senderId'] == "Unknown"

@patch('director.client')
def test_generate_story_failure(mock_client):
    # Setup mock to raise an exception
    mock_client.models.generate_content.side_effect = Exception("API Error")

    story = generate_story()

    assert story is None

@patch('director.db')
def test_upload_to_firestore(mock_db):
    # Setup mock firestore batch and references
    mock_batch = MagicMock()
    mock_db.batch.return_value = mock_batch
    
    mock_col = MagicMock()
    mock_doc = MagicMock()
    mock_db.collection.return_value = mock_col
    mock_col.document.return_value = mock_doc
    
    mock_story_ref = MagicMock()
    mock_col.document.return_value = mock_story_ref
    
    # Run the function
    story_id = upload_to_firestore(mock_story_data)
    
    assert story_id is not None
    assert story_id.startswith("story_")
    
    # Check if batch.set was called correctly
    # 1 journal + 1 chat + 1 email + 1 receipt = 4 subcollection items
    assert mock_batch.set.call_count == 4
    assert mock_batch.commit.called
