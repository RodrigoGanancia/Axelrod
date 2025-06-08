# Properties of winning Iterated Prisoner’s Dilemma strategies (Axelrod Library)

## How to run
Create a virtual environment and install the requirements:
```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

You can run the tournaments (will take 8-10 minutes):
```bash
python3 3matchtournament.py
```

Or run the GUI to visualize examples of individual strategies pitting against each other.

You may need to adjust the `SCREEN_HEIGHT` and `SCREEN_WIDTH` variables in `3p_gui.py` to fit your screen resolution. You can also change the `TURNS_PER_MATCH` to see more or less turns
```bash
python3 3p_gui.py
```
