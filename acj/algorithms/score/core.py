from importlib import import_module

def calculate_score(package_name="true_skill_rating", **kargs):
    package = import_module("acj.algorithms.score."+package_name)
    return package.calculate_score(**kargs)

def calculate_score_1vs1(package_name="true_skill_rating", **kargs):
    package = import_module("acj.algorithms.score."+package_name)
    return package.calculate_score_1vs1(**kargs)