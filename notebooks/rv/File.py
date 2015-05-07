import os
import time
import math

import rv

class FileBase (object):
    def __init__(self, path, root=""):
        self.fullpath = path
        if root and path.startswith(root):
            path = path[len(root):]
            if path.startswith("/"):
                path = path[1:]
        self.path = path
        self.name = os.path.basename(path)
        self.basename, self.ext = os.path.splitext(self.name)
        self.size = os.path.getsize(self.fullpath)
        self.mtime = os.path.getmtime(self.fullpath)
        self.mtime_str = time.strftime(rv.TIMEFORMAT,time.localtime(self.mtime))
        # human-friendly size
        if self.size > 0:
            exponent = min(int(math.log(self.size, 1024)), len(self._unit_list) - 1)
            quotient = float(self.size) / 1024**exponent
            unit, num_decimals = self._unit_list[exponent]
            format_string = '{:.%sf}{}' % (num_decimals)
            self.size_str = format_string.format(quotient, unit)
        else:
            self.size_str = '0'

    def __str__(self):
        return self.path

    def _repr_html_(self):
        return self.show() or self.path

    def show(self, **kw):
        print self.path

    _unit_list = zip(['', 'k', 'M', 'G', 'T', 'P'], [0, 0, 1, 2, 2, 2])



def DataFile(path, root=""):
    """Creates DataFile object of appropriate type, based on filename extension"""
    from rv.FITSFile import FITSFile
    from rv.ImageFile import ImageFile

    ext = os.path.splitext(path)[1]
    if ext.lower() in [".fits", ".fts"]:
        return FITSFile(path, root=root)
    elif ext.lower() in [".png", ".jpg", ".jpeg"]:
        return ImageFile(path, root=root)
    return FileBase(path, root=root)

def compute_thumb_geometry(N, ncol, mincol, maxcol, width, maxwidth):
    """Works out thumbnail geometry.
     Given nfiles thumbsnails to display, how many rows and columns do we need 
     to make, and how wide do we need to make the plot?
     N:      number of thumbnails to display
     ncol:   use a fixed number of columns. If 0, uses mincol/maxcol.
     mincol or rv.MINCOL: use a minimum of that many columns, even if N is fewer.
                          If N<mincol, will use mincol columns
     maxcol or rv.MAXCOL: use a maximum of that many columns. If 0, makes a single row of N columns.
     width:               if non-zero, fixes width of individual thumbnail, in inches
     maxwidth or rv.MAXWIDTH:  if width is 0, uses a width of maxwidth/ncol for each thumbnail

    Returns tuple of nrow, ncol, width
    """
    # figure out number of columns
    if not ncol:
        mincol = mincol or rv.MINCOL or 0
        maxcol = maxcol or rv.MAXCOL or 8
        ncol = max(mincol,min(maxcol,N))
    # number of rows
    nrow = int(math.ceil(N / float(ncol)))
    # individual thumbnail width
    width = width or ( (maxwidth or rv.WIDTH or 16) / float(ncol) )
    return nrow, ncol, width
