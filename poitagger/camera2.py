from __future__ import print_function
import numpy as np
from .rotation import euler,quaternions
from enum import IntEnum
import traceback

def homo(mat3d):
    mat4d = np.vstack((mat3d,[0,0,0]))
    return np.hstack((mat4d,[[0],[0],[0],[1]]))
    
def invtrans(X,Y,Z):
    return np.array([[1,0,0,X],[0,1,0,Y],[0,0,1,Z],[0,0,0,1]])# inverse Matrix
    
class CamModel(IntEnum):
    NOCAM = 0
    PINHOLE = 1
    BROWN = 2
    LUT = 3

class CoSy(IntEnum):
    UAV = 0
    CAMERA = 1
    SBA = 2
    FALCON8 = 3
    
class Camera(object):
    K = None
    S = np.eye(4)
    def __init__(self,cosy = CoSy.FALCON8):
        '''
        standalone means the camera is not mounted on a uav. 
        the coordinate system is then the camera coordinate system (x points right, y points down on the image and z points to the scene)
        if standalone is false we assume that the camera is mounted on a uav
        and the coordinate system is the uav-coordinate system (the geocoordinate system / left handed, see pose for more details)
        '''
        self.pose(0,0,0,0,0,0)
        
        self.boresight(0,0,0,0,0,0)
            
        if cosy == CoSy.CAMERA:
            cosymat = np.eye(4)
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

        elif cosy == CoSy.UAV:
        #''' 
        #    same cosytransform as falcon8
        #'''
            self.cosymat = np.array([[0,1,0,0],[0,0,-1,0],[1,0,0,0],[0,0,0,1]])
        
        elif cosy == CoSy.SBA:
            pass
            # to be done!!!
            #self.boresight(-90,0,90,0,0,0)
        self.distortionmodel = CamModel.NOCAM
        
        
#
# ROTATION STUFF 
# 
    def pose(self,roll=0,pitch=0,yaw=0,X=0,Y=0,Z=0): 
        '''
        roll: Fluglage um die X-Achse (pos. Richtung: linke Handregel, weil Linkssystem) in degree (0-360) im World-KoSy
        pitch: Fluglage um die Y-Achse (pos. Richtung: linke Handregel, weil Linkssystem) in degree 
        yaw: Fluglage um die Z-Achse/Kompass (pos. Richtung: im Uhrzeigersinn,weil Linkssystem ) in degree
        X: UTM-Hochachse, in m
        Y: UTM-Rechtsachse, in m
        Z: positive Elevation, in m 
        '''
        self.R_uav = homo(euler.ZYXdeg(yaw,pitch,roll).T) # transponierte Matrix, weil das Koordinatensystem gedreht wird, nicht der Vektor (passive Rotation)
        self.Ri_uav = self.R_uav.T # inverse Matrix
        self.T_uav = np.array([[1,0,0,-X],[0,1,0,-Y],[0,0,1,-Z],[0,0,0,1]])
        self.Ti_uav = invtrans(X,Y,Z)
        
    def gimbal(self,roll=0,pitch=0,yaw=0,dx=0,dy=0,dz=0,dir="ZYX"):
        if dir == "ZXY":
            R = euler.ZXYdeg(yaw,roll,pitch)
        else :    
            R = euler.ZYXdeg(yaw,pitch,roll)
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
        self.R_boresight = homo(euler.ZYXdeg(yaw,pitch,roll).T)
        self.T_boresight = np.array([[1,0,0,-dx],[0,1,0,-dy],[0,0,1,-dz],[0,0,0,1]])
        self.Ri_boresight = self.R_boresight.T
        self.Ti_boresight = invtrans(dx,dy,dz)
        
    def transform(self):
        self.S = self.cosymat.dot(self.R_boresight).dot(self.T_boresight).dot(self.R_gimbal).dot(self.T_gimbal).dot(self.R_uav).dot(self.T_uav)
        self.Si = self.Ti_uav.dot(self.Ri_uav).dot(self.Ti_gimbal).dot(self.Ri_gimbal).dot(self.Ti_boresight).dot(self.Ri_boresight).dot(self.cosymat.T)
        
    def position(self):
        return self.Si.dot(np.array([[0],[0],[0],[1]]))
    
    def visible(self,X):
        if 0<X[0]<self.imgwidth and 0<X[1]<self.imgheight:  
            return True
        else:
            return False
        
