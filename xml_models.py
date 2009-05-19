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
import xpath_twister as xpath

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
        find = xpath.find_unique(xml_doc, self.xpath, namespace)
        if find == None:
            return self._default
        return find

    
    def _parse(self, xml, namespace):
        try:
            return self.__cached_value
        except:
            self.__cached_value = self.parse(xml, namespace)
            return self.__cached_value
    
class CharField(BaseField):
    
    def parse(self, xml, namespace):
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
        matches = xpath.find_all(xml, self.xpath, namespace)

        if not BaseField in self.field_type.__bases__:
            
            results = [self.field_type(xml=match) for match in matches]
        else:
            field = self.field_type(xpath = '.')
            results = [field.parse(xpath.domify(match), namespace) for match in matches]
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
                self._dom = xpath.domify(self._xml)
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
    
class Address(Model):
    number = IntField(xpath='/address/number')
    street = CharField(xpath='/address/street')
    city = CharField(xpath='/address/city')
    foobars = Collection(CharField, xpath='/address/foobar')

    finders = { (number,): "/number/%s",
                (number, street): "/number/%s/street/%s",
                (city,): "/place/%s"
              }
        
class MyModel(Model):
    muppet_name = CharField(xpath='/root/kiddie/value')
    muppet_type = CharField(xpath='/root/kiddie/type', default='frog')
    muppet_names = Collection(CharField, xpath='/root/kiddie/value')
    muppet_ages = Collection(IntField, xpath='/root/kiddie/age')
    muppet_addresses = Collection(Address, xpath='/root/kiddie/address', order_by='number')
    
class NsModel(Model):
    namespace='urn:test:namespace'
    name=CharField(xpath='/root/name')
    age=IntField(xpath='/root/age')
    
