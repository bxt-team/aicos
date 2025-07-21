#!/bin/bash

echo "Fixing dependency conflicts..."

# First, upgrade pip
pip install --upgrade pip

# Upgrade the conflicting packages to compatible versions
pip install --upgrade \
    httpx>=0.27.0 \
    requests>=2.32.3 \
    pydantic>=2.7.4 \
    pydantic-settings>=2.4.0 \
    pydantic-core>=2.18.2 \
    orjson>=3.9.14

# Install moviepy and its dependencies
pip install moviepy==1.0.3 imageio-ffmpeg==0.4.9

# Reinstall packages that depend on the upgraded ones
pip install --upgrade --force-reinstall \
    langchain \
    langchain-community \
    langchain-core \
    chromadb \
    instructor \
    crewai \
    crewai-tools

echo "Dependencies fixed! You may need to restart your Python environment."