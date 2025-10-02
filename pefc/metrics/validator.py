#!/usr/bin/env python3
"""
Metrics validation module.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict

log = logging.getLogger(__name__)


def validate_metrics_data(data: Dict[str, Any], schema_path: Path) -> bool:
    """Validate metrics data against JSON schema.

    Args:
        data: Metrics data to validate
        schema_path: Path to JSON schema

    Returns:
        True if valid, False otherwise
    """
    try:
        # Load schema
        with open(schema_path, "r") as f:
            schema = json.load(f)

        # Validate data against schema
        return _validate_against_schema(data, schema)
    except Exception as e:
        log.error("Failed to validate metrics data: %s", e)
        return False


def _validate_against_schema(data: Dict[str, Any], schema: Dict[str, Any]) -> bool:
    """Validate data against JSON schema.

    Args:
        data: Data to validate
        schema: JSON schema

    Returns:
        True if valid, False otherwise
    """
    try:
        # Basic validation
        if not isinstance(data, dict):
            return False

        # Check required fields
        required_fields = schema.get("required", [])
        for field in required_fields:
            if field not in data:
                log.error("Missing required field: %s", field)
                return False

        # Check field types
        properties = schema.get("properties", {})
        for field, field_schema in properties.items():
            if field in data:
                if not _validate_field(data[field], field_schema):
                    log.error("Invalid field %s: %s", field, data[field])
                    return False

        return True
    except Exception as e:
        log.error("Schema validation failed: %s", e)
        return False


def _validate_field(value: Any, field_schema: Dict[str, Any]) -> bool:
    """Validate a single field against its schema.

    Args:
        value: Value to validate
        field_schema: Schema for the field

    Returns:
        True if valid, False otherwise
    """
    try:
        # Check type
        expected_type = field_schema.get("type")
        if expected_type:
            if not _check_type(value, expected_type):
                return False

        # Check minimum/maximum for numbers
        if isinstance(value, (int, float)):
            if "minimum" in field_schema and value < field_schema["minimum"]:
                return False
            if "maximum" in field_schema and value > field_schema["maximum"]:
                return False

        # Check string constraints
        if isinstance(value, str):
            if "minLength" in field_schema and len(value) < field_schema["minLength"]:
                return False
            if "maxLength" in field_schema and len(value) > field_schema["maxLength"]:
                return False

        # Check array constraints
        if isinstance(value, list):
            if "minItems" in field_schema and len(value) < field_schema["minItems"]:
                return False
            if "maxItems" in field_schema and len(value) > field_schema["maxItems"]:
                return False

        return True
    except Exception as e:
        log.error("Field validation failed: %s", e)
        return False


def _check_type(value: Any, expected_type: str) -> bool:
    """Check if value matches expected type.

    Args:
        value: Value to check
        expected_type: Expected type string

    Returns:
        True if type matches, False otherwise
    """
    type_mapping = {
        "string": str,
        "number": (int, float),
        "integer": int,
        "boolean": bool,
        "array": list,
        "object": dict,
    }

    expected_python_type = type_mapping.get(expected_type)
    if expected_python_type is None:
        return True  # Unknown type, assume valid

    return isinstance(value, expected_python_type)


def validate_metrics_run(run_data: Dict[str, Any]) -> bool:
    """Validate a single metrics run.

    Args:
        run_data: Metrics run data

    Returns:
        True if valid, False otherwise
    """
    try:
        # Check required fields
        required_fields = ["run_id", "timestamp", "metrics"]
        for field in required_fields:
            if field not in run_data:
                log.error("Missing required field in metrics run: %s", field)
                return False

        # Check field types
        if not isinstance(run_data["run_id"], str):
            log.error("run_id must be a string")
            return False

        if not isinstance(run_data["timestamp"], str):
            log.error("timestamp must be a string")
            return False

        if not isinstance(run_data["metrics"], dict):
            log.error("metrics must be a dictionary")
            return False

        # Check metrics values
        for metric_name, metric_value in run_data["metrics"].items():
            if not isinstance(metric_value, (int, float)):
                log.error("Metric %s must be a number", metric_name)
                return False
            if metric_value < 0:
                log.error("Metric %s must be non-negative", metric_name)
                return False

        return True
    except Exception as e:
        log.error("Metrics run validation failed: %s", e)
        return False


def validate_metrics_summary(summary_data: Dict[str, Any]) -> bool:
    """Validate metrics summary.

    Args:
        summary_data: Summary data

    Returns:
        True if valid, False otherwise
    """
    try:
        # Check required fields
        required_fields = ["overall_score", "metrics"]
        for field in required_fields:
            if field not in summary_data:
                log.error("Missing required field in summary: %s", field)
                return False

        # Check overall_score
        overall_score = summary_data["overall_score"]
        if not isinstance(overall_score, (int, float)):
            log.error("overall_score must be a number")
            return False
        if not (0.0 <= overall_score <= 1.0):
            log.error("overall_score must be between 0.0 and 1.0")
            return False

        # Check metrics
        metrics = summary_data["metrics"]
        if not isinstance(metrics, dict):
            log.error("metrics must be a dictionary")
            return False

        # Check each metric summary
        for metric_name, metric_summary in metrics.items():
            if not isinstance(metric_summary, dict):
                log.error("Metric summary for %s must be a dictionary", metric_name)
                return False

            # Check required fields in metric summary
            required_metric_fields = ["value", "weighted_avg", "min", "max", "count"]
            for field in required_metric_fields:
                if field not in metric_summary:
                    log.error(
                        "Missing required field in metric summary %s: %s",
                        metric_name,
                        field,
                    )
                    return False
                if not isinstance(metric_summary[field], (int, float)):
                    log.error(
                        "Field %s in metric summary %s must be a number",
                        field,
                        metric_name,
                    )
                    return False

        return True
    except Exception as e:
        log.error("Metrics summary validation failed: %s", e)
        return False


def validate_schema_file(schema_path: Path) -> bool:
    """Validate JSON schema file.

    Args:
        schema_path: Path to schema file

    Returns:
        True if valid, False otherwise
    """
    try:
        # Check if file exists
        if not schema_path.exists():
            log.error("Schema file does not exist: %s", schema_path)
            return False

        # Load and parse JSON
        with open(schema_path, "r") as f:
            schema = json.load(f)

        # Check basic schema structure
        if not isinstance(schema, dict):
            log.error("Schema must be a JSON object")
            return False

        # Check required schema fields
        required_schema_fields = ["$schema", "type", "properties"]
        for field in required_schema_fields:
            if field not in schema:
                log.error("Missing required schema field: %s", field)
                return False

        return True
    except Exception as e:
        log.error("Schema file validation failed: %s", e)
        return False
