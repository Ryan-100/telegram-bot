FROM python:3.12-slim
WORKDIR /app
COPY bot.py .
ENV DATA_FILE=/data/data.json
VOLUME ["/data"]
CMD ["python", "-u", "bot.py"]
