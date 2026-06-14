import os
import subprocess

from .logging import log_and_print


def check_conversion(core: object, state_data: dict, ext: str, output_path: str):
    """
    Check if the output needs to be converted based on state settings.

    Args:
        core (object): The core application object.
        state_data (dict): The state data containing settings.
        ext (str): The file extension of the output.
        output_path (str): The original output file path.
    """

    if core.appPlugin.pluginName == "Houdini":
        if state_data["state_type"] == "pb" and state_data["extension"] == ".mp4":
            directory = os.path.dirname(output_path)
            base = os.path.basename(output_path).split(".")[0]
            output = f"{directory}/{base}{state_data['extension']}"
            return [output]

    if ext not in ["png", "jpg", "exr", "tif"]:
        return [output_path]

    if state_data["range_type"] == "Expression":
        core.popup(
            "Your render has been published but the Slack plugin does not support expression ranges yet."
        )
        raise ValueError("Invalid range type.")

    if core.getPlugin("MediaExtension"):
        if state_data["convert_media"] is True:
            return _handle_media_conversion_checkbox(state_data, core, output_path)

    if state_data["range_type"] == "Single Frame":
        return _handle_single_frame(state_data, core, output_path)

    if state_data["range_type"] in ["Scene", "Shot", "Custom", "Node"]:
        return _handle_scene_shot_custom_node(state_data, core, output_path)

    if state_data["range_type"] == "Shot + 1":
        return _shot_plus_one(state_data, core, output_path)

    else:
        raise ValueError("Invalid range type.")


def _handle_media_conversion_checkbox(state_data: dict, core: object, outputPath: str):
    """
    Handle media conversion based on the media extension.

    Args:
        state_data (dict): The state data containing settings.
        core (object): The core application object.
        outputPath (str): The original output file path.
    """

    conversion_option = state_data["converted_extension"].lower()
    conversion_option = _retrieve_extension(conversion_option)
    base = os.path.basename(outputPath).split(".")[0]
    top_directory = os.path.dirname(outputPath)

    prism_version = core.version.replace("v", "")

    if prism_version < "2.1.2":
        try:
            if state_data["state_type"] == "pb":
                if conversion_option in ["mp4", "mov"]:
                    converted_file = f"{top_directory} ({conversion_option})/{base} ({conversion_option}).{conversion_option}"
                    existing_file = _existing_path(converted_file)
                    if existing_file:
                        return [existing_file]

                elif conversion_option in ["png", "jpg", "tif"]:
                    framePad = "#" * core.framePadding
                    sequence = f"{top_directory} ({conversion_option})/{base} ({conversion_option}).{framePad}.{conversion_option}"
                    convert = _convert_image_sequence(core, sequence, state_data)
                    existing_file = _existing_path(convert)
                    if existing_file:
                        return [existing_file]

            elif state_data["state_type"] == "render":
                aov = os.path.dirname(outputPath).split("/")[-1]
                version_folder = os.path.dirname(os.path.dirname(outputPath)).split(
                    "/"
                )[-1]
                top_directory = os.path.dirname(
                    os.path.dirname(os.path.dirname(outputPath))
                )
                version_directory_ext = f"{version_folder} ({conversion_option})"
                base = base.replace(version_folder, version_directory_ext)

                if conversion_option in ["mp4", "mov"]:
                    converted_file = f"{top_directory}/{version_directory_ext}/{aov}/{base}.{conversion_option}"
                    existing_file = _existing_path(converted_file)
                    if existing_file:
                        return [existing_file]

                elif conversion_option in ["png", "jpg", "tif"]:
                    if state_data["app"] == "AfterEffects":
                        framePad = "#" * core.framePadding
                    else:
                        framePad = "#" * core.framePadding
                    sequence = f"{top_directory}/{version_directory_ext}/{aov}/{base}.{framePad}.{conversion_option}"
                    convert = _convert_image_sequence(core, sequence, state_data)
                    existing_file = _existing_path(convert)
                    if existing_file:
                        return [existing_file]
        except Exception:
            log_and_print(
                20,
                "Could not find the converted file or media. Trying to locate in the same folder as image(s)",
            )

    else:
        try:
            if state_data["state_type"] == "pb":
                if conversion_option in ["mp4", "mov"]:
                    converted_file = f"{top_directory}/{base}.{conversion_option}"
                    existing_file = _existing_path(converted_file)
                    if existing_file:
                        log_and_print(20, f"Found converted file at: {existing_file}")
                        return [existing_file]

                elif conversion_option in ["png", "jpg", "tif"]:
                    framePad = "#" * core.framePadding
                    sequence = f"{top_directory}/{base}.{framePad}.{conversion_option}"
                    convert = _convert_image_sequence(core, sequence, state_data)
                    existing_file = _existing_path(convert)
                    if existing_file:
                        return [existing_file]

            if state_data["state_type"] == "render":
                if conversion_option in ["mp4", "mov"]:
                    converted_file = f"{top_directory}/{base}.{conversion_option}"
                    existing_file = _existing_path(converted_file)
                    if existing_file:
                        return [existing_file]

                elif conversion_option in ["png", "jpg", "tif"]:
                    if state_data["app"] == "AfterEffects":
                        framePad = "#" * core.framePadding
                    else:
                        framePad = "#" * core.framePadding
                    sequence = f"{top_directory}/{base}.{framePad}.{conversion_option}"
                    convert = _convert_image_sequence(core, sequence, state_data)
                    existing_file = _existing_path(convert)
                    if existing_file:
                        return [existing_file]

        except Exception:
            log_and_print(
                30,
                "Could not find the converted file or media. Please check your conversion settings and ensure the file has been converted.",
            )

        raise FileNotFoundError(
            f"Could not locate converted media for {outputPath} using conversion option '{conversion_option}'."
        )


