# Use an official Python runtime as a parent image
FROM --platform=linux/amd64 python:3.9.0-slim
# FROM python:3.8-slim

# Set the working directory in docker
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install any needed packages specified in requirements.txt
# RUN pip install -r requirements.txt
RUN pip install --trusted-host pypi.python.org -r requirements.txt

# Make port 5000 available to the world outside this container
EXPOSE 5000

# Define environment variable
ENV FLASK_APP=application.py
ENV FLASK_RUN_HOST=0.0.0.0

# Run your_flask_app.py when the container launches
CMD ["flask", "run"]