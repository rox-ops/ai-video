# Debugging "Failed to Fetch" Error

## Quick Fix - Restart the Backend

The backend code was updated but the process is still running an old version. To fix:

### Option 1: Using the Browser Debug Console
1. Open your browser (where you have the app open at localhost:3000)
2. Press **F12** to open Developer Tools
3. Go to the **Console** tab
4. Try to look for red error messages
5. Check the **Network** tab to see what request is failing and what error it returns

### Option 2: Kill and Restart Backend
Open a terminal and run:

```bash
# Kill the existing backend process
lsof -ti:8000 | xargs kill -9 2>/dev/null || true

# Go to backend directory
cd /workspaces/ai-video/videoapp/backend

# Start fresh backend
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### Option 3: Start Everything From Scratch

```bash
# Terminal 1 - Backend
cd /workspaces/ai-video/videoapp/backend
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000

# Terminal 2 - Frontend  
cd /workspaces/ai-video/videoapp/frontend
python3 -m http.server 3000
```

Then open: **http://localhost:3000**

---

## What I Fixed

1. ✅ Added missing **gTTS** dependency to requirements.txt (for Hindi voice fallback)
2. ✅ Fixed incorrect `genai.Client()` API call in image generation
3. ✅ Added uvicorn startup code to main.py

## Expected Behavior

When you submit a prompt:
1. Backend creates a job and returns a `job_id`
2. Frontend polls `/api/status/{job_id}` every 1.5 seconds
3. You should see progress updates (script → images → audio → rendering)
4. Final video appears when done

If it still fails, check the **Network tab** in browser DevTools to see the exact API error message.
