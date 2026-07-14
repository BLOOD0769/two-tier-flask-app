# ---------------------------------------------------------------
# Dockerfile - builds the Flask app into a container image
# ---------------------------------------------------------------

# Start from a small, official Python image (keeps the image size down)
FROM python:3.12-slim

# Set the working directory inside the container
WORKDIR /app

# Copy only the requirements file first.
# Docker caches layers - this means if requirements.txt doesn't change,
# Docker won't re-install dependencies every time you rebuild, which
# makes builds much faster.
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Now copy the rest of the application code into the container
COPY . .

# Tell Docker this container listens on port 5000
EXPOSE 5000

# Run the app using gunicorn (a production-grade WSGI server),
# NOT the Flask development server, which is not safe/stable for real use.
# --bind 0.0.0.0:5000 makes it reachable from outside the container.
# --workers 3 runs 3 worker processes to handle multiple requests.
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "3", "app:app"]
