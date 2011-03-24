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

import unittest, json
from datetime import datetime
from json_models import *

class JsonModelsTest(unittest.TestCase):
    def test_char_returns_value_for_item_passed_in(self):
        json_data = AttrDict(json.loads('{"kiddie":{"value":"Muppets rock"}}'))
        field = CharField(path="kiddie.value")
        response = field.parse(json_data)
        self.assertEquals('Muppets rock', response)
        
    def test_int_returns_value_for_item_passed_in(self):
        json_data = AttrDict(json.loads('{"kiddie":{"value":30}}'))
        field = IntField(path="kiddie.value")
        response = field.parse(json_data)
        self.assertEquals(30,response)

    def test_int_field_raises_exception_when_non_int_value_is_parsed(self):
        json_data = AttrDict(json.loads('{"kiddie":{"value":"NaN"}}'))
        field = IntField(path="kiddie.value")
        try:
            response = field.parse(json_data)
            self.fail('Should have raised an exception')
        except:
            pass
            # Exception raised, all is right with the world

    def test_date_returns_value_for_item_passed_in(self):
        json_data = AttrDict(json.loads('{"kiddie":{"value":135}}'))
        field = DateField(path="kiddie.value")
        response = field.parse(json_data)
        self.assertEquals(datetime(1970,1,1,0,0,0,135000), response)

    def test_date_returns_None_for_item_not_in(self):
        json_data = AttrDict(json.loads('{"kiddie":{"value":null}}'))
        field = DateField(path="kiddie.value")
        response = field.parse(json_data)
        self.assertEquals(None, response)

    def test_bool_returns_false_for_item_passed_in_when_false(self):
        json_data = AttrDict(json.loads('{"kiddie":{"value":false}}'))
        field = BoolField(path="kiddie.value")
        response = field.parse(json_data)
        self.assertFalse(response)

    def test_bool_returns_true_for_item_passed_in_when_true(self):
        json_data = AttrDict(json.loads('{"kiddie":{"value":false}}'))
        field = BoolField(path="kiddie.value")
        response = field.parse(json_data)
        self.assertFalse(response)


    def test_collection_returns_expected_number_of_correcty_typed_results(self):
        my_model = MyModel('{"kiddie":{"names": ["Rowlf","Kermit","Ms.Piggy"]}}')
        self.assertTrue('Rowlf' in my_model.muppet_names)
        self.assertTrue('Kermit' in my_model.muppet_names)
        self.assertTrue('Ms.Piggy' in my_model.muppet_names)

    def test_collection_returns_expected_number_of_integer_results(self):
        my_model = MyModel('{"kiddie":{"ages":[5,12,3,8]}}')
        self.assertTrue(5 in my_model.muppet_ages)
        self.assertTrue(12 in my_model.muppet_ages)
        self.assertTrue(3 in my_model.muppet_ages)
        self.assertTrue(8 in my_model.muppet_ages)

    def test_collection_returns_user_model_types(self):
        my_model = MyModel('{"kiddie":{ "address": [{"number" :10,"street": "1st Ave. South", "city": "MuppetVille", "foobars" : ["foo","bar"]},{"number": 5, "street": "Mockingbird Lane", "city": "Bedrock"}]}}')
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
        my_model = MyModel('{"kiddie":{ "address": [{"number" :10,"street": "1st Ave. South", "city": "MuppetVille", "foobars" : ["foo","bar"]},{"number": 5, "street": "Mockingbird Lane", "city": "Bedrock"}]}}')
        self.assertEquals(2,len(my_model.muppet_addresses))
        address1 = my_model.muppet_addresses[0]
        self.assertEquals(5, address1.number)
        address2 = my_model.muppet_addresses[1]
        self.assertEquals(10, address2.number)

    def test_collection_empty_collection_returned_when_json_not_found(self):
        my_model = MyModel('{"kiddie":{ "address": [{"number" :10,"street": "1st Ave. South", "city": "MuppetVille"},{"number": 5, "street": "Mockingbird Lane", "city": "Bedrock"}]}}')
        self.assertEquals([], my_model.muppet_addresses[0].foobars)
        
    def test_can_set_charfield_to_model(self):
        my_model = MyModel('{"kiddie":{"muppet_name":"Gonzo"}}')
        my_model.muppet_name = "Kermit"
        self.assertEquals("Kermit", my_model.muppet_name)

    def test_can_set_datefield_to_model(self):
        my_model = MyModel('{"kiddie":{"opened":123456}}')
        my_model.opened = datetime(1980,1,1,0,0,0,135000)
        self.assertEquals(datetime(1980,1,1,0,0,0,135000), my_model.opened)

    def test_can_set_None_to_datefield(self):
        my_model = MyModel('{"kiddie":{"opened":123456}}')
        my_model.opened = None
        self.assertEquals(None, my_model.opened)


    def test_collection_fields_can_be_appended_to(self):
        my_model = MyModel('{"kiddie":{"names": ["Kermit"]}}')
        my_model.muppet_names.append("Fozzie")
        self.assertTrue('Kermit' in my_model.muppet_names)
        self.assertTrue('Fozzie' in my_model.muppet_names)


class Address(Model):
    number = IntField(path='number')
    street = CharField(path='street')
    city = CharField(path='city')
    foobars = Collection(CharField, path='foobars')

class MyModel(Model):
    muppet_name = CharField(path='kiddie.value')
    muppet_type = CharField(path='kiddie.type')
    muppet_names = Collection(CharField, path='kiddie.names')
    muppet_ages = Collection(IntField, path='kiddie.ages')
    muppet_addresses = Collection(Address, path='kiddie.address', order_by='number')

if __name__=='__main__':
    unittest.main()