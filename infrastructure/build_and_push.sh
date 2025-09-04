#!/bin/bash

# Script to build and push Docker images
# Update REGISTRY variable with your Docker registry

set -e

# Configuration
REGISTRY="your-dockerhub-username"  # Change this!
VERSION="v1.0"
PROJECT_NAME="kafka-malicious-text"

echo "🏗️ Building and pushing Docker images..."
echo "Registry: $REGISTRY"
echo "Version: $VERSION"
echo ""

# Function to build and push image
build_and_push() {
    local service_name=$1
    local dockerfile_path=$2
    local image_name="$REGISTRY/${service_name}:$VERSION"
    
    echo "🔨 Building $service_name..."
    docker build -f $dockerfile_path -t $image_name .
    
    echo "📤 Pushing $service_name..."
    docker push $image_name
    
    echo "✅ $service_name completed: $image_name"
    echo ""
}

# Check if registry is updated
if [ "$REGISTRY" = "your-dockerhub-username" ]; then
    echo "❌ Please update the REGISTRY variable in this script!"
    exit 1
fi

# Build and push each service
build_and_push "data-retrieval" "services/data_retrieval/Dockerfile"
build_and_push "retriever" "services/retriever/Dockerfile"
build_and_push "preprocessor" "services/preprocessor/Dockerfile"
build_and_push "enricher" "services/enricher/Dockerfile"
build_and_push "persister" "services/persister/Dockerfile"

echo "🎉 All images built and pushed successfully!"
echo ""
echo "📝 Next steps:"
echo "1. Update the image references in your YAML files:"
echo "   sed -i 's/your-registry/$REGISTRY/g' *.yaml"
echo ""
echo "2. Update image versions:"
echo "   sed -i 's/:latest/:$VERSION/g' *.yaml"
echo ""
echo "3. Run the deployment script:"
echo "   ./deployment-script.sh"