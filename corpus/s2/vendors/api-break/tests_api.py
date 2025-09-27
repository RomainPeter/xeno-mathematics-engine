#!/usr/bin/env python3
"""
API compatibility tests for api-break scenario
"""

import pytest
import requests


class TestAPICompatibility:
    """Test API compatibility before and after breaking changes"""

    def test_api_v1_compatibility(self):
        """Test that API v1 still works with old clients"""
        # This should work - old clients don't send email_verification_token
        payload = {"name": "John Doe", "email": "john@example.com"}

        # Simulate v1 client call
        response = requests.post(
            "http://localhost:5000/api/v1/users", json=payload, timeout=5
        )

        # Should succeed for v1
        assert response.status_code == 201
        data = response.json()
        assert "id" in data
        assert data["name"] == "John Doe"
        assert data["email"] == "john@example.com"

    def test_api_v2_new_requirements(self):
        """Test that API v2 requires new parameters"""
        # This should fail - missing email_verification_token
        payload = {"name": "John Doe", "email": "john@example.com"}

        response = requests.post(
            "http://localhost:5000/api/v2/users", json=payload, timeout=5
        )

        # Should fail for v2 without token
        assert response.status_code == 400
        data = response.json()
        assert "Missing required field: email_verification_token" in data["error"]

    def test_api_v2_with_token(self):
        """Test that API v2 works with new parameters"""
        # This should work - includes email_verification_token
        payload = {
            "name": "John Doe",
            "email": "john@example.com",
            "email_verification_token": "token123",
        }

        response = requests.post(
            "http://localhost:5000/api/v2/users", json=payload, timeout=5
        )

        # Should succeed for v2
        assert response.status_code == 201
        data = response.json()
        assert "id" in data
        assert data["name"] == "John Doe"
        assert data["email"] == "john@example.com"
        assert data["email_verification_token"] == "token123"


if __name__ == "__main__":
    pytest.main([__file__])
