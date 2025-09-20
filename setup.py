from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="villager",
    version="0.2.1rc1",
    author="stupidfish001",
    author_email="shovel@hscsec.cn",
    description="This was an experimental technology project",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/gregcmartin/villager",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "villager=villager.interfaces.boot:main",
        ],
    },
    include_package_data=True,
    package_data={
        "scheduler": ["core/RAGLibrary/statics/*"],
    },
)
