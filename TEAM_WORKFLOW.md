# Team workflow

Use Git, not WhatsApp/Google Drive, for source code.

Recommended branches:
- `main` — stable demo version;
- `dev` — shared integration;
- `feature/frontend-*` — frontend work;
- `feature/backend-*` — backend/API work;
- `feature/ai-*` — AI/RAG/tools;
- `fix/*` — bug fixes.

Example:

```bash
git checkout dev
git pull
git checkout -b feature/frontend-chat
# work
git add .
git commit -m "feat(frontend): add chat workspace"
git push -u origin feature/frontend-chat
```

Then open a Pull Request into `dev`.

Frontend and backend checks are separate CI jobs, so a frontend build error does not hide backend status and vice versa.

Before the demo, freeze large changes 60–90 minutes early, merge only tested fixes into `main`, make a DB backup, and run the demo flow twice.
