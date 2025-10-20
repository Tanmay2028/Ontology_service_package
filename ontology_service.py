# filepath: /ontology_service_package/ontology_service_package/ontology_service.py
######################################################################
######################## import libraries ############################
######################################################################
from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse
from contextlib import asynccontextmanager
from owlready2 import get_ontology, sync_reasoner
from owlready2.namespace import Ontology

import os
import logging

# Configure logging for better debugging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

#######################################################################
################## application state and setup ########################
#######################################################################

# We'll store the loaded ontologies in a simple dictionary.
# The key will be the ontology name (from the filename), and the value
# will be the owlready2 ontology object.
loaded_ontologies = {}
ONTOLOGY_DIR = "ontologies"

def load_ontologies_from_directory(directory: str):
    """
    Scans a directory for .owl files and loads them into memory.
    This function is called once at application startup.
    """
    if not os.path.exists(directory):
        logger.warning(f"Ontology directory '{directory}' not found. Creating it.")
        os.makedirs(directory)
        # Inform the user that they need to add files.
        logger.info(f"Please add your .owl ontology files to the '{directory}' directory and restart the application.")
        return

    logger.info(f"Scanning for ontologies in: {directory}")
    for filename in os.listdir(directory):
        if filename.endswith(".owl"):
            ontology_name = os.path.splitext(filename)[0]
            owl_file_path = os.path.join(directory, filename)
            try:
                logger.info(f"Loading ontology '{ontology_name}' from: {owl_file_path}")
                # The 'file://' prefix is crucial for owlready2 to correctly resolve local files.
                ontology = get_ontology(f"file://{os.path.abspath(owl_file_path)}").load()
                loaded_ontologies[ontology_name] = ontology
                logger.info(f"Successfully loaded '{ontology_name}'.")
            except Exception as e:
                logger.error(f"Failed to load ontology '{filename}': {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # This code runs on startup
    print("--- Starting up Ontology Service ---")
    load_ontologies_from_directory(ONTOLOGY_DIR)
    
    if loaded_ontologies:
        print("--- Running Reasoner (HermiT) on all loaded ontologies ---")
        try:
            # We run the reasoner on the entire world or explicitly on the loaded ontologies.
            # Using sync_reasoner_hermit() without arguments usually runs it on all loaded ontologies.
            # The reasoner updates the in-memory representation of the ontologies, including 
            # the superclass hierarchy, which is exactly what fetch_superclasses uses.
            # You can pass a list of ontologies if you want to be explicit:
            # sync_reasoner_hermit(list(loaded_ontologies.values()))
            
            # Simple call to reason over the entire world (which contains our loaded ontologies)
            sync_reasoner() 
            print("--- Reasoning completed successfully. ---")
            
        except Exception as e:
            # A common issue is Java not being found or the reasoner failing to download/start.
            logger.error(f"Reasoning failed. Check if Java is installed and accessible. Error: {e}")
            logger.warning("The service will continue using only explicitly asserted (non-inferred) knowledge.")

    yield
    # This code runs on shutdown
    print("--- Shutting down Ontology Service ---")
    loaded_ontologies.clear()


#######################################################################
########################## define app and functions ###################
#######################################################################
app = FastAPI(
    title="Ontology Service",
    description="A service to provide ontological information by querying multiple local ontologies.",
    lifespan=lifespan
)

def get_labels(entity):
    """
    Utility function to get human-readable labels for an ontology entity.
    """
    if hasattr(entity, 'label') and entity.label:
        return entity.label
    return [entity.name]

def fetch_superclasses(ontology: Ontology, class_name: str):
    """
    Searches a given ontology for a class and returns its ancestors.
    """
    logger.debug(f"Fetching superclasses for class: '{class_name}' in ontology '{ontology.name}'")
    
    # Search for the class within the ontology. This is more robust.
    cls = ontology.search_one(iri=f"*{class_name}")

    if cls is None:
        raise ValueError(f"Class '{class_name}' not found in the ontology '{ontology.name}'.")
    
    # Return the class itself and all its ancestors
    return cls.ancestors()

#######################################################################
########################## application routes #########################
#######################################################################
@app.get("/", include_in_schema=False)
def root():
    """Redirect to the API documentation."""
    return RedirectResponse(url="/docs")


@app.get("/ontologies", tags=["Ontology Management"])
def get_available_ontologies():
    """
    Returns a list of all successfully loaded ontology names.
    """
    if not loaded_ontologies:
        return {"message": f"No ontologies found or loaded. Please add .owl files to the '{ONTOLOGY_DIR}' directory."}
    return {"available_ontologies": list(loaded_ontologies.keys())}


@app.get("/ontologies/{ontology_name}/superclasses/{class_name}", tags=["Querying"])
def get_superclasses_route(ontology_name: str, class_name: str):
    """
    Gets all superclasses (ancestors) for a given class name from a specific ontology.
    """
    if ontology_name not in loaded_ontologies:
        raise HTTPException(status_code=404, detail=f"Ontology '{ontology_name}' not found. Available ontologies: {list(loaded_ontologies.keys())}")

    try:
        ontology = loaded_ontologies[ontology_name]
        superclasses = fetch_superclasses(ontology, class_name)

        # Build a response with human-readable labels where possible

        response_superclasses = []
        for cls in superclasses:
            labels = get_labels(cls)
            response_superclasses.append(labels[0] if labels else cls.name)
            
        return {
            "superclasses": response_superclasses
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"An unexpected error occurred while processing request: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="An unexpected error occurred while processing the request.")