"""
Time tracking tools for YouTrack issues.
"""

import logging
from typing import Any, Dict, List, Optional
from datetime import datetime

from youtrack_mcp.api.client import YouTrackClient
from youtrack_mcp.api.issues import IssuesClient
from youtrack_mcp.api.projects import ProjectsClient
from youtrack_mcp.utils import format_json_response

logger = logging.getLogger(__name__)


class TimeTracking:
    """Time tracking operations for YouTrack issues."""

    def __init__(self, issues_api: IssuesClient, projects_api: ProjectsClient):
        """Initialize with API clients."""
        self.issues_api = issues_api
        self.projects_api = projects_api
        logger.info("TimeTracking module initialized")

    def add_work_item(
        self,
        issue_id: str,
        duration_minutes: int,
        description: str = "",
        work_date: Optional[str] = None,
        work_type_id: Optional[str] = None
    ) -> str:
        """
        Add a work item (time log) to an issue.

        This function logs time spent on an issue, which is the standard way to track
        time in YouTrack. The logged time will be reflected in the issue's "Spent time" field.

        Args:
            issue_id: The ID of the issue (e.g., "DEMO-123" or "AGI-456")
            duration_minutes: Duration in minutes (e.g., 30 for 30 minutes, 120 for 2 hours)
            description: Optional description of the work performed
            work_date: Optional date in YYYY-MM-DD format (defaults to today)
            work_type_id: Optional work type ID (defaults to project's default type)

        Returns:
            JSON response with the created work item details

        Examples:
            add_work_item("DEMO-123", 60, "Fixed bug in authentication")
            add_work_item("AGI-456", 30, "Code review", "2024-01-15")
        """
        logger.info(f"Adding work item to issue {issue_id}: {duration_minutes} minutes")

        # Convert date string to timestamp if provided
        work_date_timestamp = None
        if work_date:
            try:
                # Parse date string and convert to timestamp in milliseconds
                dt = datetime.strptime(work_date, "%Y-%m-%d")
                work_date_timestamp = int(dt.timestamp() * 1000)
            except ValueError:
                raise ValueError(f"Invalid date format '{work_date}'. Use YYYY-MM-DD format.")

        try:
            response = self.issues_api.add_work_item(
                issue_id=issue_id,
                duration_minutes=duration_minutes,
                description=description,
                work_date=work_date_timestamp,
                work_type_id=work_type_id
            )

            # Format the response for better readability
            formatted_response = {
                "work_item": response,
                "summary": {
                    "issue_id": issue_id,
                    "duration_logged": f"{duration_minutes} minutes",
                    "description": description if description else "(no description)",
                    "date": work_date or "today"
                }
            }

            return format_json_response(formatted_response)

        except Exception as e:
            error_msg = f"Failed to add work item to issue {issue_id}: {str(e)}"
            logger.error(error_msg)
            return format_json_response({
                "error": error_msg,
                "issue_id": issue_id,
                "attempted_duration": f"{duration_minutes} minutes"
            })

    def get_work_items(self, issue_id: str) -> str:
        """
        Get all work items (time logs) for an issue.

        This function retrieves all time entries logged against an issue,
        showing who logged time, when, how much, and any descriptions.

        Args:
            issue_id: The ID of the issue (e.g., "DEMO-123" or "AGI-456")

        Returns:
            JSON response with all work items for the issue

        Examples:
            get_work_items("DEMO-123")
            get_work_items("AGI-456")
        """
        logger.info(f"Retrieving work items for issue {issue_id}")

        try:
            work_items = self.issues_api.get_work_items(issue_id)

            # Calculate total time spent
            total_minutes = sum(
                item.get("duration", {}).get("minutes", 0)
                for item in work_items
            )

            # Format the response with summary
            formatted_response = {
                "issue_id": issue_id,
                "work_items": work_items,
                "summary": {
                    "total_entries": len(work_items),
                    "total_time_minutes": total_minutes,
                    "total_time_hours": round(total_minutes / 60, 2) if total_minutes > 0 else 0
                }
            }

            return format_json_response(formatted_response)

        except Exception as e:
            error_msg = f"Failed to get work items for issue {issue_id}: {str(e)}"
            logger.error(error_msg)
            return format_json_response({
                "error": error_msg,
                "issue_id": issue_id
            })

    def add_spent_time(
        self,
        issue_id: str,
        time_string: str,
        description: str = "",
        work_date: Optional[str] = None,
        work_type_id: Optional[str] = None
    ) -> str:
        """
        Add spent time to an issue using natural time formats.

        This is a convenience function that parses common time formats and converts
        them to minutes before logging the work item.

        Args:
            issue_id: The ID of the issue (e.g., "DEMO-123" or "AGI-456")
            time_string: Time in natural format (e.g., "1h", "30m", "2h 15m", "90 minutes")
            description: Optional description of the work performed
            work_date: Optional date in YYYY-MM-DD format (defaults to today)
            work_type_id: Optional work type ID (e.g., "Development", "Documentation", "Testing")

        Returns:
            JSON response with the created work item details

        Examples:
            add_spent_time("DEMO-123", "1h", "Fixed authentication bug")
            add_spent_time("AGI-456", "30m", "Code review", work_type_id="Development")
            add_spent_time("PROJ-789", "2h 15m", "Implementation work", "2024-01-15", "Development")
        """
        logger.info(f"Adding spent time to issue {issue_id}: {time_string}")

        try:
            # Parse time string to minutes
            minutes = self._parse_time_string(time_string)

            # Use the main add_work_item function
            return self.add_work_item(
                issue_id=issue_id,
                duration_minutes=minutes,
                description=description,
                work_date=work_date,
                work_type_id=work_type_id
            )

        except Exception as e:
            error_msg = f"Failed to add spent time to issue {issue_id}: {str(e)}"
            logger.error(error_msg)
            return format_json_response({
                "error": error_msg,
                "issue_id": issue_id,
                "attempted_time": time_string
            })

    def _parse_time_string(self, time_string: str) -> int:
        """
        Parse a time string into minutes.

        Supported formats:
        - "30m" or "30 minutes" -> 30 minutes
        - "1h" or "1 hour" -> 60 minutes
        - "2h 30m" -> 150 minutes
        - "90" (plain number) -> 90 minutes

        Args:
            time_string: The time string to parse

        Returns:
            Duration in minutes

        Raises:
            ValueError: If the time string cannot be parsed
        """
        import re

        time_string = time_string.lower().strip()

        # Handle plain numbers (assume minutes)
        if time_string.isdigit():
            return int(time_string)

        total_minutes = 0

        # Extract hours
        hour_match = re.search(r'(\d+)\s*h(?:ours?)?', time_string)
        if hour_match:
            total_minutes += int(hour_match.group(1)) * 60

        # Extract minutes
        minute_match = re.search(r'(\d+)\s*m(?:in(?:utes?)?)?', time_string)
        if minute_match:
            total_minutes += int(minute_match.group(1))

        # If no patterns matched and not a plain number, try to extract any number
        if total_minutes == 0:
            number_match = re.search(r'(\d+)', time_string)
            if number_match:
                total_minutes = int(number_match.group(1))

        if total_minutes == 0:
            raise ValueError(f"Could not parse time string: '{time_string}'. Use formats like '1h', '30m', '2h 15m', or plain minutes.")

        return total_minutes

    def get_work_types(self, project_id: str) -> str:
        """
        Get available work types for a project.

        Args:
            project_id: The project ID (e.g., "DEMO", "AGI")

        Returns:
            JSON response with available work types

        Examples:
            get_work_types("DEMO")
            get_work_types("AGI")
        """
        logger.info(f"Getting work types for project {project_id}")

        try:
            work_types = self.issues_api.get_work_types(project_id)

            formatted_response = {
                "project_id": project_id,
                "work_types": work_types,
                "summary": {
                    "total_types": len(work_types),
                    "available_types": [wt.get("name", "Unknown") for wt in work_types]
                }
            }

            return format_json_response(formatted_response)

        except Exception as e:
            error_msg = f"Failed to get work types for project {project_id}: {str(e)}"
            logger.error(error_msg)
            return format_json_response({
                "error": error_msg,
                "project_id": project_id
            })


