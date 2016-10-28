from importlib import import_module

def calculate_score(package_name="elo_rating", **kargs):
    package = import_module("compair.algorithms.score."+package_name)
    return package.calculate_score(**kargs)

def calculate_score_1vs1(package_name="elo_rating", **kargs):
    package = import_module("compair.algorithms.score."+package_name)
    return package.calculate_score_1vs1(**kargs)