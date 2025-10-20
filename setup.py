from setuptools import setup, find_packages

setup(
    name="ontology_service_package",
    version="0.1.0",
    author="Tanmay Kulkarni",
    author_email="tanmay.kulkarni@fau.de",
    description="A FastAPI service for querying ontological information from OWL files.",
    packages=find_packages(),
    install_requires=[
        "fastapi",
        "uvicorn",
        "owlready2",
        "pydantic"
    ],
    entry_points={
        "console_scripts": [
            "ontology_service=ontology_service:app"
        ]
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "Framework :: FastAPI"
    ],
    python_requires='>=3.6',
)