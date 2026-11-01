#!/usr/bin/env bash
set -euo pipefail

# Safe local verification pipeline. It never publishes or pushes changes.
case "${1:-}" in
  test)
    python -m pytest
    ;;
  compile)
    python -m compileall -q agent bridge channel common expert_system models
    ;;
  security)
    python -m pytest security_remediation_test.py tests/security_test.py
    ;;
  review)
    echo "Run the read-only code review workflow for this repository."
    ;;
  deploy)
    echo "Deployment is intentionally manual; this script never runs git push." >&2
    exit 2
    ;;
  *)
    echo "Usage: $0 {test|compile|security|review|deploy}" >&2
    exit 2
    ;;
esac
