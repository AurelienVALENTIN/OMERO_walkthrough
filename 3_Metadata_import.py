#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Image search and processing with OMERO - part 3

This script will show you how to import some image metadata following the example used in the relative video.

Aurélien VALENTIN for the ImHorPhen research team (Angers, France) - July 2023
"""


# IMPORT
import omero, omero.clients
from omero.gateway import BlitzGateway
from omero.rtypes import rstring
from omero_sys_ParametersI import ParametersI
from time import time
from tqdm import tqdm

start_time = time()


# CONNECTION
client = omero.client("localhost")
session = client.createSession("root", "omero_root_password") 


# FUNCTIONS
def add_key_value_pair(key_value: list, type: str, id: int):
    """Add annotation based on Key:Value pairs such as Year:2020 to a given object.

    Parameters
    ----------
    key_value: list of list(s) of two str
        The Key:Value pair(s) to add as a list of [Key, Value]. For example: [["Year", "2020"], ["Species", "Arabidopsis thaliana"]].
    type: str
        The type of the object, e. g. Image, Dataset or Project.
    id: int
        The ID of the object.
    """

    map_ann = omero.gateway.MapAnnotationWrapper(conn)
    map_ann.setNs(omero.constants.metadata.NSCLIENTMAPANNOTATION)
    map_ann.setValue(key_value)
    map_ann.save()
    object = conn.getObject(type, id)
    object.linkAnnotation(map_ann)
    return

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
    detect that but it is not necessary in the example shown.
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


# FUNCTIONS CALL
with BlitzGateway("root", "omero_root_password", host = "localhost", secure = True) as conn: # Connection
    path = "/home/stagiaire-imhorphen/Documents/Demo_omero/sample/" # Path to the three examples
    for year in ["2020", "2021", "2022"]:
        with open(path + year + ".csv") as fpi:
            fpi.readline()
            fpi.readline()
            for line in tqdm(fpi.readlines(), desc = year):
                image, disease, lighting = line.strip().split(", ")
                add_key_value_pair([["Year", year], ["Disease", disease], ["Lighting", lighting]], "Image", get_ID(image, "Image"))
    # NB : This import may be used only one time for one image. Reapply it will change the MapAnnotation link and could disturb some codes.
            
client.closeSession() # Disconnection

print("Program executed in {time} seconds".format(time = time() - start_time))


# LINKS
# Metadata import can also be realized with OMERO.web. Note that the .csv files used have a header corresponding to OMERO requirements for a such import: https://omero-guides.readthedocs.io/en/latest/upload/docs/metadata-ui.html#
# There is also another way to import metadata with the CLI: https://omero-guides.readthedocs.io/en/latest/upload/docs/metadata.html
# add_key_value_pair function from https://omero.readthedocs.io/en/stable/developers/Python.html#write-data
# get_ID function based on https://github.com/ome/openmicroscopy/blob/e23c38e6fc92e8681a8bae619019b49f51613d07/examples/OmeroClients/queries.py