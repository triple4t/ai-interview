# Interview Assistant - Workflow Guide

## Important: Question Loading Behavior

The Interview Assistant loads interview questions when the **LiveKit agent starts**. This means:

### ⚠️ Critical Steps for Correct Question Selection

1. **Select the Job Description (JD) First**
   - Go to the Jobs page
   - Click on the job you want to interview for
   - This will save your selection to `selected_jd.txt`

2. **Restart the Backend Agent** (REQUIRED!)
   - After selecting a new JD, you MUST restart the LiveKit agent
   - The agent only loads questions at startup
   - Without restart, it will use the previous selection

3. **Start the Interview**
   - Now you can start the interview
   - The questions will match your selected job description

## How to Restart the Backend

### Option 1: Using the terminal
```bash
cd "voice assistant/backend"

# Stop the current agent process
# Press Ctrl+C in the terminal where app.py is running

# Restart the agent
python app.py start
```

### Option 2: Kill and restart
```bash
# Find the process
ps aux | grep "python app.py"

# Kill it (replace <PID> with the actual process ID)
kill <PID>

# Start it again
cd "voice assistant/backend"
python app.py start
```

## Troubleshooting

### Problem: Wrong Questions Being Asked

**Symptoms:**
- Selected "Full Stack Developer" but getting GenAI questions
- Questions don't match the job description
- Seeing fallback questions like "What is a prompt?", "What is a knowledge cutoff?"

**Solution:**
1. Check `voice assistant/backend/selected_jd.txt` - it should contain your JD filename
2. Restart the LiveKit agent (see above)
3. Check the agent logs for:
   ```
   [Interview] ===== LOADING INTERVIEW QUESTIONS =====
   [Interview] Selected JD filename: full_stack_developer.txt
   [Interview] ✅ Successfully loaded 100 questions from full_stack_developer.txt
   ```
4. If you see `⚠️ FALLING BACK TO STATIC GENAI QUESTIONS`, the questions file wasn't loaded correctly

### Problem: "Failed to fetch" Error on Result Page

**Symptoms:**
- Result page shows error in console: "Failed to fetch"
- Interview results don't load
- API returns 404 or connection refused

**Solution:**
1. Make sure the backend API is running:
   ```bash
   cd "voice assistant/backend"
   python main.py
   ```
2. Check that it's running on port **8002** (not 8001)
3. Verify the frontend is trying to connect to `http://localhost:8002/api/v1`

### Problem: Transcript Shows Wrong Questions

**Symptoms:**
- The actual questions asked don't match the job description
- Result page shows questions that weren't asked
- Transcript is mismatched

**Root Cause:**
The transcript in the result page shows **exactly what was asked** during the interview. If it shows the wrong questions, it means:
1. The agent was using old questions when the interview started
2. You forgot to restart the agent after changing the JD selection

**Solution:**
1. Delete the old interview result from the database
2. Restart the agent
3. Start a new interview

## Best Practices

1. **Always restart the agent after selecting a new JD**
2. **Check the agent logs** to confirm the correct questions were loaded
3. **Complete one interview at a time** to avoid confusion
4. **Keep the agent running** between interviews for the same job description

## Technical Details

### How Questions are Loaded

1. When the agent starts, it calls `get_random_interview_questions()`
2. This function:
   - Reads `selected_jd.txt` to get the JD filename
   - Loads questions from `interview_questions/{jd_filename}`
   - Falls back to hardcoded GenAI questions if loading fails
   - Randomly selects 5 questions from the pool

3. These 5 questions are passed to the Assistant and used throughout the interview session

### Why Restart is Required

The LiveKit agent is a long-running process that:
- Loads questions once at initialization
- Keeps them in memory for the entire session
- Doesn't reload questions dynamically

This design ensures:
- Consistent question sets for each interview
- Better performance (no file I/O during interviews)
- Predictable behavior

However, it means you must restart the agent to pick up new JD selections.


