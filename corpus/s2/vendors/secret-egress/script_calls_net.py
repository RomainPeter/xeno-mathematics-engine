#!/usr/bin/env python3
"""
Script that attempts secret exposure and egress (for testing)
"""

import requests
import json

# Simulated API key (should be blocked)
API_KEY = "sk_live_1234567890abcdef"  # This should trigger secret detection


def call_external_api():
    """Attempt to call external API (should be blocked)"""
    try:
        response = requests.get(
            "https://api.external-service.com/data",
            headers={"Authorization": f"Bearer {API_KEY}"},
            timeout=5,
        )
        return response.json()
    except Exception as e:
        print(f"Egress blocked: {e}")
        return None


def main():
    """Main function that demonstrates secret/egress issues"""
    print("Attempting external API call...")
    result = call_external_api()

    if result:
        print("External API call successful")
        print(json.dumps(result, indent=2))
    else:
        print("External API call failed (expected)")


if __name__ == "__main__":
    main()