#
# PINHOLE
#        
    def intrinsics(self,width,height,fx,cx,cy,ar=1.0,skew=0.0):
        self.fx = fx
        self.ar = ar
        self.fy = ar*fx
        self.cx = cx
        self.cy = cy
        self.skew = skew
        self.K = np.array([[fx,skew,cx,0],[0,self.fy,cy,0],[0,0,1,0],[0,0,0,1]])
        self.P = np.array([[1,0,0,0],[0,1,0,0],[0,0,1,0],[0,0,-1.0/self.fx-1,1]])
        self.Pi = np.array([[1,0,0,0],[0,1,0,0],[0,0,1,0],[0,0,1.0/self.fx+1,1]])
        
        self.imgwidth = width
        self.imgheight = height
        self.distortionmodel = CamModel.PINHOLE if self.distortionmodel == CamModel.NOCAM else self.distortionmodel
    
    def Kinv(self):
        return np.array([[1.0/self.fx,-float(self.skew)/(self.fx*self.fy),
                -(self.cx*self.fy-self.skew*self.cy)/(self.fx*self.fy),0],
                [0,1.0/self.fy,-float(self.cy)/self.fx,0],[0,0,1,0],[0,0,0,1]])    
    
    def project(self,X):
        '''
        projects a world 3d-point on the camera plane
        returns a 2d point on the imageplane
        (except for NOCAM: then its just a 3d-ray )
        '''
        if self.distortionmodel == CamModel.NOCAM:
            x = self.S.dot(X)
            return x 
        if self.distortionmodel == CamModel.PINHOLE:
            #P = self.extrinsics(self.K_cam.dot(self.P_cam),X)#.ravel()
            x = self.P.dot(self.K).dot(self.S).dot(X)
            x_norm = x/x[3]
            return np.array([x_norm[0]/x_norm[2],x_norm[1]/x_norm[2]])
        # if self.distortionmodel == CamModel.PINHOLE:
            # P = np.array([[1,0,0,0],[0,1,0,0],[0,0,1,0],[0,0,-1.0/self.f-1,1]])
            # x = P.dot(self.S).dot(X)
            # x_norm = x/x[3]
            # x_cam = x_norm/x_norm[2]
            # #print "PINHOLE\n x_norm",x_norm
            # return np.array([x_norm[0]/x_norm[2],x_norm[1]/x_norm[2]])
        elif self.distortionmodel == CamModel.BROWN:
            pass
            #return self.brown(self.extrinsics(self.P_cam,X))
        elif self.distortionmodel == CamModel.LUT:
            pass
            # P = self.extrinsics(self.P_cam,X) #.ravel()
            # x,y = P[0]/P[2],P[1]/P[2]
            # out = []
            # for x_,y_ in zip(x,y):
                # out.append(self.inverselut(x_,y_))
            # return np.array(out).T
    
    def reproject(self,X,distance=1):
        '''
        reprojects a pixel to a 3d-ray
        '''
        if self.distortionmodel == CamModel.NOCAM:
           # print "REPRO-NOCAM"
            Xi = self.Si.dot(X)
            return Xi 
        elif self.distortionmodel == CamModel.PINHOLE:
          #  print "REPRO-PINHOLE"
            X3d = np.array([X[0],X[1],np.ones_like(X[0]),np.ones_like(X[0])])
            Xi = self.Si.dot(self.Kinv()).dot(self.Pi).dot(X3d)
          #  print "Xi",Xi
            return Xi/Xi[3]
            #X_i = self.R_cam.T.dot(X_k)+self.T_cam
            #return self.R_uav.T.dot(X_i*distance)+self.T_uav    
        #print "REPRO:",self.distortionmodel
        
    def ray_intersect_plane(self,raypos, raydir, plane, front_only=True):
        """Calculates the intersection point of a ray and a plane.

        :param numpy.array ray: The ray to test for intersection.
        :param numpy.array plane: The ray to test for intersection.
        :param boolean front_only: Specifies if the ray should
        only hit the front of the plane.
        Collisions from the rear of the plane will be
        ignored.

        :return The intersection point, or None
        if the ray is parallel to the plane.
        Returns None if the ray intersects the back
        of the plane and front_only is True.
        """
        """
        Distance to plane is defined as
        t = (pd - p0.n) / rd.n
        where:
        rd is the ray direction
        pd is the point on plane . plane normal
        p0 is the ray position
        n is the plane normal

        if rd.n == 0, the ray is parallel to the
        plane.
        >>> a = np.array([[4.],[0.],[5.]])
        >>> b = np.array([[0.],[2.],[-3.]])
        >>> plane = np.array([0.,0.,1.,0.])
        >>> erg =  ray_intersect_plane(a,b,plane)
        >>> print erg
        [[ 4.        ]
        [ 3.33333333]
        [ 0.        ]]
        
        """
        #print "raypos",raypos
        #print "raydir",raydir
        #print "plane",plane
        p = plane[:3] * plane[3]
        n = plane[:3]
        rd_n = np.dot(raydir.ravel(), n)
        if rd_n == 0.0:
            return np.array([[None],[None],[None]])

        if front_only == True:
            if rd_n >= 0.0:
                return np.array([[None],[None],[None]])

        pd = np.dot(p, n)
        p0_n = np.dot(raypos.ravel(), n)
        t = (pd - p0_n) / rd_n
        return raypos + (raydir * t)

    
    def poi(self,x,y,ele=0):
        if self.distortionmodel == CamModel.NOCAM:
            raise("Error- with NOCAM this method doeas not work!")
        poi_cam = np.array([[x],[y],[1],[1]])
        rp = self.reproject(poi_cam)
        campos = self.position()
        raydir = rp - campos
        #print "campos",campos[0:3]
        #print "raydir",raydir[0:3]
        poi = self.ray_intersect_plane(campos[0:3],raydir[0:3],np.array([0,0,1,ele]))
        return poi
            
