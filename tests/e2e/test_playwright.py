import pytest
from playwright.sync_api import Page, expect
import os
import time

class TestE2ECalculatorApp:
    """End-to-end tests for the Calculator web application."""
    
    BASE_URL = "http://localhost:8000"
    
    TEST_USER = {
        "username": "testuser_e2e_simple",
        "email": "testuser_e2e_simple@example.com",
        "first_name": "Test",
        "last_name": "User",
        "password": "TestPassword123!",
        "confirm_password": "TestPassword123!"
    }
    
    def test_homepage_loads(self, page: Page):
        """Test that the homepage loads correctly."""
        page.goto(self.BASE_URL)
        
        # Check page title
        expect(page).to_have_title("Home")
        
        # Check welcome message
        expect(page.locator("h1")).to_contain_text("Welcome to the Calculations App")
        # Be more specific with the paragraph selector
        expect(page.locator("p").first).to_contain_text("A simple yet powerful way to perform, store, and manage your calculations")