#!/bin/bash
set -euo pipefail

AWS_PROFILE="algo-trading"
AWS_REGION="us-west-2"
AWS_ACCOUNT_ID="767828760457"
REPO_NAME="algo-trading"
ECR_URL="$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$REPO_NAME"

echo ">>> 构建镜像..."
docker build --platform linux/amd64 -t $REPO_NAME .

echo ">>> 登录 ECR..."
aws ecr get-login-password --region $AWS_REGION --profile $AWS_PROFILE | \
    docker login --username AWS --password-stdin $ECR_URL

echo ">>> 推送镜像..."
docker tag $REPO_NAME:latest $ECR_URL:latest
docker push $ECR_URL:latest

echo ">>> 完成: $ECR_URL:latest"
