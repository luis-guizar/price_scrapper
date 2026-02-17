FROM mcr.microsoft.com/playwright/python:v1.58.0-jammy

WORKDIR /code

ENV TZ=America/Mexico_City
RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y tzdata && \
    ln -fs /usr/share/zoneinfo/$TZ /etc/localtime && \
    echo $TZ > /etc/timezone && \
    dpkg-reconfigure --frontend noninteractive tzdata

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers (Chromium only to save space/time if possible, but the base image has them)
# The base image mcr.microsoft.com/playwright/python ALREADY has browsers installed!
# We just need to ensure dependencies are met.

COPY . .