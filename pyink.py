import pybInkscape
import pygtk
import gtk
import os
from yai import Wrapper

wrapper = None

def activate_desktop(ptr):
  global wrapper
  """ Handler for desktop activation events."""
  # Get Python wrapper of SPDesktop passed by ptr.
  desktop = pybInkscape.GPointer_2_PYSPDesktop(ptr)
  print "A desktop has connected: %s" % desktop

  top = desktop.getToplevel()
  if not top:
    print "But there were no active top window."
    #For some reason getToplevel doesn't work properly on Windows.
    if os.name != "nt":
      return

  wrapper = Wrapper(desktop, top)
  wrapper.show()

def deactivate_desktop(ptr):
  print "Deactivating desktop!"
  desktop = pybInkscape.GPointer_2_PYSPDesktop(ptr)
  wrapper.xml.desktop = None  #Won't work if there's more than one

def pyink_start():
  print "Starting pyink and waiting for active desktop to connect"
  pybInkscape.connect("activate_desktop", activate_desktop)
  pybInkscape.connect("deactivate_desktop", deactivate_desktop)
