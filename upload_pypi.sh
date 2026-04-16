#!/bin/bash
set -e

echo "========================================="
echo "  JiuZhang (九章) PyPI Upload Script"
echo "========================================="

# Step 1: Bump patch version
echo ""
echo "Step 1: Bumping patch version..."
INIT_FILE="jiuzhang/__init__.py"
CURRENT_VERSION=$(grep '__version__' "$INIT_FILE" | cut -d'"' -f2)
MAJOR=$(echo "$CURRENT_VERSION" | cut -d. -f1)
MINOR=$(echo "$CURRENT_VERSION" | cut -d. -f2)
PATCH=$(echo "$CURRENT_VERSION" | cut -d. -f3)
NEW_PATCH=$((PATCH + 1))
NEW_VERSION="${MAJOR}.${MINOR}.${NEW_PATCH}"

sed -i '' "s/__version__ = \"${CURRENT_VERSION}\"/__version__ = \"${NEW_VERSION}\"/" "$INIT_FILE"
echo "Version bumped: ${CURRENT_VERSION} -> ${NEW_VERSION}"

# Step 2: Clean old builds
echo ""
echo "Step 2: Cleaning old builds..."
rm -rf dist/ build/ *.egg-info jiuzhang.egg-info/

# Step 3: Install build tools
echo ""
echo "Step 3: Installing build tools..."
pip install --upgrade build twine

# Step 4: Build package
echo ""
echo "Step 4: Building package..."
python -m build
echo "Running twine check..."
twine check dist/*

# Step 5: Upload to PyPI
echo ""
echo "Step 5: Uploading to PyPI..."
twine upload dist/*

echo ""
echo "========================================="
echo "  Upload complete! Version: ${NEW_VERSION}"
echo "========================================="
