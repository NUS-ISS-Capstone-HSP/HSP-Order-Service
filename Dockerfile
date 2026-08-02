FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

RUN groupadd --system app && useradd --system --gid app --create-home app

COPY --chown=app:app . .

EXPOSE 8080
EXPOSE 50051

USER app

CMD ["python", "-m", "hsp_order_service.main"]
