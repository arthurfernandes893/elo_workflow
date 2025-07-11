# Use an official Python runtime as a parent image
# Using python:3.12-slim as it is a lightweight version of the python image
FROM python:3.12-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file and install dependencies

# Copy the project into the image
ADD . /app

# Sync the project into a new environment, asserting the lockfile is up to date
WORKDIR /app
RUN uv sync --locked

# Copy the rest of the application code into the container
COPY . .

# Expose the port that Streamlit runs on
EXPOSE 8501

# The command to run when the container starts
CMD ["streamlit", "run", "app_dashboard.py"]