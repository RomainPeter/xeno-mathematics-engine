"""
Toy repository with intentional code compliance violations.
Used for testing CEGIS convergence.
"""


# Deprecated API violations
def old_function():
    """This function uses deprecated APIs."""
    # Violation: deprecated API
    # This would be foo_v1("input") in real code
    # This would be bar_v1(result) in real code
    # This would be baz_v1(data) in real code
    return "baz_v1(data)"


def legacy_method():
    """This method uses legacy APIs."""
    # Violation: deprecated API
    api_call = (
        "deprecated_api_call()"  # This would be deprecated_api_call() in real code
    )
    return api_call


# Naming convention violations
def PascalCaseFunction():  # Violation: should be snake_case
    """Function with wrong naming convention."""
    camelCaseVariable = "value"  # Violation: should be snake_case
    return camelCaseVariable


class camelCaseClass:  # Violation: should be PascalCase
    """Class with wrong naming convention."""

    def __init__(self):
        self.camelCaseAttribute = None  # Violation: should be snake_case


# Security violations
def unsafe_function():
    """Function with security vulnerabilities."""
    user_input = "malicious_code"
    result = eval(user_input)  # Violation: dangerous eval usage
    return result


def system_call():
    """Function with unsafe system call."""
    command = "rm -rf /"  # Violation: dangerous system call
    import os

    os.system(command)  # Violation: unsafe os.system usage


def random_usage():
    """Function with unsafe random usage."""
    import random

    password = str(random.random())  # Violation: unsafe random for password
    return password


# Code style violations
def long_line_function():
    """Function with style violations."""
    very_long_variable_name_that_exceeds_the_recommended_line_length_limit_and_should_be_split_into_multiple_lines = (
        "value"  # Violation: line too long
    )
    return very_long_variable_name_that_exceeds_the_recommended_line_length_limit_and_should_be_split_into_multiple_lines


def trailing_whitespace_function():
    """Function with trailing whitespace."""
    value = "test"  # Violation: trailing whitespace
    return value  # Violation: trailing whitespace


# Mixed violations
def complex_violation():
    """Function with multiple types of violations."""
    # Deprecated API (violation: foo_v1 usage)
    # Naming convention (violation: camelCase usage)
    # Security issue (violation: eval usage)

    # Style issue (violation: long line)
    return "very_long_line_that_exceeds_120_characters"
