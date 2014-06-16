from functools import wraps
from flask import request

def pagination(model):
	"""
	The decorator for Restful list pagination. It takes the Model for the parameter. For
	paging information, it reads the `page` and `results_per_page` parameters from request
	object. It also injects the queried objects into the get list method. e.g.::

		class UserAPI
			@pagination(Users)
			@marshal_with(user_fields)
			def get(self, objects):
				# change objects if necessary here
				return objects

	It can work with marshal_with, but has to be called before it.
	"""
	def wrap(func):
		@wraps(func)
		def paging(*args, **kwargs):
			# pagination parameters from GET
			page = request.args.get('page', 1)
			page = int(page) # they need to be ints
			results_per_page = request.args.get('results_per_page', 30)
			results_per_page = int(results_per_page)
			# calculate offset
			offset = (page - 1) * results_per_page
			# get data
			query_results = model.query.limit(results_per_page).offset(offset).all()
			#query_results_dict = to_dict(query_results, relations_to_remove)
			# need to bundle in the pagination information into the return
			total_pages = model.query.count() / results_per_page # assumes integer div
			if total_pages < 1:
				total_pages = 1

			kwargs['objects'] = query_results
			objects = func(*args, **kwargs)

			return {
				"num_results": len(objects),
				"objects": objects,
				"page": page,
				"total_pages": total_pages
			}
		return paging
	return wrap

