FROM python:3.12-slim-bookworm
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PORT=8080
WORKDIR /app
# Debian supplies the IANA database locally; assert it during the build.
RUN python -c "from zoneinfo import ZoneInfo; ZoneInfo('Europe/Berlin'); ZoneInfo('America/New_York')"
COPY *.py /app/
RUN chmod 644 /app/*.py
USER 65534:65534
EXPOSE 8080
CMD ["python", "server.py"]
