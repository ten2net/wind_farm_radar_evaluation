.PHONY: help install test run docker-build docker-run clean

help:
	@echo "电子战对抗仿真系统 - Makefile"
	@echo ""
	@echo "可用命令:"
	@echo "  make install    安装依赖"
	@echo "  make test       运行测试"
	@echo "  make run        运行应用"
	@echo "  make docker     使用Docker运行"
	@echo "  make clean      清理文件"
	@echo "  make help       显示此帮助"

install:
	pip install -r requirements.txt
	pip install -r requirements-dev.txt

test:
	python -m pytest tests/ -v --cov=src --cov-report=html

run:
	streamlit run app.py

docker-build:
	docker build -t ew-simulation .

docker-run: docker-build
	docker run -p 8501:8501 \
		-v $(PWD)/data:/app/data \
		-v $(PWD)/config:/app/config \
		-v $(PWD)/logs:/app/logs \
		--name ew-simulation \
		ew-simulation

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	rm -rf build/ dist/ *.egg-info/
	rm -rf .pytest_cache/ .coverage htmlcov/
