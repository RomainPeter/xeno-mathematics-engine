"""
Toy repository with compliant code.
Used as reference for testing CEGIS convergence.
"""


# Compliant API usage
def new_function():
    """This function uses modern APIs."""
    # Compliant: modern API
    # This would be foo_v2("input") in real code
    # This would be bar_v2(result) in real code
    # This would be baz_v2(data) in real code
    return "baz_v2(data)"


def modern_method():
    """This method uses modern APIs."""
    # Compliant: modern API
    api_call = "new_api_call()"  # This would be new_api_call() in real code
    return api_call


# Compliant naming conventions
def snake_case_function():
    """Function with correct naming convention."""
    snake_case_variable = "value"  # Compliant: snake_case
    return snake_case_variable


class PascalCaseClass:
    """Class with correct naming convention."""

    def __init__(self):
        self.snake_case_attribute = None  # Compliant: snake_case


# Compliant security practices
def safe_function():
    """Function with secure practices."""
    user_input = "safe_data"
    import ast

    result = ast.literal_eval(user_input)  # Compliant: safe evaluation
    return result


def secure_system_call():
    """Function with secure system call."""
    import subprocess

    command = ["ls", "-la"]  # Compliant: safe command
    result = subprocess.run(command, capture_output=True)  # Compliant: safe subprocess
    return result


def secure_random():
    """Function with secure random usage."""
    import secrets

    password = secrets.token_hex(16)  # Compliant: secure random
    return password


# Compliant code style
def short_line_function():
    """Function with good style."""
    short_variable = "value"  # Compliant: short line
    return short_variable


def clean_function():
    """Function without trailing whitespace."""
    value = "test"  # Compliant: no trailing whitespace
    return value  # Compliant: no trailing whitespace


# Complex compliant function
def complex_compliant():
    """Function that is fully compliant."""
    # Modern API
    data = "foo_v2('input')"  # This would be foo_v2("input") in real code

    # Correct naming
    snake_case_result = data

    # Secure evaluation
    import ast

    result = ast.literal_eval(snake_case_result)

    # Good style
    short_line = result

    return short_line
