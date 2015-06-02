import pybInkscape
import pygtk
import gtk
import os
from yai import Wrapper

wrapper = None

def act_desktop(inkscape, ptr):
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

  wrapper = Wrapper(desktop, top, inkscape)
  wrapper.show()

def deact_desktop(inkscape, ptr):
  print "Deactivating desktop!"
  desktop = pybInkscape.GPointer_2_PYSPDesktop(ptr)
  wrapper.xml.desktop = None  #Won't work if there's more than one

def pyink_start():
  print "Starting pyink and waiting for active desktop to connect"
  pybInkscape.inkscape.connect('activate_desktop', act_desktop)
  pybInkscape.inkscape.connect('deactivate_desktop', deact_desktop)
