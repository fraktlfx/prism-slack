import os
import re
import glob

from .logging import log_and_print
from .determine_frame_range import determine_frame_range


AE_FRAME_TOKEN_PATTERN = re.compile(r"\[(#+)\]")
FRAME_HASH_TOKEN_PATTERN = re.compile(r"#+")
FRAME_NUMBER_PATTERN = re.compile(r"^(.*?)(\d+)(\.[^.]+)$")

VIDEO_EXTS = [".mov", ".mp4", ".avi"]
IMAGE_EXTS = [".exr", ".png", ".jpg", ".jpeg", ".tif"]


def normalize_path(path: str) -> str:
    return path.replace("\\", "/")


def _find_aftereffects_sequence_matches(sequence_base_output: str, ext: str) -> list[str]:
    sequence_pattern = AE_FRAME_TOKEN_PATTERN.sub("*", sequence_base_output)
    sequence_pattern = FRAME_HASH_TOKEN_PATTERN.sub("*", sequence_pattern)

    return sorted(glob.glob(f"{sequence_pattern}{ext}"))


def _resolve_video_output(movie_base_output: str) -> str | None:
    for ext in VIDEO_EXTS:
        candidate = normalize_path(movie_base_output + ext)
        candidate_alt = normalize_path(movie_base_output + "." + ext)

        if os.path.exists(candidate):
            return candidate

        if os.path.exists(candidate_alt):
            log_and_print(
                20,
                (
                    "[AE] Found video output path with an extra dot in the filename: "
                    f"{candidate_alt}. This should not happen and should be reported."
                ),
            )
            return candidate_alt

        log_and_print(
            20,
            f"[AE] Video output not found for {ext}. Checking next option.",
        )

    return None


def _build_sequence_path(
    core: object, first_frame: str, sequence_base_output: str, ext: str
) -> str:
    first_frame = normalize_path(first_frame)
    frame_basename = os.path.basename(first_frame)

    frame_match = FRAME_NUMBER_PATTERN.match(frame_basename)

    if not frame_match:
        sequence_path = sequence_base_output + ("#" * core.framePadding) + ext
        sequence_path = normalize_path(sequence_path)

        log_and_print(
            20,
            f"[AE] Could not parse frame pattern. Using default sequence path: {sequence_path}",
        )

        return sequence_path

    frame_prefix, frame_digits, frame_suffix = frame_match.groups()
    hash_pattern = f"{frame_prefix}{'#' * len(frame_digits)}{frame_suffix}"

    sequence_path = os.path.join(os.path.dirname(first_frame), hash_pattern)
    sequence_path = normalize_path(sequence_path)

    log_and_print(
        20,
        f"[AE] Constructed image sequence path: {sequence_path}",
    )

    return sequence_path


def _resolve_image_sequence_output(core: object, sequence_base_output: str) -> str | None:
    for ext in IMAGE_EXTS:
        sequence_matches = _find_aftereffects_sequence_matches(sequence_base_output, ext)

        if not sequence_matches:
            continue

        first_frame = normalize_path(sequence_matches[0])
        log_and_print(20, f"[AE] Found image sequence output: {first_frame}")

        return _build_sequence_path(core, first_frame, sequence_base_output, ext)

    return None


def resolve_aftereffects_output(core: object, output: str) -> str | None:
    """
    Resolve an After Effects render output path.

    Tries the provided output path first, then common video extensions,
    then image-sequence patterns.

    Args:
        core (object): Prism core object.
        output (str): The original output path from After Effects.

    Returns:
        str | None: The resolved output path if it exists, otherwise None.
    """
    normalized_output = normalize_path(output)

    if os.path.exists(normalized_output):
        return normalized_output

    movie_base_output, sequence_base_output = normalize_aftereffects_output_patterns(
        normalized_output
    )

    log_and_print(
        20,
        f"[AE] Normalized output path does not exist: {normalized_output}",
    )
    log_and_print(
        20,
        f"[AE] Base output path for resolution: {movie_base_output}",
    )

    video_output = _resolve_video_output(movie_base_output)
    if video_output:
        return video_output

    sequence_output = _resolve_image_sequence_output(core, sequence_base_output)
    if sequence_output:
        return sequence_output

    log_and_print(
        20,
        f"[AE] Could not resolve After Effects output path: {normalized_output}",
    )

    return None


def get_aftereffects_frame_data(output: str) -> dict[str, str]:
    """
    Determine the frame range for an After Effects render output by checking for image sequence patterns.

    Args:
        output (str): The original output path from After Effects.

    Returns:
        dict[str, str]: A dictionary containing the range type, start frame, and end frame.
    """
    normalized_output = normalize_path(output)

    if os.path.exists(normalized_output):
        return {}

    _, sequence_base_output = normalize_aftereffects_output_patterns(normalized_output)

    for ext in IMAGE_EXTS:
        sequence_matches = _find_aftereffects_sequence_matches(sequence_base_output, ext)

        if not sequence_matches:
            continue

        first_frame = normalize_path(sequence_matches[0])
        return determine_frame_range(first_frame)

    return {}


def normalize_aftereffects_output_patterns(output: str) -> tuple[str, str]:
    """
    Split an AE output into a concrete movie base path and a sequence glob base path.

    Args:
        output (str): The original output path from After Effects.

    Returns:
        tuple[str, str]:
            - movie_base_output: path without the file extension and without AE frame tokens
            - sequence_base_output: path without the file extension, preserving AE frame tokens
    """
    normalized_output = normalize_path(output)

    sequence_base_output = os.path.splitext(normalized_output)[0]

    movie_base_output = AE_FRAME_TOKEN_PATTERN.sub("", sequence_base_output)
    movie_base_output = re.sub(r"\.+$", "", movie_base_output)

    return movie_base_output, sequence_base_output
