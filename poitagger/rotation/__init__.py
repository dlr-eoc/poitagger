from numpy import sin as s, cos as c, radians, array, around, all
from .euler import *
from .quaternions import *

def XdxYdyZdzDeg(a,b,g,dx,dy,dz):
    Zdeg(g).dot(Ydeg(b).dot(Xdeg(a)))
  

def leftToLeftCoSy(Rotationmatrix):
    return Rotationmatrix.T

def leftToRightCoSy(Rotationmatrix):
    return -Rotationmatrix.T

def rightToLeftCoSy(Rotationmatrix):
    return -Rotationmatrix.T

def rightToRightCoSy(Rotationmatrix):
    return Rotationmatrix.T

def passive(Rotationmatrix):
    '''
    If you want to rotate the coordinate system instead of the point use the tranpose of the rotationmatrix.
    This is called a passive transformation.
    see http://en.wikipedia.org/wiki/Active_and_passive_transformation
    '''
    return Rotationmatrix.T

    
def AThenB(A,B):
    '''
    rotate first with Rotationmatrix A and afterwards with Rotationmatrix B
    returns a Rotationmatrix
    '''
    return B.dot(A)
   
def rotate(R,vec):
    return R.dot(vec)      
