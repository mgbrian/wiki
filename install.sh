#!/bin/bash

# Create and activate a virtual env
if [ ! -d ".requirements" ]; then
    echo "Creating virtual environment in '.requirements/'..."
    python3 -m venv .requirements/ || { echo "Failed to create virtual environment."; exit 1; }
fi

source .requirements/bin/activate || { echo "Failed to activate virtual environment."; exit 1; }

echo ""
echo "Installing main repository dependencies..."

# Install OS-level dependencies
OS=$(uname -s)
if [ "$OS" = "Darwin" ]; then
    DEP_FILE="dependencies/macos.txt"
    INSTALL_CMD="brew install"
elif [ -f /etc/debian_version ]; then
    DEP_FILE="dependencies/linux.txt"
    INSTALL_CMD="sudo apt-get install -y"
elif [ -f /etc/alpine-release ]; then
    DEP_FILE="dependencies/linux.txt"
    INSTALL_CMD="sudo apk add"
else
    echo "Error: Unsupported OS. Only macOS, Debian and Alpine are supported."
    exit 1
fi

if [ -f "$DEP_FILE" ]; then

    # Need brew on macOS to install packages.
    if [ "$OS" = "Darwin"]; then
        if ! command -v brew &> /dev/null; then
            echo "Homebrew is not installed. Please install and re-run!"
            exit 1
        fi
    fi

    while read -r package; do
        if [ -n "$package" ]; then
            echo "Installing $package..."
            $INSTALL_CMD "$package"
        fi
    done < "$DEP_FILE"
fi

# Install Python dependencies
if [ -f requirements.txt ]; then
    # Save the current cursor position
    tput sc
    python3 -m pip install -r requirements.txt || exit 1

    # Clear screen up to saved cursor
    tput rc
    tput ed
else
    echo "No requirements to install..."
fi

# Start generating env.py by copying the main repository's sample_env.py
if [ -f sample_env.py ]; then
    echo ""
    echo "Creating env.py from main repository's sample_env.py..."
    cp sample_env.py env.py || { echo "Failed to create env.py."; exit 1; }
fi

# Install submodules if they exist
# TODO: This should probably run the install.sh there. Think about side-effects.
if [ -f submodules.txt ]; then
    echo ""
    # Go through submodules in submodules.txt. Clone each if it doesn't already exist.
    while IFS= read -r submodule; do
        # Extract the folder name - remove ".git"" and stripping out any additional
        # paths after the repo name
        folder=$(basename "${submodule%%.git*}")

        if [ ! -d "$folder" ]; then
            echo "Adding submodule: $folder..."
            git submodule add "$submodule" || exit 1
        else
            echo "Submodule: $folder already exists. Skipping..."
        fi
    done < submodules.txt

    # Initialize and update the submodules
    git submodule update --init --recursive || exit 1

    echo ""
    # Install requirements for each submodule and concatenate sample_env.py if it exists
    while IFS= read -r submodule; do
        # Extract the folder name by removing any .git and stripping out any additional paths after the repo name
        folder=$(basename "${submodule%%.git*}")

        if [ -f "$folder/requirements.txt" ]; then
            echo "Installing dependencies for submodule: $folder..."
            tput sc
            python3 -m pip install -r "$folder/requirements.txt" || exit 1
            tput rc
            tput ed
        else
            echo "No requirements.txt found in submodule $folder. Skipping..."
        fi

        # Concatenate sample_env.py from the submodule, if it exists
        if [ -f "$folder/sample_env.py" ]; then
            echo "Appending $folder/sample_env.py to env.py..."
            echo -e "\n# Environment variables from $folder/sample_env.py" >> env.py
            cat "$folder/sample_env.py" >> env.py || { echo "Failed to append $folder/sample_env.py to env.py."; exit 1; }
        fi
    done < submodules.txt
fi

# Pull Ollama models if necessary.
if [ -f models.txt ]; then
    echo ""
    echo "Pulling Ollama models..."
    if ! command -v ollama &> /dev/null; then
        echo "Ollama is not installed. Please install and re-run. Skipping model pulls for now..."
    fi

    while IFS= read -r model; do
        echo "Pulling $model..."
        tput sc
        ollama pull "$model" || { echo "Failed to pull $model"; }
        tput rc
        tput ed
    done < models.txt
fi

echo ""
echo "All dependencies installed successfully."

if [ -f env.py ]; then
    echo ""
    echo "Please update the variables in env.py accordingly."

    # Reminder to install and migrate Django database. The modified manage.py
    # here ensures the dabatase is created if it doesn't exist...
    if [ -f manage.py ]; then
        echo "Once you've added the DB env variables, run python3 manage.py migrate..."
    fi
fi
