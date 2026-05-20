import pytest
import re

LOG_REGEX = re.compile(
    r'(?P<ip>[\d\.]+) - - \[(?P<timestamp>[^\]]+)\] "(?P<method>\w+) (?P<endpoint>[^\s]+) HTTP/[^\s]+" (?P<status>\d+) (?P<bytes>\d+)'
)

def test_valid_log_line_parsing():
    sample = '192.168.1.1 - - [20/May/2026:10:00:00 +0000] "GET /api/v1/users HTTP/1.1" 200 4212'
    match = LOG_REGEX.match(sample)
    assert match is not None
    
    data = match.groupdict()
    assert data["ip"] == "192.168.1.1"
    assert data["timestamp"] == "20/May/2026:10:00:00 +0000"
    assert data["method"] == "GET"
    assert data["endpoint"] == "/api/v1/users"
    assert data["status"] == "200"
    assert data["bytes"] == "4212"

def test_invalid_log_line_returns_none():
    corrupted_sample = 'Malformed string with no real pattern data'
    match = LOG_REGEX.match(corrupted_sample)
    assert match is None