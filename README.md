# Ontology Service Package

## Overview
The Ontology Service Package is a Python package designed to provide an interface for querying ontological information using FastAPI. In its current version it allows users to load OWL ontologies and retrieve information about class hierarchies.

## Directory Structure
```
ontology_service_package/
├── ontologies/          # Directory for storing OWL ontology files
├── ontology_service.py  # FastAPI application for querying ontologies
├── setup.py             # Package configuration and metadata
├── __init__.py         # Package initialization
└── README.md            # Project documentation
```

## Installation
To install the Ontology Service Package, clone the repository and run the following command in the project directory:

```
pip install .
```

## Usage
1. Place your OWL ontology files in the `ontologies/` directory.
2. Run the FastAPI application:

```
uvicorn ontology_service:app --reload --port 8089
```

3. Access the API documentation at `http://127.0.0.1:8089/docs`.

## API Endpoints
- **GET /**: Redirects to the API documentation.
- **GET /ontologies**: Returns a list of all successfully loaded ontology names.
- **GET /ontologies/{ontology_name}/superclasses/{class_name}**: Retrieves all superclasses (ancestors) for a given class name from a specific ontology.