# Logic Puzzles

## Development

- `game_state` is the initial_state
- `game_board` is the solution_state

Ensure you have `python3`, and `npm` installed to develop this project.

The default environment variables run the app in debug mode. The `Dockerfile` that builds this webapp will ensure the app is run in production mode, where the only required environment variables will be `SECRET_KEY` and `DATABASE_URL`.

1. Open in VSCode (I have tasks inside `.vscode/tasks.json` to make setup easy)
2. Setup your python virtual environment. Use your preferred method or the following command to set one up locally. Either way, ensure that it is selected in vscode with `Python: Select Interpreter` from the command palette.
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```
3. Setup the npm environment: `cd frontend && npm install`
4. Run the task titled `frontend+backend: run dev servers`
5. Open [http://localhost:3000](http://localhost:3000)


## Deployment
1. Run the following commands from the root of the project
```bash
# build container with
docker build . -t logicapp

# run deployed version locally with
docker run -it -p "8000:8000" --rm logicap
```

# Determine if game has correct solution
- Kakurasu (non-strict):    Only check for `1` which means `black cell`
- Kakurasu (strict):        `1` means `black cell`, 0 means `red cross`
- Sudoku (only strict):      The input must match the solution exactly
- Lightup (non-strict):     Only check for `7` which means `lighted cell`
- Minesweeper (non-strict): Only check for `10` which means 'flag'
- Minesweeper (strict):     `10` == 'flag', `11` == 'safe'
