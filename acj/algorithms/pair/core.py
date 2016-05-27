from importlib import import_module

def generate_pair(package_name="adaptive", **kargs):
    package = import_module("acj.algorithms.pair."+package_name)
    return package.generate_pair(**kargs)
