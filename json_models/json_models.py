"""
Copyright 2009 Chris Tarttelin and Point2 Technologies

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

import json, time
from datetime import datetime

class BaseField(object):
    def __init__(self, field):
        self.path = field

    def get_nested_value(self, data,nodes):
        node = nodes.pop(0)
        if len(nodes) > 0:
            return self.get_nested_value(getattr(data,node),nodes)
        else:
            return getattr(data,node)

    def parse(self, json_data):
        nodes = self.path.split('.')
        return self.get_nested_value(json_data, nodes)

    def save(self,value):
        return value

class CharField(BaseField):
    pass

class IntField(BaseField):
    pass

class BoolField(BaseField):
    pass

class DateField(BaseField):
    def parse(self, json_data):
        microseconds_from_epoch = super(DateField, self).parse(json_data)
        return microseconds_from_epoch and datetime.utcfromtimestamp(microseconds_from_epoch / 1000.0) or None

    def save(self,value):
        return value and (long)((time.mktime(value.utctimetuple()) - time.timezone) * 1000.0 + value.microsecond / 1000.0) or None

class ModelBase(type):
    def __init__(cls, name, bases, attrs):
        fields = [field_name for field_name in attrs.keys() if isinstance(attrs[field_name], BaseField)]
        for field_name in fields:
            setattr(cls, field_name, cls._get_path(field_name, attrs[field_name]))

    def _get_path(cls, field_name, field_impl):
        return property(fget=lambda cls: cls._parse_field(field_impl),fset=lambda cls, value : cls._set_field(field_impl, value) )

class Model:
    __metaclass__ = ModelBase

    def __init__(self,json_data=None):
        self._json = AttrDict(json.loads(json_data))

    def _parse_field(self, field):
        return field.parse(self._json)

    def _set_field(self, field, value):
        value = field.save(value)
        nodes = field.path.split('.')
        self.set_nested_value(self._json,nodes, value)

    def set_nested_value(self, data, nodes, value):
        node = nodes.pop(0)
        if len(nodes) > 0:
            self.set_nested_value(getattr(data,node),nodes, value)
        else:
            setattr(data,node, value)

    def __unicode__(self):
        return json.dumps(self._json,separators=(',',':'))

    def __str__(self):
        return self.__unicode__()

class AttrDict(dict):
    def __init__(self, value=None):
        if value is None:
            pass
        elif isinstance(value,dict):
            for key in value:
                self.__setitem__(key,value[key])
        else:
            TypeError, 'expected Dict'

    def __setitem__(self,key,value):
        if isinstance(value,dict) and not isinstance(value, AttrDict):
            value = AttrDict(value)
        dict.__setitem__(self,key,value)

    place_holder = object()
    def __getitem__(self,key):
        found = self.get(key, AttrDict.place_holder)
        if found is AttrDict.place_holder:
            found = AttrDict()
            dict.__setitem__(self,key,found)
        return found

    __setattr__ = __setitem__
    __getattr__ = __getitem__