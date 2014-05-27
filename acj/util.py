from flask_restless import helpers as restless_helper

# Looks for 2 params in the request to determine how to paginate results.
# page: the page we're supposed to retrieve, defaults to 1 if not given
# results_per_page: the number of results on each page, defaults to 30 if not given
def to_dict_paginated(relations_to_remove, request, query):
	# pagination parameters from GET
	page = request.args.get('page', 1)
	page = int(page) # they need to be ints
	results_per_page = request.args.get('results_per_page', 30)
	results_per_page = int(results_per_page)
	# calculate offset
	offset = (page - 1) * results_per_page
	# get data
	query_results = query.limit(results_per_page).offset(offset).all()
	query_results_dict = to_dict(query_results, relations_to_remove)
	# need to bundle in the pagination information into the return
	total_pages = query.count() / results_per_page # assumes integer div
	if total_pages < 1: total_pages = 1
	ret = {
		"num_results": len(query_results_dict),
		"objects": query_results_dict,
		"page": page,
		"total_pages": total_pages
	}
	return ret

# Use Flask-Restless to convert sqlalchemy results into an array or dict that ca be fed to Flask's
# jsonify() method.
#
# objects - can be a list or a single instance of sqlalchemy model objects to be converted, can be a list or a single object
# relations_to_remove - model relations that should be ignored as part of the resulting dict
def to_dict(objects, relations_to_remove=[]):
	single_instance = True
	if type(objects) is list:
		if not objects: # empty list
			return []
		single_instance = False
	else:
		# treat single instance objects like a multi-instance to save some code
		objects = [objects]

	# get all of the related models that can be pulled
	relations = restless_helper.get_relations(objects[0].__class__)
	# conversion required for restless helper's to_dict method
	relations = dict((r, {}) for r in relations)
	# remove the related models that we don't want to pull
	for relation in relations_to_remove:
		if relation in relations:
			del relations[relation]
	# perform conversion
	ret = []
	for object in objects:
		ret.append(restless_helper.to_dict(object, deep=relations))

	if single_instance:
		return ret[0]
	else:
		return ret

