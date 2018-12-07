import numpy as np
import cv2
import traceback
import utils2
import bisect
import math
import logging
from scipy import optimize

def contLen(thresh,dog,c=0):
    ret2,thresh2 = cv2.threshold(dog,thresh,255,cv2.THRESH_BINARY)
    fcont  = cv2.findContours(thresh2, cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
    if len(fcont)== 2:
        cont, hierarchy = fcont
    else:
        _,cont, hierarchy = fcont
    return len(cont)-c

    
class ImgProcModel(object):
    #def __init__(self):
    r_mask_i = 1.5
    r_mask_a = 2.5
    r_minkitz = 0.015
    r_maxkitz = 0.1
            
    def load(self,ara):
        self.pixelseitenlaenge = 17e-6
        self.brennweite = 19e-3
        try:
            self.image = ara.image
            self.rawimage = ara.rawbody
            self.gsd = ara.header["gps"].get("rel_altitude",0)*self.pixelseitenlaenge/self.brennweite if ara.header["gps"].get("rel_altitude",0) > 0 else 0.01
            #self.gsd = ara.header.baro*self.pixelseitenlaenge/self.brennweite if ara.header.baro > 0 else 0.01
            self.height = self.image.shape[0]
            self.width = self.image.shape[1]
            self.params = self.calc_sizeparams(self.gsd,self.r_mask_i,self.r_mask_a,self.r_minkitz,self.r_maxkitz)
        except:
            logging.error("imgproc2 load: load image header failed",exc_info=True)
            
    def setParams(self,r_mask_i,r_mask_a,r_minkitz,r_maxkitz):
        self.r_mask_i = r_mask_i
        self.r_mask_a = r_mask_a
        self.r_minkitz = r_minkitz
        self.r_maxkitz = r_maxkitz
        
    def flir_analog(self,image,percent):
        ma = image.max()
        mi = image.min()
        hist,edges = np.histogram(image,ma-mi)
        h, w = image.shape
        tailreject = w*h/100*percent
        reversed_hist = hist[::-1]
        reversed_edges = edges[::-1]
        tr_ridx = np.argmax(np.cumsum(reversed_hist)>tailreject)
        tr_idx = np.argmax(np.cumsum(hist)>tailreject)
        black = edges[tr_idx]
        white = reversed_edges[tr_ridx]
        compressed = self.image
        compressed[compressed > white] = white
        compressed[compressed < black] = black
        norm = compressed - black
        norm *= 255.0/norm.max()
        return np.array(norm, dtype=np.uint8)
        
    def homogenize(self,image,aperture_x=149,aperture_y=149):
        gaus = cv2.GaussianBlur(image,(aperture_x,aperture_y),0)
        hpf = 16384 - gaus
        mat = hpf.astype("float")/16384
        self.mat = mat
        return np.array(image * mat, dtype=np.uint16)
    
    def eigenimage(self,pos,num=10,backward=True):     
        """
        noch nicht fertig!!!
        """    
        matrix = np.zeros((512,640))
        if backward:
            if pos-num>=0: 
                a = pos-num
                b = pos
            else:
                a = 0
                b = num
        else:
            if pos+num>len(self.aralist):
                b = len(self.aralist)
                a = b-num
            else:
                a = pos
                b = pos + num
        for i in self.aralist[a:b]:
            raw = flirsd.ConvertRaw(i["filename"],np.int16)
            myimg = raw.rawbody.ravel()
            try:
                matrix = np.vstack((matrix, myimg))        
            except:
                matrix = myimg
        else:
            raw = flirsd.ConvertRaw(self.aralist[pos],np.int16)
            myimg = raw.rawbody.ravel()
            matrix = np.vstack((matrix, myimg))        
            
        mean = np.mean(matrix, axis=0).reshape(1,-1)
        img = flirsd.ConvertRaw(Files[pos],np.int16)
        mean.resize((512,640))
        diff = img.rawbody - mean
        return np.array(diff, dtype=np.uint16) 
        
    def differenceOfGaussians(self,lopass=None,hipass=None):
        if not lopass==None:
            self.dog_lp = lopass
        else:
            self.dog_lp = utils2.round_up_to_odd(self.r_minkitz/self.gsd)
        if not hipass==None:
            self.dog_hp = hipass
        else:
            self.dog_hp = utils2.round_up_to_odd(self.r_maxkitz/self.gsd)
        blur1 = np.array(cv2.blur(self.image,(self.dog_lp,self.dog_lp)), dtype=np.float) 
        blur2 = np.array(cv2.blur(self.image,(self.dog_hp,self.dog_hp)), dtype=np.float) 
        self.dog = utils2.normalize(blur1 - blur2)
        self.dog_mean = np.mean(self.dog)
        self.dog_std = np.std(self.dog)
        
    def extractContours(self,thresh=None,fac=None):
        if not thresh == None:
            self.thresh = thresh
        else:
            if not fac == None:
                self.fac = fac
                self.thresh = self.dog_mean + self.dog_std * self.fac
            else:
                self.fac = 5
                thresh1 = self.dog_mean + self.dog_std * 1.0
                thresh2 = self.dog_mean + self.dog_std * 6.0
                out = optimize.bisect(contLen,thresh1,thresh2,args=(self.dog,60),xtol=2,maxiter=16,full_output=True)
                #print out
                self.thresh = out[0]
                #stdval = [5,7,9,12,15,22,30,255]
                #factor = [6,5,4.5,4,3.5,3,2.5,2]
                #idx = bisect.bisect(stdval,self.dog_std)
                #self.fac = factor[idx]
            #self.thresh = self.dog_mean + self.dog_std * self.fac
        
        ret2,thresh2 = cv2.threshold(self.dog,self.thresh,255,cv2.THRESH_BINARY)
        fcont  = cv2.findContours(thresh2, cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
        if len(fcont)== 2:
            self.cont, hierarchy = fcont
        else:
            _,self.cont, hierarchy = fcont
            
   
        
    def calc_sizeparams(self,gsd,mask_i,mask_a,r_min,r_max):
        rmaskA = int(mask_a*r_max/gsd)
        rmaskI = int(mask_i*r_max/gsd)
        A_min = 2*math.pi*(r_min/gsd)**2
        A_max = 2*math.pi*(r_max/gsd)**2
        return (A_min,A_max,rmaskI,rmaskA)
    
    def feature_extract(self,bin_thresh=90,difcol_thresh=0, col_thresh=0):
        A_min,A_max,rmaskI,rmaskA = self.params
        relevantlist = []
        areaoklist = []
        imgblobs = np.zeros((512,640),np.uint8)
        cv2.drawContours(imgblobs,self.cont,-1,255,-1)
        for i,con_item in enumerate(self.cont):
            moments = cv2.moments(con_item)
            if A_min < moments["m00"] < A_max:
                x = moments["m10"]/moments["m00"]
                y = moments["m01"]/moments["m00"]
                area = moments["m00"]
                perimeter = cv2.arcLength(con_item,True)
                circularity = 4*math.pi*area/perimeter**2
                areaoklist.append(i)
                b_x,b_y,b_w,b_h = cv2.boundingRect(con_item)
                #print b_x, b_y, b_w, b_h
                blobraw = self.image[b_y:b_y+b_h,b_x:b_x+b_w]
                blobmask = imgblobs[b_y:b_y+b_h,b_x:b_x+b_w]
                blob = blobraw[blobmask==255]
              #  print "blobraw",blobraw
              #  print "bobmask",blobmask
              #  print "blob",blob
                col_mean = np.mean(blob)
                col_sigma = np.std(blob)
               # print "rawmean",np.mean(self.image),np.std(self.image)
            #    print "mean", col_mean,col_thresh,col_mean > col_thresh
                if col_mean > col_thresh :# and bin_thresh < 230: #fuer kitze bin_thresh auf 110
                   # print "in"
                    imgmask = np.zeros((512,640),np.uint8)
                    cv2.circle(imgmask,(int(x),int(y)),rmaskA,255,-1)
                    cv2.circle(imgmask,(int(x),int(y)),rmaskI,0,-1)
                   # print self.image.shape, imgmask.shape
                    surimg = cv2.bitwise_and(self.image,self.image,mask=imgmask)
                    surcol_mean = np.mean(surimg[surimg>0])
                    surcol_sigma = np.std(surimg)
                    diffcol = col_mean - surcol_mean
                  #  print diffcol
                    if diffcol>difcol_thresh:
                        hu = cv2.HuMoments(moments)
                        relevantlist.append({"idx":i,"x":str(int(x)),"y":str(int(y)),"area":moments["m00"],"circularity":float(circularity),"perimeter":int(perimeter),
                                        "hu0":float(hu[0][0]),"hu1":float(hu[1][0]),"hu2":float(hu[2][0]),"hu3":float(hu[3][0]),"hu4":float(hu[4][0]),"hu5":float(hu[5][0]),"hu6":float(hu[6][0]),
                                        "col_mean":int(col_mean),"col_sigma":int(col_sigma), "surcol_mean":int(surcol_mean),"surcol_sigma":int(surcol_sigma),"diffcol":int(diffcol),"bin_thresh":bin_thresh})
        return relevantlist,areaoklist
     
   
        
    