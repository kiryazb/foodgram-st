FROM python:3.9

WORKDIR /app

COPY . .

RUN pip install --upgrade pip && \
    pip install -r requirements.txt --no-cache-dir

RUN python manage.py migrate --noinput && \
    python manage.py collectstatic --noinput

CMD ["gunicorn", "foodgram.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "4", "--timeout", "120"]