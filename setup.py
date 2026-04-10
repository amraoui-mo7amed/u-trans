from setuptools import setup, find_packages

setup(
    name="u-translator",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "google-genai",
        "openai",
        "groq",
        "python-decouple",
        "tqdm",
    ],
    entry_points={
        "console_scripts": [
            "u-trans=u_translator.cli:main",
        ],
    },
    author="mohamed",
    description="A multi-provider CLI translator tool for .po files.",
)
