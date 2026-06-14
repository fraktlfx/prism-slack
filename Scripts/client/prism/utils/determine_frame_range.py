import os
import glob
import re

from .logging import log_and_print


def determine_frame_range(output: str) -> dict:
    """
    Determine the start and end frame from the output string.

    Args:
        output (str): The output string containing frame range information.

    Returns:
        range (dict): A dictionary with 'range_type', 'start_frame' and 'end_frame'.
    """

    filename = os.path.basename(output)
    directory = os.path.dirname(output)

    prefix = ""
    extension = ""
    padding_length = 0
    glob_pattern = ""
    frame_regex = None

    hash_dot_match = re.match(r"(.*)\.(#+)\.(\w+)$", filename)
    hash_underscore_match = re.match(r"(.*)_(#+)\.(\w+)$", filename)
    hash_direct_match = re.match(r"(.*)(#+)\.(\w+)$", filename)
    concrete_match = re.match(r"(.*?)(\d+)\.(\w+)$", filename)

    if hash_dot_match:
        prefix, padding, extension = hash_dot_match.groups()
        padding_length = len(padding)
        glob_pattern = f"{prefix}.*.{extension}"
        frame_regex = re.compile(
            rf"{re.escape(prefix)}\.(\d{{{padding_length}}})\.{re.escape(extension)}$"
        )
    elif hash_underscore_match:
        prefix, padding, extension = hash_underscore_match.groups()
        padding_length = len(padding)
        glob_pattern = f"{prefix}_*.{extension}"
        frame_regex = re.compile(
            rf"{re.escape(prefix)}_(\d{{{padding_length}}})\.{re.escape(extension)}$"
        )
    elif hash_direct_match:
        prefix, padding, extension = hash_direct_match.groups()
        padding_length = len(padding)
        glob_pattern = f"{prefix}*.{extension}"
        frame_regex = re.compile(
            rf"{re.escape(prefix)}(\d{{{padding_length}}})\.{re.escape(extension)}$"
        )
    elif concrete_match:
        prefix, digits, extension = concrete_match.groups()
        padding_length = len(digits)
        glob_pattern = f"{prefix}*.{extension}"
        frame_regex = re.compile(
            rf"{re.escape(prefix)}(\d{{{padding_length}}})\.{re.escape(extension)}$"
        )
    else:
        raise RuntimeError(f"Could not parse sequence pattern from: {output}")

    files = glob.glob(os.path.join(directory, glob_pattern))
    log_and_print(
        20, f"Looking for files with pattern: {os.path.join(directory, glob_pattern)}"
    )

    frames = []

    for f in files:
        base = os.path.basename(f)
        m = frame_regex.match(base)
        if m:
            frames.append(int(m.group(1)))

    if not frames:
        log_and_print(40, f"No matching frames found for pattern: {glob_pattern}")
        raise RuntimeError("No matching frames found")

    frames.sort()

    frame_range = {}

    if frames[0] == frames[-1]:
        frame_range["range_type"] = "Single Frame"
        frame_range["start_frame"] = frames[0]
        frame_range["end_frame"] = frames[-1]

    else:
        frame_range["range_type"] = "Custom"
        frame_range["start_frame"] = frames[0]
        frame_range["end_frame"] = frames[-1]

    return frame_range
