#!/bin/bash

# Deployment script for Kafka Malicious Text project
# Run this script to deploy everything in the correct order

set -e  # Exit on error

echo "🚀 Starting Kubernetes deployment..."

# Step 1: Create namespace
echo "📁 Creating namespace..."
kubectl apply -f 01-namespace.yaml

# Step 2: Deploy infrastructure configuration
echo "⚙️ Deploying configuration..."
kubectl apply -f 02-kafka-config.yaml
kubectl apply -f 09-app-config.yaml

# Step 3: Deploy Kafka
echo "🔄 Deploying Kafka..."
kubectl apply -f 03-kafka-statefulset.yaml
kubectl apply -f 04-kafka-services.yaml

# Wait for Kafka to be ready
echo "⏳ Waiting for Kafka to be ready..."
kubectl wait --for=condition=ready pod -l app=kafka -n kafka-malicious-text --timeout=300s

# Step 4: Deploy MongoDB
echo "🍃 Deploying MongoDB..."
kubectl apply -f 05-mongodb-statefulset.yaml
kubectl apply -f 06-mongodb-services.yaml

# Wait for MongoDB to be ready
echo "⏳ Waiting for MongoDB to be ready..."
kubectl wait --for=condition=ready pod -l app=mongodb -n kafka-malicious-text --timeout=300s

# Step 5: Deploy UIs
echo "🖥️ Deploying UIs..."
kubectl apply -f 07-kafka-ui.yaml
kubectl apply -f 08-mongo-express.yaml

# Step 6: Deploy microservices (only if images are ready)
echo "🔧 Deploying microservices..."
echo "⚠️  Make sure you've updated the image references in the YAML files!"
read -p "Have you updated the Docker images in the YAML files? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    kubectl apply -f 10-data-retrieval.yaml
    kubectl apply -f 11-retriever.yaml
    kubectl apply -f 12-preprocessor.yaml
    kubectl apply -f 13-enricher.yaml
    kubectl apply -f 14-persister.yaml
    echo "✅ Microservices deployed!"
else
    echo "⏸️ Skipping microservices deployment. Update images first!"
fi

# Step 7: Deploy ingress (optional)
echo "🌐 Deploying ingress..."
read -p "Do you want to deploy ingress? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    kubectl apply -f 15-ingress.yaml
    echo "✅ Ingress deployed!"
fi

# Step 8: Deploy network policies (optional)
echo "🔒 Deploying network policies..."
read -p "Do you want to deploy network policies? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    kubectl apply -f 16-network-policies.yaml
    echo "✅ Network policies deployed!"
fi

# Final status check
echo ""
echo "📊 Current deployment status:"
kubectl get all -n kafka-malicious-text

echo ""
echo "🎉 Deployment completed!"
echo ""
echo "📝 Next steps:"
echo "1. Check pod status: kubectl get pods -n kafka-malicious-text"
echo "2. View logs: kubectl logs -f deployment/kafka -n kafka-malicious-text"
echo "3. Port forward UIs:"
echo "   - Kafka UI: kubectl port-forward service/kafka-ui 9080:8080 -n kafka-malicious-text"
echo "   - Mongo Express: kubectl port-forward service/mongo-express 8081:8081 -n kafka-malicious-text"
echo "   - Data Retrieval: kubectl port-forward service/data-retrieval 8082:8082 -n kafka-malicious-text"
echo ""
echo "🔧 To scale services:"
echo "kubectl scale deployment preprocessor --replicas=5 -n kafka-malicious-text"