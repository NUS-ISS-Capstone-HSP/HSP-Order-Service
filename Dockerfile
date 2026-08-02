FROM python:3.12-alpine3.23

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

RUN addgroup -S app && adduser -S -G app app

COPY --chown=app:app . .

EXPOSE 8080
EXPOSE 50051

USER app

CMD ["python", "-m", "hsp_order_service.main"]
