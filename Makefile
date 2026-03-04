.PHONY: help run test clean

# Default target
help:
	@echo "Space Battle Duel - Makefile"
	@echo "---------------------------"
	@echo "run   : Start the game"
	@echo "test  : Run all unit tests"
	@echo "capture-gif : Capture a 10-second gameplay GIF to assets/demo/gameplay.gif"
	@echo "help  : Show this help message"
	@echo "clean : Remove python cache files"

run:
	uv run python -m src.main

test:
	PYTHONPATH=. uv run python -m coverage run --source=src -m unittest discover tests
	uv run python -m coverage report -m

test-docs:
	PYTHONPATH=. phmdoctest docs/manual.md --outfile tests/test_manual.py
	PYTHONPATH=. uv run python -m pytest tests/test_manual.py
	rm tests/test_manual.py

capture-gif:
	./scripts/capture_demo_gif.sh --duration 10 --output assets/demo/gameplay.gif --fps 20 --display :0.0 --geometry 1280x720

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
