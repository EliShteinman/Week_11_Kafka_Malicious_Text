#!/bin/bash

# Script to update image references in YAML files
# Run this after building and pushing your images

set -e

# Configuration
REGISTRY="your-dockerhub-username"  # Change this!
VERSION="v1.0"

echo "🔧 Updating image references in YAML files..."

# Check if registry is updated
if [ "$REGISTRY" = "your-dockerhub-username" ]; then
    echo "❌ Please update the REGISTRY variable in this script!"
    exit 1
fi

# Files to update
FILES=(
    "10-data-retrieval.yaml"
    "11-retriever.yaml" 
    "12-preprocessor.yaml"
    "13-enricher.yaml"
    "14-persister.yaml"
)

# Update each file
for file in "${FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "📝 Updating $file..."
        
        # Replace registry placeholder
        sed -i.bak "s/your-registry/$REGISTRY/g" "$file"
        
        # Replace version if needed
        sed -i.bak "s/:latest/:$VERSION/g" "$file"
        
        # Remove backup file
        rm "$file.bak"
        
        echo "✅ $file updated"
    else
        echo "⚠️ $file not found, skipping..."
    fi
done

echo ""
echo "🎉 All YAML files updated!"
echo ""
echo "📝 Updated images:"
echo "- $REGISTRY/data-retrieval:$VERSION"
echo "- $REGISTRY/retriever:$VERSION"
echo "- $REGISTRY/preprocessor:$VERSION"
echo "- $REGISTRY/enricher:$VERSION"
echo "- $REGISTRY/persister:$VERSION"
echo ""
echo "🚀 Ready to deploy! Run:"
echo "   ./deployment-script.sh"