import os
#from scipy.spatial import ConvexHull, convex_hull_plot_2d
#import matplotlib.pyplot as plt
import numpy as np
import shapely
from shapely.ops import unary_union, cascaded_union
from shapely.geometry import Polygon
import camproject

from . import image
from . import db


def import_flight(indir):
    for root, dirs, files in os.walk(indir):
        for f in files: 
            fname, fext = os.path.splitext(f)
            if fext.lower() not in [".jpg", ".ara",".raw"]: continue
            myimg = image.Image.factory(os.path.join(root,f),True)
            uniqueinsert
            flightpath["X"].append(myimg.header["gps"]["UTM_X"])
            flightpath["Y"].append(myimg.header["gps"]["UTM_Y"])
            flightpath["Z"].append(myimg.header["gps"]["rel_altitude"])
            flightpath["campitch"].append(myimg.header["camera"]["pitch"])
            flightpath["yaw"].append(myimg.header["uav"]["yaw"])


def extract_poly_coords(geom):
    if geom.type == 'Polygon':
        exterior_coords = geom.exterior.coords[:]
        interior_coords = []
        for interior in geom.interiors:
            interior_coords += interior.coords[:]
    elif geom.type == 'MultiPolygon':
        exterior_coords = []
        interior_coords = []
        for part in geom:
            epc = extract_poly_coords(part)  # Recursive call
            exterior_coords += epc['exterior_coords']
            interior_coords += epc['interior_coords']
    else:
        raise ValueError('Unhandled geometry type: ' + repr(geom.type))
    return {'exterior_coords': exterior_coords,
            'interior_coords': interior_coords}
            
def scan(indir):            
    #indir = "C:/WILDRETTER DATEN/2020_Easy/201005_1426_naehe_ulm"
    print(indir)
    for root, dirs, files in os.walk(indir):
        flightpath = {"UTMZone":[],"X":[],"Y":[],"Z":[],"yaw":[],"campitch":[]}
        for f in files: 
            fname, fext = os.path.splitext(f)
            if fext.lower() not in [".jpg", ".ara",".raw"]: continue
            myimg = image.Image.factory(os.path.join(root,f),True)
            flightpath["X"].append(myimg.header["gps"]["UTM_X"])
            flightpath["Y"].append(myimg.header["gps"]["UTM_Y"])
            flightpath["Z"].append(myimg.header["gps"]["rel_altitude"])
            flightpath["campitch"].append(myimg.header["camera"]["pitch"])
            flightpath["yaw"].append(myimg.header["uav"]["yaw"])
            zone = str(myimg.header["gps"]["UTM_ZoneNumber"])+str(myimg.header["gps"]["UTM_ZoneLetter"])
            if zone not in flightpath["UTMZone"]:
                flightpath["UTMZone"].append(zone)
            
        if len(flightpath["UTMZone"])>1:
            raise NotImplementedError("This flight has more than one UTM Zone. This special case is not yet implemented")

    X = np.array(flightpath["X"])
    Y = np.array(flightpath["Y"])
    Z = np.array(flightpath["Z"])
    Yaw = np.array(flightpath["yaw"])
    Campitch = np.array(flightpath["campitch"])

    cam = camproject.Camera()
    ext = camproject.Extrinsics()
    cam.intrinsics(640,512,1167,320,256)
    poly = []
    for i in range(1,len(X)):
        if Campitch[i] > -85 or Campitch[i] < -95: 
            #print (i,"cam pitch falsch: ",Campitch[i])
            continue
        ext.setPose(X[i],Y[i],Z[i])
        ext.setGimbal(0,Campitch[i],Yaw[i])
        print(Campitch[i],Yaw[i],X[i],Y[i],Z[i])
        cam.attitudeMat(ext.transform())
        P = []
        P.append(cam.reprojectToPlane(np.array([0,0])))
        P.append(cam.reprojectToPlane(np.array([639,0])))
        P.append(cam.reprojectToPlane(np.array([639,511])))
        P.append(cam.reprojectToPlane(np.array([0,511])))
        P.append(cam.reprojectToPlane(np.array([0,0])))

    all_polygons = unary_union(poly)

    ei =extract_poly_coords(all_polygons)
    intc = np.array([[i[0],i[1]] for i in ei["interior_coords"]])
    if len(intc)>0:
        inp = Polygon(intc)
        area = all_polygons.area - inp.area
    else:
        area = all_polygons.area
        
    print ("Area: {:.2f} ha".format(area/10000.0) )
    print ("Images:", len(X))
            