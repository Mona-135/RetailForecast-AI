# Makefile for Retail Sales Forecasting & Inventory Planning System

.PHONY: help setup data kafka-producer kafka-consumer etl train evaluate forecast test up down logs backend frontend

help:
	@echo "Available commands:"
	@echo "  make setup          - Set up virtual environment and install dependencies"
	@echo "  make data           - Generate benchmark Walmart dataset"
	@echo "  make up             - Start all Docker infrastructure services"
	@echo "  make down           - Stop all Docker services"
	@echo "  make kafka-producer - Stream sales records into Kafka topic 'retail-sales'"
	@echo "  make kafka-consumer - Consume sales records and stage to HDFS destination"
	@echo "  make etl            - Run PySpark ETL and feature engineering pipeline"
	@echo "  make train          - Train Baseline, SARIMA, and XGBoost models"
	@echo "  make evaluate       - Generate 7 evaluation plots into reports/figures/"
	@echo "  make forecast       - Generate 7-period predictions and inventory plan"
	@echo "  make test           - Run automated test suite using pytest"
	@echo "  make backend        - Launch FastAPI backend locally on port 8000"
	@echo "  make frontend       - Start Vite development server for React dashboard"

setup:
	python -m venv venv
	venv/Scripts/pip install --upgrade pip
	venv/Scripts/pip install -r requirements.txt

data:
	venv/Scripts/python scripts/prepare_dataset.py

up:
	docker compose up -d

down:
	docker compose down

logs:
	docker compose logs -f

kafka-producer:
	venv/Scripts/python kafka/producer.py --file data/raw/train.csv --topic retail-sales

kafka-consumer:
	venv/Scripts/python kafka/consumer.py --topic retail-sales

etl:
	venv/Scripts/python spark/spark_etl.py

train:
	venv/Scripts/python models/train_model.py

evaluate:
	venv/Scripts/python models/evaluate.py

forecast:
	venv/Scripts/python models/forecast.py --store 1 --dept 1 --horizon 7

test:
	venv/Scripts/pytest -v

backend:
	venv/Scripts/uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload

frontend:
	cd frontend && npm run dev
