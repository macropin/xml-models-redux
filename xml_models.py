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

__doc__="""Based on Django Database backed models, provides a means for mapping models 
to xml, and specifying finders that map to a remote REST service.  For parsing XML
XPath expressions, xml_models attempts to use lxml if it is available.  If not, it 
uses pyxml_xpath.  Better performance will be gained by installing lxml."""

import unittest, re, datetime, time
import xpath_twister as xpath


class NoRegisteredFinderError(Exception):
    pass

class BaseField:
    """All fields must specify an xpath as a keyword arg in their constructor.  Fields may optionally specify a 
    default value using the default keyword arg."""
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
    """Returns the single value found by the xpath expression, as a string"""
    def parse(self, xml, namespace):
        return self._fetch_by_xpath(xml, namespace)
        

class IntField(BaseField):
    """Returns the single value found by the xpath expression, as an int"""
    def parse(self, xml, namespace):
        value = self._fetch_by_xpath(xml, namespace)
        if value:
            return int(value)
        return self._default
    
class DateField(BaseField):
    """
    Returns the single value found by the xpath expression, as a datetime. By default, expects
    dates that match the ISO date format (same as Java JAXB supplies).  If a date_format keyword
    arg is supplied, that will be used instead.  Uses datetime.strptime under the hood, so the
    date_format should be defined according to strptime rules.
    
    We sometimes get dates that include a UTC offset.  We don't have a nice way to handle these, 
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
    """Returns the single value found by the xpath expression, as a float"""
    def parse(self, xml, namespace):
        value = self._fetch_by_xpath(xml, namespace)
        if value:
            return float(value)
        return self._default

class BoolField(BaseField):
    """Returns the single value found by the xpath expression, as a boolean"""
    def parse(self, xml, namespace):
        value = self._fetch_by_xpath(xml, namespace)
        if value is not None:
            if value.lower() == 'true':
                return True
            elif value.lower() == 'false':
                return False
        return self._default

class Collection(BaseField):
    """Returns a collection found by the xpath expression.  Requires a field_type to be supplied, which can
    either be a field type, e.g. IntField, which returns a collection ints, or it can be a model type
    e.g. Person may contain a collection of Address objects."""
    def __init__(self, field_type, order_by=None, **kw):
        self.field_type = field_type
        self.order_by = order_by
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
    "Meta class for declarative xml_model building"
    def __init__(cls, name, bases, attrs):
        xml_fields = [field_name for field_name in attrs.keys() if isinstance(attrs[field_name], BaseField)]
        for field_name in xml_fields:
            setattr(cls, field_name, cls._get_xpath(field_name, attrs[field_name]))
        if attrs.has_key("finders"):
            setattr(cls, "objects", XmlModelManager(cls, attrs["finders"]))
    
    def _get_xpath(cls, field_name, field_impl):
        return property(fget=lambda cls: cls._parse_field(field_impl), fset=lambda cls, value : cls._set_value(field_impl, value))
        
class XmlModelManager(object):

    def __init__(self, model, finders):
        self.model = model
        self.finders = {}
        for key in finders.keys():
            print dir(key[0])
            field_names = [field.__name__ for field in key]
            self.finders[tuple(field_names)] = finders[key]
        self.query = XmlModelQuery()

    def filter(self, **kw):        
        return XmlModelQuery(self).filter(**kw)

    def count(self):
        raise NoRegisteredFinderError("foo")

class XmlModelQuery(object):

    def __init__(self, manager):
        self.manager = manager
        self.args = {}

    def filter(self, **kw):
        for key in kw.keys():
            self.args[key] = kw[key]

    def count(self):
        return self.model(rest_client.Client().GET(self._find_query_path()).content) 

    def _find_query_path(self):
        key_tuple = tuple(self.args.keys())
        try:
            path = self.manager.finders[key_tuple]
        except KeyError:
            raise NoRegisteredFinderError(str(key_tuple))
        return path

class Model:
    __metaclass__ = ModelBase
    __doc__="""A model can be constructed with either an xml string, or an appropriate document supplied by
    the xpath_twister.domify() method.
    
    An example:
    
    class Person(xml_models.Model):
        namespace="urn:my.default.namespace"
        name = xml_models.CharField(xpath"/Person/@Name", default="John")
        nicknames = xml_models.CollectionField(CharField, xpath="/Person/Nicknames/Name")
        addresses = xml_models.CollectionField(Address, xpath="/Person/Addresses/Address")
        date_of_birth = xml_models.DateField(xpath="/Person/@DateOfBirth", date_format="%d-%m-%Y")
    """
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



