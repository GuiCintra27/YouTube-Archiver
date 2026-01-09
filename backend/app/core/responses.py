"""
Response helpers for common API payloads.
"""


def job_response(job_id: str, message: str, status: str = "success") -> dict:
    return {
        "status": status,
        "job_id": job_id,
        "message": message,
    }
