package proof.no_secrets

deny[msg] {
    input.diff.contains_secret == true
    msg := "secret detected in diff"
}

# Additional rules for secret detection
deny[msg] {
    contains(input.code, "sk-")
    msg := "API key pattern detected"
}

deny[msg] {
    contains(input.code, "password")
    contains(input.code, "=")
    msg := "password assignment detected"
}

deny[msg] {
    contains(input.code, "token")
    contains(input.code, "=")
    msg := "token assignment detected"
}
