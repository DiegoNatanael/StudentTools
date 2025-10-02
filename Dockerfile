# Use a slim Python base image
FROM python:3.9-slim-bullseye

# Set the working directory in the container
WORKDIR /app

# Copy your requirements file and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your application code and frontend files
COPY . .

# Expose the port your FastAPI application will listen on
EXPOSE 8000

# Command to run your FastAPI application with Uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]