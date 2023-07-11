#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Image search and processing with OMERO - part 2

This script will show you how to import your images following the example used in the relative video.

Aurélien VALENTIN for the ImHorPhen research team (Angers, France) - July 2023
"""


# IMPORT
import omero, omero.clients, subprocess
from omero.gateway import BlitzGateway
from omero.rtypes import rstring
from omero_sys_ParametersI import ParametersI
from os import system, listdir
from sys import exit
from time import time
from tqdm import tqdm

start_time = time()

# CONNECTION
client = omero.client("localhost")
session = client.createSession("root", "omero_root_password") 


# FUNCTIONS
def import_image(image_path: str, dataset_id: int) -> int:
    """Import an image using in-place import (avoinding to copy your data), see the "LINKS" section below.

    Parameters
    ----------
    image_path: str
        The local path to your image. It can be a path to an image on a server that you can browse from your machine.
    dataset_id: int
        The ID of the dataset where your image should be located.
    
    Returns
    -------
    image_id : int
        The ID of the image uploaded.
    
    Note
    ----
    This function uses the CLI (Command Line Interface) since no equivalent with Python was found.
    """
    
    image_id = int(str(subprocess.check_output("omero import --transfer=ln_s " + image_path + " -d " + dataset_id, shell = True)).split(":")[1].split("\\n")[0])
    return image_id

def get_ID(name: str, type: str) -> int:
    """Get the ID of an object based on its name.
    
    Parameters
    ----------
    name: str
        The name of the object.
    type: int
        The type of the object, e. g. Image, Dataset or Project.
    
    Returns
    -------
    object_id: int
        The ID researched of the object.
    
    Note
    ----
    Be careful with the use of this function since in OMERO you can use the same name for different objects. This function
    is coded to detect that but it is not necessary in the example shown.
    """
    
    q = session.getQueryService()
    query_string = ("select i from " + type + " i where name = :namedParameter")
    p = ParametersI()
    p.add("namedParameter", rstring(name))
    results = q.findAllByQuery(query_string, p)

    if len(results) == 0:
        print("There is no {type} with the name {name}".format(type = type, name = name))
        exit()
    elif len(results) != 1:
        print("There are more than one {type} with the same name {name}. You should use IDs which are unique.".format(type = type, name = name))
        exit()
    else:
        object_id = str(results[0].id).split("= ")[-1].split("\n")[0]
        return(object_id)


# FUNCTION CALLs
with BlitzGateway("root", "omero_root_password", host = "localhost", secure = True) as conn: # Connection
    system("omero login -s localhost -u root -w omero_root_password")
    path = "/home/stagiaire-imhorphen/Documents/Demo_omero/sample/" # Path to the three example folders
    for year in ["2020", "2021", "2022"]: # Looking in all directories
        for image in tqdm(listdir(path + year), desc = year): # Looking for all images
            import_image(path + "/" + year + "/" + image, get_ID(year, "Dataset"))  

client.closeSession() # Disconnection

print("Program executed in {time} seconds".format(time = time() - start_time))


# LINKS
# In-place import: https://omero-guides.readthedocs.io/en/latest/upload/docs/import-cli.html#in-place-import-using-the-cli
# More information about writing queries with OMERO: https://docs.openmicroscopy.org/omero/5.6.0/developers/Server/Queries.html
# More information about functions to query (such as the findAllByQuery used here): https://omero.readthedocs.io/en/stable/developers/Modules/Search.html#ome-api-iquery
# get_ID function based on https://github.com/ome/openmicroscopy/blob/e23c38e6fc92e8681a8bae619019b49f51613d07/examples/OmeroClients/queries.py