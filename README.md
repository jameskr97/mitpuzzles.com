<div align="center">
  <picture>
      <source media="(prefers-color-scheme: dark)" srcset="frontend/public/assets/logo.light.png" width="250px">
      <img alt="mitpuzzles.com logo" src="frontend/public/assets/logo.dark.png" width="250px">
    </picture>
  <h3 align="center">mitpuzzles.com</h3>
</div>

## Development

Ensure you have `python3`, and `npm` installed to develop this project.

The default environment variables run the app in debug mode. The `Dockerfile` that builds this webapp will ensure the app is run in production mode, where the only required environment variables will be `SECRET_KEY` and `DATABASE_URL`.

1. Open in VSCode (I have tasks inside `.vscode/tasks.json` to make setup easy)
2. Setup your python virtual environment. Use your preferred method or the following commands to set one up locally. Either way, ensure that it is selected in vscode with `Python: Select Interpreter` from the command palette.
```bash
cd backend
uv venv
source .venv/bin/activate
uv sync
```
3. Setup the npm environment: `cd frontend && npm install`
4. Run the task titled `frontend+backend: run dev servers`
5. Open [http://localhost:3000](http://localhost:3000)

### New Feature
In general, I prefer to squash all commits realted to a single feature.  How I set a new feature:

```bash
git checkout -b feat/new-feature
# make changes...
git add .
git commit -m "wip: whatever"
git commit -m "wip: more stuff"
# when ready to merge
git checkout main
git merge --squash feat/new-feature
git commit -m "feat: description of complete feature"
```

## Deployment
1. Run the following commands from the root of the project
```bash
# build container with
docker build . -t mitpuzzles

# run deployed version locally with
docker run -it -p "8000:8000" --rm mitpuzzles
```
