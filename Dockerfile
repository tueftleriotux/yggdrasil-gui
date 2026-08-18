FROM python:3.13-slim

# Optimize Python runtime behavior inside Docker:
# 1. Prevent writing .pyc files to disk
# 2. Force unbuffered stdout/stderr (essential for real-time `docker logs`)
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Copy requirements first to leverage Docker layer caching
COPY requirements.txt /app/
RUN pip install --no-cache-dir --root-user-action ignore -r requirements.txt

# Copy application source code
COPY ./src /app

# Expose the default application port
EXPOSE 9999

CMD ["python3", "main.py"]
