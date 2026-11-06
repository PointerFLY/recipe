# recipe

This is my personal code snippet collection.
Feel free to view, use or copy.

Python dependencies for the whole repository are managed with [uv](https://docs.astral.sh/uv/).
Use Python 3.11 or newer. From the repository root, install the locked dependencies:

```sh
uv sync --locked
```

One shared `.venv` serves all Python projects. Dependencies are declared in the
root `pyproject.toml`; `uv.lock` records the resolved versions. Add or remove
repository dependencies with `uv add PACKAGE` or `uv remove PACKAGE`.

Run scripts through the shared environment:

```sh
uv run python chopsticks/play_ai.py
uv run python chopsticks/solve.py
uv run python wordy/wordy.py --help
```

SciPy supports compact policy optimization in Chopsticks. NumPy, Matplotlib,
and OpenCV support the image-color example in `kmeans/colorspace.py`, which
expects an `img.jpg` in the working directory.

Chopsticks tests live in `chopsticks/tests/`. Run them from the repository root:

```sh
uv run python -m unittest discover -s chopsticks/tests -v
```

See [Chopsticks](chopsticks/README.md) for game rules and strategy details.
