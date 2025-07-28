# Use a lightweight Python base image compatible with AMD64
FROM --platform=linux/amd64 python:3.9-slim-bullseye

# Set environment variables for better Python behavior in containers
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Set the working directory in the container
WORKDIR /app

# Install system dependencies if needed (minimal)
RUN apt-get update && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/*

# Copy the requirements file first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Download NLTK data during the build process
RUN python -c "import nltk; nltk.download('punkt', download_dir='/usr/local/nltk_data')"
RUN python -c "import nltk; nltk.download('stopwords', download_dir='/usr/local/nltk_data')"
ENV NLTK_DATA=/usr/local/nltk_data

# Copy the application code into the container
COPY app.py .
COPY process_pdfs.py .

# Make the processing script executable
RUN chmod +x process_pdfs.py

# Create directories for input and output (will be mounted)
RUN mkdir -p /app/input /app/output

# Health check to ensure the container is working
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import fitz; print('PyMuPDF OK')" || exit 1

# Command to run the batch processing script
CMD ["python3", "process_pdfs.py"]


COPY config.py .


