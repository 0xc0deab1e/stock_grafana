FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Set PYTHONPATH to include the current directory for imports to work
ENV PYTHONPATH=/app

# Run the script
CMD ["python", "-u", "main.py"]
