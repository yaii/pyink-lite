from animtree import Animation, Timing, Evaluator
import gtk
import animtree, xmltree
import re, random
import gobject
import colorsys
from uielem import ui, uidict
from followpath import FollowPath

RADIUS = 20
XDISTANCE = 50
YDISTANCE = 50

class EditableAnimation(Animation):
  def __init__(self, *args, **kwargs):
    Animation.__init__(self, *args, **kwargs)
    self.cx = kwargs.get("cx", 0)
    self.cy = kwargs.get("cy", -YDISTANCE)
    self.r = RADIUS
    self.visualnode = None
    self.datanode = None

  def add(self, anim):
    Animation.add(self, anim)
    anim.resetxy()
    if self.checknodes():
      anim.addnode(self)

  def remove(self, anim):
    """ Remove a child animation. """
    # Remove anim node.
    if anim not in self.children:
      raise "Could find child %s to remove" % anim
    self.children.remove(anim)
    anim.parent = None
    # Remove auxiliary nodes.
    if anim.datanode in self.datanode.children:
      self.datanode.removeChild(anim.datanode)
    else:
      print "Warning: child not present in datanode, not removing!"
    vnodes = self.visualnode.xml.nodes["vnodes"]
    if anim.visualnode in vnodes.children:
      vnodes.removeChild(anim.visualnode)
    else:
      print "Warning: child not present in vnodes, not removing!"

  def checknodes(self):
    """ Makes sure the visualnode and linked nodes are still there and they are what we think they are.
    """
    return (self.visualnode and self.datanode and
            self.visualnode.alive() and self.datanode.alive())

  def addnode(self, parent):
    self.visualnode = VisualNode(self, "svg:circle", parent.visualnode.xml,
                                 params = {"id":"visual"+str(random.randint(0,10000)), "style":"fill:none;stroke:#000000;stroke-width:3"})
    self.datanode = LinkedNode(self, "yai:animation", parent.datanode.xml)
    parent.datanode.appendChild(self.datanode)
    # Way too many levels of indirection...
    vnodes = parent.visualnode.xml.nodes["vnodes"]
    vnodes.appendChild(self.visualnode)

  def resetxy(self):
    pcx, pcy = self.parent.getxy()
    self.cx = pcx + XDISTANCE
    self.cy = pcy - (len(self.parent.children)-1)*YDISTANCE

  def getxy(self):
    if hasattr(self, "transform"):
      match = re.match("translate\(([-]?\d+[.]?\d+),([-]?\d+[.]?\d+)", self.transform)
    if hasattr(self, "transform") and match:
      dxy = map(float, match.groups())
      return self.cx + dxy[0], self.cy + dxy[1]
    else:
      return self.cx, self.cy

  def setvalue(self, attrib, value):
    #Probably don't need double prevention
    if hasattr(self, attrib) and getattr(self, attrib) == value:
      return
    if hasattr(self, "gettransf") and attrib in ["init", "final"]:
      setattr(self, attrib, self.gettransf(value))
    else:
      setattr(self, attrib, value)
    #Update visual node
    if attrib in ["cx", "cy", "r", "transform"]:
      self.visualnode[attrib] = value
    else:
      self.datanode[attrib] = value

  def update(self, t, started = True, finished = None):
    # Odd, there doesn't seem to be a self.t value. They are always passed as parameter...
    if finished == None:
      finished = self.timing.finished
    if not started:
      fill = colors["black"]
    elif finished:
      fill = colors["blue"]
    else:
      ratio, ended, newt = self.timing.diff(t)
      fill = colorterp(colors["black"], colors["green"], ratio)
    self.visualnode["style.fill"] = colorhex(fill)
    self.visualnode["style.stroke-width"] = "5"

  def simulate(self, t):
    ended, newt, alteration = Animation.simulate(self, t)
    self.update(t, True, ended)
    return ended, newt, alteration

def colorhex(rgb):
  return '#%02x%02x%02x' % tuple([c*255 for c in rgb])

colors = {"black":(0, 0, 0), "blue":(0, 0, 1), "green":(0, 1, 0)}
      
