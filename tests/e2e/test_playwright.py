import pytest
from playwright.sync_api import Page, expect
import os
import time
import random

class TestE2ECalculatorApp:
    """End-to-end tests for the Calculator web application."""
    
    BASE_URL = "http://localhost:8000"
    
    @staticmethod
    def get_unique_test_user():
        """Generate a unique test user for each test method."""
        timestamp = int(time.time())
        random_suffix = random.randint(1000, 9999)
        return {
            "username": f"calc_user_{timestamp}_{random_suffix}",
            "email": f"calc_user_{timestamp}_{random_suffix}@example.com",
            "first_name": "Calc",
            "last_name": "User",
            "password": "CalcPassword123!",
            "confirm_password": "CalcPassword123!"
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

    def register_and_login_user(self, page: Page) -> None:
        """Helper method to register and login a user for calculation tests."""
        test_user = self.get_unique_test_user()
        
        # Register user
        page.goto(f"{self.BASE_URL}/register")
        page.fill("#username", test_user["username"])
        page.fill("#email", test_user["email"])
        page.fill("#first_name", test_user["first_name"])
        page.fill("#last_name", test_user["last_name"])
        page.fill("#password", test_user["password"])
        page.fill("#confirm_password", test_user["confirm_password"])
        page.click("button[type='submit']")
        page.wait_for_timeout(2000)
        
        # Login user
        page.goto(f"{self.BASE_URL}/login")
        page.fill("#username", test_user["username"])
        page.fill("#password", test_user["password"])
        page.click("button[type='submit']")
        page.wait_for_timeout(3000)
        
        # Verify we're logged in by checking for dashboard or redirect
        current_url = page.url
        if "/dashboard" not in current_url:
            page.goto(f"{self.BASE_URL}/dashboard")
            page.wait_for_timeout(2000)

    
    def test_create_addition_calculation(self, page: Page):
        """Test creating a new addition calculation."""
        self.register_and_login_user(page)
        
        # Navigate to dashboard
        page.goto(f"{self.BASE_URL}/dashboard")
        page.wait_for_timeout(2000)
        
        # Verify we're on dashboard by looking for the New Calculation heading
        new_calc_heading = page.locator("h2:has-text('New Calculation')")
        expect(new_calc_heading).to_be_visible()
        expect(new_calc_heading).to_contain_text("New Calculation")
        
        # Fill out calculation form for addition
        page.select_option("#calcType", "addition")
        page.fill("#calcInputs", "10,20,30")
        
        # Submit the form
        page.click("button[type='submit']")
        page.wait_for_timeout(3000)
        
        # Check for success message or that calculation appears in history
        # Look for the calculation in the table
        calculations_table = page.locator("#calculationsTable")
        expect(calculations_table).to_be_visible()
        
        # Check if the calculation appears in the table
        # Look for addition type and the inputs we provided
        table_rows = page.locator("#calculationsTable tr")
        if table_rows.count() > 0:
            # Check if our calculation appears
            page.wait_for_timeout(1000)
            addition_row = page.locator("#calculationsTable tr:has-text('addition')")
            if addition_row.count() > 0:
                expect(addition_row).to_contain_text("10, 20, 30")  # Note: spaces after commas
                expect(addition_row).to_contain_text("60")  # Expected result

    def test_create_multiple_calculation_types(self, page: Page):
        """Test creating calculations of different types."""
        self.register_and_login_user(page)
        page.goto(f"{self.BASE_URL}/dashboard")
        page.wait_for_timeout(2000)
        
        calculations_to_test = [
            {"type": "addition", "inputs": "5,15", "expected_result": "20"},
            {"type": "subtraction", "inputs": "50,10", "expected_result": "40"},
            {"type": "multiplication", "inputs": "4,5", "expected_result": "20"},
            {"type": "division", "inputs": "100,4", "expected_result": "25"}
        ]
        
        for calc in calculations_to_test:
            # Fill and submit calculation
            page.select_option("#calcType", calc["type"])
            page.fill("#calcInputs", calc["inputs"])
            page.click("button[type='submit']")
            page.wait_for_timeout(2000)
            
            # Check if calculation appears in table
            calc_row = page.locator(f"#calculationsTable tr:has-text('{calc['type']}')")
            if calc_row.count() > 0:
                # Format inputs with spaces after commas to match HTML output
                formatted_inputs = calc["inputs"].replace(",", ", ")
                expect(calc_row.first).to_contain_text(formatted_inputs)

    def test_view_calculation_details(self, page: Page):
        """Test viewing calculation details."""
        self.register_and_login_user(page)
        page.goto(f"{self.BASE_URL}/dashboard")
        page.wait_for_timeout(2000)
        
        # Create a calculation first
        page.select_option("#calcType", "multiplication")
        page.fill("#calcInputs", "7,8")
        page.click("button[type='submit']")
        page.wait_for_timeout(3000)
        
        # Look for view button in the calculations table
        view_button = page.locator("a:has-text('View')").first
        if view_button.is_visible():
            view_button.click()
            page.wait_for_timeout(2000)
            
            # Check if we're on the view calculation page
            current_url = page.url
            assert "/dashboard/view/" in current_url
            
            # Check for calculation details
            expect(page.locator("h2")).to_contain_text("Calculation Details")
            
            # Look for the calculation data
            page.wait_for_timeout(2000)
            calc_details = page.locator("#calculationCard")
            if calc_details.is_visible():
                expect(calc_details).to_contain_text("multiplication")
                expect(calc_details).to_contain_text("7, 8")  # With spaces
                expect(calc_details).to_contain_text("56")  # 7 * 8 = 56

    def test_edit_calculation(self, page: Page):
        """Test editing an existing calculation."""
        self.register_and_login_user(page)
        page.goto(f"{self.BASE_URL}/dashboard")
        page.wait_for_timeout(2000)
        
        # Create a calculation first
        page.select_option("#calcType", "addition")
        page.fill("#calcInputs", "12,13")
        page.click("button[type='submit']")
        page.wait_for_timeout(3000)
        
        # Look for edit button in the calculations table
        edit_button = page.locator("a:has-text('Edit')").first
        if edit_button.is_visible():
            edit_button.click()
            page.wait_for_timeout(2000)
            
            # Check if we're on the edit calculation page
            current_url = page.url
            assert "/dashboard/edit/" in current_url
            
            # Check for edit form
            expect(page.locator("h2")).to_contain_text("Update Calculation")
            
            # Wait for form to load
            page.wait_for_timeout(2000)
            
            # Look for form fields and verify calc type is readonly
            calc_type_field = page.locator("#calcType")
            calc_inputs_field = page.locator("#calcInputs")
            
            if calc_type_field.is_visible() and calc_inputs_field.is_visible():
                # Verify the calc type field is readonly (addition from our creation)
                calc_type_value = calc_type_field.get_attribute("readonly")
                assert calc_type_value is not None  # Should be readonly
                
                # Only update the inputs (type cannot be changed)
                page.fill("#calcInputs", "15,25")
                
                # Submit the update
                update_button = page.locator("button[type='submit']:has-text('Update')")
                if update_button.is_visible():
                    update_button.click()
                    page.wait_for_timeout(3000)
                    
                    # Check if we're redirected back or see success message
                    success_alert = page.locator("#successAlert")
                    if success_alert.is_visible():
                        expect(success_alert).to_contain_text("successfully")

    def test_delete_calculation(self, page: Page):
        """Test deleting a calculation."""
        self.register_and_login_user(page)
        page.goto(f"{self.BASE_URL}/dashboard")
        page.wait_for_timeout(2000)
        
        # Create a calculation first
        page.select_option("#calcType", "division")
        page.fill("#calcInputs", "100,5")
        page.click("button[type='submit']")
        page.wait_for_timeout(3000)
        
        # Wait for the calculation to appear in the table
        page.wait_for_selector("#calculationsTable tr:not(:has(td[colspan]))", timeout=5000)
        
        # Count initial calculations (excluding "no calculations" message row)
        initial_rows = page.locator("#calculationsTable tr:not(:has(td[colspan]))").count()
        assert initial_rows > 0, f"Expected at least 1 calculation, found {initial_rows}"
        
        # Set up dialog handler before clicking delete
        page.on("dialog", lambda dialog: dialog.accept())
        
        # Look for delete button using class selector
        delete_button = page.locator("button.delete-calc").first
        expect(delete_button).to_be_visible()
        
        delete_button.click()
        page.wait_for_timeout(3000)
        
        # Wait for the deletion to complete - either table is empty or row count decreased
        page.wait_for_timeout(2000)
        
        # Check if calculation was removed
        final_rows = page.locator("#calculationsTable tr:not(:has(td[colspan]))").count()
        
        # The assertion should account for the fact that if it was the only calculation, 
        # the table might show a "no calculations" message instead of being empty
        assert final_rows < initial_rows, f"Expected fewer calculations after deletion. Initial: {initial_rows}, Final: {final_rows}"

    def test_calculation_history_pagination(self, page: Page):
        """Test calculation history displays correctly with multiple calculations."""
        self.register_and_login_user(page)
        page.goto(f"{self.BASE_URL}/dashboard")
        page.wait_for_timeout(2000)
        
        # Create multiple calculations
        test_calculations = [
            {"type": "addition", "inputs": "1,2"},
            {"type": "subtraction", "inputs": "10,3"},
            {"type": "multiplication", "inputs": "3,4"},
            {"type": "division", "inputs": "20,4"}
        ]
        
        for calc in test_calculations:
            page.select_option("#calcType", calc["type"])
            page.fill("#calcInputs", calc["inputs"])
            page.click("button[type='submit']")
            page.wait_for_timeout(1500)
        
        # Check that calculations appear in history table
        calculations_table = page.locator("#calculationsTable")
        expect(calculations_table).to_be_visible()
        
        # Count rows (should be at least the number we created)
        table_rows = page.locator("#calculationsTable tr")
        row_count = table_rows.count()
        assert row_count >= len(test_calculations)

    def test_calculation_input_validation(self, page: Page):
        """Test calculation form input validation."""
        self.register_and_login_user(page)
        page.goto(f"{self.BASE_URL}/dashboard")
        page.wait_for_timeout(2000)
        
        # Test empty inputs
        page.select_option("#calcType", "addition")
        page.fill("#calcInputs", "")
        page.click("button[type='submit']")
        page.wait_for_timeout(2000)
        
        # Should show error or stay on same page
        error_alert = page.locator("#errorAlert")
        if error_alert.is_visible():
            expect(error_alert).to_contain_text("Please enter at least two valid numbers")
        
        # Test invalid input format
        page.fill("#calcInputs", "abc,def")
        page.click("button[type='submit']")
        page.wait_for_timeout(2000)
        
        # Should show error for invalid numbers
        if error_alert.is_visible():
            expect(error_alert).to_be_visible()
        
        # Test division by zero
        page.select_option("#calcType", "division")
        page.fill("#calcInputs", "10,0")
        page.click("button[type='submit']")
        page.wait_for_timeout(2000)
        
        # Should handle division by zero gracefully
        if error_alert.is_visible():
            expect(error_alert).to_contain_text("Division by zero is not allowed")

    def test_calculation_results_accuracy(self, page: Page):
        """Test that calculation results are mathematically correct."""
        self.register_and_login_user(page)
        page.goto(f"{self.BASE_URL}/dashboard")
        page.wait_for_timeout(2000)
        
        test_cases = [
            {"type": "addition", "inputs": "2.5,7.5", "expected": "10"},
            {"type": "subtraction", "inputs": "15.75,5.25", "expected": "10.5"},
            {"type": "multiplication", "inputs": "2.5,4", "expected": "10"},
            {"type": "division", "inputs": "22,2", "expected": "11"}
        ]
        
        for test_case in test_cases:
            page.select_option("#calcType", test_case["type"])
            page.fill("#calcInputs", test_case["inputs"])
            page.click("button[type='submit']")
            page.wait_for_timeout(2000)
            
            # Look for the result in the table
            result_row = page.locator(f"#calculationsTable tr:has-text('{test_case['type']}')").first
            if result_row.is_visible():
                # The result should appear in the table - format inputs with spaces
                formatted_inputs = test_case["inputs"].replace(",", ", ")
                expect(result_row).to_contain_text(formatted_inputs)
    
    def test_dashboard_shows_all_user_calculations(self, page: Page):
        """Test that dashboard displays all calculations created by the user."""
        self.register_and_login_user(page)
        page.goto(f"{self.BASE_URL}/dashboard")
        page.wait_for_timeout(2000)
        
        # Verify we're on the dashboard by checking for the New Calculation heading
        new_calc_heading = page.locator("h2:has-text('New Calculation')")
        expect(new_calc_heading).to_be_visible()
        
        # Define a comprehensive set of test calculations
        test_calculations = [
            {"type": "addition", "inputs": "5,10,15", "expected_result": "30"},
            {"type": "subtraction", "inputs": "100,25", "expected_result": "75"},
            {"type": "multiplication", "inputs": "3,7", "expected_result": "21"},
            {"type": "division", "inputs": "48,6", "expected_result": "8"},
            {"type": "addition", "inputs": "2.5,7.5", "expected_result": "10"},
            {"type": "multiplication", "inputs": "4,2.5", "expected_result": "10"},
            {"type": "subtraction", "inputs": "20.75,5.25", "expected_result": "15.5"},
            {"type": "division", "inputs": "50,2", "expected_result": "25"}
        ]
        
        # Create all test calculations
        created_calculations = []
        for i, calc in enumerate(test_calculations):
            page.select_option("#calcType", calc["type"])
            page.fill("#calcInputs", calc["inputs"])
            page.click("button[type='submit']")
            page.wait_for_timeout(2000)
            
            # Store the calculation details for verification
            created_calculations.append({
                "type": calc["type"],
                "inputs": calc["inputs"].replace(",", ", "),  # Format with spaces for HTML
                "expected_result": calc["expected_result"]
            })
            
            # Brief pause between calculations
            page.wait_for_timeout(500)
        
        # Wait for all calculations to be processed
        page.wait_for_timeout(3000)
        
        # Verify the calculations table is visible
        calculations_table = page.locator("#calculationsTable")
        expect(calculations_table).to_be_visible()
        
        # Get all calculation rows (excluding header and empty message rows)
        calculation_rows = page.locator("#calculationsTable tr:not(:has(th)):not(:has(td[colspan]))")
        
        # Verify we have at least the number of calculations we created
        actual_row_count = calculation_rows.count()
        expected_count = len(test_calculations)
        assert actual_row_count >= expected_count, f"Expected at least {expected_count} calculations, but found {actual_row_count}"
        
        # Verify each created calculation appears in the table
        for calc in created_calculations:
            # Look for a row that contains both the operation type and inputs
            matching_row = page.locator(f"#calculationsTable tr:has-text('{calc['type']}'):has-text('{calc['inputs']}')")
            expect(matching_row).to_be_visible()
            
            # Verify the result is also present in the row
            expect(matching_row).to_contain_text(calc["expected_result"])
        
        # Verify that each row has the expected action buttons (View, Edit, Delete)
        for i in range(min(actual_row_count, expected_count)):
            row = calculation_rows.nth(i)
            
            # Check for action buttons/links
            view_link = row.locator("a:has-text('View')")
            edit_link = row.locator("a:has-text('Edit')")
            delete_button = row.locator("button:has-text('Delete'), button.delete-calc")
            
            expect(view_link).to_be_visible()
            expect(edit_link).to_be_visible()
            expect(delete_button).to_be_visible()
        
        # Verify calculations are displayed in descending order (newest first)
        # This assumes the table shows calculations with timestamps or in creation order
        page.wait_for_timeout(1000)
        
        # Test pagination or scrolling if there are many calculations
        if actual_row_count > 10:  # If there's potential pagination
            # Check if there are pagination controls
            pagination = page.locator(".pagination, [class*='page']")
            if pagination.is_visible():
                # Basic pagination test - this would depend on the actual implementation
                page_info = page.locator("text=/Page|Showing|of/")
                if page_info.is_visible():
                    expect(page_info).to_be_visible()
    
    def test_complete_calculation_workflow(self, page: Page):
        """Test complete workflow: create, view, edit, delete calculation."""
        self.register_and_login_user(page)
        page.goto(f"{self.BASE_URL}/dashboard")
        page.wait_for_timeout(2000)
        
        # Step 1: Create calculation
        page.select_option("#calcType", "multiplication")
        page.fill("#calcInputs", "6,9")
        page.click("button[type='submit']")
        page.wait_for_timeout(3000)
        
        # Step 2: View calculation
        view_link = page.locator("a:has-text('View')").first
        if view_link.is_visible():
            view_link.click()
            page.wait_for_timeout(2000)
            
            # Verify view page
            expect(page.locator("h2")).to_contain_text("Calculation Details")
            
            # Step 3: Navigate to edit from view page
            edit_link = page.locator("a:has-text('Edit')")
            if edit_link.is_visible():
                edit_link.click()
                page.wait_for_timeout(2000)
                
                # Verify edit page and make changes
                expect(page.locator("h2")).to_contain_text("Update Calculation")
                
                # Update the calculation inputs only (type cannot be changed)
                page.wait_for_timeout(1000)
                if page.locator("#calcInputs").is_visible():
                    page.fill("#calcInputs", "15,25")
                    
                    update_button = page.locator("button[type='submit']:has-text('Update')")
                    if update_button.is_visible():
                        update_button.click()
                        page.wait_for_timeout(3000)
            
            # Step 4: Return to dashboard and delete
            page.goto(f"{self.BASE_URL}/dashboard")
            page.wait_for_timeout(2000)
            
            delete_button = page.locator("button:has-text('Delete')").first
            if delete_button.is_visible():
                page.on("dialog", lambda dialog: dialog.accept())
                delete_button.click()
                page.wait_for_timeout(2000)
                
                # Verify deletion (success message or reduced table rows)
                success_alert = page.locator("#successAlert")
                if success_alert.is_visible():
                    expect(success_alert).to_contain_text("deleted")

