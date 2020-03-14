from werkzeug.wrappers import Request
def wsgi_app(app, environ, start_response):
	request=Request(environ)
	reponse=app.dispatch_request(request)
	return reponse(environ,start_response)