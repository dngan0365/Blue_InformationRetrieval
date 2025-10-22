# Project Information Retrieval

This repository contains code, data processing notebooks, and a small web app used for an information retrieval project. It includes document collection, deduplication, indexing, and a Next.js frontend (with a backend folder for APIs). The repository is intentionally small and modular so you can run the data pipeline locally and explore the frontend.

## Files & Directory Structure

Top-level layout (important files and folders):

- `readme.md` - this file.
- `requirements.txt` - Python dependencies for data processing and notebooks.
- `1.CollectingDocuments/` - Jupyter notebook(s) used to collect and prepare documents.
  - `CollectingDocuments.ipynb` - the main notebook for document collection.
- `2.RemoveDuplicateWeb/` - (pipeline) scripts/notebooks for removing duplicate web content.
- `3.Indexing/` - indexing code and related resources.
- `4.Searching/` - search/index query examples and evaluation code.
- `app/` - web application (frontend + backend)
  - `backend/` - API and server code (implement your API here).
  - `frontend/` - frontend source (if present) — the Next.js app is under `app/` (see files below).
  - `package.json`, `next.config.ts`, `tsconfig.json`, `postcss.config.mjs`, etc. — Node and Next configuration files for the web app.
  - `app/` (inside `app/`) - the Next.js application pages/components (Next 13+ app router), includes `globals.css`, `layout.tsx`, `page.tsx`.
  - `public/` - static assets for the web app.

Note: Some folders may be placeholders or contain experimental code. Inspect each folder for README or run instructions specific to that component.

## Quickstart — system requirements

- OS: Windows / macOS / Linux (examples below use PowerShell for Windows).
- Python 3.8+ (recommended)
- Node.js 16+ (for the Next.js app)

## Installation

1) Clone the repository (if you haven't already):

```powershell
git clone <repo-url>
cd Project_InformationRetrieval
```

2) Python environment (for notebooks, indexing, searching):

```powershell
# create a venv (PowerShell)
python -m venv .venv
# activate
.\.venv\Scripts\Activate.ps1
# install Python deps
python -m pip install --upgrade pip
pip install -r requirements.txt
```

3) (Optional) Install Jupyter if not already present and run the notebook:

```powershell
pip install jupyterlab
# start Jupyter Lab and open the notebook
jupyter lab 1.CollectingDocuments\CollectingDocuments.ipynb
```

4) Frontend (Next.js app):

```powershell
cd app
npm install
# start the development server
npm run dev
# open http://localhost:3000 in your browser
```

5) Backend: inspect `app/backend/` for server code or API instructions. If the backend is a Node or Python service, follow instructions inside that folder (or run your preferred server). If there's no explicit backend implementation, the frontend may be a static demo that calls public APIs or mocks.

## Running the Parts

- Notebook (data collection & preprocessing): open `1.CollectingDocuments/CollectingDocuments.ipynb` in Jupyter Lab/Notebook and run cells top-to-bottom. The notebook contains the data collection steps and basic examples.
- Indexing and Searching: see `3.Indexing/` and `4.Searching/` for scripts or helper modules. Typical flow: run preprocessing (notebook), run indexing scripts to build an index, then use search scripts to query the index.
- Web App: run the Next.js app under `app/` as shown above. The app will typically serve the UI and call APIs under `app/backend/` if implemented.

## Notes & Tips

- If you add large datasets, keep them out of Git; use a data directory and .gitignore.
- For reproducibility, pin Python package versions in `requirements.txt` and Node versions in `package.json` (use an `.nvmrc` or engines field if needed).
- If you see TypeScript or build errors in the frontend, run `npm run build` in `app/` to get the full diagnostics.

## Contributing

1. Create an issue describing the change or bug.
2. Create a feature branch, make your changes, and open a PR.

## License

Add your license here (MIT, Apache-2.0, etc.).

---

If you'd like, I can also:
- Add per-folder README files (for `2.RemoveDuplicateWeb`, `3.Indexing`, `4.Searching`, `app/backend`).
- Create a simple start script to run the entire pipeline (notebook -> index -> search) locally.

Tell me which you'd like next.
