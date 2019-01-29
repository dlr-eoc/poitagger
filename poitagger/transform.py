from __future__ import print_function
from numpy import sin as s, cos as c, radians, array, around, all
import logging
import numpy as np
from . import utils2
from . import PATHS


#right handed Coordinate Systems
#natural Euler Angles 
def rad(a,b,g,dir):
    if dir=="XYX": return XYXrad(a,b,g)
    elif dir=="XZX": return XZXrad(a,b,g)
    elif dir=="XZX": return XZXrad(a,b,g)
    elif dir=="YXY": return YXYrad(a,b,g)
    elif dir=="ZXZ": return ZXZrad(a,b,g)
    elif dir=="ZYZ": return ZYZrad(a,b,g)
    elif dir=="XYZ": return XYZrad(a,b,g)
    elif dir=="XZY": return XZYrad(a,b,g)
    elif dir=="YXZ": return YXZrad(a,b,g)
    elif dir=="YZX": return YZXrad(a,b,g)
    elif dir=="ZXY": return ZXYrad(a,b,g)
    elif dir=="ZYX": return ZYXrad(a,b,g)

def deg(a,b,g,dir):
    if dir=="XYX": return XYXdeg(a,b,g)
    elif dir=="XZX": return XZXdeg(a,b,g)
    elif dir=="XZX": return XZXdeg(a,b,g)
    elif dir=="YXY": return YXYdeg(a,b,g)
    elif dir=="ZXZ": return ZXZdeg(a,b,g)
    elif dir=="ZYZ": return ZYZdeg(a,b,g)
    elif dir=="XYZ": return XYZdeg(a,b,g)
    elif dir=="XZY": return XZYdeg(a,b,g)
    elif dir=="YXZ": return YXZdeg(a,b,g)
    elif dir=="YZX": return YZXdeg(a,b,g)
    elif dir=="ZXY": return ZXYdeg(a,b,g)
    elif dir=="ZYX": return ZYXdeg(a,b,g)    
    
def XYXrad(a,b,g):
    '''
    This is the rotationmatrix for an active rotation of the vector (or point).
    Angles are in Radians.
    rotates the vector at first with a degrees around the X-axis of the right-handed coordinate system,
    then it rotates with b degrees around the Y-axis and last with g degrees around the X-axis. 
    '''
    return array([[c(b), s(b)*s(g),c(g)*s(b)],
      [s(a)*s(b), c(a)*c(g)-c(b)*s(a)*s(g), -c(a)*s(g)-c(b)*c(g)*s(a)],
      [-c(a)*s(b), c(g)*s(a) + c(a)*c(b)*s(g), c(a)*c(b)*c(g)-s(a)*s(g)]])

def XZXrad(a,b,g):
    return array([[c(b), -c(g)*s(b),s(b)*s(g)],
      [c(a)*s(b), c(a)*c(b)*c(g)-s(a)*s(g), -c(g)*s(a)-c(a)*c(b)*s(g)],
      [s(a)*s(b), c(a)*s(g) + c(b)*c(g)*s(a), c(a)*c(g)-c(b)*s(a)*s(g)]])

def YXYrad(a,b,g):
    return array([[c(a)*c(g)-c(b)*s(a)*s(g), s(a)*s(b), c(a)*s(g)+c(b)*c(g)*s(a)],
      [s(b)*s(g), c(b), -c(g)*s(b)],
      [-c(g)*s(a)-c(a)*c(b)*s(g), c(a)*s(b), c(a)*c(b)*c(g)-s(a)*s(g)]])

def YZYrad(a,b,g):
    return array([[c(a)*c(b)*c(g)-s(a)*s(g), -c(a)*s(b), c(g)*s(a)+c(a)*c(b)*s(g)],
      [c(g)*s(b), c(b), s(b)*s(g)],
      [-c(a)*s(g)-c(b)*c(g)*s(a), s(a)*s(b), c(a)*c(g)-c(b)*s(a)*s(g)]])

def ZXZrad(a,b,g):
    return array([[c(a)*c(g)-c(b)*s(a)*s(g), -c(a)*s(g)-c(b)*c(g)*s(a), s(a)*s(b)],
      [c(g)*s(a)+c(a)*c(b)*s(g), c(a)*c(b)*c(g)-s(a)*s(g), -c(a)*s(b)],
      [s(b)*s(g), c(g)*s(b), c(b)]])

def ZYZrad(a,b,g):
    return array([[c(a)*c(b)*c(g)-s(a)*s(g), -c(g)*s(a)-c(a)*c(b)*s(g), c(a)*s(b)],
      [c(a)*s(g)+c(b)*c(g)*s(a), c(a)*c(g)-c(b)*s(a)*s(g), s(a)*s(b)],
      [-c(g)*s(b), s(b)*s(g), c(b)]])

