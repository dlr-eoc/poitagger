'''
quaternion.py


Author: 
    Martin Israel <Martin.Israel@dlr.de>

    
This Quaternion-Class is based on a python-translation from the Code here:
http://content.gpwiki.org/OpenGL:Tutorials:Using_Quaternions_to_represent_rotation
with help from this document 
http://didaktik.mathematik.hu-berlin.de/files/2011_quaternionen.pdf
(to understand the mathematics behind all this)
'''
from __future__ import print_function
import numpy as np
import math
TOLERANCE = 0.000001

def normalize(w,x,y,z):
    mag2 = w * w + x * x + y * y + z * z
    if (abs(mag2) > TOLERANCE and abs(mag2 - 1.0) > TOLERANCE):
        mag = math.sqrt(mag2)
        w /= mag
        x /= mag
        y /= mag
        z /= mag
    return w,x,y,z

def fromVector(v):
    q = np.sqrt(1.0 - v[0]*v[0]-v[1]*v[1]-v[2]*v[2]).reshape(v.shape[1],1)#q0
    return np.concatenate((q,v.T), axis=1).T #[q0,q1,q2,q3]

# def normalize(q):
    # TOLERANCE = 0.00001
    # mag2 = q[0] * q[0] + q[1] * q[1] + q[2] * q[2] + q[3] * q[3]
    # if (np.all(np.abs(mag2) > TOLERANCE) and np.all(np.abs(mag2 - 1.0) > TOLERANCE)):
        # mag = np.sqrt(mag2)
        # q[0] /= mag
        # q[1] /= mag
        # q[2] /= mag
        # q[3] /= mag
    # return q
    
def multiplyFast(q1, q2):
    if q1.shape[0]==3:
        q1 = fromVector(q1)
    if q2.shape[0]==3:
        q2 = fromVector(q2)
    t1=(q1[0]+q1[1])*(q2[0]+q2[1]) # q1[0]*q2[0]+q1[1]*q2[0]+q1[0]*q2[1]+q1[1]*q2[1]
    t2=(q1[3]-q1[2])*(q2[2]-q2[3]) # dq0  *q0   + dq1 * q0  + dq0 *q1   + dq1 * q1 
    t3=(q1[1]-q1[0])*(q2[2]+q2[3]) # t8   *t11  + t1  * t11 + t8 * t9   + t1* t9 
    t4=(q1[2]+q1[3])*(q2[1]-q2[0])
    t5=(q1[1]+q1[3])*(q2[1]+q2[2])
    t6=(q1[1]-q1[3])*(q2[1]-q2[2])
    t7=(q1[0]+q1[2])*(q2[0]-q2[3])
    t8=(q1[0]-q1[2])*(q2[0]+q2[3])
    t9=0.5*(t5-t6+t7+t8)
    return np.array([t2 + t9-t5, t1 - t9-t6, -t3 + t9-t8,-t4 + t9-t7])

    
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
    
def ZYXEulerToQuaternions(roll,pitch,yaw): #this rotates actively a vector around the axis Z then Y then X
    r = roll * np.pi/(180 * 2.0)
    p = pitch * np.pi/(180 * 2.0)
    y = yaw * np.pi/(180 * 2.0)
    sinr = np.sin(r);
    sinp = np.sin(p);
    siny = np.sin(y);
    cosr = np.cos(r);
    cosp = np.cos(p);
    cosy = np.cos(y);
    #this is the ZY'X'' Representation
    x = sinr * cosp * cosy - cosr * sinp * siny
    y = cosr * sinp * cosy + sinr * cosp * siny
    z = cosr * cosp * siny - sinr * sinp * cosy
    w = cosr * cosp * cosy + sinr * sinp * siny
    mag2 = w * w + x * x + y * y + z * z
    if (np.abs(mag2) > TOLERANCE and np.abs(mag2 - 1.0) > TOLERANCE):
        mag = np.sqrt(mag2)
        w /= mag
        x /= mag
        y /= mag
        z /= mag
    return  np.array([w,x,y,z])

