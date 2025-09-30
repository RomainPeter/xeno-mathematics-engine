from setuptools import setup, find_packages

setup(
    name="proofengine",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "openai>=1.43.0",
        "tenacity>=8.4.2",
        "pydantic>=2.7.0",
        "python-dotenv>=1.0.1",
        "typer>=0.12.3",
        "rich>=13.7.1",
        "pytest>=7.0.0",
        "flake8>=6.0.0",
        "mypy>=1.0.0",
        "bandit>=1.7.0",
        "radon>=6.0.0",
    ],
)