#Tait-Bryan Angles
def XYZrad(a,b,g):
    return array([[c(b)*c(g), -c(b)*s(g), s(b)],
      [c(a)*s(g)+c(g)*s(a)*s(b), c(a)*c(g)-s(a)*s(b)*s(g), -c(b)*s(a)],
      [s(a)*s(g)-c(a)*c(g)*s(b), c(g)*s(a)+c(a)*s(b)*s(g), c(a)*c(b)]])

def XZYrad(a,b,g):
    return array([[c(b)*c(g), -s(b), c(b)*s(g)],
      [s(a)*s(g)+c(a)*c(g)*s(b), c(a)*c(b), c(a)*s(b)*s(g)-c(g)*s(a)],
      [c(g)*s(a)*s(b)-c(a)*s(g), c(b)*s(a), c(a)*c(g)+s(a)*s(b)*s(g)]])

def YXZrad(a,b,g):
    return array([[c(a)*c(g)+s(a)*s(b)*s(g), c(g)*s(a)*s(b)-c(a)*s(g), c(b)*s(a)],
      [c(b)*s(g), c(b)*c(g), -s(b)],
      [c(a)*s(b)*s(g)-c(g)*s(a), s(a)*s(g)+c(a)*c(g)*s(b), c(a)*c(b)]])

def YZXrad(a,b,g):
    return array([[c(a)*c(b), s(a)*s(g)-c(a)*c(g)*s(b), c(g)*s(a)+c(a)*s(b)*s(g)],
      [s(b), c(b)*c(g), -c(b)*s(g)],
      [-c(b)*s(a), c(a)*s(g)+c(g)*s(a)*s(b), c(a)*c(g)-s(a)*s(b)*s(g)]])

def ZXYrad(a,b,g):
    return array([[c(a)*c(g)-s(a)*s(b)*s(g), -c(b)*s(a), c(a)*s(g)+c(g)*s(a)*s(b)],
      [c(g)*s(a)+c(a)*s(b)*s(g), c(a)*c(b), s(a)*s(g)-c(a)*c(g)*s(b)],
      [-c(b)*s(g), s(b), c(b)*c(g)]])

def ZYXrad(a,b,g): #Standard Aerospace Navigation (yaw,pitch,roll)
    return array([[c(a)*c(b), c(a)*s(b)*s(g)-c(g)*s(a), s(a)*s(g)+c(a)*c(g)*s(b)],
      [c(b)*s(a), c(a)*c(g)+s(a)*s(b)*s(g), c(g)*s(a)*s(b)-c(a)*s(g)],
      [-s(b), c(b)*s(g), c(b)*c(g)]])

def XYXdeg(a,b,g):
    return XYXrad(radians(a),radians(b),radians(g))
def XZXdeg(a,b,g):
    return XZXrad(radians(a),radians(b),radians(g))
def YXYdeg(a,b,g):
    return YXYrad(radians(a),radians(b),radians(g))
def YZYdeg(a,b,g):
    return YZYrad(radians(a),radians(b),radians(g))
def ZXZdeg(a,b,g):
    return ZXZrad(radians(a),radians(b),radians(g))
def ZYZdeg(a,b,g):
    return ZYZrad(radians(a),radians(b),radians(g))
def XYZdeg(a,b,g):
    return XYZrad(radians(a),radians(b),radians(g))
def XZYdeg(a,b,g):
    return XZYrad(radians(a),radians(b),radians(g))
def YXZdeg(a,b,g):
    return YXZrad(radians(a),radians(b),radians(g))
def YZXdeg(a,b,g):
    return YZXrad(radians(a),radians(b),radians(g))
def ZXYdeg(a,b,g):
    return ZXYrad(radians(a),radians(b),radians(g))
def ZYXdeg(a,b,g):
    return ZYXrad(radians(a),radians(b),radians(g))
    
class CoSy(object):
    UAV = 0
    CAMERA = 1
    SBA = 2
    FALCON8 = 3
    FALCON8_TRINITY = 4


def homo(mat3d):
    mat4d = np.vstack((mat3d,[0,0,0]))
    return np.hstack((mat4d,[[0],[0],[0],[1]]))
    
def invtrans(X,Y,Z):
    return np.array([[1,0,0,X],[0,1,0,Y],[0,0,1,Z],[0,0,0,1]])# inverse Matrix
        
