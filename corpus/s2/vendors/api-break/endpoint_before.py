#!/usr/bin/env python3
"""
API endpoint before modification (v1.0.0)
"""

from flask import Flask, request, jsonify

app = Flask(__name__)


@app.route("/api/v1/users", methods=["POST"])
def create_user():
    """Create user endpoint - BEFORE modification"""
    data = request.get_json()

    # Original endpoint - no email_verification_token required
    required_fields = ["name", "email"]

    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"Missing required field: {field}"}), 400

    # Create user logic
    user = {
        "id": 123,
        "name": data["name"],
        "email": data["email"],
        "created_at": "2024-01-01T00:00:00Z",
    }

    return jsonify(user), 201


if __name__ == "__main__":
    app.run(debug=True, port=5000)
