
import falcon

print "Ciao"

def appd(environ, start_response):
        """Simplest possible application object"""
        data = 'Hello, World!\n'
        status = '200 OK'
        response_headers = [
            ('Content-type','text/plain'),
            ('Content-Length', str(len(data)))
        ]
        start_response(status, response_headers)
        return iter([data])

class TheApp(object):
    
    def __init__(self, environ, start_response):
        """Simplest possible application object"""
        data = 'Hello, World!\n'
        status = '200 OK'
        response_headers = [
            ('Content-type','text/plain'),
            ('Content-Length', str(len(data)))
        ]
        start_response(status, response_headers)
        return iter([data])


class UpperLayerOrchestrator(object):
    
    def on_get(self, request, response, nffg_id):
        response.body = "The NF-FG is "+nffg_id
        response.status = falcon.HTTP_200
        return
    
ul = UpperLayerOrchestrator()

app = falcon.API()
app.add_route('/NF-FG', ul)
app.add_route('/NF-FG/{nffg_id}', ul)







