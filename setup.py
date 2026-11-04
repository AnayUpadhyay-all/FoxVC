from setuptools import setup, find_packages

setup(
    name="foxvc",
    version="0.6.0a0",
    description="FoxVC Programming Language: Ultra-Compact 25-Keyword C Virtual Machine & Compiler",
    author="Anay Upadhyay",
    packages=find_packages(),
    package_data={
        "engine": ["foxvm.c", "foxvm.so"],
        "studio": ["web/*", "*.html", "manifest.json"],
    },
    include_package_data=True,
    entry_points={
        "console_scripts": [
            "foxvc=engine.cli:main",
        ],
    },
    python_requires=">=3.8",
)
