from __future__ import print_function

import gpstime
import configparser
import traceback
import os
NO_COMPENSATION = 1
PITCH = 2
PITCH_AND_ROLL = 3
ROLL = 4


class Meta(object):
    def __init__(self):
        self.cfg = configparser.SafeConfigParser()
        self.txtfile = None
        self.compensation = PITCH_AND_ROLL
    def set_ircam_deviations(self,campitch,camroll,camyaw=0):
        '''
        all angles are in degree. Directions: 
        pitch: in flight direction is 0 deg, nadir is 90 deg
        roll: to the right is 0 deg, nadir is 90 deg
        yaw: north is 0 deg, east is 90 deg
        '''
        self.cfg.set("ACCURACY","ircam-pitch-deviation",str(campitch) + " d")
        self.cfg.set("ACCURACY","ircam-roll-deviation",str(camroll) + " d")
        self.cfg.set("ACCURACY","ircam-yaw-deviation",str(camyaw) + " d")
        
    def from_flirsd(self,header):
        if not self.cfg.has_section("GENERAL"):
            self.cfg.add_section("GENERAL")
        self.cfg.set("GENERAL", "metaversion", "4.1")
        
        if not self.cfg.has_section("CAMERA"):
            self.cfg.add_section("CAMERA")
        self.cfg.set("CAMERA", "serial", str(header["camera"]["sernum"]))
        self.cfg.set("CAMERA", "sernum_sensor", str(header["camera"]["sernum_sensor"]))
        self.cfg.set("CAMERA", "version", str(header["camera"]["version"]))
        self.cfg.set("CAMERA", "fw_version", str(header["camera"]["fw_version"]))
        self.cfg.set("CAMERA", "sensortemperature", str(header["camera"]["sensortemperature"]))
        self.cfg.set("CAMERA", "partnum", header["camera"]["partnum"].strip('\x00'))
        
        if not self.cfg.has_section("TIME"):
            self.cfg.add_section("TIME")
        self.cfg.set("TIME", "system-up-time", "%.2f s" % (header["falcon"]["time_ms"]/1000.0) )
        utc = gpstime.UTCFromGps(header["falcon"]["gps_week"],header["falcon"]["gps_time_ms"]/1000)
        self.cfg.set("TIME", "gps-date", "%04d-%02d-%02d"%(utc[0],utc[1],utc[2]) )
        self.cfg.set("TIME", "gps-utc-time", "%02d:%02d:%02d"%(utc[3],utc[4],int(utc[5])) )
        
        if not self.cfg.has_section("ACCURACY"):
            self.cfg.add_section("ACCURACY")
        self.cfg.set("ACCURACY","speed_x",str(header["falcon"]["gps_speed_x"]/(10.0**3)) + " m/s")
        self.cfg.set("ACCURACY","speed_y",str(header["falcon"]["gps_speed_y"]/(10.0**3)) + " m/s")
        self.cfg.set("ACCURACY","speed_accuracy",str(header["falcon"]["gps_speed_accuracy"]/(10.0**3)) + " m/s")
        self.cfg.set("ACCURACY","horizontal_accuracy",str(header["falcon"]["gps_hor_accuracy"]/(10.0**3)) + " m")
        self.cfg.set("ACCURACY","vertical_accuracy",str(header["falcon"]["gps_vert_accuracy"]/(10.0**3)) + " m")
        
        
        if not self.cfg.has_section("CURRENT_LOCATION"):
            self.cfg.add_section("CURRENT_LOCATION")
        latlon = "%.7f,%.7f" % (header["falcon"]["gps_lat"]/(10.0**7),header["falcon"]["gps_long"]/(10.0**7))
        self.cfg.set("CURRENT_LOCATION", "latlon", latlon)
        #self.cfg.set("CURRENT_LOCATION", "gps-height", str(header["falcon"]["gps_height"]/(10.0**3)) + " m" )
        self.cfg.set("CURRENT_LOCATION", "camera-pitch-angle", str(header["falcon"]["cam_angle_pitch"]/(10.0**2)) + " d" )
        self.cfg.set("CURRENT_LOCATION", "camera-roll-angle", str(header["falcon"]["cam_angle_roll"]/(10.0**2)) + " d" )
        self.cfg.set("CURRENT_LOCATION", "camera-yaw-angle", str(header["falcon"]["cam_angle_yaw"]/(10.0**2)) + " d" )
        self.cfg.set("CURRENT_LOCATION", "heading", str(header["falcon"]["angle_yaw"]/(10.0**2)) + " d" )
        
        self.cfg.set("CURRENT_LOCATION", "pitch", str(header["falcon"]["angle_pitch"]/(10.0**2)) + " d" )
        self.cfg.set("CURRENT_LOCATION", "roll", str(header["falcon"]["angle_roll"]/(10.0**2)) + " d" )
        
        self.cfg.set("CURRENT_LOCATION", "pressure-height", str(header["falcon"]["baro_height"]/(10.0**3)) + " m" )
        if not self.cfg.has_section("LOCATION AT START"):
            self.cfg.add_section("LOCATION AT START")
        ll_start = "%.7f,%.7f" % (header["startup_gps"]["lat"]/10.0**7,header["startup_gps"]["long"]/10.0**7)
        self.cfg.set("LOCATION AT START", "latlon", ll_start )
        self.cfg.set("LOCATION AT START", "gps-height", str(header["startup_gps"]["height"]/(10.0**3)) + " m" )
        
        if not self.cfg.has_section("ACCURACY AT START"):
            self.cfg.add_section("ACCURACY AT START")
        self.cfg.set("ACCURACY AT START","speed_x",str(header["startup_gps"]["speed_x"]/(10.0**3)) + " m/s")
        self.cfg.set("ACCURACY AT START","speed_y",str(header["startup_gps"]["speed_y"]/(10.0**3)) + " m/s")
        self.cfg.set("ACCURACY AT START","speed_accuracy",str(header["startup_gps"]["speed_accuracy"]/(10.0**3)) + " m/s")
        self.cfg.set("ACCURACY AT START","horizontal_accuracy",str(header["startup_gps"]["hor_accuracy"]/(10.0**3)) + " m")
        self.cfg.set("ACCURACY AT START","vertical_accuracy",str(header["startup_gps"]["vert_accuracy"]/(10.0**3)) + " m")
        
    def update(self, section, key, value): 
        if not self.cfg.has_section(section):
            self.cfg.add_section(section)
        self.cfg.set(section, key, value)
        return self.cfg
        
    def save(self,txtfile):
        self.txtfile = txtfile
        with open(txtfile, 'wb') as cfgfile:
            self.cfg.write(cfgfile)

    def load(self,txtfile):
        self.txtfile = txtfile
        try:
            self.cfg.read(txtfile)
        except:
            print(traceback.format_exc())
        
    def get(self,section,option,type="str",trim=None,returnvalue=None):
        if self.cfg.has_option(section,option):
            if type=="int":
                return int(self.cfg.get(section,option)[:trim])
            if type=="float":
                return float(self.cfg.get(section,option)[:trim])
            if type=="bool":
                return bool(self.cfg.get(section,option)[:trim])
            if type=="str":
                return self.cfg.get(section,option)[:trim]
        else:
            return returnvalue    
    
    def load_poi_points(self):
        dict_string = self.get("POI", "points")
        if dict_string == None:
            return list()
        
        points_list = eval(dict_string)
        if len(points_list)>0: 
            if points_list[0].get("pos"):
                return points_list
        else:
            return list()
    
    def load_pois(self):
        poilist = []
        pointss = self.get("POI", "points")
        if pointss == None: return list()
        points_list = eval(pointss)
        featuress = self.get("POI", "features")
        if featuress:
            features_list = eval(featuress)
        else:
            features_list = []
        if len(points_list)>0: 
            if points_list[0].get("pos"):
                for i in points_list:
                    poi = {"poi":i}
                    if len(features_list)>0:
                        try:
                            poi["features"] = next((item for item in features_list if item.get("pos",(-1,-1)) == i.get("pos",(-2,-2))))
                        except:
                            print("stop iteration-Exception")
                            #print poi
                    campitch = self.get('CURRENT_LOCATION', 'camera-pitch-angle',"float",-2,0.0)
                    camroll = self.get('CURRENT_LOCATION', 'camera-roll-angle',"float",-2,0.0)
                    pitch = self.get('CURRENT_LOCATION', 'pitch',"float",-2,0.0)
                    roll = self.get('CURRENT_LOCATION', 'roll',"float",-2,0.0)
                    yaw = self.get('CURRENT_LOCATION', 'heading',"float",-2,0.0)
                    dpitch = self.get('ACCURACY', "ircam-pitch-deviation","float",-2,0.0)
                    droll = self.get('ACCURACY', "ircam-roll-deviation","float",-2,0.0)
                    dyaw = self.get('ACCURACY', "ircam-yaw-deviation","float",-2,0.0)
                    base,ext = os.path.splitext(self.txtfile)
                    
                    if self.compensation == PITCH_AND_ROLL:
                        poi["outer_orientation"] = {"pitch":campitch + dpitch, "roll":0.0 + droll ,"yaw":yaw + dyaw,"type":"pitchrollcomp"}
                    elif self.compensation == NO_COMPENSATION:
                        poi["outer_orientation"] = {"pitch":campitch + pitch + dpitch, "roll":roll + droll ,"yaw":yaw + dyaw,"type":"nocomp"}
                    elif self.compensation == PITCH:
                        poi["outer_orientation"] = {"pitch":campitch + dpitch, "roll":roll + droll ,"yaw":yaw + dyaw,"type":"pitchcomp"}
                    elif self.compensation == ROLL:
                        poi["outer_orientation"] = {"pitch":campitch + pitch + dpitch, "roll":droll ,"yaw":yaw + dyaw,"type":"pitchcomp"}
                    poi["meta"] = {"image":base+".jpg", "time":self.get('TIME', 'gps-utc-time'),"date": self.get('TIME', 'gps-date') ,\
                                "latlon":self.get('CURRENT_LOCATION', 'latlon'),"baro_height":self.get('CURRENT_LOCATION', 'pressure-height',"float",-2,0.0),\
                                "start_latlon":self.get('LOCATION AT START', 'latlon'),"start_gps_height":self.get('LOCATION AT START', 'gps-height',"float",-2)}
                    poilist.append(poi)
                return poilist
        else:
            return list()
            
    
    def to_dict(self):
        meta = {}
        meta["txt_path"] = self.txtfile
        if self.txtfile: 
            meta["img_path"] = self.txtfile[:-4]+".jpg"
            meta["basepath"] , meta["img_filename"] = os.path.split(meta["img_path"])
        meta["gps-date"] = self.get('TIME', 'gps-date')
        meta["gps-utc-time"] = self.get('TIME', 'gps-utc-time')
        meta["system-up-time"] = self.get('TIME', 'system-up-time',"str",-2)
        meta["camera"] = self.get('CAMERA', 'camera')
        meta["device"] = self.get('CAMERA', 'device')
        meta["cam-type"] = self.get('CAMERA', 'type')
        meta["cam_owner"] = self.get('CAMERA', 'owner')
        meta["height"] = self.get('CURRENT_LOCATION', 'pressure-height',"float",-2)
        meta["latlon"] = self.get('CURRENT_LOCATION', 'latlon')
        if meta["latlon"]:
            (lat,lon) = meta["latlon"].split(",")
            meta["lat"]= float(lat)
            meta["lon"]= float(lon)
        meta["cam-angle"] = self.get('CURRENT_LOCATION', 'camera-pitch-angle',"float",-2)
        meta["pitch"] = self.get('CURRENT_LOCATION', 'pitch',"float",-2)
        meta["roll"] = self.get('CURRENT_LOCATION', 'roll',"float",-2)
        meta["heading"] = self.get('CURRENT_LOCATION', 'heading',"float",-2)
        meta["gps-height"] = self.get('CURRENT_LOCATION', 'gps-height',"float",-2)
        meta["metaversion"] = self.get('GENERAL', 'metaversion',"float")
        meta["software-comments"] = self.get('GENERAL', 'software-comments')
        meta["start_height"] = self.get('LOCATION AT START', 'pressure-height',"float",-2)
        meta["start_latlon"] = self.get('LOCATION AT START', 'latlon')
        if meta["start_latlon"]:
            (lat,lon) = meta["start_latlon"].split(",")
            meta["start_lat"]= float(lat)
            meta["start_lon"]= float(lon)
        meta["start_gps-height"] = self.get('LOCATION AT START', 'gps-height',"float",-2)
        meta["start_heading"] = self.get('LOCATION AT START', 'heading',"float",-2)
        meta["resolution"] = self.get('FRAMEGRABBER', 'resolution')
        meta["payload-version"] = self.get('SYSTEM', 'payload-version')
        meta["software-version"] = self.get('SYSTEM', 'software-version')
        meta["nbr_of_satellites"] = self.get('ACCURACY', 'nbr_of_satellites',"int")
        meta["speed_x"] = self.get('ACCURACY', 'speed_x',"float",-4)
        meta["speed_y"] = self.get('ACCURACY', 'speed_y',"float",-4)
        meta["speed_accuracy"] = self.get('ACCURACY', 'speed_accuracy',"float",-4)
        meta["vertical_accuracy"] = self.get('ACCURACY', 'vertical_accuracy',"float",-2)
        meta["horizontal_accuracy"] = self.get('ACCURACY', 'horizontal_accuracy',"float",-2)
        meta["start_nbr_of_satellites"] = self.get('ACCURACY AT START', 'nbr_of_satellites',"int")
        meta["start_vertical_accuracy"] = self.get('ACCURACY AT START', 'vertical_accuracy',"float",-2)
        meta["start_horizontal_accuracy"] = self.get('ACCURACY AT START', 'horizontal_accuracy',"float",-2)
        meta["prooved"] = self.get( "POI", "prooved")
        meta["poitype"] = self.get('POI','type')
        meta["points"] = self.load_poi_points()
        meta["pois"] = self.load_pois()
        meta["uav_owner"] = self.get('UAV', 'owner')
        meta["uav_logfile"] = self.get('UAV', 'logfile')
        meta["uav_type"] = self.get('UAV', 'type')
        meta["sensor_temp"] = self.get('CAMERA', 'sensortemperature')
        
        return meta        
 
