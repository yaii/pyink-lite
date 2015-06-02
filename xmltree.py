import re
import pybInkscape

class Node(pybInkscape.PYElementNode, object):
  def __init__(self, name, xml, params={}):
    if xml.__class__.__name__ != "XML":
      raise "Expected an XML class object as second parameter but got %s. This will segfault if not stopped here" % xml.__class__.__name__
    pybInkscape.PYElementNode.__init__(self, name, xml.doc)
    self.xml = xml
    self.updateparams(params)
    # Set the underlying C pointer to this python object.
    # Remove if debugging is needed
    self.wrapper = self

  def updateparams(self, params):
    for key, value in params.items():
      self[key] = str(value)

  def alive(self):
    """ Check if this node is still in its xml own tree."""
    return self.xml.contains(self)

class XML:
  """ Extract useful fields from various places. 
      Interfaces with the XML tree directly.
      Including layers selection and manipulation."""
  def __init__(self, desktop):
    self.desktop = desktop
    self.update()

  def update(self):
    if not self.desktop:
      print "Desktop lost by xml. Document has been destroyed..."
      return
    self.doc = self.desktop.doc.rdoc
    self.selection = self.desktop.selection.list()
    self.selector = self.desktop.selection
    self.root = self.desktop.doc.rdoc.root
    self.nodes = self.updatenodes()

  def layers(self):
    return [child for child in self.root.childlist()
            if child.get("inkscape:groupmode") == "layer"]

  def updatenodes(self, node = None):
    nodes = self.applytoall(lambda node: None)
    return nodes

  def hide(self, node, visible = True):
    if not visible:
      node["style.display"] = "none"
    else:
      del node["style.display"] # Not sure this works yet      

  def commit(self, verb, message):
    self.desktop.doc.done(verb, message)

  def commitgroup(self, groupkey, verb, message):
    self.desktop.doc.maybe_undo(groupkey, verb, message)

  def create(self, id, name, params = {}, parent = None):
    """ Create new node or replace old node with a fresh one."""
    if id in self.nodes:
      oldnode = self.nodes[id]
      for child in list(oldnode.children):
        oldnode.removeChild(child)
      oldnode.updateparams(params)
      return oldnode
    else:
      node = Node(name, self, params)
      node["id"] = id
      if parent:
        parent.appendChild(node)
      return node

  #This version allows newly created nodes to be traversed too.
  def applytoall(self, func, node = None, *args):
    """ node is the subtree root """
    if not node:
      node = self.root
    seen = [node]
    nodes = {}
    nodeindex = 0
    while nodeindex < len(seen):
      node = seen[nodeindex]
      nodeid = node.get('id')
      if nodeid is not None:
        func(node)
        nodes[nodeid] = node
        seen.extend(node.children)
      nodeindex += 1
    return nodes

  def wrapnode(self, pynode):
    items = [(k, pynode[k]) for k in pynode.keys()]
    return Node(pynode.name(), self, params = dict(items))

  def addwrapper(self, node):
    if not node.wrapper and node.parent:
      print "Wrapping node", node.get("id")
      newnode = self.wrapnode(node)
      for child in list(node.children):
        node.removeChild(child)
        newnode.appendChild(child)
      selected = node in self.selection
      parent = node.parent
      parent.removeChild(node)
      parent.appendChild(newnode)
      if selected:
        self.selector.add(newnode)
      return newnode

  def contains(self, node, subtreeroot = None):
    allnodes = self.updatenodes(subtreeroot)
    return any(node.wrapper == treenode.wrapper for treenode in allnodes.values())

  def addconstant(self, name):
    if name == "Arrow1Mend":
      params = {"id":"Arrow1Mend", "inkscape:stockid":"Arrow1Mend", "orient":"auto"}
      group = Node("svg:marker", self, params=params)
      defsnode = (self.nodes[name] for name in self.nodes.keys() if name.startswith("defs")).next()
      defsnode.appendChild(group)
      params = {"d":"M 0.0,0.0 L 5.0,-5.0 L -12.5,0.0 L 5.0,5.0 L 0.0,0.0 z ",
                "style":"fill-rule:evenodd;stroke:#000000;stroke-width:1.0pt;",
                "transform":"scale(0.4) rotate(180) translate(10,0)",
                "id":"Arrow1Mend-path"}
      path = Node("svg:path", self, params=params)
      group.appendChild(path)
      self.update()
    else:
      raise "Could not find constant '%s' to add" % name

class ObjectWatcher(pybInkscape.PYNodeObserver):
  def __init__(self, obj, func):
    self.obj = obj
    self.func = func
    
  def child_added(self, node, child, prev):
    self.func('insert', self.obj, node, child)
  def child_removed(self, node, child, prev):
    self.func('remove', self.obj, node, child)
  def child_order_changed(self,node,child,prev):
    self.func('order', self.obj, node, child, prev)
  def content_changed(self,node,old_content,new_content):
    self.func('subtree', self.obj, node)
  def attribute_changed(self,node, name, old_value, new_value):
    self.func('attribute', self.obj, node, name, old_value, new_value)

def addlistener(obj, func):
  obs = ObjectWatcher(obj, func)
  obj.addSubtreeObserver(obs)
  return obs

def removelistener(obs):
  obs.obj.removeSubtreeObserver(obs)
