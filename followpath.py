from numpy import array
import xmltree
import re

def fastgetcommands(svgpath):
  commands = []
  for element in svgpath:
    command = element[0]
    #print element
    points = [array(map(float,e.split(","))) if "," in e else float(e) for e in element[1:]]
    #if len(points)>1:
    if command in ["C","Q"]:
      commands.append([command,commands[-1][-1]]+points)
    else:
      commands.append([command]+points)
  return commands

def getbezpoint(p,c,t):
  return ((1-t)*(1-t)*(1-t)*p[0] + 3*t*(1-t)*(1-t)*c[0]
          + 3*t*t*(1-t)*c[1] + t*t*t*p[1])

class FollowPath(object):
  def __init__(self, target, path):
    self.target = target
    self.path = path
    self.path.wrapper = self.path
    self.path.pystore["fp"] = self
    self._t = 0
    self.clones = []
    self.pathstring = ""
    self.update()
    # Need an observer for path["d"]
    self.listener = xmltree.addlistener(self.path, self.pathchanged)

  def pathchanged(self, changetype, node, *args):
    if changetype == "attribute" and self.pathstring != self.path["d"]:
      self.update()

  def update(self):
    if self.pathstring == self.path["d"]:
      return
    self.pathstring = self.path["d"]
    parsedpath = map(lambda x:x.strip().split(), re.findall("[LCQMlcqmz][^LCQMlcqmz]*", self.pathstring))
    self.commands = fastgetcommands(parsedpath)
    for clone in self.clones:
      clone.update()

  def updatetarget(self):
    point = self.point()
    self.target["transform"] = "translate(%.6f, %.6f)" % tuple(point)

  def point(self, t = None):
    if t is None:
      t = self.t
    step = int(t) + 1
    if step >= len(self.commands):
      return self.commands[-1][-1]
    fraction = t - int(t)
    #print step, fraction
    element = self.commands[step]
    command = element[0]
    if command == 'C':
      p, c = (element[1], element[4]), (element[2], element[3])
      return getbezpoint(p, c, fraction)
    elif command == 'L':
      start, end = self.commands[step-1][-1], element[1]
      return (1-fraction) * start + fraction * end
    elif command == 'M':
      return element[1]
    else:
      print "Unknown command", element
      return element[1]

  def setpath(self, commands = None):
    if commands is None:
      commands = self.commands
    def pstr(p):
      return str(p[0])+","+str(p[1])
    def elemstr(element):
      if element[0] in ["C","Q"]:
        return " ".join([element[0]]+map(pstr,element[2:]))
      else:
        return " ".join([element[0]]+map(pstr,element[1:]))
    #print "Setting path to", " ".join(map(elemstr, self.commands))
    self.path["d"] = " ".join(map(elemstr, self.commands))
    self.update()

  def addclone(self, t):
    self.clones.append(FollowPathClone(self, t))

  def addclones(self):
    for t in range(1, len(self.commands)):
      self.addclone(t)

  def gett(self):
    return self._t

  def sett(self, t):
    self._t = t
    self.updatetarget()

  t = property(gett, sett)

class FollowPathClone(object):
  def __init__(self, followpath, t):
    self.followpath = followpath
    target = self.followpath.target
    self.t = t
    self.clone = xmltree.Node("svg:use", target.xml,
                              {"xlink:href": "#"+target["id"]})
    target.parent.appendChild(self.clone)
    self.update()
    self.listeners = [xmltree.addlistener(self.followpath.target, self.pathchange),
                      xmltree.addlistener(self.clone, self.clonechanged)]

  def pathchange(self, changetype, *args):
    if changetype == "attribute":
      self.update()

  def update(self):
    point = self.followpath.point(self.t) - self.followpath.point()
    if not all(gettranslate(self.clone.get("transform", "")) == point):
      self.clone["transform"] = "translate(%.6f, %.6f)" % tuple(point)

  def clonechanged(self, changetype, node, *args):
    if changetype == "attribute":
      #print node["id"], "changed!",
      # Break path, change coord, reassemble path
      step = int(self.t)
      point = gettranslate(self.clone["transform"]) + self.followpath.point()
      #print point, self.followpath.commands[step][-1]
      if not all(self.followpath.commands[step][-1] == point):
        # Bad!
        self.followpath.commands[step][-1] = point
        # In some cases, might have to update the step + 1 point too.
        self.followpath.setpath()

  def removelistener(self):
    for listener in self.listeners:
      xmltree.removelistener(listener)

def gettranslate(string):
  mo = re.match("translate\(([-]?[0-9.]*),\s*([-]?[0-9.]*)\)", string)
  if mo:
    return array(map(float, mo.groups()))
  else:
    return array([0, 0])

def settranslate(point):
  return "translate(%.6f, %.6f)" % tuple(point)
