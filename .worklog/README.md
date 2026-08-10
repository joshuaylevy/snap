# Worklog -- session research record

A durable, in-repo record of the work done across Claude Code sessions on this
project. The goal: **every task leaves a greppable trace** -- what was done, why,
and how to re-open the exact session -- so the work is reconstructable long after
the context window is gone.

This directory is the *data* only. The *mechanism* (the `/worklog` skill, the
`worklog.py` helper, and the SessionStart/SessionEnd hooks) lives globally in
`~/.claude/` and is shared by every project; it created this directory on the
first `/worklog` run here and will keep appending to it.

## What's here

```
.worklog/
|- worklog.csv     # the database: one row per session/task
|- entries/        # one .md per task -- the narrative record
|  `- YYYY-MM-DD_<slug>_<short-id>.md
|- _template.md    # entry template
`- README.md       # this file
```

Ephemeral session-id state is NOT here -- it lives globally under
`~/.claude/worklog-state/`, keyed by this project.

## The workflow

```
... work a task ...        (use /compact within a task if context balloons)
/worklog                   <- writes the record (bootstraps this dir on first use)
/clear                     <- fresh context for the next task
```

If you forget to run `/worklog`, the SessionEnd hook appends a stub row
(`status=unlogged`) with a crude auto-summary, so no session is lost. Upgrade a
stub later by re-reading the session and running `/worklog` again.

## Re-reading a past session

Grab the `session_id` from `worklog.csv` (or an entry's front matter), then:

```
claude --resume <session_id>
```

or read the raw transcript directly at the `transcript_path` in the row.