def colorterp(src, dest, t):
  src = colorsys.rgb_to_hls(*src)
  dest = colorsys.rgb_to_hls(*dest)
  t = max(0, min(t, 1))
  midcol = [src[i]*(1-t) + dest[i]*t for i in xrange(len(src))]
  return colorsys.hls_to_rgb(*midcol)

class VisualNode(xmltree.Node):
  """ The animation does all the modifications on these nodes instead of the nodes themselves. These nodes just call the animation's functions when they are edited (currently in the observer)."""
  def __init__(self, anim, name, xml, params={}):
    params.update({"cx":anim.cx, "cy":anim.cy, "r":anim.r})
    xmltree.Node.__init__(self, name, xml, params = params)
    self.wrapper = self
    self.anim = anim

class LinkedNode(xmltree.Node):
  """ The animation does all the modifications on these nodes instead of the nodes themselves. These nodes just call the animation's functions when they are edited (currently in the observer)."""
  def __init__(self, anim, name, xml, **kwargs):
    xmltree.Node.__init__(self, name, xml, **kwargs)
    self.wrapper = self
    self.anim = anim
    self.update()
    self["id"] = "animationdata%s" % random.randint(0,10000)

  def update(self):
    for key, value in self.anim.timing.__dict__.items() + self.anim.__dict__.items():
      if not callable(value):
        self[key] = str(value)

#Expects itself to be made of EditableAnimation 
class Animator(animtree.Animator):
  """ Text-based animation tree editor. """
  def __init__(self, xml):
    self.xml = xml
    animtree.Animator.__init__(self)
    self.dirty = True    #Need update/redraw if True
    self.observers = []

  def initdraw(self):
    self.xml.update()
    self.drawarrows()
    self.addobserver()
    self.xml.update()

  # Should this be in XML? But it is also very animator specific.
  def addxml(self):
    tree = self.xml.create("animtree", "yai:animtree", parent = self.xml.root)
    vanimtree = self.xml.create("vanimtree", "svg:g", parent = self.xml.root,
                                params = {"inkscape:groupmode":"layer",
                                          "inkscape:label":"Visual animation"})
    vnodes = self.xml.create("vnodes", "svg:g", parent = vanimtree,
                             params = {"inkscape:groupmode":"layer",
                                       "inkscape:label":"Visual nodes"})
    tree.appendChild(self.root.datanode)
    vnodes.appendChild(self.root.visualnode)

  def drawarrows(self):
    if not self.dirty:
      return
    self.dirty = False
    self.xml.update()

    arrows = self.xml.create("varrows", "svg:g", {"sodipodi:insensitive":"true"},
                             self.xml.nodes["vanimtree"])
    if "Arrow1Mend" not in self.xml.nodes:
      self.xml.addconstant("Arrow1Mend")

    queue = [self.root]
    while queue:
      anim = queue.pop()
      if anim.parent:
        params = {"d": "M %s,%s L %s,%s" % tuple(getxy(anim)+getxy(anim.parent)),
                  "style":"marker-end:url(#Arrow1Mend);stroke:#000000;stroke-width:4"}
        arrows.appendChild(xmltree.Node("svg:path", self.xml, params=params))
      queue.extend(anim.children)
    self.xml.update()

  def treechange(self, changetype, source, node, *args):
    #print source["id"], "listener called with", changetype, node, args
    if source["id"] == "animtree" and changetype == "attribute":
      attrib, oldvalue, value = args
      if oldvalue != value:
        # Not sure what to do with memory addresses yet.
        if attrib not in ["id", "parent", "target", "visualnode"]:
          node.anim.setvalue(attrib, value)
    elif changetype == "remove":
      child = args[0]
      self.removeanim(child.anim)
    self.dirty = True
    gobject.idle_add(self.drawarrows)

  def removeanim(self, anim):
    # Need to avoid loops somehow...
    if anim.parent:
      anim.parent.remove(anim)
      for child in anim.children:
        anim.remove(child)
    # Should we recalculate maxanim after this?

  def addobserver(self):
    self.observers = [xmltree.addlistener(self.xml.nodes["vnodes"], self.treechange), 
                      xmltree.addlistener(self.xml.nodes["animtree"], self.treechange)]

  def removeobserver(self):
    for observer in self.observers:
      xmltree.removelistener(observer)

  def newroot(self):
    self.root = EditableAnimation(None, None, None, timing = Timing(duration=0))
    self.root.datanode = LinkedNode(self.root, "yai:animation", self.xml)
    self.root.visualnode = VisualNode(self.root, "svg:circle", self.xml, params = {"id":"visual"+str(random.randint(0,10000))})
    self.maxanim = self.root
    self.addxml()

