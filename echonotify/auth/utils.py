import datetime


def utc_now_naive() -> datetime.datetime:
    """Returns the current UTC time as a naive datetime object."""
    return datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)
