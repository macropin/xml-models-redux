import BaseHTTPServer, cgi, threading, re
import unittest, urllib, urllib2, time
from unittest import TestCase


class StubServer(object):

    _expectations = []
    
    def __init__(self, port):
        self.port = port

    def run(self):
        server_address = ('localhost', self.port)
        self.httpd = BaseHTTPServer.HTTPServer(server_address, StubResponse)
        t = threading.Thread(target=self._run)
        t.start()
        time.sleep(0.5)
        
    def stop(self):
        self.httpd.server_close()

    def _run(self, ):
        try:
            self.httpd.serve_forever()
        except:
            pass

    def verify(self):
        pass
        # check each expectation was called

    def expect(self, method="GET", url="^UrlRegExpMather$", data=None, data_capture={}, file_content=None):
        expected = Expectation(method, url, data, data_capture)
        self._expectations.append(expected)
        return expected

class Expectation(object):
    def __init__(self, method, url, data, data_capture):
        self.method = method
        self.url = url
        self.data = data
        self.data_capture = data_capture
        
    def and_return(self, mime_type="text/html", reply_code=200, content="", file_content=None):
        if file_content:
            f = open(file_content, "r")
            content = f.read()
            f.close()
        self.response = (reply_code, mime_type, content)

class StubResponse(BaseHTTPServer.BaseHTTPRequestHandler):

    def __init__(self, request, clientaddress, parent):
        self.expected = StubServer._expectations
        BaseHTTPServer.BaseHTTPRequestHandler.__init__(self, request, clientaddress, parent)

    def _get_data(self):
        max_chunk_size = 10*1024*1024
        if not self.headers.has_key("content-length"):
            return ""
        size_remaining = int(self.headers["content-length"])
        L = []
        while size_remaining:
            chunk_size = min(size_remaining, max_chunk_size)
            L.append(self.rfile.read(chunk_size))
            size_remaining -= len(L[-1])
        return ''.join(L)

    def handle_one_request(self):
        """Handle a single HTTP request.

        You normally don't need to override this method; see the class
        __doc__ string for information on how to handle specific HTTP
        commands such as GET and POST.
S
        """
        self.raw_requestline = self.rfile.readline()
        if not self.raw_requestline:
            self.close_connection = 1
            return
        if not self.parse_request(): # An error code has been sent, just exit
            return
        method = self.command
        for exp in self.expected:
            if exp.method == method and re.search(exp.url, self.path):
                self.send_response(exp.response[0], "Python")
                self.send_header("Content-Type", exp.response[1])
                self.end_headers()
                self.wfile.write(exp.response[2])
                exp.data_capture["body"] = self._get_data()
                break
        self.wfile.flush()


class WebTest(TestCase):
    
    def setUp(self):
        self.server = StubServer(8998)
        self.server.run()
        
    def tearDown(self):
        self.server.stop()
        self.server.verify()
        
    def _make_request(self, url, method="GET", payload="", headers={}):
        self.opener = urllib2.OpenerDirector()
        self.opener.add_handler(urllib2.HTTPHandler())
        request = urllib2.Request(url, headers=headers, data=payload)
        request.get_method = lambda: method
        response = self.opener.open(request)
        response_code = getattr(response, 'code', -1)
        return (response, response_code)
    
    def test_get_with_file_call(self):
        f = open('data.txt', 'w')
        f.write("test file")
        f.close()
        self.server.expect(method="GET", url="/address/\d+$").and_return(mime_type="text/xml", file_content="./data.txt")
        response, response_code = self._make_request("http://localhost:8998/address/25", method="GET")
        expected = open("./data.txt", "r").read()
        try:
            self.assertEquals(expected, response.read())
        finally:
            response.close()

    def test_put_with_capture(self):
        capture = {}
        self.server.expect(method="PUT", url="/address/\d+$", data_capture=capture).and_return(reply_code=201)
        f, reply_code = self._make_request("http://localhost:8998/address/45", method="PUT", payload=str({"hello": "world", "hi": "mum"}))
        try:
            self.assertEquals("", f.read())
            captured = eval(capture["body"])
            self.assertEquals("world", captured["hello"])
            self.assertEquals("mum", captured["hi"])
            self.assertEquals(201, reply_code)
        finally:
            f.close()

    def test_post_with_data_and_no_body_response(self):
        self.server.expect(method="POST", url="address/\d+/inhabitant", data='<inhabitant name="Chris"/>').and_return(reply_code=204)
        f, reply_code = self._make_request("http://localhost:8998/address/45/inhabitant", method="POST", payload='<inhabitant name="Chris"/>')
        self.assertEquals(204, reply_code)
        
    def test_get_with_data(self):
        self.server.expect(method="GET", url="/monitor/server_status$").and_return(content="<html><body>Server is up</body></html>", mime_type="text/html")
        f, reply_code = self._make_request("http://localhost:8998/monitor/server_status", method="GET")
        try:
            self.assertTrue("Server is up" in f.read())
            self.assertEquals(200, reply_code)
        finally:
            f.close()

if __name__=='__main__':
        unittest.main()