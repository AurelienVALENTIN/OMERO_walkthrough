#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Image search and processing with OMERO - part 4

This script will show you how to browse images depending on their Key:Value pairs following the example used in the relative video.

Aurélien VALENTIN for the ImHorPhen research team (Angers, France) - July 2023
"""


# IMPORT
import omero, omero.clients
from omero.gateway import BlitzGateway
from omero.rtypes import rstring
from omero.sys import Parameters
from time import time

start_time = time()


# CONNECTION
client = omero.client("localhost")
session = client.createSession("root", "omero_root_password") 


# FUNCTIONS
def filter_by_kv(conn: BlitzGateway, key_value_list: list, type = "", id = 0) -> list:
    """Filter a given set of images (from dataset or project) with given key:value pair(s).

    Parameters
    ----------
    conn: omero.gateway.BlitzGateway object
        OMERO connection.
    key_value: list of list(s) of two str
        The Key:Value pair(s) to add as a list of [Key, Value]. For example: [["Year", "2020"], ["Species", "Arabidopsis thaliana"]].
    type: str
        The type of the object, e. g. Image, Dataset or Project.
    id: int
        The ID of the object.
    
    Returns
    -------
    img_ids: list of ints
        The result IDs from the query.
    
    Note
    ----
    type and id arguments are optional but if you add one you need to add the other.
    """

    # Picking all image IDs
    img_ids = []
    if type == "":
        for img in conn.getObjects("Image"):
            img_ids.append(img.id)
    elif type == "Image":
        img_ids.append(id)
    elif type == "Dataset":
        for img in conn.getObject("Dataset", id).listChildren():
            img_ids.append(img.id)
    elif type == "Project":
        for dataset in conn.getObject("Project", id).listChildren():
            print(dataset)
            for img in conn.getObject("Dataset", id).listChildren():
                img_ids.append(img.id)
    
    # Processing the query/queries.
    q = conn.getQueryService()
    params = Parameters()
    for key, value in key_value_list:
        params.map = {"key": rstring(key),
                    "value": rstring(value)}
        results = q.projection(
            "SELECT i.id FROM Image i"
            " JOIN i.annotationLinks al"
            " JOIN al.child ann"
            " JOIN ann.mapValue as nv"
            " WHERE nv.name = :key"
            " AND nv.value = :value",
            params,
            conn.SERVICE_OPTS
            )
        img_id_matches = [r[0].val for r in results]
        img_ids = list(set(img_ids) & set(img_id_matches))
    return img_ids


# FUNCTION CALL
with BlitzGateway("root", "omero_root_password", host = "localhost", secure = True) as conn: # Connection
    result = filter_by_kv(conn, [["Disease", "Big"], ["Lighting", "Medium"]], "Dataset", 49)
    print(result)
client.closeSession() # Disconnection

print("Program executed in {time} seconds".format(time = time() - start_time))


# LINKS
# More information about writing queries with OMERO: https://docs.openmicroscopy.org/omero/5.6.0/developers/Server/Queries.html
# filter_by_kv function adapted from the eponymous ezomero function: https://thejacksonlaboratory.github.io/ezomero/ezomero.html
