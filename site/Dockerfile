FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY entrypoint.sh /app/entrypoint.sh
RUN sed -i 's/\r$//' /app/entrypoint.sh && chmod +x /app/entrypoint.sh

COPY ITRexHelper /app/ITRexHelper

WORKDIR /app/ITRexHelper

EXPOSE 8090

ENTRYPOINT ["sh", "/app/entrypoint.sh"]
CMD ["gunicorn", "ITRexHelper.wsgi:application", "--bind", "0.0.0.0:8090", "--workers", "2"]
