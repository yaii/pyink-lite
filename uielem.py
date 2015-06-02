uidict = {}

def ui(elem, *args, **kwargs):
    name = kwargs.pop("name", None)
    children = kwargs.pop("children", [])
    child = kwargs.pop("child", None)
    items = kwargs.pop("items", [])
    show = kwargs.pop("show", False)
    signals = [(k, v) for k, v in kwargs.items() if k.startswith("on_")]
    kwargs = dict((k, v) for k, v in kwargs.items() if not k.startswith("on_"))
    to_set = [(k, v) for k, v in kwargs.items() if k.startswith("set_")]
    kwargs = dict((k, v) for k, v in kwargs.items() if not k.startswith("set_"))
    newelem = elem(*args, **kwargs)
    for k, v in signals:
        newelem.connect(k[3:].replace("_", "-"), *v)
    for k, v in to_set:
        getattr(newelem, k)(*v)
    for item in items:
        newelem.append_text(item)
    if child != None:
        newelem.add(child)
    for child in children:
        newelem.pack_start(child, expand = False, fill = False)
    if show:
        newelem.show()
    if name:
        uidict[name] = newelem
    return newelem
