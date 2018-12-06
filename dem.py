from PyQt5 import QtCore,QtGui,uic
import numpy as np
import utm
import gdal
import os
import traceback

class Dem(QtGui.QWidget):
    delta_x = 0.0008333333333333334
    delta_y = -0.0008333333333333334
    rotation_x = 0
    rotation_y = 0
    nodata = -9999
    srs_wkt = "EPSG:4326"
    filename = None
    dem = None
    
    log = QtCore.pyqtSignal(str)
    
    def __init__(self):
        QtGui.QWidget.__init__(self)
        uic.loadUi('ui/dem.ui',self)
        self.openFile.clicked.connect(self.load_file)
        self.ladenButton.clicked.connect(lambda: self.load_geotif(str(self.filename.text())))
        
    def load_file(self):
        filename = QtGui.QFileDialog.getOpenFileName(None, 'Load File')
        self.filename.setText(filename)
        self.fromFile.setChecked(True)
    
    def fill_params(self):
        self.projection_sB.setText(self.srs_wkt)
        self.dx_sB.setValue(self.delta_x)
        self.dy_sB.setValue(self.delta_y)
        self.rot_x_sB.setValue(self.rotation_x)
        self.rot_y_sB.setValue(self.rotation_y)
        self.nodata_sB.setValue(self.nodata)
        self.Nx_sB.setValue(self.Nx)
        self.Ny_sB.setValue(self.Ny)
        
    def load_geotif(self, source):
        try:
            ds = gdal.Open(source, gdal.GA_ReadOnly)
            (self.x_start, self.delta_x, self.rotation_x, self.y_start, self.rotation_y, self.delta_y) = ds.GetGeoTransform()
            self.srs_wkt = ds.GetProjection()
            self.Nx = ds.RasterXSize
            self.Ny = ds.RasterYSize
            self.dem = np.array(ds.GetRasterBand(1).ReadAsArray())
        except:
            raise Exception(traceback.format_exc())
        self.fill_params()
    def save_geotif(self,filename):
        import osr
        Ny, Nx = self.dem.shape
        driver = gdal.GetDriverByName("GTiff")
        ds = driver.Create(filename, Nx, Ny, 1,gdal.GDT_Float32)
        ds.SetGeoTransform([self.x_start, self.delta_x, self.rotation_x, self.y_start, self.rotation_y, self.delta_y])
        srs = osr.SpatialReference()
        srs.SetWellKnownGeogCS( self.WKT );
        ds.SetProjection( srs.ExportToWkt() )
        ds.GetRasterBand(1).WriteArray(self.dem)
        ds = None
    
    def create_empty_raster(self, width, height):
        """
        @param width: amount of pixels or datapoints in x-direction of the whole raster / geotif 
        @param height: amount of datapoints in y-direction
        
        @see Raster.set_params for the rest of the parameters 
        """
       # x_start = int(lon_topleft / (width * self.delta_x)) * width * self.delta_x - self.delta_x
       # y_start = int(lat_topleft / (height * self.delta_y)) * height * self.delta_y - self.delta_y 
       # self.set_params(x_start, self.delta_x, 0, y_start, 0, self.delta_y)
        self.dem = np.empty((width, height,)) 
        self.dem.fill(self.nodata)
    
        
    def fill(self, x, y,ele_array, overwrite = True):
        sh = ele_array.shape
        shd = self.dem.shape
 #       print "sh,shd",sh,shd
        Y2 = y+sh[0] > shd[0] and shd[0] or y+sh[0]
        X2 = x+sh[1] > shd[1] and shd[1] or x+sh[1]
        y2 = int(y+sh[0] > shd[0] and shd[0]-y+1 or sh[0])
        x2 = int(x+sh[1] > shd[1] and shd[1]-x+1 or sh[1])
#        print "x,y,X2,Y2,x2,y2",x,y,X2,Y2,x2,y2
        a = self.dem[y:Y2,x:X2] 
        if overwrite == False:
            self.dem[y:Y2,x:X2]  = np.array([((i == self.nodata) and [ele_array.ravel()[idx]] or [i])[0] 
                for idx,i in enumerate(a.ravel()) ]).reshape(y2,x2)
        else :
            self.dem[y:Y2,x:X2]  = ele_array[:y2,:x2]

            
    def crop_dem(self,lower_y,left_x,upper_y,right_x):
        x = sorted([int((x - self.x_start)/self.delta_x ) for x in (left_y,right_y)] )
        y = sorted([int((y - self.y_start)/self.delta_y ) for y in (upper_x,lower_x)]) 
        self.x_start = x[0]*self.delta_x + self.x_start
        self.y_start = y[0]*self.delta_y + self.y_start
        self.dem = self.dem[y[0]:y[1]+2, x[0]:x[1]+2]
        
    
    