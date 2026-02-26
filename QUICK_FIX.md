# Fix Interview Scoring - Quick Setup

## The Issue
User answers in interviews are getting a score of **50** (default) instead of real scores from Gemini.

## Root Cause
The Gemini API is not being called properly. Most likely reasons:
1. ❌ GEMINI_API_KEY not set in `.env` file
2. ❌ API key is invalid or expired
3. ❌ Backend not restarted after adding API key

## Quick Fix (3 Steps)

### Step 1: Get Your Gemini API Key
1. Go to: https://ai.google.dev/
2. Click "Get API Key" button
3. Choose or create a project
4. Copy the API key (long text starting with "AIza..." or similar)

### Step 2: Add to .env File
**File**: `backend/.env`

```
GEMINI_API_KEY=paste_your_key_here
```

Example (this key is fake, use your real one):
```
GEMINI_API_KEY=AIzaSyD_2qQ8K9hRqKj5xZ8q_ZxJqK_zxK9qKj5
```

### Step 3: Restart Backend
```bash
# In terminal where backend is running:
# Press Ctrl + C to stop

# Then restart:
cd backend
python -m uvicorn app.main:app --reload
```

Look for this in the console:
```
   - Gemini API Key: AIzaSyD***
```

If you see that ✓ it means API key is loaded!

---

## Test It's Working

### Test 1: Check API (Easiest)
Open in browser:
```
http://localhost:8000/test-gemini
```

You should see:
```json
{
  "gemini_configured": true,
  "api_key_set": true,
  "test_call_success": true,
  "error": null
}
```

### Test 2: Submit Interview Answer
1. Start a new interview
2. Answer a question (type something real)
3. Submit answer
4. **Score should NOT be 50** (unless actual evaluation is low)

If score is 75, 82, 45, 60 (anything but 50) ✓ **It's working!**

---

## Check Backend Logs

When you submit an answer, look in the backend terminal for:

**Good (working):**
```
[Evaluator] API Key configured: True
[Evaluator] Gemini response received: {"score": 78...
[Evaluator] Final score: 78
```

**Bad (not working):**
```
[ERROR] GEMINI_API_KEY not configured!
```

---

## Still Not Working?

1. **Stop backend** - Press Ctrl+C in terminal
2. **Edit .env file** - Add/verify GEMINI_API_KEY
3. **Save file** - Make sure file is saved
4. **Start backend** - Run: `python -m uvicorn app.main:app --reload`
5. **Wait 5 seconds** - Let it initialize  
6. **Test again** - Submit an interview answer

---

## If API Key Error

If you see error like:
- "Invalid API key"
- "Unauthorized"
- "API key error"

**Solutions:**
1. Go back to https://ai.google.dev/ 
2. Delete the old key and generate a **new** one
3. Copy the new key carefully (watch for spaces)
4. Update `.env` with new key
5. Restart backend

---

## Verify Setup

**Backend startup should show:**
```
🚀 Starting AI Virtual Interviewer Backend
   - App: AI Virtual Interviewer
   - Version: 1.0.0
   - Debug: True
   - Gemini API Key: AIzaSyD***
```

If you see `Gemini API Key: AIzaSyD***` ✓ **All set!**
If you see `⚠️ GEMINI_API_KEY not set!` ❌ **Need to fix**

---

## Expected Results After Fix

### Before Fix
- Submit answer → Always get score 50
- No variation based on answer quality

### After Fix  
- Submit answer → Get real score (65-85 for decent answer)
- Different answers get different scores
- Feedback is specific to the answer given

---

## Files You Edited/Need

| File | Purpose |
|------|---------|
| `backend/.env` | Add GEMINI_API_KEY here |
| `backend/app/services/interview_evaluator.py` | Evaluates answers (FIXED) |
| `backend/app/main.py` | Added /test-gemini endpoint |

---

## One-Minute Verification

```bash
# 1. Check backend is running
# Should see: "Gemini API Key: AIzaSyD***"

# 2. Test Gemini connection
curl http://localhost:8000/test-gemini
# Should show: "test_call_success": true

# 3. Submit interview answer
# Score should NOT be 50

# Done! ✓
```

---

## Need More Help?

1. Check **DEBUGGING_GUIDE.md** for detailed troubleshooting
2. Look at backend logs when submitting answer
3. Search for `[ERROR]` in logs to find issues
4. Use `/test-gemini` endpoint to verify Gemini connection

---

**Status**: After these 3 steps, your interview scoring will work! 🎉
