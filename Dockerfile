from python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt
COPY . /app/

EXPOSE 8000

ENV SECRET_KEY=dummy-key-for-build-time-only
RUN python manage.py collectstatic --noinput

CMD ["gunicorn", "core.wsgi:application","--bind", "0000:8000"]