# Standalone functions for backward compatibility


def add_work_item(
    client: YouTrackClient,
    issue_id: str,
    duration_minutes: int,
    description: str = "",
    work_date: Optional[str] = None,
    work_type_id: Optional[str] = None
) -> str:
    """
    Add a work item (time log) to an issue.

    This function logs time spent on an issue, which is the standard way to track
    time in YouTrack. The logged time will be reflected in the issue's "Spent time" field.

    Args:
        issue_id: The ID of the issue (e.g., "DEMO-123" or "AGI-456")
        duration_minutes: Duration in minutes (e.g., 30 for 30 minutes, 120 for 2 hours)
        description: Optional description of the work performed
        work_date: Optional date in YYYY-MM-DD format (defaults to today)
        work_type_id: Optional work type ID (defaults to project's default type)

    Returns:
        JSON response with the created work item details

    Examples:
        add_work_item("DEMO-123", 60, "Fixed bug in authentication")
        add_work_item("AGI-456", 30, "Code review", "2024-01-15")
    """
    logger.info(f"Adding work item to issue {issue_id}: {duration_minutes} minutes")

    # Convert date string to timestamp if provided
    work_date_timestamp = None
    if work_date:
        try:
            # Parse date string and convert to timestamp in milliseconds
            dt = datetime.strptime(work_date, "%Y-%m-%d")
            work_date_timestamp = int(dt.timestamp() * 1000)
        except ValueError:
            raise ValueError(f"Invalid date format '{work_date}'. Use YYYY-MM-DD format.")

    try:
        response = client.issues.add_work_item(
            issue_id=issue_id,
            duration_minutes=duration_minutes,
            description=description,
            work_date=work_date_timestamp,
            work_type_id=work_type_id
        )

        # Format the response for better readability
        formatted_response = {
            "work_item": response,
            "summary": {
                "issue_id": issue_id,
                "duration_logged": f"{duration_minutes} minutes",
                "description": description or f"Logged {duration_minutes} minutes",
                "date": work_date or "today"
            }
        }

        return format_json_response(formatted_response)

    except Exception as e:
        error_msg = f"Failed to add work item to issue {issue_id}: {str(e)}"
        logger.error(error_msg)
        return format_json_response({
            "error": error_msg,
            "issue_id": issue_id,
            "attempted_duration": f"{duration_minutes} minutes"
        })


