#!/bin/bash

# === Load Environment Variables from .env File ===
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
fi

# === Configuration ===
AWS_REGION="us-west-2"
AWS_ACCOUNT_ID="${AWS_ACCOUNT_ID:?AWS_ACCOUNT_ID is required}"  # Load from .env
REPO_NAME="trading"
LAMBDA_FUNCTION_NAME="tradingview-alpaca"

# Get the ECR URL
ECR_URL="$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$REPO_NAME"

# === Step 1: Authenticate with AWS ECR ===
echo "🔑 Logging into AWS ECR..."
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $ECR_URL

# === Step 2: Build the Docker Image ===
echo "🐳 Building the Docker image..."
docker build -t $REPO_NAME .

# === Step 3: Tag and Push the Image to AWS ECR ===
echo "🏷️ Tagging and pushing the Docker image to AWS ECR..."
docker tag $REPO_NAME:latest $ECR_URL:latest
docker push $ECR_URL:latest

# === Step 4: Deploy to AWS Lambda ===
echo "🚀 Deploying new image to AWS Lambda..."
aws lambda update-function-code --function-name $LAMBDA_FUNCTION_NAME --image-uri $ECR_URL:latest

echo "✅ Deployment complete!"
