# Lab 4: VibeCoding (Scenario 19: Battleship vs AI)

**SRN:** PES2UG24CS022
**Assigned repo:** [SETAPESU26/19_battleship](https://github.com/SETAPESU26/19_battleship) (cloned; no PR raised to SETAPESU26)

| Deliverable | File |
|---|---|
| Video before changes (10 s) | [`videos/before_changes.mp4`](videos/before_changes.mp4) |
| Video after changes (12 s) | [`videos/after_changes.mp4`](videos/after_changes.mp4) |
| Updated code | [`battleship/`](battleship/) |
| LLM chat history | [`PES2UG24CS022_Lab4_Chat_History.pdf`](PES2UG24CS022_Lab4_Chat_History.pdf) / `.docx` |

## Run

```bash
cd Lab-4/battleship
python main.py          # random game
python main.py 42       # repeatable game (fixed seed)
python -m unittest -v   # 22 tests
```

Enter shots as `row,col` (1 to 6), for example `2,3`. Type `q` to quit.

## What was fixed and added

- **Task 1: coordinates.** The AI returned 1-based `"r,c"` strings that were compared with 0-based ship cells, so real hits were missed. All modules now use 0-based `(row, col)` tuples; text is converted only in `game.py`.
- **Task 2: fleet and win.** Adds a Cruiser (3), Destroyer (2) and Submarine (2), placed randomly. Each ship's damage is tracked and SUNK is reported by name. Repeated shots are rejected without using a turn. The game ends when either fleet is sunk.
- **Task 3: AI.** After a hit, the AI targets untried neighbouring cells and prefers cells that continue a line of hits. It never repeats a cell and returns `None` when the board is full.
- **Task 4: feedback.** `AI.choose()` only selects a cell. Exactly one HIT, MISS or SUNK line is printed for each real shot.

Git history shows each step: the original code, then the Task 1 fix, then Tasks 2–4. Standard library only; no persistent storage.
