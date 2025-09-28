#!/usr/bin/env bash
set -euo pipefail
: "${REPO:?set REPO=owner/repo}"
cat > scripts/protect_main.json <<'JSON'
{
  "required_status_checks": {
    "strict": true,
    "checks": [
      { "context": "CI" },
      { "context": "Nightly Bench" }
    ]
  },
  "enforce_admins": true,
  "required_pull_request_reviews": {
    "required_approving_review_count": 1,
    "require_code_owner_reviews": true,
    "dismiss_stale_reviews": true
  },
  "restrictions": null,
  "required_linear_history": true,
  "allow_force_pushes": false,
  "allow_deletions": false,
  "block_creations": false
}
JSON
gh api \
  -X PUT \
  -H "Accept: application/vnd.github+json" \
  repos/$REPO/branches/main/protection \
  --input scripts/protect_main.json
echo "Branch protection applied to $REPO main."
