#!/usr/bin/env bash

function get_python_command() {
    prism_directory=$1

    python_command=""
    python313_path="$prism_directory/Python313/bin/python"
    python311_path="$prism_directory/Python311/bin/python"
    if [ -f "$python313_path" ]; then
        echo "Found Python 3.13 at ${python313_path}" >&2
        python_command="$python313_path"
    elif [ -f "$python311_path" ]; then
        echo "Found Python 3.11 at ${python311_path}" >&2
        python_command="$python311_path"
    else
        echo "Error: Could not find Python executable in the Prism directory." >&2
        exit 1
    fi

    echo "$python_command"
}

function install_packages() {
    target_directory=$1
    prism_directory=$2
    python_command=$(get_python_command "$prism_directory") || exit 1

    echo "Installing packages to ${target_directory} using ${python_command}..." >&2

    echo "Creating target directory if it doesn't exist..." >&2
    mkdir -p "$target_directory"

    echo "Ensuring pip is up to date..." >&2
    "$python_command" -m ensurepip --upgrade
    "$python_command" -m pip install --upgrade pip

    "$python_command" -m pip install \
        --target "$target_directory" \
        slack_sdk \
        slack_bolt \
        requests \
        flask \
        py-machineid \
        cryptography
}

function main() {
    prism_directory=$(bash -ic '
		bind "set show-all-if-ambiguous on";
		bind "set colored-stats on";
		bind "set colored-completion-prefix on";
		bind "set visible-stats on";
		bind "set page-completions off";

		bind "\"\t\": menu-complete"; 
		bind "\"\e[Z\": menu-complete-backward";

		read -r -e -p "Please enter the location of the Prism directory on your system (including \"Prism\" at end): " prism_directory; 
		echo "$prism_directory"
	')
    prism_directory=$(echo "$prism_directory" | sed 's:/*$::') # Remove trailing slashes
    prism_directory="$(cd -- "$prism_directory" && pwd -P)" # Get absolute path
    if [ ! -d "$prism_directory" ]; then
        echo "Error: The specified directory does not exist." >&2
        exit 1
    fi
    script_dir=$(
        cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P
    )
    if [ $# -lt 1 ]; then
        target_directory="${script_dir}/PythonLibs"
    else
        target_directory=$1
    fi

    install_packages "$target_directory" "$prism_directory"
}

main "$@"
