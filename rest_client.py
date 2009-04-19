"""
The FreeBSD Copyright

Copyright 1994-2009 The FreeBSD Project. All rights reserved.

Redistribution and use in source and binary forms, with or without modification, are
permitted provided that the following conditions are met:

Redistributions of source code must retain the above copyright notice, this list of
conditions and the following disclaimer.

Redistributions in binary form must reproduce the above copyright notice, this list
of conditions and the following disclaimer in the documentation and/or other materials
provided with the distribution.

THIS SOFTWARE IS PROVIDED BY THE FREEBSD PROJECT ``AS IS'' AND ANY EXPRESS OR IMPLIED
WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND
FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE FREEBSD PROJECT OR
CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF
ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

The views and conclusions contained in the software and documentation are those of the
authors and should not be interpreted as representing official policies, either expressed
or implied, of the FreeBSD Project.
"""

import urllib2

opener = urllib2.OpenerDirector()
opener.add_handler(urllib2.HTTPHandler())


""" Contributors: Chris Tarttelin and Cam McHugh
    Point2 Technologies Ltd 
"""

class Client(object):
    
    def GET(self, url, headers={}):
        return self._make_request(url, 'GET', None, headers)
        
    def PUT(self, url, payload=None, headers={}):
        return self._make_request(url, 'PUT', payload, headers)
        
    def POST(self, url, payload=None, headers={}):
        return self._make_request(url, 'POST', payload, headers)
        
    def DELETE(self, url, payload=None, headers={}):
            return self._make_request(url, 'DELETE', payload, headers)
        
    def _make_request(self, url, method, payload, headers):
        request = urllib2.Request(url, headers=headers, data=payload)
        request.get_method = lambda: method
        response = opener.open(request)
        response_code = getattr(response, 'code', -1)
        if response_code == -1:
            raise urllib2.HTTPError(url, response_code, "Error accessing external resource", None, None)
        return Response(url, response_code, response.headers, response)
        
class Response(object):
    
    def __init__(self, url, response_code, headers, content):
        self.url = url
        self.response_code = response_code
        self.headers = dict(headers)
        self.content = content.read()
        
    def expect(self, response_code):
        if self.response_code != response_code:
            raise urllib2.HTTPError(self.url, self.response_code, "Expected response code: %s, but was %s" % (response_code, self.response_code), None, None)
        
    def __getattr__(self, attr_name):
        if self.headers.has_key(attr_name):
            return self.headers[attr_name]
        raise AttributeError
    
    def __str__(self):
        return self.content