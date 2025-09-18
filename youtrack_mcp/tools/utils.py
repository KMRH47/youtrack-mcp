def normalize_issue_id(issue_id: str, default_project: str | None) -> str:
    if default_project and not issue_id.upper().startswith(f"{default_project}-"):
        return f"{default_project}-{issue_id}"
    return issue_id
