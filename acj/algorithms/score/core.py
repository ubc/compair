from importlib import import_module

def calculate_score(package_name="comparative_judgement", **kargs):
    package = import_module("acj.algorithms.score."+package_name)
    return package.calculate_score(**kargs)