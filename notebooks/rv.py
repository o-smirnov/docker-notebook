import os,time,math,astropy,pyfits,traceback,fnmatch
from pandas import DataFrame,Series
import IPython.display 
import matplotlib.pyplot as plt

ROOTDIR = "";

DPI = 80

class DataFileBase (object):
  def __init__ (self,path,root=""):
    self.fullpath = path
    if root and path.startswith(root):
      path = path[len(root):]
      if path.startswith("/"):
        path = path[1:];
    self.path = path
    self.name = os.path.basename(path)
    self.basename, self.ext = os.path.splitext(self.name)
    self.size = os.path.getsize(self.fullpath)
    self.mtime = os.path.getmtime(self.fullpath)
    self.mtime_str = time.ctime(self.mtime) 

  def __str__ (self):
    return self.path

  def _repr_html_ (self):
    return self.show() or self.path

  def show (self,**kw):
    print self.path

class FITSFile (DataFileBase):

  FITSAxisLabels = dict(
    STOKES = [ "I","Q","U","V","YX","XY","YY","XX","LR","RL","LL","RR"  ],
    COMPLEX = [ "real","imag","weight" ]
  )

  def __init__ (self,*args,**kw):
    DataFileBase.__init__(self,*args,**kw)
    self._ff = self._image_data = None

  def open (self):
    if not self._ff:
      self._ff = pyfits.open(self.fullpath)
    return self._ff

  def info (self):
    hdr = self.open()[0].header
    sizes = [ str(hdr["NAXIS%d"%i]) for i in range(1,hdr["NAXIS"]+1) ]
    axes = [ hdr.get("CTYPE%d"%i,str(i)) for i in range(1,hdr["NAXIS"]+1) ]
    print self.path,"x".join(sizes),",".join(axes)

  @staticmethod 
  def _show_thumbs (fits_files,width=None,ncol=None,maxwidth=16,maxcol=4,**kw):
    if not fits_files:
      return None
    nrow = int(math.ceil(len(fits_files)/float(ncol or maxcol)))
    ncol = ncol or min(len(fits_files),maxcol)
    width = width or maxwidth/float(ncol)
    fig = plt.figure(figsize=(width*ncol,width*nrow),dpi=DPI)
    for iplot,ff in enumerate(fits_files):
      plt.subplot(nrow,ncol,iplot+1);
      ff.show(index=[0]*10,unroll=None,colorbar=False,filename_in_title=True,make_figure=False,fs_title='small',**kw)

  def show (self,index=0,xyaxes=(0,1),unroll='STOKES',vmin=None,vmax=None,zoom=None,
            width=None,maxwidth=16,ncol=None,maxcol=4,
            fs_title='medium',colorbar=True,
            make_figure=True,
            filename_in_title=False):
    ff = pyfits.open(self.fullpath)
    hdr = ff[0].header
    # make base slice with ":" for every axis
    naxis = hdr['NAXIS'];
    dims  = [ hdr['NAXIS%d'%i] for i in range(1,naxis+1) ]
    axis_type = [ hdr.get("CTYPE%d"%i,str(i)) for i in range(1,hdr["NAXIS"]+1) ]
    baseslice = [slice(None)]*hdr['NAXIS']
    # create status string
    status = "%s (%s,%s)"%(self.path,axis_type[xyaxes[0]].split("-")[0],axis_type[xyaxes[1]].split("-")[0]);
    title = self.basename if filename_in_title else "";
    # zoom in if asked
    if zoom:
      x0, y0 = int(dims[xyaxes[0]]/2), int(dims[xyaxes[1]]/2)
      xz, yz = int(dims[xyaxes[0]]/(zoom*2)), int(dims[xyaxes[1]]/(zoom*2))
      baseslice[xyaxes[0]] = slice(x0-xz,x0+xz)
      baseslice[xyaxes[1]] = slice(y0-yz,y0+yz)
      status += " zoom x%s"%zoom;
    # this is the set of axes that we need to index into -- remove the XY axes first
    remaining_axes = set(range(naxis)) - set(xyaxes)
    # get axis labels ("1" to "N", unless a special axis like STOKES is used)
    axis_labels = {}
    for ax in remaining_axes:
      labels = self.FITSAxisLabels.get(axis_type[ax],None)
      rval,rpix,delt,unit =  [ hdr.get("C%s%d"%(kw,ax+1),1) for kw in "RVAL","RPIX","DELT","UNIT" ]
      if labels:
        axis_labels[ax] = [ "%s %s"%(axis_type[ax],labels[int(rval-1+delt*(i+1-rpix))]) for i in range(dims[ax]) ]
      elif unit == 1:
        axis_labels[ax] = [ "%s %g"%(axis_type[ax],rval+delt*(i+1-rpix)) for i in range(dims[ax]) ]
      else:
        axis_labels[ax] = [ "%s %g%s"%(axis_type[ax],rval+delt*(i+1-rpix),unit) for i in range(dims[ax]) ]
    # is there an unroll axis specified
    if unroll is not None:
      if type(unroll) is str:
        unroll = axis_type.index(unroll) if unroll in axis_type else None
      if unroll is not None:
        if unroll in remaining_axes:
          remaining_axes.remove(unroll)
        else:
          raise ValueError,"unknown unroll axis %s"%unroll
    # we'd better have enough elements in index to take care of the remaining axes
    index = [index] if type(index) is int else list(index)
    for remaxis in sorted(remaining_axes):
      if dims[remaxis] == 1:
        baseslice[remaxis] = 0;
      elif not index:
        raise TypeError,"not enough elements in index to index into axis %s"%axis_type[remaxis];
      else:
        baseslice[remaxis] = i = index.pop(0);
        status += " "+(axis_labels[remaxis][i])
        title += " "+(axis_labels[remaxis][i])
    data = ff[0].data.transpose();
    if unroll is None:
      # show single image
      if make_figure:
        plt.figure(figsize=(width or maxwidth,width or maxwidth),dpi=DPI)
      plt.imshow(data[tuple(baseslice)],vmin=vmin,vmax=vmax)
      colorbar and plt.colorbar()
      plt.xlabel(axis_type[xyaxes[0]])
      plt.ylabel(axis_type[xyaxes[1]])
      plt.title(title,fontsize=fs_title)
    else:
      status += ", unrolling "+axis_type[unroll]
      nrow = int(math.ceil(dims[unroll]/float(maxcol or ncol)))
      ncol = ncol or min(dims[unroll],maxcol)
      width = width or maxwidth/float(ncol)
      fig = plt.figure(figsize=(width*ncol,width*nrow),dpi=DPI)
      for iplot in range(dims[unroll]):
        plt.subplot(nrow,ncol,iplot+1)
        baseslice[unroll] = iplot
        plt.imshow(data[tuple(baseslice)],vmin=vmin,vmax=vmax)
        title = title+" "+axis_labels[unroll][iplot]
        plt.title(title,fontsize=fs_title)
        plt.xlabel(axis_type[xyaxes[0]])
        plt.ylabel(axis_type[xyaxes[1]])
        colorbar and plt.colorbar()
    return status

