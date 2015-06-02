import gtk
import texttree
from xmltree import XML
import pybInkscape
from xreload import xreload
from uielem import ui, uidict
import traceback

class Wrapper:
  def __init__(self, desktop, window, inkscape):
    self.xml = XML(desktop)
    self.window = window
    self.top = None
    self.inkscape = inkscape

    inkscape.connect('change_selection', self.changesel)

  def show(self):
    if self.top == None and not self.window:
      print "Created a new top window since no top window was found", self.window
      self.window = ui(gtk.Window, gtk.WINDOW_TOPLEVEL, show = True,
                       child = ui(gtk.VBox, False, 0, name = "top"))
    elif self.top == None:
      self.window.child.child.pack_end(ui(gtk.VBox, False, 0, name = "top"), expand=False)
    else:
      self.top.remove(self.outerbox)

    self.animator = texttree.Animator(self.xml)
    self.animui = texttree.AnimatorUI(self.xml, self.animator)
    self.animator.initdraw()

    outerbox = ui(gtk.VBox, False, 0, name = "outerbox", children = [
      ui(gtk.HBox, False, 0, children = self.buttons() + [
         ui(gtk.Entry, on_activate = (self.pressbutton,"Set"), name = "editor")]),
      ui(gtk.HBox, False, 0, name = "buttonbox", children = self.animui.buttons()),
      ui(gtk.HBox, False, 0, children = [
        ui(gtk.Label, "Console:"),
        ui(gtk.Entry, on_activate = [self.eval], name = "console")]),
      self.animui.extraui()])
    uidict["editor"].prop = "id"
    self.__dict__.update(uidict)
    self.top.pack_start(outerbox, expand=False)
    self.top.show_all()
    return False

  def addbutton(self, name, func):
    """ Add new button `name` executing the function `func`. """
    btn = ui(gtk.Button, name, on_clicked = (func), name = name+"-button", show = True)
    self.buttonbox.pack_start(btn, expand=False, fill=False)

  def buttons(self):
    """ Default buttons."""
    return [ui(gtk.Button, name, on_clicked = (self.pressbutton, name))
            for name in ["Reload code", "Set"]]

  def changesel(self, inkscape, obj):
    print "Changed selection"
    self.xml.update()
    if self.xml.selection:
      self.editor.set_text(self.xml.selection[0].get(self.editor.prop,""))
    else:
      self.editor.set_text('')

  def pressbutton(self, button, event):
    self.xml.update()
    if event == "Reload code":
      import yai, xmltree
      for module in [yai, xmltree, texttree]:
        xreload(module)
    elif event == "Set":
      obj = self.xml.selection[0]
      obj[self.editor.prop] = self.editor.get_text()
      self.xml.update()

  def eval(self, widget):
    cmd = self.console.get_text()
    self.xml.update()
    print ">>> %s" % cmd
    try:
      co = compile(cmd, "<console>", "single")
      exec co in globals()
    except:
      traceback.print_exc()
