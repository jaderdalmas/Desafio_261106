FROM python:3.12-slim

WORKDIR /app

COPY . .

RUN pip install -e .

CMD ["python","-m","battery_optimizer.cli.main"]