# Convert an image sequence to a video
def _convert_image_sequence(core: object, sequence: str, state_data: dict):
    """
    Start the conversion process from an image sequence to an mp4 video using ffmpeg.

    Args:
        core (object): The core application object.
        sequence (str): The image sequence path.
        state_data (dict): The state data containing settings.
    """

    folder_path = os.path.dirname(sequence)
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)

    input_sequence = _convert_sequence_path(core, sequence, state_data)

    # Determine the starting frame
    start_frame = state_data["start_frame"]

    # Construct input and output paths
    contstructed_file = _construct_output_file(input_sequence)

    fps = state_data["fps"]

    # Run ffmpeg to create the video
    output_file = _convert_to_mp4(
        core, input_sequence, start_frame, fps, contstructed_file
    )

    return output_file


# Convert the sequence path to a more universal format
def _convert_sequence_path(core: object, sequence: str, state_data: dict):
    """
    Convert the image sequence path to a format compatible with ffmpeg.

    Args:
        core (object): The core application object.
        sequence (str): The image sequence path.
        state_data (dict): The state data containing settings.
    """

    if state_data["app"] == "Houdini":
        if state_data["convert_media"] is True:
            input_sequence = sequence.replace("#" * core.framePadding, "%04d")
        else:
            input_sequence = sequence.replace(".$F4.", ".%04d.")

    elif state_data["app"] == "Cinema4D":
        if state_data["convert_media"] is True:
            input_sequence = sequence.replace("#" * core.framePadding, "%04d")
        else:
            input_sequence = sequence.replace("..", ".%04d.")

    elif state_data["app"] == "AfterEffects":
        input_sequence = sequence.replace("#" * core.framePadding, "%04d")

    else:
        input_sequence = sequence.replace("#" * core.framePadding, "%04d")

    return input_sequence


# Construct the output file path for ffmpeg
def _construct_output_file(input_sequence: str, state_data: dict = None):
    """
    Construct the output file path for the converted mp4 video.

    Args:
        input_sequence (str): The input image sequence path.
        state_data (dict, optional): The state data containing settings.
    """

    sequence_name = os.path.basename(input_sequence)
    basename = os.path.splitext(sequence_name)[0]

    for token in [".%04d", ".%05d", "_%04d", "_%05d", "%04d", "%05d"]:
        if basename.endswith(token):
            basename = basename[: -len(token)]
            break

    directory = os.path.dirname(input_sequence)
    output_file = os.path.join(directory, basename + ".mp4")

    return output_file


# Convert the image sequence to an mp4 video
def _convert_to_mp4(
    core: object, input_sequence: str, start_frame: str, fps: str, output_file: str
):
    ffmpegPath = os.path.join(core.prismLibs, "Tools", "FFmpeg", "bin", "ffmpeg.exe")
    ffmpegPath = ffmpegPath.replace("\\", "/")

    if not os.path.exists(ffmpegPath):
        raise SystemError(f"ffmpeg not found at {ffmpegPath}")
        return

    try:
        subprocess.run(
            [
                ffmpegPath,
                "-y",
                "-framerate",
                fps,
                "-start_number",
                start_frame,
                "-i",
                input_sequence,
                "-c:v",
                "libx264",
                "-pix_fmt",
                "yuv420p",
                output_file,
            ],
            capture_output=True,
            check=True,
        )
    except subprocess.CalledProcessError as e:
        print(f"Error running ffmpeg: {e.stderr.decode()}")
        return

    output_file = output_file.replace("\\", "/")

    return output_file


def _handle_single_frame(state_data: dict, core: object, output_path: str):
    output_ext = os.path.splitext(output_path)[1]
    output_basename = os.path.splitext(output_path)[0]

    if os.path.exists(f"{output_basename}{output_ext}"):
        output = f"{output_basename}{output_ext}"
    else:
        output = output_path.replace("#" * core.framePadding, state_data["start_frame"])

    return [output]


def _handle_scene_shot_custom_node(state_data: dict, core: object, output_path: str):
    if int(state_data["start_frame"]) == int(state_data["end_frame"]):
        if core.appPlugin.pluginName == "Houdini":
            file = output_path.replace("$F4", state_data["start_frame"])

        elif core.appPlugin.pluginName == "Cinema4D":
            file = output_path.replace("..", f".{state_data['start_frame']}.")

        elif core.appPlugin.pluginName == "AfterEffects":
            file = output_path.replace(
                "#" * core.framePadding, state_data["start_frame"]
            )

        else:
            file = output_path.replace(
                "#" * core.framePadding, state_data["start_frame"]
            )

        outputList = [file]

    elif int(state_data["start_frame"]) < int(state_data["end_frame"]):
        convert = _convert_image_sequence(core, output_path, state_data)
        outputList = [convert]

    else:
        raise ValueError("Invalid range.")

    return outputList


def _shot_plus_one(state_data: dict, core: object, output_path: str):
    convert = _convert_image_sequence(core, output_path, state_data)
    outputList = [convert]

    return outputList


# Get proper extension from media conversion type
def _retrieve_extension(option: str):
    if "png" in option:
        ext = "png"
    elif "jpg" in option:
        ext = "jpg"
    elif "mp4" in option:
        ext = "mp4"
    elif "mov" in option:
        ext = "mov"
    else:
        ext = option

    return ext


def _existing_path(*candidates: str) -> str | None:
    for candidate in candidates:
        normalized_candidate = candidate.replace("\\", "/")
        if os.path.exists(normalized_candidate):
            return normalized_candidate

    return None
