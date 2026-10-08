# From zero to a public link (Windows)
**Step 1 - Install tools.** Install Python 3.11+ from python.org (tick "Add Python to PATH") and Git from git-scm.com. Open *Command Prompt*; check `py --version` and `git --version`.
**Step 2 - Unzip** `ozolab-ai.zip` to `C:\Projects\ozolab-ai` (folder must contain `app.py` directly).
**Step 3 - Dataset location.** Already at `data\raw\ACS_EngAu_2026_TableS1.xlsx`. If missing: unzip `eg5c00088_si_001.zip`, copy `ACSEngAu_ML_PPM_Table_S1.xlsx` there under that name.
**Step 4 - Install dependencies:** `cd C:\Projects\ozolab-ai` then `py -m venv .venv`, `.venv\Scripts\activate`, `pip install -r requirements.txt`.
**Step 5 - Test locally:** `streamlit run app.py` -> browser opens http://localhost:8501. Click every page in the left sidebar. (Optional: `python tests\test_smoke.py`.) Stop with Ctrl+C.
**Step 6 - Create the GitHub repository.** Go to github.com -> sign in -> top-right "+" -> *New repository*. Name: `ozolab-ai`. Choose **Public**. Do NOT tick README/.gitignore/licence. Click *Create repository*.
**Step 7 - Push the files** (in Command Prompt, inside the project folder):
```
git init
git add .
git commit -m "OzoLab AI first version"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/ozolab-ai.git
git push -u origin main
```
(Use your real username. If asked to log in, use the browser window that opens.) Files that must be committed: everything in the folder, **including** `models/*.joblib`, `data/`, `config/`, `Project_Archive/`, `requirements.txt`. `.venv` is excluded by `.gitignore`. No secrets exist in the project.
**Step 8 - Streamlit Community Cloud.** Open share.streamlit.io -> *Continue with GitHub* -> authorise. Click *Create app* -> *Deploy a public app from GitHub*.
**Step 9 - Fill the form:** Repository `YOUR_USERNAME/ozolab-ai`; Branch `main`; Main file path `app.py`; (optional) pick your own sub-domain, e.g. `ozolab-ai`. Click **Deploy**.
**Step 10 - Wait 2-5 minutes.** "Your app is in the oven" log appears; when it finishes the dashboard opens at `https://<subdomain>.streamlit.app` - that is your public URL.
**Step 11 - Verify:** open the URL on your phone (mobile data, not Wi-Fi) and click all 10 pages.
**Step 12 - Update later:** edit files, then `git add .`, `git commit -m "update"`, `git push`. Streamlit redeploys automatically.
## Common errors
- *ModuleNotFoundError*: package missing in `requirements.txt` -> add it, push.
- *FileNotFoundError ... xlsx*: dataset not committed -> `git add -f data/raw/ACS_EngAu_2026_TableS1.xlsx`, push.
- *Model version mismatch / sklearn unpickle warning*: harmless; the app retrains automatically in seconds.
- *App sleeping*: click "Yes, get this app back up".
- *Experiments vanished*: Cloud storage is temporary - download `experiments.csv` from Experiment History each session and commit it to `data/own/`.
- *git push rejected*: run `git pull origin main --rebase` then push again.
