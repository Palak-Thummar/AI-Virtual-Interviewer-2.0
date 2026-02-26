# Debugging Guide - Interview Score Issue

## Problem
Interview answers are always getting a score of 50 (default fallback), not real scores from Gemini.

## Solution Steps

### Step 1: Check Gemini API Key
**File**: `.env`

Make sure you have:
```
GEMINI_API_KEY=your_actual_api_key_here
```

⚠️ **Common Issues:**
- Missing API key entirely
- API key has extra spaces: `GEMINI_API_KEY= [SPACE] key` 
- Wrong API key (copy-paste error)
- API key from wrong Google project

### Step 2: Test Gemini Connection

**Option A: Using the diagnostic endpoint**
```
GET http://localhost:8000/test-gemini
```

Expected response:
```json
{
  "gemini_configured": true,
  "api_key_set": true,
  "test_call_success": true,
  "error": null
}
```

If you see `false` values or an error, check your API key.

**Option B: Run diagnostic script** (from backend directory)
```bash
python test_gemini.py
```

This will test:
1. API key is set ✓
2. Gemini can be called ✓
3. JSON parsing works ✓
4. Interview evaluation format works ✓

### Step 3: Check Backend Logs

When you submit an answer, look for these logs in the terminal running the backend:

**Good logs (will show real score):**
```
[Evaluator] Starting evaluation...
[Evaluator] Question: What is Python?...
[Evaluator] Answer: It is a programming...
[Evaluator] API Key configured: True
[Evaluator] Gemini response received: {"score": 75...
[Parser] ✓ Successfully parsed JSON directly
[Evaluator] Final score: 75
```

**Bad logs (will show score 50):**
```
[ERROR] GEMINI_API_KEY not configured!
```

OR

```
[Evaluator] Starting evaluation...
[Evaluator] API Key configured: False  ← PROBLEM HERE
```

### Step 4: Monitor Backend Output

**Start backend with logging:**
```bash
cd backend
python -m uvicorn app.main:app --reload
```

Watch the terminal output carefully when you submit an answer. You should see detailed logs like:
```
[Evaluator] Starting evaluation...
[Evaluator] Gemini response received: ...
[Parser] Successfully parsed JSON...
[Evaluator] Final score: XX
```

### Step 5: Test Manually

**Using curl or Postman:**

1. Get interview ID and resume ID from your database or previous requests
2. Submit an answer:
```bash
curl -X POST "http://localhost:8000/api/interview/{interview_id}/submit-answer" \
  -H "Authorization: Bearer {your_token}" \
  -H "Content-Type: application/json" \
  -d '{
    "question_id": 0,
    "answer": "This is my detailed answer to the question about Python programming and its applications."
  }'
```

3. Check the response - it should have a real score, not 50
4. Check backend logs for debug info

---

## Quick Checklist

- [ ] `.env` file exists in backend directory
- [ ] GEMINI_API_KEY is set in `.env`
- [ ] API key is valid (test with `/test-gemini` endpoint)
- [ ] Backend is running and shows "Gemini API Key: ..." in startup logs
- [ ] Backend logs show `[Evaluator] Starting evaluation...` when you submit answer
- [ ] Response score is different from 50

---

## Common Issues & Solutions

### Issue 1: Still getting score 50
**Solution:**
```bash
# Restart backend
# This ensures new .env values are loaded
```

### Issue 2: "GEMINI_API_KEY not configured"
**Solution:**
1. Add `GEMINI_API_KEY=your_key` to `.env`
2. Restart backend
3. Test with `/test-gemini`

### Issue 3: "Invalid JSON response"
**Solution:**
1. Check Gemini is returning valid JSON
2. Visit `/test-gemini` to verify
3. Check backend logs for the actual Gemini response

### Issue 4: Network/Connection error
**Solution:**
1. Check internet connection
2. Verify Gemini API is available: https://ai.google.dev/
3. Make sure API key has correct permissions

### Issue 5: "API key error" or "Invalid API key"
**Solution:**
1. Generate new API key: https://ai.google.dev/
2. Copy exact key (no spaces)
3. Update `.env` file
4. Restart backend
5. Verify with `/test-gemini`

---

## Files Modified for Debugging

1. **interview_evaluator.py**
   - Added logging at each step
   - Better error messages
   - Added API key check

2. **jd_resume_analyzer.py**
   - Added logging for ATS calculation
   - Better JSON parsing

3. **main.py**
   - Added `/test-gemini` endpoint
   - Startup logs show Gemini configuration

4. **test_gemini.py** (new)
   - Standalone diagnostic tool

---

## Expected Behavior After Fix

When user submits an answer:

1. ✅ Backend logs show Gemini is being called
2. ✅ Gemini returns JSON with score
3. ✅ Score is parsed and validated
4. ✅ Frontend shows score (not 50)
5. ✅ Score varies based on answer quality

---

## Debug Output Example

**Good response:**
```
[Evaluator] Starting evaluation...
[Evaluator] Question: What is Python?...
[Evaluator] API Key configured: True
[Evaluator] Gemini response received: {"score": 82, "feedback": "Good explanation...","strengths": ["clear", "accurate"],...}
[Parser] ✓ Successfully parsed JSON directly
[Evaluator] Final score: 82
```

**Bad response (stuck at 50):**
```
[ERROR] GEMINI_API_KEY not configured!
```

OR

```
[ERROR] Exception in evaluate_answer: [Errno 3] No address associated with hostname
```

---

## Next Steps

1. **Verify API key** - Use `/test-gemini` endpoint
2. **Check logs** - Submit an answer and watch backend terminal
3. **Restart backend** - If you added/changed API key
4. **Test again** - Submit new answer and verify score changes

Once you see different scores (not always 50), the fix is working!

---

## Need More Help?

Check the backend logs and look for:
- `[ERROR]` messages
- `[Evaluator]` section logs
- `[Gemini API]` section logs
- `[Parser]` section logs

These will tell you exactly where the issue is.
