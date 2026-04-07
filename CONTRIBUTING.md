# Contributing to Paner

Thanks for your interest in improving Paner! Contributions are welcome whether you want to fix a bug, expand the CLI, or improve docs. This guide outlines the preferred workflow.

## Getting Started

1. **Fork and clone** the repository.
2. **Create a virtual environment** (e.g., `python -m venv .venv && source .venv/bin/activate`).
3. **Install dependencies** in editable mode:
   ```bash
   pip install -e .
   ```
4. **Install dev tools** you plan to use (e.g., `ruff`, `black`, `pytest`).

## Development Workflow

1. **Create a branch** for your change:
   ```bash
   git checkout -b feature/your-change
   ```
2. **Make your changes** with clear commits and descriptive messages.
3. **Run tests / manual checks:**
   - Exercise the CLI (`paner`) against sample PDFs.
   - If you add functionality that can be automated, include tests.
4. **Format & lint** (recommended):
   ```bash
   ruff check .
   black src
   ```

## Submitting Changes

1. **Push your branch** to your fork.
2. **Open a Pull Request** against `main`, describing the change, motivation, and any testing steps.
3. **Respond to feedback** promptly; reviewers may request tweaks or additional verification.

## Reporting Issues

If you encounter a bug or have a feature idea:

- Search existing issues to avoid duplicates.
- Include reproduction steps, logs, and environment details.

## Code of Conduct

Please keep discussions respectful and constructive. Harassment or offensive behavior won’t be tolerated.

Thanks for helping make Paner better!
