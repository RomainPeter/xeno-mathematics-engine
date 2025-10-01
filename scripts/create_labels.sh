#!/usr/bin/env bash
set -euo pipefail

# Create GitHub labels for Xeno Mathematics Engine
# This script creates labels for epic organization and priority management

echo "🏷️  Creating GitHub labels for Xeno Mathematics Engine..."

# Epic labels
gh label create "epic:0" --color FFD700 --description "Infrastructure and CI/CD"
gh label create "epic:1" --color 7FFFD4 --description "PSP/PCAP Core functionality"
gh label create "epic:2" --color 98FB98 --description "Orchestrator and Engines"
gh label create "epic:3" --color F0E68C --description "Advanced Proof Methods"
gh label create "epic:4" --color DDA0DD --description "Integration and Deployment"

# Priority labels
gh label create "priority:highest" --color FF0000 --description "Critical issues requiring immediate attention"
gh label create "priority:high" --color FF8C00 --description "Important issues that should be addressed soon"
gh label create "priority:medium" --color 1E90FF --description "Normal priority issues"
gh label create "priority:low" --color 32CD32 --description "Low priority issues"
gh label create "priority:lowest" --color 808080 --description "Lowest priority issues"

# Component labels
gh label create "component:psp" --color 4169E1 --description "Proof Structure Protocol"
gh label create "component:pcap" --color 228B22 --description "Proof Capability Protocol"
gh label create "component:orchestrator" --color DC143C --description "Orchestration system"
gh label create "component:engines" --color FF6347 --description "Proof verification engines"
gh label create "component:persistence" --color 8A2BE2 --description "Data persistence layer"
gh label create "component:policy" --color 20B2AA --description "Security and policy management"
gh label create "component:ci" --color 4682B4 --description "CI/CD and build system"
gh label create "component:docker" --color 00CED1 --description "Docker and containerization"
gh label create "component:docs" --color 32CD32 --description "Documentation"
gh label create "component:security" --color FF4500 --description "Security and supply chain"

# Type labels
gh label create "type:bug" --color D73A4A --description "Something isn't working"
gh label create "type:enhancement" --color A2EEEF --description "New feature or request"
gh label create "type:documentation" --color 0075CA --description "Improvements or additions to documentation"
gh label create "type:refactor" --color 7057FF --description "Code change that neither fixes a bug nor adds a feature"
gh label create "type:test" --color 008672 --description "Adding missing tests or correcting existing tests"
gh label create "type:chore" --color 0E8A16 --description "Changes to the build process or auxiliary tools"
gh label create "type:security" --color B60205 --description "Security vulnerability or hardening"

# Status labels
gh label create "status:blocked" --color FF0000 --description "Blocked by another issue"
gh label create "status:in-progress" --color FF8C00 --description "Currently being worked on"
gh label create "status:needs-review" --color 1E90FF --description "Ready for review"
gh label create "status:needs-testing" --color 32CD32 --description "Ready for testing"
gh label create "status:ready" --color 00FF00 --description "Ready to be worked on"

# Size labels
gh label create "size:xs" --color 00FF00 --description "Extra small (1-2 hours)"
gh label create "size:s" --color 32CD32 --description "Small (half day)"
gh label create "size:m" --color FFD700 --description "Medium (1-2 days)"
gh label create "size:l" --color FF8C00 --description "Large (3-5 days)"
gh label create "size:xl" --color FF0000 --description "Extra large (1+ weeks)"

echo "✅ GitHub labels created successfully!"
echo ""
echo "📋 Created labels:"
echo "  🏗️  Epic labels (epic:0-4)"
echo "  ⚡ Priority labels (priority:highest-lowest)"
echo "  🔧 Component labels (component:*)"
echo "  📝 Type labels (type:*)"
echo "  📊 Status labels (status:*)"
echo "  📏 Size labels (size:xs-xl)"
echo ""
echo "🎯 You can now use these labels to organize issues and pull requests!"