def fromRotationMatrix(R):
    t1 = 1 + R[0,0] + R[1,1] + R[2,2]
    t2 = 1 + R[0,0] - R[1,1] - R[2,2]
    t3 = 1 + R[1,1] - R[0,0] - R[2,2]
    t4 = 1 + R[2,2] - R[0,0] - R[1,1] 
    lst = [t1,t2,t3,t4]
    if t1 == max(lst) and t1 >= 0:
        w = math.sqrt(t1) / 2.0
        x = (R[2,1] - R[1,2])/( 4.0 *w)
        y = (R[0,2] - R[2,0])/( 4.0 *w)
        z = (R[1,0] - R[0,1])/( 4.0 *w)
    elif t2 == max(lst) and t2 >= 0:
        x = math.sqrt(t2)/ 2.0
        w = (R[2,1]-R[1,2])/(4.0*x)
        y = (R[1,0]+R[0,1])/(4.0*x)
        z = (R[0,2]+R[2,0])/(4.0*x)
    elif t3 == max(lst) and t3 >= 0:
        y = math.sqrt(t3) / 2.0
        w = (R[0,2]-R[2,0])/(4.0*y)
        x = (R[1,0]+R[0,1])/(4.0*y)
        z = (R[2,1]+R[1,2])/(4.0*y)
    elif t4 == max(lst) and t4 >= 0:
        z = math.sqrt(t4) / 2.0 
        w = (R[1,0]-R[0,1])/(4.0*z)
        x = (R[0,2]+R[2,0])/(4.0*z)
        y = (R[2,1]+R[1,2])/(4.0*z)
    else:
        raise Exception("Matrix To Quaternion Transformation failed")
    return np.array([w,x,y,z])    
        
def toRotationMatrix(w,x,y,z):
    """returns the rotation matrix for a 3d-Vektor in euclidean space
    rotated vector[3] = R.dot(vec[3])
    """
    w2 = w * w
    x2 = x * x
    y2 = y * y
    z2 = z * z
    wx = w * x
    wy = w * y
    wz = w * z
    xy = x * y
    xz = x * z
    yz = y * z
    return  np.array([[w2+x2-y2-z2, 2*(xy-wz), 2*(wy+xz)],\
        [2*(xy+wz),w2-x2+y2-z2,2*(yz-wx)],\
        [2*(xz-wy), 2*(wx+yz),w2-x2-y2+z2]])
        
def multiply (q1,q2):
    ''' 
    Multiplying q1 with q2 applies the rotation q2 to q1
    the constructor takes its arguments as (x, y, z, w)
    '''
    return np.array([q1[0] * q2[0] - q1[1] * q2[1] - q1[2] * q2[2] - q1[3] * q2[3],
            q1[0] * q2[1] + q1[1] * q2[0] + q1[2] * q2[3] - q1[3] * q2[2],
                  q1[0] * q2[2] + q1[2] * q2[0] + q1[3] * q2[1] - q1[1] * q2[3],
                  q1[0] * q2[3] + q1[3] * q2[0] + q1[1] * q2[2] - q1[2] * q2[1]])
                  

def conjugate(q):
    return np.array([q[0],-q[1], -q[2], -q[3]])
    
def rotate(quat,vec3d,active = True):
    ''' 
    Multiplying a quaternion q with a vector v applies the q-rotation to v
    '''
    #vn = normalized(vec3d)
    #vq = np.array([0.0,vn[0][0],vn[0][1],vn[0][2]])
    if vec3d.shape in [(3,),(1,3),(3,1)]:
        vq = np.array([0.0,vec3d[0],vec3d[1],vec3d[2]])
    else:
        vq = vec3d
    #if quat.shape in [(3,),(1,3),(3,1)]:
    #    quat = np.array([0.0,quat[0],quat[1],quat[2]])
    #print "vec",vq
    #    quat[0]= -quat[0]
        
    if active:
        resQuat = multiply(vq,conjugate(quat))
        resQuat = multiply(quat,resQuat)
    else:
        resQuat = multiply(vq,quat)
        resQuat = multiply(conjugate(quat),resQuat)
    
    #print "erg",resQuat
    return np.array([resQuat[1], resQuat[2], resQuat[3]])

if __name__=="__main__":
    import rotation
    R = rotation.ZYXdeg(0,-90,90)
    
    print("TEST Quaternions")
    print("R",np.around(R))
    q = fromRotationMatrix(R)
    print("Q",q)
    R1 = toRotationMatrix(*q)
    print("R1",np.around(R1))
    print("rotate Vector")
    v = np.array([0,1,2])
    print("v",v)
    v1 = R.dot(v)
    print("active vector rotation",np.around(v1))
    v2 = R.T.dot(v)
    print("passive rotation, rotates the coordinate system",np.around(v2))
    v3 = v.dot(R)
    print("v dot R",v3)
    print("\nnow with Quaternions")
    v4 = rotate(q,v)
    print("active",v4)
    print("passive",rotate(q,v,False))
    print("\npassive due to transpose Matrix")
    
    q2 = fromRotationMatrix(R.T)
    print("passive R.T",rotate(q2,v)) 
    