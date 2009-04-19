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

import unittest, re, datetime, time
from lxml import etree, objectify
import lxml

""" Contributors: Chris Tarttelin and Cam McHugh
    Point2 Technologies Ltd 
"""

class BaseField:
    
    def __init__(self, **kw):
        if not kw.has_key('xpath'):
            raise Exception('No XPath supplied for xml field')
        self.xpath = kw['xpath']
        self._default = kw.pop('default', None)
            
    
    def _fetch_by_xpath(self, xml_doc, namespace):
        if namespace:
            find = etree.XPath(self.get_xpath(namespace), namespaces={'x': namespace})
        else:
            find = etree.XPath(self.get_xpath(namespace))
        matches = find(xml_doc)
        if len(matches) == 1:
            matched = matches[0]
            if type(matched) == type(''):
                return unicode(matched).strip()
            if isinstance(matched, etree._ElementStringResult):
                return str(matched)
            if matched or matched == False:
                return unicode(matched.text).strip()
            if isinstance(matched, etree._Element):
                if matched.text is not None:
                    return str(matched.text)
        if len(matches) > 1:
            print matches
        return self._default
        
    def get_xpath(self, namespace):
        if namespace:
            xpath_list = self.xpath.split('/')
            xpath_with_ns = ""
            for element in xpath_list:
                if not element.startswith('@') and not element == '' :
                    xpath_with_ns += "/x:" + element
                elif element == '':
                    pass
                else:
                    xpath_with_ns += "/" + element
            return xpath_with_ns
        else:
            return self.xpath
    
    def _parse(self, xml, namespace):
        try:
            return self.__cached_value
        except:
            self.__cached_value = self.parse(xml, namespace)
            return self.__cached_value
    
class CharField(BaseField):
    
    def parse(self, xml, namespace, fetch_element_name=False):
        return self._fetch_by_xpath(xml, namespace)
        

class IntField(BaseField):
        
    def parse(self, xml, namespace):
        value = self._fetch_by_xpath(xml, namespace)
        if value:
            return int(value)
        return self._default
    
class DateField(BaseField):
    """We sometimes get dates that include a UTC offset.  We don't have a nice way to handle these, 
    so for now we are going to strip the offset and throw it away"""
    match_utcoffset = re.compile(r"(^.*?)[+|-]\d{2}:\d{2}$")
    
    def __init__(self, date_format="%Y-%m-%dT%H:%M:%S", **kw):
        BaseField.__init__(self,**kw)
        self.date_format = date_format
        
    def parse(self, xml, namespace):
        value = self._fetch_by_xpath(xml, namespace)
        if value:
            utc_stripped = self.match_utcoffset.findall(value)
            if len(utc_stripped) == 1:
                value = utc_stripped[0]
            try:
                return datetime.datetime.strptime(value, self.date_format)
            except ValueError, msg:
                if "%S" in self.date_format:
                    msg = str(msg)
                    rematch = re.match(r"unconverted data remains:"
                        " \.([0-9]{1,6})$", msg)
                    if rematch is not None:
                        frac = "." + rematch.group(1)
                        value = value[:-len(frac)]
                        value = datetime.datetime(*time.strptime(value, self.date_format)[0:6])
                        microsecond = int(float(frac)*1e6)
                        return value.replace(microsecond=microsecond)
                    else:
                        rematch = re.match(r"unconverted data remains:"
                            " \,([0-9]{3,3})$", msg)
                        if rematch is not None:
                            frac = "." + rematch.group(1)
                            value = value[:-len(frac)]
                            value = datetime.datetime(*time.strptime(value, self.date_format)[0:6])
                            microsecond = int(float(frac)*1e6)
                            return value.replace(microsecond=microsecond)
                raise
        return self._default
        
class FloatField(BaseField):

    def parse(self, xml, namespace):
        value = self._fetch_by_xpath(xml, namespace)
        if value:
            return float(value)
        return self._default

class BoolField(BaseField):
    
    def parse(self, xml, namespace):
        value = self._fetch_by_xpath(xml, namespace)
        if value is not None:
            if value.lower() == 'true':
                return True
            elif value.lower() == 'false':
                return False
        return self._default

class Collection(BaseField):
    
    def __init__(self, field_type, element_name=False, order_by=None, **kw):
        self.field_type = field_type
        self.order_by = order_by
        self.element_name = element_name
        BaseField.__init__(self,**kw)
        
    def parse(self, xml, namespace):
        if namespace:
            find = etree.XPath(self.get_xpath(namespace), namespaces={'x': namespace})
        else:
            find = etree.XPath(self.get_xpath(namespace))
        matches = find(xml)
        if not BaseField in self.field_type.__bases__:
            results = [self.field_type(xml=etree.tostring(match)) for match in matches]
        else:
            field = self.field_type(xpath = '.')
            results = [field.parse(match, namespace) for match in matches]
        # this is a hack to get the elemen
        if self.element_name:
            element_names = [etree.XPath("local-name(%s[text()='%s'])" % (self.get_xpath(namespace), value ))(xml) for value in results]
            results = element_names
        if self.order_by:
            results.sort(lambda a,b : cmp(getattr(a, self.order_by), getattr(b, self.order_by)))
        return results
    
