"""Package setup for cli-anything-sam."""
from setuptools import setup, find_namespace_packages

setup(
    name="cli-anything-sam",
    version="1.0.0",
    description="CLI harness for NREL System Advisor Model (SAM) via PySAM",
    long_description=open("cli_anything/sam/README.md").read(),
    long_description_content_type="text/markdown",
    author="cli-anything",
    url="https://github.com/NREL/SAM",
    license="BSD-3-Clause",
    packages=find_namespace_packages(include=["cli_anything.*"]),
    package_data={
        "cli_anything.sam": ["skills/*.md"],
    },
    install_requires=[
        "click>=8.0.0",
        "prompt-toolkit>=3.0.0",
        "NREL-PySAM>=6.0.0",
    ],
    entry_points={
        "console_scripts": [
            "cli-anything-sam=cli_anything.sam.sam_cli:main",
        ],
    },
    python_requires=">=3.10",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Physics",
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: BSD Software License",
    ],
)
