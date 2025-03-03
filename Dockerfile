# Use AWS Lambda Python runtime as base image
FROM public.ecr.aws/lambda/python:3.10

# Set working directory
WORKDIR /var/task

# Copy requirements.txt and install dependencies
COPY src/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy Lambda function
COPY src/lambda_function.py .

# Set the command to run the Lambda function
CMD ["lambda_function.lambda_handler"]