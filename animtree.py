""" An animation tree (Animator class). Each vertex of the tree is a simple animation (Animation class) which moves some parameter of an object from one value to another.

The root starts at t=0. Every other animation starts when their parent is finished.

The tree could be a DAG instead (so an animation starts when all predecessors are finished) but a tree seems easier to think about.

Any sequence of animations with "start with previous" and "start after previous" timing conditions can be represented with the animation tree.
"""
import time

DEBUG = False

def out(method):
    def outmethod(t):
        return 1-method(1-t)
    return outmethod

def constant(t):
    return 1*(t >= 1)

def linear(t):
    return t

def cubic(t):
    return t*t*t

class Timing(object):
    def __init__(self, duration=500.0, delay=0.0, delaytiming="after previous", interpolator=out(cubic)):
        self.duration = duration
        self.delay = delay
        self.delaytiming = delaytiming
        self.interpolator = interpolator

    def simended(self, t):
        t = min(self.duration, t - self.delay)
        return (t==self.duration)

    def diff(self, t):
        """ Used by simulate(), ignores startt. """
        newt = (t - self.duration - self.delay)
        t = min(self.duration, t - self.delay)
        if self.duration == 0:
            return 1*(t >= 0), (t >= 0), newt
        t = max(0, t)
        ratio = self.interpolator(t/self.duration)
        return ratio, (t==self.duration), newt

class Evaluator(object):
    def __init__(self, final, init=None, finaltype="absolute"):
        self.init = init
        self.final = final
        self.finaltype = finaltype

    def value(self, ratio):
        if self.finaltype == "relative":
            return self.final * ratio + self.init
        else:
            return (self.final - self.init) * ratio + self.init

    def start(self, value):
        if self.init is None:
            if self.finaltype == "absolute":
                #Should not alter this value...but this is always None by the above condition check.
                self.originit = self.init
                self.init = value

class Animation(object):
    def __init__(self, target, param, evaluator, timing = None, **kwargs):
        self.param = param
        self.target = target
        if evaluator.__class__.__name__ != "Evaluator":
            self.evaluator = Evaluator(evaluator)
        else:
            self.evaluator = evaluator
        if not timing:
            self.timing = Timing()
        else:
            self.timing = timing
        self.children = []
        self.parent = None

    def add(self,anim):
        self.children.append(anim)
        anim.parent = self

    def getval(self):
        return getattr(self.target, self.param)

    def getrawval(self):
        return getattr(self.target, self.param)

    def setval(self, value):
        setattr(self.target, self.param, value)

    value = property(getval, setval)

    def simulate(self, t):
        if self.target is None:
            ratio, ended, newt = self.timing.diff(t)
            return ended, newt, None
        self.evaluator.start(self.value)
        ratio, ended, newt = self.timing.diff(t)
        alteration = [self.target, self.param, self.getrawval()]
        # This seemed wrong regardless. But we also need to take into account finaltype = "relative"...
        self.value = self.evaluator.value(ratio)
        return ended, newt, alteration

    def printdata(self):
        print self.printdatas()

    def printdatas(self):
        l = [self.target, self.param, self.evaluator.final]
        if self.parent:
            l += [self.parent.target]
        else:
            l += [self.parent]
        return l

class WDictAnimation(Animation):
    def __init__(self, *args, **kwargs):
        Animation.__init__(self, *args, **kwargs)
        self.gettransf = kwargs.get("gettransf", None)
        self.settransf = kwargs.get("settransf", None)

    def getval(self):
        value = self.target[self.param]
        if self.gettransf:
            return self.gettransf(value)
        else:
            return value

    def setval(self, value):
        if self.settransf:
            value = self.settransf(value)
        self.target[self.param] = value

    value = property(getval, setval)

class Animator:
    def __init__(self):
        self.newroot()

    def simulate(self, finalt):
        """
        Assumes no animation has started (not even the root).
        Generate the position of all objects at time t.
        """
        altered = []#{}
        queue = [(finalt, self.root)]
        while queue:
            t, anim = queue.pop(0)
            ended, newt, alteration = anim.simulate(t)
            if alteration:
                target, param, value = alteration
                altered.append(alteration)
            if ended:
                for child in anim.children:
                    queue.append((newt, child))
        return altered

    def reset(self, altered):
        for target, param, oldval in reversed(altered):
            if param.startswith("["):
                key = param[1:-1]
                #With wrappers, we really want to call anim's function now...
                target[key] = oldval
            else:
                setattr(target, param, oldval)

    def addbasic(self, anim):
        #backwards compatibility
        if anim.timing.delaytiming == "after previous":
            self.maxanim.add(anim)
            self.maxanim = anim
        elif anim.timing.delaytiming == "with previous":
            if self.maxanim == self.root:
                self.maxanim.add(anim)
            else:
                self.maxanim.parent.add(anim)
            self.maxanim = anim

    def printanimtree(self):
        for depth, s in self.printanimtrees():
            print depth*" ", s

    def printanimtrees(self):
        queue = [(0, self.root)]
        while queue:
            depth, anim = queue.pop()
            yield (depth, anim.printdatas())
            queue.extend([(depth+1, x) for x in anim.children])
            if depth>100:
                raise Exception("Maximum printing depth of 100 exceeded!")

    def newroot(self):
        self.root = Animation(None, None, None, timing = Timing(duration=0))
        self.maxanim = self.root
