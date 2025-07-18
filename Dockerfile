# Use an official uv runtime as a parent image which is based on python:3.12-slim
FROM python:3.12-slim-bookworm
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Set the working directory in the container
WORKDIR /app

# Copy project definition and lock file to leverage Docker layer caching
COPY pyproject.toml uv.lock ./

# Copy the project into the image
ADD . /app

RUN uv sync --locked

# Install dependencies using uv
RUN uv sync --locked

# Copy the rest of the application code into the container
COPY . .

# Expose the port that Streamlit runs on
EXPOSE 8501

# The command to run when the container starts
CMD ["streamlit", "run", "app_dashboard.py"]