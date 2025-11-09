"""Setup script for packaging the APL reference implementation."""

from __future__ import annotations

from pathlib import Path

from setuptools import find_packages, setup

ROOT = Path(__file__).parent
README = ROOT / "docs" / "README.md"

setup(
    name="apl",
    version="0.1.0",
    description="Reference compiler, runtime, and CLI for the Agent Programming Language (APL).",
    long_description=README.read_text(encoding="utf-8"),
    long_description_content_type="text/markdown",
    author="Agent Programming Language maintainers",
    python_requires=">=3.10",
    package_dir={"": "packages/python/src"},
    packages=find_packages(where="packages/python/src"),
    include_package_data=True,
    install_requires=[
        # Add core runtime dependencies here when they become non-stdlib.
    ],
    extras_require={
        "dev": [
            "lark-parser>=0.12.0",
            "pytest>=7.0.0",
            "black>=23.0.0",
            "ruff>=0.1.0",
        ],
    },
    entry_points={"console_scripts": ["apl=apl.cli:main"]},
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: Software Development :: Compilers",
        "Topic :: Software Development :: Libraries",
    ],
    project_urls={
        "Source": "https://github.com/AgentProgrammingLanguage",
        "Documentation": "https://github.com/AgentProgrammingLanguage",
    },
)
