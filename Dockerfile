# Use an official Python runtime as a parent image
FROM python:3.11-alpine

WORKDIR /app

COPY . /app

RUN apk update && apk add -y --no-install-recommends --no-cache libmagic
RUN curl -fsSL https://ollama.com/install.sh | sh

RUN chmod +x install.h && ./install.h

# Make port 5000 available to the world outside this container
EXPOSE 5000

# Environment variable for Hypercorn to run the app on port 5000
ENV PORT=5000


CMD ["hypercorn", "--workers=3", "--bind", "0.0.0.0:5000", "app:app"]
