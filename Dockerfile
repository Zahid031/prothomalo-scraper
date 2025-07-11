# Use an official Python runtime as a parent image
FROM python:3.11

# Upgrade pip and system packages to reduce vulnerabilities
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app


COPY requirements.txt /app/
RUN pip install --upgrade pip && pip install -r requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app/

EXPOSE 8000

# CMD ["gunicorn", "--bind", "0.0.0.0:8000", "prothomalo_api.wsgi:application"]
