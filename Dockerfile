# Use a minimal base image with a static ffmpeg build
FROM jrottenberg/ffmpeg:5.1-alpine

# 1. Install Python and pip
RUN apk add --no-cache python3 py3-pip

# 2. Set up the working directory
WORKDIR /app

# 3. Copy the application script and web viewer into the container
COPY app.py web.py ./
COPY static/ ./static/

# 4. Install web viewer dependencies
RUN pip3 install --no-cache-dir fastapi uvicorn httpx

# 5. Set the command to run the Python script
# Using -u for unbuffered output, which is good for logging in containers
ENTRYPOINT ["python3", "-u", "app.py"]
