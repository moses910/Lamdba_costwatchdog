# Contributing Guide

## Development Setup

1. Fork the repository
2. Clone your fork
3. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
4. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Testing

Run tests with:
```bash
python -m pytest tests/
```

## Code Style

- Follow PEP 8
- Use type hints
- Write docstrings for functions

## Pull Requests

1. Create a feature branch
2. Make your changes
3. Add tests
4. Ensure all tests pass
5. Submit a pull request