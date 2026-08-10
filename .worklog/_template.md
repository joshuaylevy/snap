---
title: <short human-readable title>
date: <YYYY-MM-DD>
session_id: <full session hash>
task_slug: <kebab-case-slug>
status: complete        # complete | wip | blocked
phase: <e.g. Phase 3>
tags: [<tag>, <tag>]
branch: <git branch>
head_commit: <short sha>
commits: [<sha>, <sha>]
transcript_path: <absolute path to the .jsonl>
---

# <title>

**Re-read the full session:** `claude --resume <session_id>`
(or read the raw transcript at `transcript_path`)

## Context / goal
<Why this task existed. What question or feature it addressed.>

## What was done
<Narrative of the work, in the order it happened. Concrete enough to
reconstruct the arc months later.>

## Key decisions & why
<The load-bearing choices -- data/functional-form/architecture -- and the
reasoning behind each. This is the part that matters later.>

## Files changed
<Paths added/modified, one line of what/why each.>

## Verification
<Tests run, checks made, what was and wasn't confirmed. Say so plainly if
something was skipped.>

## Open threads / next steps
<What's unfinished, what to pick up next, known caveats.>
