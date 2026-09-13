# HackAlem Automation v1

## What it adds

- `Automation` page in Team Console.
- Local **HackAlem Developer Center** at `http://127.0.0.1:8766`.
- One-click task creation from `dev`.
- One-click Docker/Backend/Frontend tests.
- One-click `git add → commit → push → Pull Request`.
- Optional **Ship + auto merge**: waits for GitHub CI and merges into `dev` only if checks pass.

## Security model

The Developer Center binds only to `127.0.0.1`. Team Console never receives the Docker socket and cannot execute arbitrary shell commands. Mutating browser requests require a random token generated each time the local helper starts.

Shipping is blocked from `main`, `dev`, and non-`feature/*` branches. `.env`, common private-key/model formats, model directories and files larger than 50 MB are blocked before commit.

## Requirements on each developer machine

- Git
- Docker + Docker Compose
- Python 3
- GitHub CLI (`gh`) authenticated once with `gh auth login`

For CachyOS/Arch the installer creates a systemd user service and desktop shortcut.

## Normal workflow

1. Open **HackAlem Developer Center**.
2. Enter a task name → **Start task**.
3. Edit files in the normal IDE/Codex workflow.
4. Press **Run tests** whenever needed.
5. Enter a commit message and press **Ship → PR** or **Ship + auto merge**.

No routine Git/Docker commands are required after installation.

Autodeploy smoke test: 2026-09-14.