class ImageFile (DataFileBase):

  @staticmethod
  def _show_thumbs (images,width=4):
    for img in images:
      img.show(width=width)
      IPython.display.display(IPython.display.HTML(img.name))

  def _show_thumbs (images,width=None,ncol=None,maxwidth=16,maxcol=4,**kw):
    nrow = int(math.ceil(len(fits_files)/float(ncol or maxcol)))
    ncol = ncol or min(len(fits_files),maxcol)
    width = width or maxwidth/float(ncol)
    fig = plt.figure(figsize=(width*ncol,width*nrow),dpi=DPI)
    for iplot,ff in enumerate(fits_files):
      plt.subplot(nrow,ncol,iplot+1);
      ff.show(index=[0]*10,unroll=None,colorbar=False,filename_in_title=True,make_figure=False,fs_title='small',**kw)


  def show (self,width=None):
    IPython.display.display(IPython.display.Image(self.fullpath,width=width*100))


def DataFile (path,root=""):
  """Creates DataFile object of appropriate type, basedon filename extension""";
  ext = os.path.splitext(path)[1]
  if ext.lower() in [".fits",".fts"]:
    return FITSFile(path,root=root)
  elif ext.lower() in [".png",".jpg",".jpeg" ]:
    return ImageFile(path,root=root)
  return DataFileBase(path,root=root)


