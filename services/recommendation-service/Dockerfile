# Use official Python base image
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install FastAPI and Uvicorn
RUN pip install fastapi uvicorn

# Copy source code
COPY . .

# Command to run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]
