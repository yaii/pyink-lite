# Pyink lite #

Python module to be used with Inkscape python bindings.

# Running #

    PYTHONPATH=/path/to/pyink-lite /path/to/inkscape

For other operating systems, the PYTHONPATH variable needs to be set to the `pyink-lite` directory.

# UI #

This readme has more of a demo than documentation.

1. Create a path with anything (the pen tool (keyboard shortcut `b`) works fine).
2. Select this path, select `Disappear` from the drop down box above the console and click `Add`.
3. Drag the slider below the console. The selected path should fade out.
4. While the path is still selected, select `Appear` from the drop down box above the console and click `Add`.
5. Drag the slider (further). The path should fade in again.
6. Draw another path and copy its id (shown to the right of the `Set` button) to your clipboard.
7. Paste the id in the box to the left of `Add`
8. Select the first path again, select `Follow path` from the drop down menu and click `Add`.
9. Drag the slider (even further). If it doesn't go far enough, type in the console `from uielem import uidict`, press enter and then type `uidict["animadj"].upper = 10` and press enter.
10. Now select the second path and click `Add clones`.
11. Try moving the clones around. Then try editing the points in the second path. (This part might only work if all the segments are straight.)

# Library #

Here are some things to try on the console. Output appears in the terminal inkscape is ran from.

The entry point is `pyink.wrapper` which is also named `wrap` for convenience. Use `dir` to find out what functions are available.

* `wrap.xml.nodes` - a dictionary of all ids in the XML document pointing to the node with that id.
* `wrap.xml.update` - updates `wrap.xml.nodes` (this is not always automatic)
* `wrap.xml.selection` - a list of selected nodes
* `wrap.top` - top level window

Nodes act a bit like dictionaries of properties.

    wrap.xml.nodes["path3344"]["d"]
	wrap.xml.nodes["path3344"]["d"] = "M 0 0 L 0 0 100 100"
	wrap.xml.nodes["path3344"].keys()
	wrap.xml.nodes["path3344"]["style.opacity"] = 0.5
	wrap.xml.nodes["path3344"].parent
	wrap.xml.nodes["path3344"].parent.children

Some things are unfortunately not in `wrap` (yes, globals in general are bad).

    from uielem import uidict
	print uidict["editor"].get_text()
	print uidict["animadj"].upper
	uidict["animadj"].upper = 10
