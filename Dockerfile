# We use the official Python 3.11 slim image as our base
FROM python:3.11-slim

# Set the working directory inside the container
WORKDIR /app

# Copy the requirements file into the container
COPY data_ingestion_crawler/requirements.txt .

# Install the Python dependencies (no cache to keep the image small)
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
# We copy from the root because we want access to the .env for local testing,
# But in production, Container Apps will inject environment variables securely.
COPY data_ingestion_crawler /app/data_ingestion_crawler

# Expose port 80 (The port Azure Event Grid will hit)
EXPOSE 80

# Command to run the FastAPI application
CMD ["uvicorn", "data_ingestion_crawler.app:app", "--host", "0.0.0.0", "--port", "80"]