#
# BROWN
#
        
    def distortion(self,k1=0.0,k2=0.0,p1=0.0,p2=0.0,k3=0.0):
        self.k1 = k1
        self.k2 = k2
        self.p1 = p1
        self.p2 = p2
        self.k3 = k3
        self.distortionmodel = CamModel.BROWN

    def brown(self,X):
        x,y  =  X[0]/X[2] , X[1]/X[2]
        r = np.sqrt(x*x+y*y)
        a = 1 + self.k1*r*r + self.k2*r*r*r*r + self.k3*r*r*r*r*r*r
        xi = x*a + self.p2*(r*r+2*x*x) + 2*self.p1*x*y
        yi = y*a + self.p1*(r*r+2*y*y) + 2*self.p2*x*y
        u = self.cx + xi*self.fx + yi*self.skew
        v = self.cy + yi*self.fy
        return np.array([u, v])#.ravel()
    
#
# LOOKUPTABLE
#        
    def lookuptable(self,horangles,verangles):
        '''
        horangles and verangles have the size of the Imageplane with the shape (imgwidth,imgheight). 
        The values are tan(deg) to the optical axis at (cx,cy).
        '''
        self.lutX = horangles.T
        self.lutY = verangles.T
        self.distortionmodel = CamModel.LUT
        self.lutXY = np.array(list(zip(self.lutX.ravel(),self.lutY.ravel())))
        
    def inverselut(self,xangle,yangle):
        '''
        is for single xangle and yangle values only (no numpy arrays here)
        '''
        def find_nearest(array,value): return (np.abs(array-value)).argmin()
        #print xangle,yangle,xangle.shape, self.lutX.shape
        xidx = [find_nearest(self.lutX[i],xangle) for i in range(0,self.lutX.shape[0])]
        Xi = np.array(list(zip(list(range(0,self.lutX.shape[0])),xidx)))       
        Ypart = self.lutY[Xi[:,0],Xi[:,1]]
        Ypix = find_nearest(Ypart,yangle) 
        Xpix = Xi[Ypix][1]
        x = self.lutX[Ypix,Xpix-1:Xpix+1] if Xpix > 0 else self.lutX[Ypix,Xpix:Xpix+2] 
        y = self.lutY[Ypix-1:Ypix+1,Xpix] if Ypix > 0 else self.lutY[Ypix:Ypix+2,Xpix] 
        return np.array((Xpix+(xangle-self.lutX[Ypix,Xpix])/(x[1]-x[0]), Ypix+(yangle-self.lutY[Ypix,Xpix])/(y[1]-y[0])))
    
    def inverselut2(self,xangle,yangle):
        '''
        is for single xangle and yangle values only (no numpy arrays here)
        '''
        def find_nearest(array,value): return (np.abs(array-value).sum(axis=1)).argmin()
        idx = find_nearest(self.lutXY,np.array([xangle,yangle]))
        Ypix,Xpix = divmod(idx, self.lutX.shape[1])
        #print "lut_shape",self.lutX.shape,self.lutY.shape
        x = self.lutX[Ypix,Xpix-1:Xpix+1] if Xpix > 0 else self.lutX[Ypix,Xpix:Xpix+2] 
        y = self.lutY[Ypix-1:Ypix+1,Xpix] if Ypix > 0 else self.lutY[Ypix:Ypix+2,Xpix] 
        return np.array((Xpix+(xangle-self.lutX[Ypix,Xpix])/(x[1]-x[0]), Ypix+(yangle-self.lutY[Ypix,Xpix])/(y[1]-y[0])))
    
    def interpolatelut(self,x,y):
        x_a = self.lutX[int(y),int(x)]
        x_b = self.lutX[int(y),int(x)+1]
        x_c = self.lutX[int(y)+1,int(x)]
        x_d = self.lutX[int(y)+1,int(x)+1]
        y_a = self.lutY[int(y),int(x)]
        y_b = self.lutY[int(y),int(x)+1]
        y_c = self.lutY[int(y)+1,int(x)]
        y_d = self.lutY[int(y)+1,int(x)+1]
        xm1 = x_a+ (x_b-x_a)*(x % 1)
        xm2 = x_c+ (x_d-x_c)*(x % 1)
        xerg = xm1 + (xm2-xm1)*(y%1)
        ym1 = y_a+ (y_b-y_a)*(x % 1)
        ym2 = y_c+ (y_d-y_c)*(x % 1)
        yerg = ym1 + (ym2-ym1)*(y%1)
        return xerg,yerg
            
    def homogenize(self,X): #make 4 dimensions (homogeneous coordinates)
        try:
            shp = X.shape
            if X.shape == (3,1):
                hom_X = np.vstack((X,1))
            elif X.shape in [(1,3),(3,)]:
                hom_X = np.hstack((X,1))
            elif X.shape in [(4,1),(1,4),(4,)]:
                hom_X = X
            elif shp[0]== 3:
                e = np.ones(shp[1]).reshape(1,shp[1])
            #    print "multiple shape is 3 ",X.shape
                hom_X = np.vstack((X,e))
            return hom_X
        except:
            print(traceback.print_exc())
            raise Exception
            
    def extrinsics(self,P_intrinsics,X):
        X_h = np.dot(self.P_uav,self.homogenize(X))
        return np.dot(P_intrinsics,self.homogenize(X_h))
            
    def project_alt(self,X):
        '''
        projects a world 3d-point on the camera plane
        returns a 2d point on the imageplane
        (except for NOCAM: then its just a 3d-ray )
        '''
        if self.distortionmodel == CamModel.NOCAM:
            P = self.extrinsics(self.P_cam,X) #.ravel()
            return np.array([P[0]/P[2],P[1]/P[2]])
        if self.distortionmodel == CamModel.PINHOLE:
           # print "PINHOLE"
            P = self.extrinsics(self.K_cam.dot(self.P_cam),X)#.ravel()
           # print "P",P
            return np.array([P[0]/P[2],P[1]/P[2]])
        elif self.distortionmodel == CamModel.BROWN:
            return self.brown(self.extrinsics(self.P_cam,X))
        elif self.distortionmodel == CamModel.LUT:
            P = self.extrinsics(self.P_cam,X) #.ravel()
            x,y = P[0]/P[2],P[1]/P[2]
            out = []
            for x_,y_ in zip(x,y):
                out.append(self.inverselut(x_,y_))
            return np.array(out).T
    
   
    # def reproject(self,X,distance=1):
        # '''
        # reprojects a pixel to a 3d-ray
        # '''
        # if self.distortionmodel == CamModel.NOCAM:
            # X3d = np.array([X[0],X[1],np.ones_like(X[0])])
           # # print "T",self.T_cam
           # # print "dist",distance
           # # print "X3d",X3d
            # X_i = self.R_cam.T.dot(X3d*distance)+self.T_cam
            # return self.R_uav.T.dot(X_i)+self.T_uav
            
        # elif self.distortionmodel == CamModel.PINHOLE:
            # X3d = np.array([X[0],X[1],np.ones_like(X[0])])
            # X_k = self.Kinv().dot(X3d)
            # X_i = self.R_cam.T.dot(X_k)+self.T_cam
            # return self.R_uav.T.dot(X_i*distance)+self.T_uav
            
        # elif self.distortionmodel == CamModel.BROWN:#is currently like pinhole
            # X3d = np.array([X[0],X[1],np.ones_like(X[0])])
            # X_k = self.Kinv().dot(X3d)
            # X_i = self.R_cam.T.dot(X_k)+self.T_cam
            # return self.R_uav.T.dot(X_i*distance)+self.T_uav
            
        # elif self.distortionmodel == CamModel.LUT:
            # try:
                # x,y = self.interpolatelut(X[0],X[1])
            # except:
                # raise Exception("the point (%d,%d) is out of range and not visible"%(X[0],X[1]))
            # X_k = np.array([[x],[y],[1]])
            # X_i = self.R_cam.T.dot(X_k)+self.T_cam
            # return self.R_uav.T.dot(X_i*distance)+self.T_uav
            
