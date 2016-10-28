from importlib import import_module

def generate_pair(package_name="random", **kargs):
    package = import_module("compair.algorithms.pair."+package_name)
    return package.generate_pair(**kargs)
