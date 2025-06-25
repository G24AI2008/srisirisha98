# Use official Python image
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Copy source code
COPY src/ /app/

# Install dependencies
RUN pip install flask

# Expose port
EXPOSE 5000

# Run the node
CMD ["python", "node.py"]