def getxy(node):
  if hasattr(node, "transform"):
    toadd = map(float, re.match("translate\(([-.0-9]*),([-.0-9]*)\)", node.transform).groups())
    xy = [node.cx + toadd[0], node.cy + toadd[1]]
  return [node.cx, node.cy]

class EWDictAnimation(EditableAnimation):
    def __init__(self, *args, **kwargs):
        EditableAnimation.__init__(self, *args, **kwargs)
        self.gettransf = kwargs.get("gettransf", None)
        self.settransf = kwargs.get("settransf", None)

    def getrawval(self):
        return self.target[self.param]

    def getval(self):
        if self.gettransf:
            return self.gettransf(self.target[self.param])
        else:
            return self.target[self.param]

    def setval(self, value):
        if self.settransf:
            value = self.settransf(value)
        self.target[self.param] = value

    value = property(getval, setval)

    def simulate(self, t):
        ended, newt, alteration = EditableAnimation.simulate(self, t)
        if alteration:
            alteration[1] = "[%s]" % alteration[1]
        return ended, newt, alteration

def floattostr(floatval):
  return "%f" % floatval

class AnimatorUI(Animator):
  def __init__(self, xml, animator):
    self.xml = xml
    self.animator = animator

  def buttons(self):
    return [ui(gtk.combo_box_new_text, name = "animbox",
               items = ["Appear", "Disappear", "Follow path"]),
            ui(gtk.Entry, name = "animeditor"),
            ui(gtk.Button, "Add", on_clicked = (self.pressbutton, "Add")),
            ui(gtk.Button, "Add clones", on_clicked = (self.pressbutton, "Add clones"))]

  def pressbutton(self, button, event):
    if event == "Add":
      self.addanim(uidict["animbox"].get_active_text(),
                   uidict["animeditor"].get_text())
    elif event == "Add clones":
      selection = self.xml.selection[0].wrapper
      fp = selection.pystore["fp"]
      fp.addclones()

  def addanim(self, animtype, *args):
    target = self.xml.selection[0]
    target = self.xml.addwrapper(target) or target
    if not target.get("style.opacity"):
      target["style.opacity"] = "1"
    if animtype == "Appear":
      anim = EWDictAnimation(target, "style.opacity", 1.0, gettransf=float, settransf=floattostr)
    elif animtype == "Disappear":
      anim = EWDictAnimation(target, "style.opacity", 0.0, gettransf=float, settransf=floattostr)
    elif animtype == "Follow path":
      path = self.xml.nodes[args[0]]
      svgfp = FollowPath(target, path)
      anim = EditableAnimation(svgfp, "t", Evaluator(len(svgfp.commands) - 1),
                               Timing(duration = len(svgfp.commands) * 1000))
    self.animator.addbasic(anim)

  def extraui(self):
    def valadj(adj):
      if "altered" in self.animator.__dict__:
        self.animator.reset(self.animator.altered)
      self.animator.altered = self.animator.simulate(1000*adj.get_value())
    adj = ui(gtk.Adjustment, lower=0, upper=3, on_value_changed=[valadj], name="animadj")
    hbox = ui(gtk.HBox, False, 0, children = [
             ui(gtk.HScale, adj, set_digits=[2], name="animscroll"),
             ui(gtk.SpinButton, adj, digits = 2)])
    hbox.set_child_packing(uidict["animscroll"], True, True, 0, gtk.PACK_START)
    return hbox
