import os, time, math, astropy, pyfits, traceback, fnmatch
from pandas import DataFrame, Series
import IPython.display
from IPython.display import Image, HTML, display

from rv.FITSFile import FITSFile
from rv.ImageFile import ImageFile

import matplotlib.pyplot as plt

NOTEBOOK_DIR = os.environ.get('RVNB_NOTEBOOK_DIR', '/notebooks')
RESULTDIR = os.environ.get('RVNB_DATA_DIR', '/data')
ORIGINAL_RESULTDIR = os.environ.get('RVNB_ORIGINAL_DIR', 'unknown')

WIDTH = None    # globally fix a plot width (inches)
MINCOL = 2      # default min # of columns to display in thumbnail view
MAXCOL = 4      # default max # of columns to display in thumbnail view
MAXWIDTH = 16   # default width of thumbnail view (inches)
DPI = 80        # screen DPI 

astropy.log.setLevel('ERROR')

import os, time, math, astropy, pyfits, traceback, fnmatch
from pandas import DataFrame, Series
import IPython.display
from IPython.display import Image, HTML, display

import matplotlib.pyplot as plt

from rv.File import DataFile

def renderTitle (title):
    return "<h4>%s</h4>"%title;

class FileList(list):

    _sort_attributes=dict(x="ext",n="basename",s="size",t="mtime")

    def __init__(self, files=[], extcol=True, thumbs=None, title="", sort="xnt"):
        list.__init__(self, files)
        self._extcol = extcol
        self._thumbs = thumbs
        self._title = title
        if sort:
            self.sort(sort)

    def sort(self, opt="xnt"):
        """Sort the filelist by name, eXtension, Time, Size, optionally Reverse"""
        opt = opt.lower()
        # build up order of comparison
        cmpattr = []
        for attr in opt:
            if attr in self._sort_attributes:
                cmpattr.append(self._sort_attributes[attr])

        def compare(a, b, attrs=cmpattr):
            for attr in attrs:
                result = cmp(getattr(a,attr),getattr(b,attr))
                if result:
                    return result
            return 0

        list.sort(self, cmp=compare, reverse='r' in opt)
        self._init_df()
        return self

    def _init_df(self):
        if self._extcol:
            df_files = [(f.basename, f.ext, f.size, f.mtime_str) for f in self]
            self._df = DataFrame(df_files,
                                 columns=('name', 'ext', 'size',
                                          'modified')) if df_files else None
        else:
            df_files = [(f.name, f.size, f.mtime_str) for f in self]
            self._df = DataFrame(
                df_files,
                columns=('name', 'size', 'modified')) if df_files else None

    def _repr_html_(self):
        return renderTitle(self._title) + \
                (self._df._repr_html_() if self._df is not None else "")

    def show(self):
        return IPython.display.display(self)

    def show_all(self):
        for f in self:
            f.show()

    def __call__(self, pattern):
        files = [f for f in self if fnmatch.fnmatch(f.name, pattern)]
        return FileList(files,
                        extcol=self._extcol,
                        thumbs=self._thumbs,
                        title=os.path.join(self._title, pattern))

    def thumbs(self, **kw):
        kw['title'] = self._title
        return self._thumbs(self, **kw) if self._thumbs else None

    def __getslice__(self, *slc):
        return FileList(list.__getslice__(self, *slc),
                        extcol=self._extcol,
                        thumbs=self._thumbs,
                        title="%s[%s]"%(self._title,":".join(map(str,slc))))


class DataDir(object):
    """This class represents a directory in the data folder"""

    def __init__(self, name, files=[], root=""):
        self.fullpath = name
        if root and name.startswith(root):
            name = name[len(root):]
            if name.startswith("/"):
                name = name[1:]
            name = name or "."
        self.name = self.path = name
        self.mtime = os.path.getmtime(self.fullpath)
        files = [ f for f in files  if not f.startswith('.') ]
        # our title, in HTML
        self._title = os.path.join(ORIGINAL_RESULTDIR, self.path
                                   if self.path is not "." else "")
        # make list of DataFiles and sort by time
        self.files = FileList([ DataFile(os.path.join(self.fullpath, f),
                                        root=root) for f in files],
                               title=self._title)
        # make separate lists of fits files and image files
        self.fits = FileList([ f for f in self.files
                                    if type(f) is FITSFile],
                                   extcol=False,
                                   thumbs=FITSFile._show_thumbs,
                                   title="FITS files, " + self._title);
        self.images = FileList([ f for f in self.files
                                   if type(f) is ImageFile],
                                  extcol=False,
                                  thumbs=ImageFile._show_thumbs,
                                  title="Images, " + self._title)
        # make DataFrame for display
        self._df = self.files._df

    def sort(self, opt):
        for f in self.files, self.fits, self.images:
            f.sort(opt)
        self._df = self.files._df
        return self

    def show(self):
        return IPython.display.display(self)

    def _repr_html_(self):
        return renderTitle(self._title) + self._df._repr_html_()


class DirList(list):
    def __init__(self, rootfolder=None, pattern="*", scan=True, title=None):
        self._root = rootfolder = rootfolder or RESULTDIR
        self._title = title or ORIGINAL_RESULTDIR
        self._df = None
        if scan:
            for dir_, _, files in os.walk(rootfolder):
                basename = os.path.basename(dir_)
                if fnmatch.fnmatch(basename, pattern) and not basename.startswith("."):
                    self.append(DataDir(dir_, files, root=rootfolder))
            self._sort()

    def _sort(self):
        self.sort(cmp=lambda x, y: cmp(x.name, y.name))
        dirlist = []
        for dir_ in self:
            nfits = len(dir_.fits)
            nimg = len(dir_.images)
            nother = len(dir_.files) - nfits - nimg
            dirlist.append(
                (dir_.name, nfits, nimg, nother, time.ctime(dir_.mtime)))
        if dirlist:
            self._df = DataFrame(
                dirlist,
                columns=("name", "# FITS", "# img", "# others", "modified"))
        else:
            self._df = None

    def _repr_html_(self):
        return renderTitle(self._title) + \
            (self._df._repr_html_() if self._df is not None else "")

    def show(self):
        return IPython.display.display(self)

    def __call__(self, pattern):
        return DirList(self._root, pattern,
                       title=os.path.join(self._title, pattern))

    def __getslice__(self, *slc):
        newlist = DirList(self._root, scan=False, 
                          title="%s[%s]"%(self._title,":".join(map(str,slc))))
        newlist += list.__getslice__(self, *slc)
        newlist._sort()
        return newlist

# def scandirs (datafolder=DATAFOLDER):
#   """Scans all directories under datafolder and populates the DIRS list"""
#   global DIRS;
#   DIRS = DirList(datafolder);

# for name,ds in sorted(all_dirs):
#     print "Contents of",name
#     display(d)