class FileList (list):
  def __init__ (self,files=[],extcol=True,thumbs=None):
    list.__init__(self,files);
    self._extcol = extcol;
    self._init_df();
    self._thumbs = thumbs;

  def sort (self,*args,**kw):
    list.sort(self,*args,**kw)
    self._init_df();

  def _init_df (self):
    if self._extcol:
      df_files = [ (f.basename,f.ext,f.size,f.mtime_str) for f in self ];
      self._df = DataFrame(df_files,columns=('name','ext','size','modified')) if df_files else None
    else:
      df_files = [ (f.name,f.size,f.mtime_str) for f in self ];
      self._df = DataFrame(df_files,columns=('name','size','modified')) if df_files else None

  def _repr_html_ (self):
    return self._df._repr_html_() if self._df is not None else "";

  def show (self):
    return IPython.display.display(self._df);

  def show_all (self):
    for f in self:
      f.show();

  def __call__ (self,pattern):
    files = [ f for f in self if fnmatch.fnmatch(f.name,pattern) ]
    return FileList(files,extcol=self._extcol,thumbs=self._thumbs)

  def thumbs (self,**kw):
    return self._thumbs(self,**kw) if self._thumbs else None;

  def __getslice__ (self,*slc):
    return FileList(list.__getslice__(self,*slc),extcol=self._extcol,thumbs=self._thumbs)

class DataDir (object):
  """This class represents a directory in the data folder""";
  def __init__ (self,name,files=[],root=""):
    self.fullpath = name
    if root and name.startswith(root):
      name = name[len(root):]
      if name.startswith("/"):
        name = name[1:]
      name = name or "."
    self.name = self.path = name
    self.mtime = os.path.getmtime(self.fullpath)
    # make list of DataFiles and sort by time
    self.files = FileList([ DataFile(os.path.join(self.fullpath,f),root=root) for f in files if not f.startswith('.') ])
    self.files.sort(cmp=lambda a,b:cmp(a.mtime,b.mtime))
    # make separate lists of fits files and image files
    self.fits_files = FileList([ f for f in self.files if type(f) is FITSFile ],extcol=False,thumbs=FITSFile._show_thumbs)
    self.img_files = FileList([ f for f in self.files if type(f) is ImageFile ],extcol=False,thumbs=ImageFile._show_thumbs)
    # make DataFrame for display
    self._df = self.files._df

  def show (self):
    return IPython.display.display(self._df);

  def _repr_html_ (self):
    return self.name


class DirList (list):
  def __init__ (self,rootfolder=None,pattern="*",scan=True):
    self._root = rootfolder
    self._df = None
    if scan:
      for dir_, _, files in os.walk(rootfolder):
        if fnmatch.fnmatch(os.path.basename(dir_),pattern):
          self.append(DataDir(dir_,files,root=rootfolder))
      self._sort()

  def _sort (self):
    self.sort(cmp=lambda x,y:cmp(x.name,y.name));
    dirlist = [];
    for dir_ in self:
      nfits =  len(dir_.fits_files);
      nimg =  len(dir_.img_files);
      nother = len(dir_.files) - nfits - nimg;
      dirlist.append( (dir_.name,nfits,nimg,nother,time.ctime(dir_.mtime)) );
    if dirlist:
      self._df = DataFrame(dirlist,columns=("name","# FITS","# img","# others","modified"));
    else:
      self._df = None;

  def _repr_html_ (self):
    return self._df._repr_html_() if self._df is not None else "";

  def show (self):
    return IPython.display.display(self._df);

  def __call__ (self,pattern):
    return DirList(self._root,pattern)

  def __getslice__ (self,*slc):
    newlist = DirList(self._root,scan=False)
    newlist += list.__getslice__(self,*slc);
    newlist._sort();
    return newlist




# def scandirs (datafolder=DATAFOLDER):
#   """Scans all directories under datafolder and populates the DIRS list"""
#   global DIRS;
#   DIRS = DirList(datafolder);

# for name,ds in sorted(all_dirs):
#     print "Contents of",name
#     display(d)