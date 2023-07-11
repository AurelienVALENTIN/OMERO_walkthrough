#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Image search and processing with OMERO - part 5

This script can be imported in OMERO in order to process an example process on a query result.

Aurélien VALENTIN for the ImHorPhen research team (Angers, France) - July 2023
"""

# IMPORT
import omero, omero.scripts as scripts
import numpy as np
from omero.gateway import BlitzGateway
from omero.rtypes import rstring
from omero.sys import Parameters
from time import time

start_time = time()


# DEFINE THE SCRIPT PARAMTERS
client = scripts.client(
    "Threshold2.py",
    """Threshold RGB images on a query.""",
    scripts.Bool("Process on a given object", optional = False, grouping = "01", default = True),
    scripts.String("Object type", optional = False, grouping = "01.1", default = "Image", values = [rstring("Image"), rstring("Dataset"), rstring("Project")]),
    scripts.Long("Object ID", optional = False, grouping = "01.1"),
    scripts.Bool("Process on a query", optional = False, grouping = "02", default = True),
    scripts.Map("Key:Value pair(s)", optional = True, grouping = "02.1"),
    scripts.Bool("RGB channel threshold values", optional = True, grouping = "03", default = True), # A simple text should be better but it doesn't seem to be possible...
    scripts.Int("Red min", optional = False, grouping = "03.1", default = 103, min = 0, max = 255),
    scripts.Int("Red max", optional = False, grouping = "03.2", default = 255, min = 0, max = 255),
    scripts.Int("Green min", optional = False, grouping = "03.3", default = 115, min = 0, max = 255),
    scripts.Int("Green max", optional = False, grouping = "03.4", default = 255, min = 0, max = 255),
    scripts.Int("Blue min", optional = False, grouping = "03.5", default = 60, min = 0, max = 255),
    scripts.Int("Blue max", optional = False, grouping = "03.6", default = 255, min = 0, max = 255),
    scripts.Bool("Thresholded images", optional = True, grouping = "04", default = True), # Once again, just a string would be nice.
    scripts.String('Image names ("[f]" will add the file name)', optional = False, grouping = "04.1", default = "[f]_thresholded"),
    scripts.String("Format", optional = False, grouping = "04.2", values = [rstring("jpeg"), rstring("png"), rstring("tif")], default = "png"),
    scripts.Bool("Output in another dataset", optional = False, grouping = "05", default = True),
    scripts.String("Dataset ID for an existing dataset OR Dataset name to create a new dataset", optional = True, grouping = "05.1"),
    scripts.Bool("Copy past Key:Value pair(s)", optional = True, grouping = "06", default = True),
    authors = ["Aurélien VALENTIN for the ImHorPhen research team (Angers, France)"]
    )

# Get the parameters
inputs = client.getInputs(unwrap=True)
thr_values = [(inputs["Red min"], inputs["Red max"]), (inputs["Green min"], inputs["Green max"]), (inputs["Blue min"], inputs["Blue max"])]

# Connection
conn = BlitzGateway(client_obj = client)


# FUNCTIONS
def planeGen(image, thr_values: list, zctList: list):
    """Create a processed image generator.

    Parameters
    ----------
    image:  omero.gateway._ImageWrapper
        Original image to process.start_time = time()
    thr_values: list of tuples of two ints
        RGB threshold values mandatory for the example process.
    zctList: list
        Not really used here, to get planes from stacks.
    """

    planes = image.getPrimaryPixels().getPlanes(zctList)
    i = 0
    for p in planes:
        # Here you can add any code you want.
        range = np.logical_and(thr_values[i][0] < p[:,:], p[:,:] < thr_values[i][1])
        if i == 0: red_range = range
        elif i == 1: green_range = range
        else: blue_range = range
        i += 1
    valid_range = np.logical_and(red_range, green_range, blue_range)

    planes = image.getPrimaryPixels().getPlanes(zctList)
    for p in planes:
        p[valid_range] = 255
        p[np.logical_not(valid_range)] = 0
        yield p

def process_image(image_id: int, image_name: str, parent_dataset):
    """Get an image with its info and adding info to the processed image.

    Parameters
    ----------
    image_id: int
        The ID of the image to process.
    image_name: str
        The name of the image processed according to the user input.
    parent_dataset: omero.gateway._ImageWrapper
        Parent dataset.
    """

    # Getting original image info
    image_or = conn.getObject("Image", image_id)
    sizeZ = image_or.getSizeZ()
    sizeC = image_or.getSizeC()
    sizeT = image_or.getSizeT()
    clist = range(sizeC)
    zctList = []
    for z in range(sizeZ):
        for c in clist:
            for t in range(sizeT):
                zctList.append((z,c,t))

    # Create the processed image
    image = conn.createImageFromNumpySeq(
        planeGen(image_or, thr_values, zctList), image_name, sizeZ = sizeZ, sizeC = sizeC, sizeT = sizeT,
        sourceImageId = image_id, channelList = clist)
    
    # Copy K:V pairs
    if inputs["Copy past Key:Value pair(s)"] == True:
        KV_pairs = []
        for anno in image_or.getAnnotation().getMapValue():
            KV_pairs.append([anno.name, anno.value])
        map_ann = omero.gateway.MapAnnotationWrapper(conn)
        map_ann.setNs(omero.constants.metadata.NSCLIENTMAPANNOTATION)
        map_ann.setValue(KV_pairs)
        map_ann.save()
        image.linkAnnotation(map_ann)

    # Link image to dataset
    link = omero.model.DatasetImageLinkI()
    link.parent = omero.model.DatasetI(parent_dataset.getId(), False)
    link.child = omero.model.ImageI(image.getId(), False)
    conn.getUpdateService().saveAndReturnObject(link)

    return

def filter_by_kv(conn, img_ids: list, key: str, value: str) -> list:
    """Filter a given list of imags with a given key:value pair.

    Parameters
    ----------
    cconn: omero.gateway.BlitzGateway object
        OMERO connection.
    img_ids: list
        The list of all image IDs to query.
    key: str
        Key to query.
    value: str
        Value to query.
    
    Returns
    -------
    img_ids: list of ints
        The result IDs from the query.
    """

    q = conn.getQueryService()
    params = Parameters()
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


# CHECKING OPTIONAL PARAMETERS
# Adapting to the object
object_type = inputs["Object type"]
object_id = inputs["Object ID"]
img_id_list = []
if  object_type == "Image":
    img_id_list.append(object_id)
elif object_type == "Project":
    project = conn.getObject("Project", object_id)
    for dataset in project.listChildren():
        for image in dataset.listChildren():
            img_id_list.append(image.getId())
else: # Dataset
    dataset = conn.getObject("Dataset", object_id)
    for image in dataset.listChildren():
        img_id_list.append(image.getId())

# Query
if inputs["Process on a query"] == True:
    try:
        key_value = inputs["Key:Value pair(s)"]
        for key in key_value.keys():
            img_id_list = filter_by_kv(conn, img_id_list, key, key_value[key])
    except: pass

# Output dataset
if inputs["Output in another dataset"] == True:
    dataset = inputs["Dataset ID for an existing dataset OR Dataset name to create a new dataset"]
    if dataset.isdigit():
        parent_dataset = conn.getObject("Dataset", int(dataset))
    else:
        # Create dataset
        parent_dataset = omero.model.DatasetI()
        parent_dataset.setName(rstring(dataset))
        parent_dataset = conn.getUpdateService().saveAndReturnObject(parent_dataset)

        # Link dataset to project
        link = omero.model.ProjectDatasetLinkI()
        link.setParent(omero.model.ProjectI(conn.getObject("Image", img_id_list[0]).getParent().getParent().getId(), False)) # Assuming that all images are from the same project.
        link.setChild(parent_dataset)
        conn.getUpdateService().saveObject(link)


# PROCESSING IMAGES ONE BY ONE
for img in img_id_list:
    image = conn.getObject("Image", img)
    if inputs["Output in another dataset"] == False:
        parent_dataset = image.getParent()
    process_image(img, inputs['Image names ("[f]" will add the file name)'].replace("[f]", image.getName()[:image.getName().rfind(".")]) + "." + inputs["Format"], parent_dataset)


# ENDING
client.setOutput("Message", rstring("Processed {img_number} images in {time} seconds.".format(img_number =  len(img_id_list), time = round(time() - start_time, 2))))
client.closeSession()


# LINKS
# For more information about OMERO.scripts: https://omero.readthedocs.io/en/stable/developers/scripts/index.html
# Threshold method adapted from https://stackoverflow.com/questions/231767/what-does-the-yield-keyword-do-in-python
# Adding key:value pairs from https://omero.readthedocs.io/en/stable/developers/Python.html#write-data
# filter_by_kv function adapted from the eponymous ezomero function: https://thejacksonlaboratory.github.io/ezomero/ezomero.html
# Apparently, output while the script is running for loading is not possible: https://omero.readthedocs.io/en/stable/developers/scripts/style-guide.html#script-outputs