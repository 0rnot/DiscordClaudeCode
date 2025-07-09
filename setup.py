#!/usr/bin/env python3
"""
Setup script for human-in-the-loop-python
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="DiscordClaudeCode",
    version="1.0.0",
    author="0rnot",
    author_email="",
    description="A Python implementation of MCP server for AI-human collaboration via Discord",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/0rnot/DiscordClaudeCode",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Communications :: Chat",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "human-in-the-loop=final_working_version:main",
        ],
    },
    keywords="ai, discord, mcp, model-context-protocol, human-in-the-loop, claude-code",
    project_urls={
        "Bug Reports": "https://github.com/0rnot/DiscordClaudeCode/issues",
        "Source": "https://github.com/0rnot/DiscordClaudeCode",
        "Documentation": "https://github.com/0rnot/DiscordClaudeCode/blob/main/README.md",
    },
)