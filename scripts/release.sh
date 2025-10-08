#!/bin/bash
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if version argument provided
if [ -z "$1" ]; then
    echo -e "${RED}Error: Version number required${NC}"
    echo "Usage: ./release.sh 3.5.8"
    exit 1
fi

VERSION=$1
echo -e "${YELLOW}Preparing release for version ${VERSION}${NC}"

# Check for uncommitted changes
if [[ -n $(git status -s) ]]; then
    echo -e "${RED}Error: You have uncommitted changes${NC}"
    git status -s
    exit 1
fi

# Check we're on main/master branch
BRANCH=$(git branch --show-current)
if [ "$BRANCH" != "main" ] && [ "$BRANCH" != "master" ]; then
    echo -e "${RED}Error: Not on main/master branch (currently on ${BRANCH})${NC}"
    exit 1
fi

echo -e "${YELLOW}Using branch: ${BRANCH}${NC}"

# Pull latest changes
echo -e "${YELLOW}Pulling latest changes...${NC}"
git pull

# Run tests
echo -e "${YELLOW}Running tests...${NC}"
uvx tox
if [ $? -ne 0 ]; then
    echo -e "${RED}Tests failed! Aborting release.${NC}"
    exit 1
fi
echo -e "${GREEN}✓ All tests passed${NC}"

# Update version in pyproject.toml
echo -e "${YELLOW}Updating version in pyproject.toml...${NC}"
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    sed -i '' "s/version = \"[^\"]*\"/version = \"${VERSION}\"/" pyproject.toml
else
    # Linux
    sed -i "s/version = \"[^\"]*\"/version = \"${VERSION}\"/" pyproject.toml
fi

# Show the diff
git diff pyproject.toml

# Confirm
echo -e "${YELLOW}Ready to release version ${VERSION}. Continue? (y/n)${NC}"
read -r response
if [[ ! "$response" =~ ^[Yy]$ ]]; then
    echo -e "${RED}Release aborted${NC}"
    git checkout pyproject.toml
    exit 1
fi

# Commit and tag
echo -e "${YELLOW}Creating commit and tag...${NC}"
git add pyproject.toml
git commit -m "Bump version to ${VERSION}"
git tag "v${VERSION}"

# Push
echo -e "${YELLOW}Pushing to origin...${NC}"
git push origin "$BRANCH"
git push origin "v${VERSION}"

echo -e "${GREEN}✓ Release ${VERSION} complete!${NC}"
echo -e "${GREEN}Check GitHub Actions for build and publish status:${NC}"
echo -e "https://github.com/dashio-connect/python-dashio/actions"