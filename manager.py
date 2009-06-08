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

import unittest, rest_client

class Manager(object):

    def __init__(self, client):
        self.client = client
        self._finders = {}

    def register_finder(self, attributes, url):
        key = list(attributes)
        key.sort()
        self._finders[tuple(key)] = (url, attributes)

    def _get_url(self, attributes):
        key = list(attributes)
        key.sort()
        url, ordered = self._finders[tuple(key)]
        return url, ordered

    def fetch(self, query_set):
        url, ordering = self._get_url(query_set.keys())
        values = query_set.values(ordering)
        self.client.GET(url % values)
        

class QuerySet(object):

    def __init__(self):
        self._queries = []

    def find(self, key, value):
        self._queries.append( (key,value) )
        return self

    def keys(self):
        keys = [key for key, value in self._queries]
        return tuple(keys)

    def values(self):
        values = [value for key, value in self._queries]
        return tuple(values)
        
    def values(self, ordering):
        order = list(ordering)
        dup = list(self._queries)
        vals = []
        for item in order:
            match = None
            for key, value in dup:
                if key == item:
                    vals.append(value)
                    match = (key, value)
                    break
            dup.remove(match)
        return tuple(vals)
                


class ManagerTest(unittest.TestCase):

    def test_fetch_builds_correct_url_when_matching_finder_is_registered(self):
        #setup
        class MyClient(rest_client.Client):

            def __init__(self, *params, **kw):
                rest_client.Client.__init__(self, *params, **kw)
                self.url = "fruitbat"

            def GET(self, url):
                self.url = url
        client = MyClient()
        manager = Manager(client)
        manager.register_finder( ("hello","mum"), "http://greetings/%s/person/%s")
        #execute
        qs = QuerySet().find("hello", "salutations").find("mum","Babs")
        manager.fetch(qs)
        #assert
        self.assertEquals("http://greetings/salutations/person/Babs", client.url)

    def test_fetch_builds_correct_url_when_matching_finder_keys_in_different_order(self):
        #setup
        class MyClient(rest_client.Client):

            def __init__(self, *params, **kw):
                rest_client.Client.__init__(self, *params, **kw)
                self.url = "fruitbat"

            def GET(self, url):
                self.url = url
        client = MyClient()
        manager = Manager(client)
        manager.register_finder( ("hello","mum"), "http://greetings/%s/person/%s")
        #execute
        qs = QuerySet().find("mum","Babs").find("hello", "salutations")
        manager.fetch(qs)
        #assert
        self.assertEquals("http://greetings/salutations/person/Babs", client.url)
        
    def test_fetch_builds_correct_url_when_matching_finder_has_duplicate_keys(self):
        #setup
        class MyClient(rest_client.Client):

            def __init__(self, *params, **kw):
                rest_client.Client.__init__(self, *params, **kw)
                self.url = "fruitbat"

            def GET(self, url):
                self.url = url
        client = MyClient()
        manager = Manager(client)
        manager.register_finder( ("hello","mum", "hello"), "http://greetings/%s/person/%s/welcome/%s")
        #execute
        qs = QuerySet().find("mum","Babs").find("hello", "salutations").find("hello", "greetings")
        manager.fetch(qs)
        #assert
        self.assertEquals("http://greetings/salutations/person/Babs/welcome/greetings", client.url)
        

if __name__ == '__main__':
    unittest.main()