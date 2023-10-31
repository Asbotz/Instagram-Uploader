# Use the official Python image as a parent image
FROM python:3.8-slim

# Create a working directory for the bot
WORKDIR /app

# Copy the bot script into the container
COPY bot.py .

# Copy the requirements file into the container
COPY requirements.txt .

# Install the required packages
RUN apt-get update && \
    apt-get install -y ffmpeg && \
    pip install --no-cache-dir -r requirements.txt

# Run the bot
CMD ["python", "bot.py"]