if __name__ == "__main__":


    from visual import *
    from rotation import euler,quaternions
    import numpy as np


    ax = arrow(pos=(0,0,0),axis=(0,0,-1),color=(1,0,0))
    ay = arrow(pos=(0,0,0),axis=(1,0,0),color=(0,1,0))
    az = arrow(pos=(0,0,0),axis=(0,1,0),color=(0,0,1))


    for i in range(-5,5):
        for j in range(-5,5):
            sphere(pos=(i,0,j), radius=0.02,color=(0,0,1))
            sphere(pos=(0,i,j), radius=0.02,color=(0,1,0))
        sphere(pos=(i,0,0), radius=0.05)
        sphere(pos=(0,i,0), radius=0.05)
        sphere(pos=(0,0,i), radius=0.05)

    def pt(pos):
        sphere(pos=(pos[1],pos[2],-pos[0]), radius=0.1)
        cylinder(pos=(0,0,0),  axis=(0,0,-pos[0]), radius=0.02,color=(1,0,0))
        cylinder(pos=(0,0,-pos[0]),  axis=(pos[1],0,0), radius=0.02,color=(0,1,0))
        cylinder(pos=(pos[1],0,-pos[0]),  axis=(0,pos[2],0), radius=0.02,color=(0,0,1))
        X3 = np.array(pos).reshape((3,1))
        return np.vstack((X3,1))
        
    def camcosy(pos, xxx_todo_changeme):
        (roll,pitch,yaw) = xxx_todo_changeme
        left = np.array([[0,0,-1],[1,0,0],[0,1,0]])
        #right = np.array([[1,0,0],[0,-1,0],[0,0,-1]])
        R = euler.ZYXdeg(yaw,pitch,roll).T.dot(left)
        Rc = np.array([[0,1,0],[0,0,-1],[1,0,0]]).dot(R)
        #ux = arrow(pos=(pos[1],pos[2],-pos[0]),axis=R[0],color=(1,0,0))
        #uy = arrow(pos=(pos[1],pos[2],-pos[0]),axis=R[1],color=(0,1,0))
        #uz = arrow(pos=(pos[1],pos[2],-pos[0]),axis=R[2],color=(0,0,1))
        cx = arrow(pos=(pos[1],pos[2],-pos[0]),axis=0.5*Rc[0],color=(1,0,0))
        cy = arrow(pos=(pos[1],pos[2],-pos[0]),axis=0.5*Rc[1],color=(0,1,0))
        cz = arrow(pos=(pos[1],pos[2],-pos[0]),axis=0.5*Rc[2],color=(0,0,1))

        
    Xw = pt((1,0.5,0))

    Xw2 = pt((-2,-3,0))
    
    
    #Xw = np.array([1,0.5,0]).reshape((3,1))#World Point (X:Hochachse,Y:Rechtsachse,Z:Elevation nach oben)
    #Xw = np.vstack((Xw,1))#make it homogenious 
    print("Xw",Xw)    
    #Xw2 = np.array([-2,-3,0]).reshape((3,1))#World Point (X:Hochachse,Y:Rechtsachse,Z:Elevation nach oben)
    #Xw2 = np.vstack((Xw2,1))#make it homogenious 
    print("Xw2",Xw2)    
    #cam = Camera(CoSy.UAV)#Camera schaut standardmaessig nach Norden und befindet sich im Ursprung
   # cam.pose(90,90,0,0,0,5)
   # cam.boresight(0,0,0,0,0,0)
    
   # print "uav",np.around(cam.P_uav.dot(Xw).ravel()) # im 3D-Kamerakoordinatensystem( X zeigt Richtung Vorne)
   # proj = np.around(cam.project(Xw).ravel())
   # print "cam ",proj
   # cam.intrinsics(640,512,1160,320,256)
    
    #cam.distortion(0)
    #import pickle
    #lut = pickle.load(open("D:\\WILDRETTER\\tau640_pelz_2014.lut","r"))
    #cam.lookuptable(lut[0],lut[1])
    #print "distmodel",cam.distortionmodel
    #print "Xc",cam.project(Xw)

    print("\nNOCAM-Example")
    cam = Camera(CoSy.UAV)#Camera schaut standardmaessig nach Norden und befindet sich im Ursprung
    #camcosy((1,2,5),(0,90,0))    
    cam.pose(0,90,0,1,2,5)
    cam.boresight(0,0,0,0,0,0) # (z''/yaw,x''/pitch,y''/roll,X,Y,Z) rechtsseitiger drehsinn, aber bezogen auf kamerakoordinaten
    cam.gimbal()
    cam.transform()
   # print "=======Transforms======"
    #print "cosymat",cam.cosymat
    #print "R_bs",  cam.R_boresight
    #print "T_bs",  cam.T_boresight
    #print "R_gi",  cam.R_gimbal
    #print "T_gi",  cam.T_gimbal
    #print "R_uav", cam.R_uav
    #print "T_uav", cam.T_uav
    #print "Ri_uav", cam.Ri_uav
    #print "Ti_uav", cam.Ti_uav
    #print "S", cam.S
    #print "Si", cam.Si
    print("===Cam_position===")
    print(cam.position())
    Xc = cam.project(Xw)
    print("Xc", Xc)
    Xcr = cam.reproject(Xc)
    print("Xcr", Xcr)
    print(Xc[0][0],Xc[1][0])
    #P = cam.poi(Xc[0][0],Xc[1][0],0)
    #print "Poi",P
    
    #cylinder(pos=(2,5,-1),  axis=(10*Xcr[0],10*Xcr[2],10*Xcr[1]), radius=0.02,color=(1,0,0))
        
    
    Xc2 = cam.project(Xw2)
    print("Xc2", Xc2)
    
    #print "ALT:"
    #cam.boresight_alt(0,0,0,0,0,0) # (z''/yaw,x''/pitch,y''/roll,X,Y,Z) rechtsseitiger drehsinn, aber bezogen auf kamerakoordinaten
    #Xc = cam.project_alt(Xw)
   # print "P:",cam.P_cam
    #print "Xc", Xc
    #Xc2 = cam.project_alt(Xw2)
    #print "Xc2", Xc2
    
    
   # Xrepro = cam.reproject(Xc,5)
   # print "Xrepro",Xrepro
    
    print("\nPINHOLE-Example")
    cam = Camera()
    camcosy((1,2,5),(0,90,0))    
    cam.pose(0,90,0,1,2,5)
    cam.boresight(4,10,3,1,0,0)
    cam.intrinsics(640,512,1160,320,256)
    cam.gimbal()
    cam.transform()
    Xc = cam.project(Xw)
    print("Xc",Xc)
    Xrepro = cam.reproject(Xc,5)#,cam.fx)
    print("Xrepro", Xrepro)
    P = cam.poi(Xc[0][0],Xc[1][0],0)
    print("Poi",P)
   
    # print "\nLUT-Example"
    # cam = Camera()
    # cam.pose(0,90,0,0,0,5)
    # cam.boresight(0,0,0,0,0,0)
    # cam.intrinsics(640,512,1160,320,256)
    # cam.lookuptable(lut[0],lut[1])
    # Xc = cam.project(Xw)
    # print "Xc",Xc
    # Xrepro = cam.reproject(Xc,5)#,cam.fx)
    # print "Xrepro", Xrepro
    
    # print "\nBrown-Example"
    # cam = Camera()
    # cam.pose(0,90,0,0,-1,5)
    # cam.boresight(0,0,0,0,0,0)
    # cam.intrinsics(640,512,1160,320,256)
    # cam.distortion(0)
    
    # Xc = cam.project(Xw)
    # print "Xc",Xc
    # Xrepro = cam.reproject(Xc,5)#,cam.fx)
    # print "Xrepro", Xrepro
    
    # print "pos",cam.position()
    
    # print "\nSBA-Camera-Example"
    # cam = Camera(CoSy.SBA)
    # cam.pose(0,0,0,0,0,5)
    # cam.intrinsics(640,512,1160,320,256)
    
    # Xc = cam.project(Xw)
    # print "Xc",Xc
    
    
    # print "\nLUT-Example"
    # cam = Camera()
    # cam.pose(0,0,0,650034,503420,605)
    # cam.boresight(0,90,0,0,0,0)
    # cam.lookuptable(lut[0],lut[1])
    # #Xc = cam.project()
    # print "Xc",Xc
    # Xrepro = cam.reproject(np.array([[320],[256]]))#,cam.fx)
    # print "Xrepro", Xrepro
    # campos = cam.position()
    # print "campos",campos
    # print campos - Xrepro
    
    
 #   print "\nreproject-Test"
 #   cam = Camera()
 #   cam.pose(00,90,90,0,0,70)#-338
 #   cam.boresight(0,0,0,0,0,0)
 #   cam.intrinsics(640,512,1160,320,256)
 #   cam.distortion(0)
    #cam.lookuptable(lut[0],lut[1])
 #   Xrepro = cam.reproject(np.array([[320],[256]]),70)#,cam.fx)
 #   print "Xrepro", Xrepro
 #   Xrepro2 = cam.reproject(np.array([[0],[256]]),70)#,cam.fx)
 #   print "Xrepro2", Xrepro2
 #   Xrepro3 = cam.reproject(np.array([[0],[0]]),70)#,cam.fx)
 #   print "Xrepro3", Xrepro3
    
    