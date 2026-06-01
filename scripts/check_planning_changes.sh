#!/usr/bin/env bash
# check_planning_changes.sh
#
# Block commits that modify planning documents without an accompanying ADR.
#
# A commit that modifies pyproject.toml must also include a new or modified ADR
# in docs/adr/.
#
# Reasoning: this file encodes project-level decisions (dependencies). Changing it
# without documenting why creates silent drift.

set -e

# Get the list of staged files
STAGED_FILES=$(git diff --cached --name-only)

# Check if any planning docs are being modified
PLANNING_CHANGED=false
PLANNING_FILES=""

for file in $STAGED_FILES; do
    case "$file" in
        pyproject.toml)
            PLANNING_CHANGED=true
            PLANNING_FILES="$PLANNING_FILES $file"
            ;;
    esac
done

if [ "$PLANNING_CHANGED" = false ]; then
    # No planning docs changed; nothing to check
    exit 0
fi

# Planning docs changed. Verify an ADR is also in this commit.
ADR_CHANGED=false
for file in $STAGED_FILES; do
    case "$file" in
        docs/adr/[0-9][0-9][0-9]-*.md)
            ADR_CHANGED=true
            break
            ;;
    esac
done

if [ "$ADR_CHANGED" = false ]; then
    echo ""
    echo "🚫 COMMIT BLOCKED: Planning documents modified without an ADR"
    echo ""
    echo "The following planning documents were changed:"
    for f in $PLANNING_FILES; do
        echo "  - $f"
    done
    echo ""
    echo "Project policy: changes to planning documents require a new or modified"
    echo "Architecture Decision Record in docs/adr/ to document the reasoning."
    echo ""
    echo "What to do:"
    echo "  1. Copy docs/adr/000-template.md to docs/adr/NNN-your-decision.md"
    echo "  2. Fill it out with context, decision, consequences, alternatives"
    echo "  3. git add the new ADR"
    echo "  4. git commit again"
    echo ""
    echo "If this change genuinely doesn't need an ADR (e.g., a formatting-only"
    echo "tweak to pyproject.toml), bypass with: git commit --no-verify"
    echo "But think twice — most planning-doc changes are worth an ADR."
    echo ""
    exit 1
fi

# Both planning doc and ADR changed. Allow.
exit 0
