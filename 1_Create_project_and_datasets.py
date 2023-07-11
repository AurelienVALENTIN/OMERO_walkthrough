#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Image search and processing with OMERO - part 1

This script will show you how to create a project and several datasets following the example used in the relative video.

Aurélien VALENTIN for the ImHorPhen research team (Angers, France) - July 2023
"""


# IMPORT
import omero, omero.clients
from omero.gateway import BlitzGateway
from omero.rtypes import rstring
from time import time

start_time = time()


# CONNECTION
client = omero.client("localhost")
session = client.createSession("root", "omero_root_password") 


# FUNCTIONS
def create_project(project_name: str, conn: BlitzGateway) -> int:
    """Create a project.

    Parameters
    ----------
    project_name: str
        The name you want to give to your project.
    conn: omero.gateway.BlitzGateway object
        OMERO connection.
    
    Returns
    -------
    project_id : int
        The ID of the project you have just created.
    """
    
    project_obj = omero.model.ProjectI()
    project_obj.setName(rstring(project_name))
    project_obj = conn.getUpdateService().saveAndReturnObject(project_obj, conn.SERVICE_OPTS)
    project_id = project_obj.getId().getValue()
    
    return project_id

def create_dataset(dataset_name: str, project_ID: int, conn: BlitzGateway) -> int:
    """Create a dataset and link it to an existing project.

    Parameters
    ----------
    dataset_name: str
        The name you want to give to your dataset.
    project_ID: int
        The ID of the project to which you want to add your dataset.
    conn: omero.gateway.BlitzGateway object
        OMERO connection.
    
    Returns
    -------
    dataset_id: int
        The ID of the dataset you have just created.
    """
    
    # Creating dataset
    dataset_obj = omero.model.DatasetI()
    dataset_obj.setName(rstring(dataset_name))
    dataset_obj = conn.getUpdateService().saveAndReturnObject(dataset_obj)
    dataset_id = dataset_obj.getId().getValue()

    # Linking dataset
    project = conn.getObject("Project", project_ID)
    link = omero.model.ProjectDatasetLinkI()
    link.setParent(omero.model.ProjectI(project.getId(), False))
    link.setChild(dataset_obj)
    conn.getUpdateService().saveObject(link)

    return dataset_id


# FUNCTION CALLS
with BlitzGateway(host = "localhost", username = "root", passwd = "omero_root_password", secure = True) as conn: # Connection
    project_id = create_project("Demo_OMERO", conn)
    create_dataset("2020", project_id, conn)
    create_dataset("2021", project_id, conn)
    create_dataset("2022", project_id, conn)

client.closeSession() # Disconnection

print("Program executed in {time} seconds".format(time = time() - start_time))


# LINKS
# Source: https://omero.readthedocs.io/en/stable/developers/Python.html#write-data
# Another way is possible using the CLI (Command Line Interface): https://omero-guides.readthedocs.io/projects/upload/en/latest/import-cli.html#id5