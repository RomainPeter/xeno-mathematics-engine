#!/usr/bin/env python3
"""
API endpoint after modification (v2.0.0)
"""

from flask import Flask, request, jsonify

app = Flask(__name__)


@app.route("/api/v2/users", methods=["POST"])
def create_user():
    """Create user endpoint - AFTER modification with breaking change"""
    data = request.get_json()

    # Modified endpoint - email_verification_token now required
    required_fields = ["name", "email", "email_verification_token"]

    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"Missing required field: {field}"}), 400

    # Create user logic
    user = {
        "id": 123,
        "name": data["name"],
        "email": data["email"],
        "email_verification_token": data["email_verification_token"],
        "created_at": "2024-01-01T00:00:00Z",
    }

    return jsonify(user), 201


if __name__ == "__main__":
    app.run(debug=True, port=5000)
