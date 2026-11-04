from setuptools import setup, find_packages

setup(
    name="foxvc",
    version="0.6.0a0",
    description="FoxVC Programming Language - Zero-Overlap Lean Edition",
    author="Nexus Systems",
    packages=find_packages(),
    py_modules=["foxvc_entry"],
    entry_points={
        "console_scripts": [
            "foxvc=engine.cli:main",
        ],
    },
    python_requires=">=3.8",
)
