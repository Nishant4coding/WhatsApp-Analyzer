import requests

# Replace with your Apps Script URL
APPS_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbzWP1utc6HsuYtQtOOUN20FyD_lBashTRKRh5pyEsifCTPZY8plmB_pwpQaDEZGawj2/exec"

def test_appscript_integration():
    # Test data
    urgent_link = "https://meet.google.com/uun-erih-bhp"
    email = "nishant4srivastava@gmail.com"  

    payload = {
        "email": email,
        "link": urgent_link,
        "title": "Test Meeting",
        "description": "This is a test meeting scheduled via Apps Script.",
        "start_time": "2025-01-07T10:00:00Z",  # Example start time in ISO 8601 format
        "end_time": "2025-01-07T11:00:00Z"      # Example end time in ISO 8601 format
    }

    # HTTP headers
    headers = {
        "Content-Type": "application/json"
    }

    try:
        # Make the POST request
        response = requests.post(APPS_SCRIPT_URL, json=payload, headers=headers)

        # Output the response details
        print(f"Status Code: {response.status_code}")
        try:
            response_data = response.json()
            print("Response:", response_data)

            # Check for success in response
            if response.status_code == 200 and response_data.get("status") == "success":
                print("Test Passed: Event successfully scheduled!")
            else:
                print("Test Failed: Something went wrong!")
        except ValueError:  # Handle JSON decoding error
            print("Error: Response is not in JSON format.")
            print("Raw Response Text:", response.text)

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_appscript_integration()
