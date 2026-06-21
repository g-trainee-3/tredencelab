# Skill: Add Activity Endpoint

## Description
Adds a new Flask route to the Mergington activities API (src/app.py).
Use when adding any new GET, POST, or DELETE endpoint that reads or
modifies the ACTIVITIES dictionary.

## Trigger
Use when asked to: "add a new endpoint", "add a new route", "implement
an API for [feature name]" in the Mergington activities codebase.

## Constraints
### NEVER_MODIFY — UAT-locked
- get_activities() in src/app.py
- signup() in src/app.py
- remove_signup() in src/app.py
- All existing functions in src/tests/test_app.py

### Forbidden operations
- Do not restructure the ACTIVITIES dictionary
- Do not add new top-level imports without lead approval
- Do not change existing function signatures

### Required test outcomes
- All existing tests must pass after the skill is used
- New tests must be added for new functionality
- Coverage must not drop

## Examples
### Input
"Add GET /activities/{name}/participants that returns the participant list"

### Expected output structure
A single new Flask route function below remove_signup() that uses
jsonify() and returns HTTP 200 or 404.

## DRI
Tech Lead — [name]
## Version
v1.0 — [date]

