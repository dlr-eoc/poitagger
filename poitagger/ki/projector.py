import .camera2 as camproject
import utm
import numpy as np
from math import sin, cos, sqrt, atan2, radians

print("projector after imports")
def raymarching(pos,vec,ele=0):
        poi = ray_intersect_plane(pos[0:3],vec[0:3],np.array([0,0,1,ele]),True)
        return poi #3D Vector


def ray_intersect_plane(raypos, raydir, plane, front_only=True):
        epsilon=1e-6
        p = plane[:3] * plane[3]
        n = plane[:3]
        rd_n = np.dot(raydir.ravel()[:3], n)
        if abs(rd_n) < epsilon:
            print("length of raydir is 0")
            return np.array([[None],[None],[None]])
        if front_only == True:
            if rd_n >= epsilon:
                print("raydir points away")
                return np.array([[None],[None],[None]])
        pd = np.dot(p, n)
        p0_n = np.dot(raypos.ravel(), n)
        t = (pd - p0_n) / rd_n
        return raypos.ravel() + (raydir.ravel()[:3] * t)


def haversine(lat1, lon1, lat2, lon2):
    # calculates distance between two coordinates in meters
    R = 6373.0 * 1000
    lat1 = radians(lat1)
    lon1 = radians(lon1)
    lat2 = radians(lat2)
    lon2 = radians(lon2)
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = (sin(dlat/2))**2 + cos(lat1) * cos(lat2) * (sin(dlon/2))**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    distance = R * c
    return round(distance, 2)

def reproject(exif_flat, u, v):
    Cam = camproject.Camera()
    Ext = camproject.Extrinsics()
    cam_focal = (exif_flat['cam_focal'] / (12/1000)) # pixel width of 12µm

    Ext.setCameraBoresight(
        droll=exif_flat['boresight_roll'],
        dpitch=exif_flat['boresight_pitch'],
        dyaw=exif_flat['boresight_yaw'],
        order=exif_flat['boresight_order'],
    )
    Ext.setPose(
        X=exif_flat['UTM_X'],
        Y=exif_flat['UTM_Y'],
        Z=exif_flat['uav_ele']
    )
    Ext.setGimbal(
        roll=exif_flat['cam_roll'],
        pitch=exif_flat['cam_pitch'],
        yaw=exif_flat['cam_yaw'],
        order=exif_flat['cam_order'],
        )
    Cam.intrinsics(
        width=exif_flat['im_width'],
        height=exif_flat['im_height'],
        fx=exif_flat['im_fx'],
        cx=exif_flat['im_cx'],
        cy=exif_flat['im_cy'],
        ar=1.0,
        skew=0.0
    )
    Cam.attitudeMat(Ext.transform())
    pixel = np.array([u, v])
    repro = Cam.reproject(pixel)
    campos = Cam.position()
    rd = repro.T - campos.ravel()
    pos = raymarching(campos, rd.reshape(4,1))

    lat, lon = utm.to_latlon(pos[1], pos[0], exif_flat['UTM_ZoneNum'], exif_flat['UTM_ZoneLet'])
    ground_dist = haversine(lat, lon, exif_flat['uav_lat'], exif_flat['uav_lon'])
    tot_dist = round(sqrt(ground_dist**2 + exif_flat['uav_ele']**2), 2)

    repr_dat = dict(
        UTM_X=pos[0],
        UTM_Y=pos[1],
        UTM_ZoneNum=exif_flat['UTM_ZoneNum'],
        UTM_ZoneLet=exif_flat['UTM_ZoneLet'],
        poi_lat=round(lat, 9),
        poi_lon=round(lon, 9),
        uav_lat=exif_flat['uav_lat'],
        uav_lon=exif_flat['uav_lon'],
        ground_dist=round(ground_dist,2),
        total_dist=round(tot_dist,2),
        uav_ele=round(exif_flat['uav_ele'], 2)
    )
    poi = dict(
        reprojection_data = repr_dat
    )
    return poi

if __name__ == "__main__":
    print(reproject("C:/Users/opati/Documents/Bachelor_local/Python/data/calib_flight/700101_000340_5.jpg", 320, 256)) # 3cm off centre