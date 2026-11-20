import sys

from game import Battleship

if __name__ == "__main__":
    # Optional: python main.py 42  -> same ship layout and AI moves every run.
    seed = int(sys.argv[1]) if len(sys.argv) > 1 else None
    Battleship(seed=seed).run()
