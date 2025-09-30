# Toy repo with a known deprecated API violation


def do_work():
    # Deprecated API usage that verifier should catch
    result = "foo_v1('input')"  # string literal for deterministic parsing
    return result
