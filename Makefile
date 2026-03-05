.PHONY: help run test clean manual-screenshots

# Default target
help:
	@echo "Space Battle Duel - Makefile"
	@echo "---------------------------"
	@echo "run   : Start the game"
	@echo "test  : Run all unit tests"
	@echo "capture-gif : Capture scripted 10-second gameplay GIF with caption"
	@echo "manual-screenshots : Regenerate manual screenshots in docs/images/manual"
	@echo "help  : Show this help message"
	@echo "clean : Remove python cache files"

run:
	uv run python -m src.main

test:
	PYTHONPATH=. uv run python -m coverage run --source=src -m unittest discover tests
	uv run python -m coverage report -m

test-docs:
	PYTHONPATH=. uv run phmdoctest docs/manual.md --outfile tests/test_manual_doctest.py
	PYTHONPATH=. uv run python -m pytest tests/test_manual_doctest.py
	rm tests/test_manual_doctest.py

capture-gif:
	./scripts/capture_demo_gif.sh --duration 10 --output assets/demo/gameplay.gif --fps 20

manual-screenshots:
	uv run python -m src.tools.capture_manual_screenshots

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
