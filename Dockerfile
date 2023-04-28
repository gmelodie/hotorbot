FROM python:3.8-slim-buster

WORKDIR /app
VOLUME /app

COPY requirements.txt .

RUN pip3 install --no-cache-dir -r requirements.txt

COPY . .

# Expose the port that the app will run on
EXPOSE 5000

ENV FLASK_ENV=production

CMD ["gunicorn", "app:app", "-b", "0.0.0.0:5000", "-w", "4"]


