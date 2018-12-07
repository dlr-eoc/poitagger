from __future__ import print_function
import numpy as np
import math

def normalized(a, axis=-1, order=2):
    '''
    normalizes a vector/matrix
    usage:
    A = np.random.randn(3,3,3)
    print normalized(A,0)
    print normalized(A,1)
    print normalized(A,2)
    print normalized(np.arange(3)[:,None])
    print normalized(np.arange(3))
    '''
    l2 = np.atleast_1d(np.linalg.norm(a, order))#, axis)
    l2[l2==0] = 1
    return a / np.expand_dims(l2, axis)
    
def rotMat(axis, theta):
    """
    Return the rotation matrix associated with counterclockwise rotation about
    the given axis by theta radians.
    """
    axis = np.asarray(axis)
    theta = np.asarray(theta)
    axis = axis/math.sqrt(np.dot(axis, axis))
    a = math.cos(theta/2)
    b, c, d = -axis*math.sin(theta/2)
    aa, bb, cc, dd = a*a, b*b, c*c, d*d
    bc, ad, ac, ab, bd, cd = b*c, a*d, a*c, a*b, b*d, c*d
    return np.array([[aa+bb-cc-dd, 2*(bc+ad), 2*(bd-ac)],
                     [2*(bc-ad), aa+cc-bb-dd, 2*(cd+ab)],
                     [2*(bd+ac), 2*(cd-ab), aa+dd-bb-cc]])


def toQuaternions(axis,angle):
    vn = normalized(axis)
    angle *= 0.5
    sinAngle = np.sin(angle)
    return np.array([np.cos(angle), vn[0][0] * sinAngle, vn[0][1] * sinAngle, vn[0][2] * sinAngle ])

    
if __name__=="__main__":
    v = [3, 5, 0]
    axis = [4, 4, 1]
    theta = 1.2 

    print(np.dot(rotMat(axis,theta), v)) 
    # [ 2.74911638  4.77180932  1.91629719]