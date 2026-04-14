# janus — Open Source Contribution Guide. Beginner-friendly open source contribution guide

*Janus — two-faced Roman god of beginnings.*

janus takes its name in that spirit. Open Source Contribution Guide. Beginner-friendly open source contribution guide.

## Why janus

janus exists to make this workflow practical. Open source contribution guide. beginner-friendly open source contribution guide. It favours a small, inspectable surface over sprawling configuration.

## Features

- `Step` — exported from `src/janus/core.py`
- `Workflow` — exported from `src/janus/core.py`
- Included test suite

## Tech Stack

- **Runtime:** Python

## How It Works

The codebase is organised into `src/`, `tests/`. The primary entry points are `src/janus/core.py`, `src/janus/__init__.py`. `src/janus/core.py` exposes `Step`, `Workflow` — the core types that drive the behaviour.

## Getting Started

```bash
pip install -e .
```

## Usage

```python
from janus.core import Step

instance = Step()
# See the source for the full API
```

## Project Structure

```
janus/
├── CLAUDE.md
├── LICENSE
├── README.md
├── index.html
├── pyproject.toml
├── src/
├── tests/
```
