#!/usr/bin/env python3
"""
Setup script for KaironDB
"""

from setuptools import setup, find_packages
import os

# Read the README file
def read_readme():
    with open("README.MD", "r", encoding="utf-8") as fh:
        return fh.read()

# Read requirements
def read_requirements():
    requirements = []
    if os.path.exists("requirements.txt"):
        with open("requirements.txt", "r", encoding="utf-8") as fh:
            requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]
    return requirements

setup(
    name="kairondb",
    version="1.0.1",
    author="Daniel Giansante",
    author_email="daniel.giansantev@gmail.com",
    description="Uma biblioteca Python para interagir com bancos de dados através de uma DLL em Go.",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/DanielGiansante/KaironDB",
    project_urls={
        "Bug Reports": "https://github.com/DanielGiansante/KaironDB/issues",
        "Source": "https://github.com/DanielGiansante/KaironDB",
        "Documentation": "https://github.com/DanielGiansante/KaironDB#readme",
    },
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    package_data={
        "kairondb": ["*.dll", "*.so"],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Topic :: Database",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires=">=3.7",
    install_requires=read_requirements(),
    extras_require={
        "dev": [
            "pytest>=6.0",
            "pytest-asyncio>=0.18.0",
            "pytest-cov>=2.0.0",
            "black>=21.0.0",
            "isort>=5.0.0",
            "mypy>=0.900",
            "pre-commit>=2.0.0",
        ],
        "docs": [
            "sphinx>=4.0.0",
            "sphinx-rtd-theme>=0.5.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "kairondb=kairondb.cli:main",
        ],
    },
    keywords="database orm async python go dll sqlite postgresql mysql sqlserver",
    zip_safe=False,
)
