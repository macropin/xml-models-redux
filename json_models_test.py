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
        json_data = AttrDict(json.loads('{"zoo":{"name":"Saskatoon Forestry Farm"}}'))
        field = CharField(path="zoo.name")
        response = field.parse(json_data)
        self.assertEquals("Saskatoon Forestry Farm",response)

    def test_int_returns_value_for_item_passed_in(self):
        json_data = AttrDict(json.loads('{"zoo":{"total_animals":30}}'))
        field = IntField(path="zoo.total_animals")
        response = field.parse(json_data)
        self.assertEquals(30,response)

    def test_bool_returns_value_for_item_passed_in(self):
        json_data = AttrDict(json.loads('{"zoo":{"has_tiger1":false}}'))
        field = BoolField(path="zoo.has_tiger")
        response = field.parse(json_data)
        self.assertFalse(response)

    def test_date_returns_value_for_item_passed_in(self):
        json_data = AttrDict(json.loads('{"zoo":{"founded_date":135}}'))
        field = DateField(path="zoo.founded_date")
        response = field.parse(json_data)
        self.assertEquals(datetime(1970,1,1,0,0,0,135000), response)

    def test_date_returns_None_for_item_not_in(self):
        json_data = AttrDict(json.loads('{"zoo":{"founded_date":null}}'))
        field = DateField(path="zoo.founded_date")
        response = field.parse(json_data)
        self.assertEquals(None, response)

    def test_can_retrieve_attribute_from_model(self):
        zoo_model = Zoos('{"zoo":{"name":"Saskatoon Forestry Farm","opened":1282360804134,"number_of_cows":33}}')
        self.assertEquals("Saskatoon Forestry Farm", zoo_model.name)
        self.assertEquals(datetime(2010,8,21,3,20,4,134000), zoo_model.opened)
        self.assertEquals(33, zoo_model.cows)

    def test_can_set_charfield_to_model(self):
        zoo_model = Zoos('{"zoo":{"name":"Saskatoon Forestry Farm"}}')
        zoo_model.name = "The Zoo"
        self.assertEquals("The Zoo", zoo_model.name)

    def test_can_set_datefield_to_model(self):
        zoo_model = Zoos('{"zoo":{"opened":123456}}')
        zoo_model.opened = datetime(1980,1,1,0,0,0,135000)
        self.assertEquals(datetime(1980,1,1,0,0,0,135000), zoo_model.opened)

    def test_can_set_None_to_datefield(self):
       zoo_model = Zoos('{"zoo":{"opened":123456}}')
       zoo_model.opened = None
       self.assertEquals(None, zoo_model.opened)

    def test_can_set_non_existed_attribute_to_model(self):
        zoo_model = Zoos('{"zoo":{"name":"Saskatoon Forestry Farm"}}')
        zoo_model.manager.name = "George"
        self.assertEquals("George", zoo_model.manager.name)

    def test_collection_returns_expected_number_of_correcty_typed_results(self):
        zoo_model = Zoos('{"zoo":{"animals":["lions","tigers","bears","oh my"]}}')
        self.assertTrue("lions" in zoo_model.animals)
        self.assertTrue("tigers" in zoo_model.animals)
        self.assertTrue("bears" in zoo_model.animals)
        self.assertTrue("oh my" in zoo_model.animals)

    def test_collection_returns_expected_number_of_integer_results(self):
        zoo_model = Zoos('{"zoo":{"animal_ages":[5,12,3,8]}}')
        self.assertTrue(5 in zoo_model.animal_ages)
        self.assertTrue(12 in zoo_model.animal_ages)
        self.assertTrue(3 in zoo_model.animal_ages)
        self.assertTrue(8 in zoo_model.animal_ages)

    def test_collection_returns_user_model_types(self):
        zoo_model = Zoos('{"zoo":{"cages":[{"environment":"Rocky","height":3,"water_feature":true},{"environment":"Ocean","height":8,"water_feature":false}]}}')
        self.assertEquals(2, len(zoo_model.cages))
        cage1 = zoo_model.cages[0]
        self.assertEquals("Rocky", cage1.environment)
        self.assertEquals(3, cage1.height)
        self.assertEquals(True, cage1.water_feature)
        cage2 = zoo_model.cages[1]
        self.assertEquals("Ocean", cage2.environment)
        self.assertEquals(8, cage2.height)
        self.assertEquals(False, cage2.water_feature)

class Cage(Model):
    environment = CharField(path="environment")
    height = IntField(path="height")
    water_feature = BoolField(path="water_feature")

class Zoos(Model):
    name = CharField(path="zoo.name")
    manager = CharField(path="zoo.manager.name")
    opened = DateField(path="zoo.opened")
    cows = IntField(path="zoo.number_of_cows")
    animals = CollectionField(CharField,path="zoo.animals")
    animal_ages = CollectionField(IntField,path="zoo.animal_ages")
    cages = CollectionField(Cage,path="zoo.cages")

if __name__=='__main__':
    unittest.main()