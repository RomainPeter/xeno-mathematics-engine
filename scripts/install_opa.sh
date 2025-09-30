#!/bin/bash
# Install OPA (Open Policy Agent) for Discovery Engine 2-Cat

set -e

echo "🔧 Installing OPA (Open Policy Agent)..."

# Detect OS and architecture
OS=$(uname -s | tr '[:upper:]' '[:lower:]')
ARCH=$(uname -m)

case $ARCH in
    x86_64)
        ARCH="amd64"
        ;;
    arm64|aarch64)
        ARCH="arm64"
        ;;
    *)
        echo "❌ Unsupported architecture: $ARCH"
        exit 1
        ;;
esac

# Download OPA
OPA_VERSION="0.58.0"
OPA_URL="https://github.com/open-policy-agent/opa/releases/download/v${OPA_VERSION}/opa_${OS}_${ARCH}_static"

echo "📥 Downloading OPA v${OPA_VERSION} for ${OS}/${ARCH}..."

if command -v curl >/dev/null 2>&1; then
    curl -L -o opa "${OPA_URL}"
elif command -v wget >/dev/null 2>&1; then
    wget -O opa "${OPA_URL}"
else
    echo "❌ Neither curl nor wget found. Please install one of them."
    exit 1
fi

# Make executable
chmod +x opa

# Install to system path
if [ -w /usr/local/bin ]; then
    sudo mv opa /usr/local/bin/
    echo "✅ OPA installed to /usr/local/bin/opa"
elif [ -w /usr/bin ]; then
    sudo mv opa /usr/bin/
    echo "✅ OPA installed to /usr/bin/opa"
else
    # Install to local bin
    mkdir -p ~/.local/bin
    mv opa ~/.local/bin/
    echo "✅ OPA installed to ~/.local/bin/opa"
    echo "💡 Add ~/.local/bin to your PATH if not already there"
fi

# Verify installation
echo "🔍 Verifying OPA installation..."
if command -v opa >/dev/null 2>&1; then
    opa version
    echo "✅ OPA installation successful!"
else
    echo "❌ OPA not found in PATH. Please check your installation."
    exit 1
fi

# Test OPA with a simple policy
echo "🧪 Testing OPA with sample policy..."
cat > test_policy.rego << 'EOF'
package test

allow {
    input.user == "admin"
}

deny[msg] {
    input.user != "admin"
    msg := "Access denied: admin required"
}
EOF

cat > test_input.json << 'EOF'
{
    "user": "admin"
}
EOF

# Test policy evaluation
echo "📋 Testing policy evaluation..."
opa eval -i test_input.json -d test_policy.rego 'data.test.allow'
opa eval -i test_input.json -d test_policy.rego 'data.test.deny'

# Cleanup test files
rm -f test_policy.rego test_input.json

echo "🎉 OPA installation and testing completed successfully!"
echo ""
echo "📚 Next steps:"
echo "   - OPA is ready for Discovery Engine 2-Cat"
echo "   - Policies are in demo/regtech/policies/"
echo "   - Test with: opa eval -i input.json -d policy.rego 'data.policy.deny'"
