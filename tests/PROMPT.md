Build me a Personal Life OS Agent using LangChain and Google APIs. This is an intelligent chief-of-staff agent that connects Gmail, Google Calendar, Google Drive, and Google Tasks.

## Core Capabilities

1. **Email Processing**
   - Read unread Gmail emails
   - Classify urgency (urgent / action-required / FYI)
   - Auto-draft replies for action-required emails
   - Extract action items and convert them into Google Tasks or Calendar events

2. **Weekly Summary (Monday Morning Briefing)**
   - Summarize emails from the past 7 days
   - List upcoming calendar events for the week
   - Surface pending tasks due this week
   - Output a clean briefing to the terminal (or a Google Doc)

3. **Conflict Detection**
   - Scan Google Calendar for overlapping events
   - Suggest reschedules when conflicts are found
   - Flag events that conflict with blocked focus time

4. **Urgent Email Flagging**
   - Detect urgency signals in email subject/body
   - Label them in Gmail and surface them immediately

## Important

Use the Lex AI MCP to scrape and thoroughly read any documentation before writing code.
