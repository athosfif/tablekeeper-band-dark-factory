FROM python:3.12-slim-bookworm@sha256:392307d22300de8b5986851a12d9176dfc0fc073e65bf6523ebd7dcbeb23564e
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PORT=8080
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends fonts-liberation2 && rm -rf /var/lib/apt/lists/* && mkdir -p /app/static && cp /usr/share/fonts/truetype/liberation2/LiberationSerif-Regular.ttf /app/static/Serif-Regular.ttf && cp /usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf /app/static/Sans-Regular.ttf && cp /usr/share/doc/fonts-liberation2/copyright /app/static/FONT-LICENSE
COPY --chmod=644 json_values.py legacy_model.py stage2_model.py model.py engine.py server.py ./
COPY --chmod=755 static/ ./static/
USER 65534:65534
EXPOSE 8080
CMD ["python", "server.py"]