CollectionField = Collection

class ModelBase(type):

    def __init__(cls, name, bases, attrs):
        xml_fields = [field_name for field_name in attrs.keys() if isinstance(attrs[field_name], BaseField)]
        for field_name in xml_fields:
            setattr(cls, field_name, cls._get_xpath(field_name, attrs[field_name]))
    
    def _get_xpath(cls, field_name, field_impl):
        return property(fget=lambda cls: cls._parse_field(field_impl), fset=lambda cls, value : cls._set_value(field_impl, value))
        

class Model:
    __metaclass__ = ModelBase

    def __init__(self, xml=None, dom=None):
        self._xml = xml
        self._dom = dom
        self._cache = {}

    def _get_xml(self):
        if self._dom is None:
            try :
                self._dom = lxml.objectify.fromstring(self._xml)
            except Exception, e:
                print self._xml
                raise e
        return self._dom
        
    def _set_value(self, field, value):
        self._cache[field] = value
        
    def _parse_field(self, field):
        if not self._cache.has_key(field):
            namespace = None
            if hasattr(self, 'namespace'):
                namespace = self.namespace
            self._cache[field] = field.parse(self._get_xml(), namespace)
        return self._cache[field]


class XmlModelsTest(unittest.TestCase):
    
    def test_char_field_returns_xpathed_value_for_the_node_passed_in(self):
        xml_string = '<root><child><value>Muppets rock</value></child></root>'
        xml = lxml.objectify.fromstring(xml_string)
        field = CharField(xpath='/root/child/value')
        response = field.parse(xml, None)
        self.assertEquals('Muppets rock', response) 
        
    def test_int_field_returns_xpathed_value_for_the_node_passed_in(self):
        xml_string = '<root><child><value>123</value></child></root>'
        xml = lxml.objectify.fromstring(xml_string)
        field = IntField(xpath='/root/child/value')
        response = field.parse(xml, None)
        self.assertEquals(123, response)
        
    def test_int_field_raises_exception_when_non_int_value_is_parsed(self):
        xml_string = '<root><child><value>NaN</value></child></root>'
        xml = lxml.objectify.fromstring(xml_string)
        field = IntField(xpath='/root/child/value')
        try:
            response = field.parse(xml, None)
            self.fail('Should have raised an exception')
        except:
            pass
            # Exception raised, all is right with the world
    
    def test_date_field_returns_xpathed_value_for_the_node_passed_in(self):
        xml_string = '<root><child><value>2008-06-21T10:36:12</value></child></root>'
        xml = lxml.objectify.fromstring(xml_string)
        field = DateField(xpath='/root/child/value')
        response = field.parse(xml,None)
        date = datetime.datetime(2008,06,21,10,36,12)
        self.assertEquals(date, response)
            
    def test_date_field_strips_utc_offset_from_xpathed_value_for_the_node_passed_in(self):
        xml_string = '<root><child><value>2008-06-21T10:36:12.280-06:00</value></child></root>'
        xml = lxml.objectify.fromstring(xml_string)
        field = DateField(xpath='/root/child/value')
        response = field.parse(xml,None)
        date = datetime.datetime(2008,06,21,10,36,12, 280000)
        self.assertEquals(date, response)
        
    def test_date_field_returns_none_when_xpathed_value_for_the_node_is_none(self):
        xml_string = '<root><child><value></value></child></root>'
        xml = lxml.objectify.fromstring(xml_string)
        field = DateField(xpath='/root/child/value')
        response = field.parse(xml, None)
        self.assertEquals(None, response)
    
    def test_bool_field_returns_false_when_xpathed_value_for_the_node_is_false(self):
        xml_string = '<root><child><value>false</value></child></root>'
        xml = lxml.objectify.fromstring(xml_string)
        field = BoolField(xpath='/root/child/value')
        response = field.parse(xml, None)
        self.assertEquals(False, response)

    def test_bool_field_returns_true_when_xpathed_value_for_the_node_is_true(self):
        xml_string = '<root><child><value>true</value></child></root>'
        xml = lxml.objectify.fromstring(xml_string)
        field = BoolField(xpath='/root/child/value')
        response = field.parse(xml, None)
        self.assertEquals(True, response)
    
    def test_can_retrieve_attribute_value_from_xml_model(self):
        my_model = MyModel('<root><child><value>Rowlf</value></child></root>')
        self.assertEquals('Rowlf', my_model.muppet_name)
        
    def test_returns_none_if_non_required_attribute_not_in_xml_and_no_default(self):
        my_model = MyModel('<root><child><valuefoo>Rolf</valuefoo></child></root>')
        self.assertEquals(None, my_model.muppet_name)
    
    def test_returns_default_if_non_required_attribute_not_in_xml_and_default_specified(self):
        my_model = MyModel('<root><child><value>Rowlf</value></child></root>')
        self.assertEquals('frog', my_model.muppet_type)
        
    def test_collection_returns_expected_number_of_correcty_typed_results(self):
        my_model = MyModel('<root><child><value>Rowlf</value><value>Kermit</value><value>Ms.Piggy</value></child></root>')
        self.assertTrue('Rowlf' in my_model.muppet_names)
        self.assertTrue('Kermit' in my_model.muppet_names)
        self.assertTrue('Ms.Piggy' in my_model.muppet_names)    
        
    def test_collection_returns_expected_number_of_integer_results(self):
        my_model = MyModel('<root><child><age>10</age><age>5</age><age>7</age></child></root>')
        self.assertTrue(5 in my_model.muppet_ages)
        self.assertTrue(7 in my_model.muppet_ages)
        self.assertTrue(10 in my_model.muppet_ages)
        
    def test_collection_returns_user_model_types(self):
        my_model = MyModel('<root><child><address><number>10</number><street>1st Ave. South</street><city>MuppetVille</city><foobar>foo</foobar><foobar>bar</foobar></address><address><number>5</number><street>Mockingbird Lane</street><city>Bedrock</city></address></child></root>')
        self.assertEquals(2,len(my_model.muppet_addresses))
        address1 = my_model.muppet_addresses[0]
        self.assertEquals(5, address1.number)
        self.assertEquals('Mockingbird Lane', address1.street)
        self.assertEquals('Bedrock', address1.city)
        address2 = my_model.muppet_addresses[1]
        self.assertEquals(10, address2.number)
        self.assertEquals('1st Ave. South', address2.street)
        self.assertEquals('MuppetVille', address2.city)
        self.assertEquals('foo', address2.foobars[0])
        self.assertEquals('bar', address2.foobars[1])
        
    def test_collection_orders_by_supplied_attribute_of_user_model_types(self):
        my_model = MyModel('<root><child><address><number>10</number><street>1st Ave. South</street><city>MuppetVille</city><foobar>foo</foobar><foobar>bar</foobar></address><address><number>5</number><street>Mockingbird Lane</street><city>Bedrock</city></address></child></root>')
        self.assertEquals(2,len(my_model.muppet_addresses))
        address1 = my_model.muppet_addresses[0]
        self.assertEquals(5, address1.number)
        address2 = my_model.muppet_addresses[1]
        self.assertEquals(10, address2.number)
        
    def test_collection_empty_collection_returned_when_xml_not_found(self):
        my_model = MyModel('<root><child><address><number>10</number><street>1st Ave. South</street><city>MuppetVille</city></address><address><number>5</number><street>Mockingbird Lane</street><city>Bedrock</city></address></child></root>')
        self.assertEquals([], my_model.muppet_addresses[0].foobars)
        
    def test_use_a_default_namespace(self):
        nsModel = NsModel("<root xmlns='urn:test:namespace'><name>Finbar</name><age>47</age></root>")
        self.assertEquals('Finbar', nsModel.name)
        self.assertEquals(47, nsModel.age)
        
    def test_model_fields_are_settable(self):
        my_model = MyModel('<root><child><value>Gonzo</value><address><number>10</number><street>1st Ave. South</street><city>MuppetVille</city></address><address><number>5</number><street>Mockingbird Lane</street><city>Bedrock</city></address></child></root>')
        my_model.muppet_name = 'Fozzie'
        self.assertEquals('Fozzie', my_model.muppet_name)
        
    def test_collection_fields_can_be_appended_to(self):
        my_model = MyModel('<root><child><value>Gonzo</value><address><number>10</number><street>1st Ave. South</street><city>MuppetVille</city></address><address><number>5</number><street>Mockingbird Lane</street><city>Bedrock</city></address></child></root>')
        my_model.muppet_names.append('Fozzie')
        self.assertTrue('Fozzie' in my_model.muppet_names)
        self.assertTrue('Gonzo' in my_model.muppet_names)
    
class Address(Model):
    number = IntField(xpath='/address/number')
    street = CharField(xpath='/address/street')
    city = CharField(xpath='/address/city')
    foobars = Collection(CharField, xpath='/address/foobar')
        
class MyModel(Model):
    muppet_name = CharField(xpath='/root/child/value')
    muppet_type = CharField(xpath='/root/child/type', default='frog')
    muppet_names = Collection(CharField, xpath='/root/child/value')
    muppet_ages = Collection(IntField, xpath='/root/child/age')
    muppet_addresses = Collection(Address, xpath='/root/child/address', order_by='number')
    
class NsModel(Model):
    namespace='urn:test:namespace'
    name=CharField(xpath='/root/name')
    age=IntField(xpath='/root/age')
    
if __name__=='__main__':
    unittest.main()