def get_work_items(client: YouTrackClient, issue_id: str) -> str:
    """
    Get all work items (time logs) for an issue.

    This function retrieves all time entries logged against an issue,
    showing who logged time, when, how much, and any descriptions.

    Args:
        issue_id: The ID of the issue (e.g., "DEMO-123" or "AGI-456")

    Returns:
        JSON response with all work items for the issue

    Examples:
        get_work_items("DEMO-123")
        get_work_items("AGI-456")
    """
    logger.info(f"Retrieving work items for issue {issue_id}")

    try:
        work_items = client.issues.get_work_items(issue_id)

        # Calculate total time spent
        total_minutes = sum(
            item.get("duration", {}).get("minutes", 0)
            for item in work_items
        )

        # Format the response with summary
        formatted_response = {
            "issue_id": issue_id,
            "work_items": work_items,
            "summary": {
                "total_entries": len(work_items),
                "total_time_minutes": total_minutes,
                "total_time_hours": round(total_minutes / 60, 2) if total_minutes > 0 else 0
            }
        }

        return format_json_response(formatted_response)

    except Exception as e:
        error_msg = f"Failed to get work items for issue {issue_id}: {str(e)}"
        logger.error(error_msg)
        return format_json_response({
            "error": error_msg,
            "issue_id": issue_id
        })


def add_spent_time(
    client: YouTrackClient,
    issue_id: str,
    time_string: str,
    description: str = ""
) -> str:
    """
    Add spent time to an issue using natural time formats.

    This is a convenience function that parses common time formats and converts
    them to minutes before logging the work item.

    Args:
        issue_id: The ID of the issue (e.g., "DEMO-123" or "AGI-456")
        time_string: Time in natural format (e.g., "1h", "30m", "2h 15m", "90 minutes")
        description: Optional description of the work performed

    Returns:
        JSON response with the created work item details

    Examples:
        add_spent_time("DEMO-123", "1h", "Fixed authentication bug")
        add_spent_time("AGI-456", "30m", "Code review")
        add_spent_time("PROJ-789", "2h 15m", "Implementation work")
    """
    logger.info(f"Adding spent time to issue {issue_id}: {time_string}")

    try:
        # Parse time string to minutes
        minutes = _parse_time_string(time_string)

        # Use the main add_work_item function
        return add_work_item(
            client=client,
            issue_id=issue_id,
            duration_minutes=minutes,
            description=description or f"Logged {time_string}"
        )

    except Exception as e:
        error_msg = f"Failed to add spent time to issue {issue_id}: {str(e)}"
        logger.error(error_msg)
        return format_json_response({
            "error": error_msg,
            "issue_id": issue_id,
            "attempted_time": time_string
        })


def _parse_time_string(time_string: str) -> int:
    """
    Parse a time string into minutes.

    Supported formats:
    - "30m" or "30 minutes" -> 30 minutes
    - "1h" or "1 hour" -> 60 minutes
    - "2h 30m" -> 150 minutes
    - "90" (plain number) -> 90 minutes

    Args:
        time_string: The time string to parse

    Returns:
        Duration in minutes

    Raises:
        ValueError: If the time string cannot be parsed
    """
    import re

    time_string = time_string.lower().strip()

    # Handle plain numbers (assume minutes)
    if time_string.isdigit():
        return int(time_string)

    total_minutes = 0

    # Extract hours
    hour_match = re.search(r'(\d+)\s*h(?:ours?)?', time_string)
    if hour_match:
        total_minutes += int(hour_match.group(1)) * 60

    # Extract minutes
    minute_match = re.search(r'(\d+)\s*m(?:in(?:utes?)?)?', time_string)
    if minute_match:
        total_minutes += int(minute_match.group(1))

    # If no patterns matched and not a plain number, try to extract any number
    if total_minutes == 0:
        number_match = re.search(r'(\d+)', time_string)
        if number_match:
            total_minutes = int(number_match.group(1))

    if total_minutes == 0:
        raise ValueError(f"Could not parse time string: '{time_string}'. Use formats like '1h', '30m', '2h 15m', or plain minutes.")

    return total_minutes