class Transform(object):
    def __init__(self, cosy = CoSy.FALCON8):
        self.S = np.eye(4)
        self.pose(0,0,0,0,0,0)
        self.boresight(0,0,0,0,0,0)
        if cosy == CoSy.CAMERA:
            self.cosymat = np.eye(4)
        elif cosy == CoSy.FALCON8:
        #    '''  
        #    z  left handed geo cosy       
        #    / \                    
        #     | _x    transforms to      _z  right handed camera cosy  
        #     | /|                       /|
        #     |/___\y                   /______\ x        
        #          /                   |       /          
        #                             \|/          
        #                               y      
        #    '''
            self.cosymat = np.array([[0,1,0,0],[0,0,-1,0],[1,0,0,0],[0,0,0,1]])
            self.gimbal(dx=0.2,dir="ZXY")
        
        elif cosy == CoSy.FALCON8_TRINITY:
            # the difference to FALCON8 is that they use now right sided coordinate system for the UAV Frame
            self.cosymat = np.array([[0,1,0,0],[0,0,-1,0],[1,0,0,0],[0,0,0,1]])
            self.gimbal(dx=0.2,dir="ZXY")

        elif cosy == CoSy.UAV:
        #''' 
        #    same cosytransform as falcon8
        #'''
            self.cosymat = np.array([[0,1,0,0],[0,0,-1,0],[1,0,0,0],[0,0,0,1]])
        
        elif cosy == CoSy.SBA:
            pass
            # to be done!!!
            #self.boresight(-90,0,90,0,0,0)
            
    def pose(self,roll=0,pitch=0,yaw=0,X=0,Y=0,Z=0,leftcosy=False): 
        '''
        roll: Fluglage um die X-Achse (pos. Richtung: linke Handregel, weil Linkssystem) in degree (0-360) im World-KoSy
        pitch: Fluglage um die Y-Achse (pos. Richtung: linke Handregel, weil Linkssystem) in degree 
        yaw: Fluglage um die Z-Achse/Kompass (pos. Richtung: im Uhrzeigersinn,weil Linkssystem ) in degree
        X: UTM-Hochachse, in m
        Y: UTM-Rechtsachse, in m
        Z: positive Elevation, in m 
        '''
        if not leftcosy:
            self.R_uav = -homo(ZYXdeg(yaw,pitch,roll).T)
        else:
            self.R_uav = homo(ZYXdeg(yaw,pitch,roll).T) # transponierte Matrix, weil das Koordinatensystem gedreht wird, nicht der Vektor (passive Rotation)
        self.Ri_uav = self.R_uav.T # inverse Matrix
        self.T_uav = np.array([[1,0,0,-X],[0,1,0,-Y],[0,0,1,-Z],[0,0,0,1]])
        self.Ti_uav = invtrans(X,Y,Z)
        
    def gimbal(self,roll=0,pitch=0,yaw=0,dx=0,dy=0,dz=0,dir="ZYX",sameCoSyAsUav=True):
        if dir == "ZXY":
            R = ZXYdeg(yaw,roll,pitch)
        elif dir == "ZYX" :    
            R = ZYXdeg(yaw,pitch,roll)
        elif dir == "XYZ":
            R = XYZdeg(roll,pitch,yaw)
        elif dir == "XZY":
            R = XZYdeg(roll,yaw,pitch)
        elif dir == "YXZ":
            R = YXZdeg(pitch,roll,yaw)
        elif dir == "YZX":
            R = YZXdeg(pitch,yaw,roll)
        if not sameCoSyAsUav:
            self.R_gimbal = -homo(R.T)
        else:
            self.R_gimbal = homo(R.T)
        self.T_gimbal = np.array([[1,0,0,-dx],[0,1,0,-dy],[0,0,1,-dz],[0,0,0,1]])
        self.Ri_gimbal = self.R_gimbal.T
        self.Ti_gimbal = invtrans(dx,dy,dz)
               
    
    def boresight(self,yaw=0,pitch=0,roll=0,dx=0,dy=0,dz=0):
        '''
        roll: Einbaulage der Kamera (Linkssystem) in degree bezogen auf das UAV-Koordinatensystem
        pitch: variabler Kamerapitchwinkel (Linkssystem) in degree
        yaw: Einbaulage der Kamera (Linkssystem) in degree
        X: Abstand Payloadpitchdrehachse von IMU in Richtung Flugspitze in m
        Y: Abstand Payloadrolldrehachse von IMU Richtung Rechts in m
        Z: Abstand Payloadroll- und pitchdrehachse von IMU Richtung Oben  in m
        Die Abstaende sind keine Abstaende zur jeweiligen Achse sondern sind Abstaende vom Zentrum des UAV.
        
        
        the cam coordinate system is as follows:
        z points to the scene
        x points right
        y points down
        '''
        self.R_boresight = homo(ZYXdeg(yaw,pitch,roll).T)
        self.T_boresight = np.array([[1,0,0,-dx],[0,1,0,-dy],[0,0,1,-dz],[0,0,0,1]])
        self.Ri_boresight = self.R_boresight.T
        self.Ti_boresight = invtrans(dx,dy,dz)
        
    def transform(self):
        self.S = self.cosymat.dot(self.R_boresight).dot(self.T_boresight).dot(self.R_gimbal).dot(self.T_gimbal).dot(self.R_uav).dot(self.T_uav)
        self.Si = self.Ti_uav.dot(self.Ri_uav).dot(self.Ti_gimbal).dot(self.Ri_gimbal).dot(self.Ti_boresight).dot(self.Ri_boresight).dot(self.cosymat.T)
        
    def attitudeMat(self):
        return self.S