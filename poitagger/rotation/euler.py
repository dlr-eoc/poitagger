from __future__ import print_function
from numpy import sin as s, cos as c, radians, array, around, all

#right handed Coordinate Systems
#natural Euler Angles 
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
    
def Xrad(a):
    return array([[1,0,0],[0,c(a),-s(a)],[0,s(a),c(a)]])
def Yrad(a):
    return array([[c(a),0,-s(a)],[0,1,0],[s(a),0,c(a)]])
def Zrad(a):
    return array([[c(a),-s(a),0],[s(a),c(a),0],[0,0,1]])
    
def Xdeg(a):
    return Xrad(radians(a))
def Ydeg(a):
    return Yrad(radians(a))
def Zdeg(a):
    return Zrad(radians(a))

def aerospace(roll,pitch,yaw):
    return ZYXdeg(yaw,pitch,roll).T

def toAxisAngle(RotMat):
    pass
    
def toQuaternions(RotMat):
    pass
if __name__=="__main__":
    
    print("EXAMPLES:\n")
    vec = array([[0], [1], [2]])
    
    print("rotate the coordinate system around the vec",vec,"with 90deg yaw then 20deg roll:", aerospace(20,0,90).dot(vec)) 
    
    #geodetic left handed cosy to a right handed cosy, where the new z points in the direction of the old x, the new x points to the old y and the new y points down to the old -z
    #we have to rotate and transpose the rotationmatrix to do that correctly.
    print("from geodetic to camera cosy:",around(-XYZdeg(90,-90,0).T.dot(vec)),"should be: [1,-2,0]^T") 
    print("from geodetic to camera cosy (other transform):",around(-ZYXdeg(-90,0,90).T.dot(vec)),"should be: [1,-2,0]^T") 
    
    print("from left to left cosy:",  around(XYZdeg(90,90,0).T.dot(vec)),"should be: [1,2,0]^T")
    print("from right to right cosy:",around(XYZdeg(90,90,0).T.dot(vec)),"should be: [1,2,0]^T")
    print("from right to left cosy:",around(-XYZdeg(90,90,0).T.dot(vec)),"should be: [-1,-2,0]^T")
    print("from left to right cosy:",around(-XYZdeg(90,90,0).T.dot(vec)),"should be: [-1,-2,0]^T")
    
    print("XYZ(90,90,90):",around(XYZdeg(90,90,90).T.dot(vec)),"should be: [2,-1,0]^T")
    print("Z(90):",around(Zdeg(90).T.dot(vec)),"should be: [1,0,2]^T")
    print("X90,Y90,Z90:",around(Zdeg(90).dot(Ydeg(90).dot(Xdeg(90))).T.dot(vec)),"should be: [2,-1,0]^T")
    
    print("X90,Y90,Z90:",around(Zdeg(90).dot(Ydeg(90).dot(Xdeg(90))).T.dot(vec)),"should be: [2,-1,0]^T")
        