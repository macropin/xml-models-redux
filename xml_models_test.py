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

import unittest
from xml_models import *
import xpath_twister as xpath

class XmlModelsTest(unittest.TestCase):
    
    def test_char_field_returns_xpathed_value_for_the_node_passed_in(self):
        xml_string = '<root><kiddie><value>Muppets rock</value></kiddie></root>'
        xml = xpath.domify(xml_string)
        field = CharField(xpath='/root/kiddie/value')
        response = field.parse(xml, None)
        self.assertEquals('Muppets rock', response) 
        
    def test_int_field_returns_xpathed_value_for_the_node_passed_in(self):
        xml_string = '<root><kiddie><value>123</value></kiddie></root>'
        xml = xpath.domify(xml_string)
        field = IntField(xpath='/root/kiddie/value')
        response = field.parse(xml, None)
        self.assertEquals(123, response)
        
    def test_int_field_raises_exception_when_non_int_value_is_parsed(self):
        xml_string = '<root><kiddie><value>NaN</value></kiddie></root>'
        xml = xpath.domify(xml_string)
        field = IntField(xpath='/root/kiddie/value')
        try:
            response = field.parse(xml, None)
            self.fail('Should have raised an exception')
        except:
            pass
            # Exception raised, all is right with the world
    
    def test_date_field_returns_xpathed_value_for_the_node_passed_in(self):
        xml_string = '<root><kiddie><value>2008-06-21T10:36:12</value></kiddie></root>'
        xml = xpath.domify(xml_string)
        field = DateField(xpath='/root/kiddie/value')
        response = field.parse(xml,None)
        date = datetime.datetime(2008,06,21,10,36,12)
        self.assertEquals(date, response)
            
    def test_date_field_strips_utc_offset_from_xpathed_value_for_the_node_passed_in(self):
        xml_string = '<root><kiddie><value>2008-06-21T10:36:12.280-06:00</value></kiddie></root>'
        xml = xpath.domify(xml_string)
        field = DateField(xpath='/root/kiddie/value')
        response = field.parse(xml,None)
        date = datetime.datetime(2008,06,21,10,36,12, 280000)
        self.assertEquals(date, response)
        
    def test_date_field_returns_none_when_xpathed_value_for_the_node_is_none(self):
        xml_string = '<root><kiddie><value></value></kiddie></root>'
        xml = xpath.domify(xml_string)
        field = DateField(xpath='/root/kiddie/value')
        response = field.parse(xml, None)
        self.assertEquals(None, response)
    
    def test_bool_field_returns_false_when_xpathed_value_for_the_node_is_false(self):
        xml_string = '<root><kiddie1><value1>false</value1></kiddie1></root>'
        xml = xpath.domify(xml_string)
        field = BoolField(xpath='/root/kiddie1/value1')
        response = field.parse(xml, None)
        self.assertEquals(False, response)

    def test_bool_field_returns_true_when_xpathed_value_for_the_node_is_true(self):
        xml_string = '<root><kiddie1><value>true</value></kiddie1></root>'
        xml = xpath.domify(xml_string)
        field = BoolField(xpath='/root/kiddie1/value')
        response = field.parse(xml, None)
        self.assertEquals(True, response)
    
    def test_can_retrieve_attribute_value_from_xml_model(self):
        my_model = MyModel('<root><kiddie><value>Rowlf</value></kiddie></root>')
        self.assertEquals('Rowlf', my_model.muppet_name)
        
    def test_returns_none_if_non_required_attribute_not_in_xml_and_no_default(self):
        my_model = MyModel('<root><kiddie><valuefoo>Rolf</valuefoo></kiddie></root>')
        self.assertEquals(None, my_model.muppet_name)
    
    def test_returns_default_if_non_required_attribute_not_in_xml_and_default_specified(self):
        my_model = MyModel('<root><kiddie><value>Rowlf</value></kiddie></root>')
        self.assertEquals('frog', my_model.muppet_type)
        
    def test_collection_returns_expected_number_of_correcty_typed_results(self):
        my_model = MyModel('<root><kiddie><value>Rowlf</value><value>Kermit</value><value>Ms.Piggy</value></kiddie></root>')
        self.assertTrue('Rowlf' in my_model.muppet_names)
        self.assertTrue('Kermit' in my_model.muppet_names)
        self.assertTrue('Ms.Piggy' in my_model.muppet_names)    
        
    def test_collection_returns_expected_number_of_integer_results(self):
        my_model = MyModel('<root><kiddie><age>10</age><age>5</age><age>7</age></kiddie></root>')
        self.assertTrue(5 in my_model.muppet_ages)
        self.assertTrue(7 in my_model.muppet_ages)
        self.assertTrue(10 in my_model.muppet_ages)
        
    def test_collection_returns_user_model_types(self):
        my_model = MyModel('<root><kiddie><address><number>10</number><street>1st Ave. South</street><city>MuppetVille</city><foobar>foo</foobar><foobar>bar</foobar></address><address><number>5</number><street>Mockingbird Lane</street><city>Bedrock</city></address></kiddie></root>')
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
        my_model = MyModel('<root><kiddie><address><number>10</number><street>1st Ave. South</street><city>MuppetVille</city><foobar>foo</foobar><foobar>bar</foobar></address><address><number>5</number><street>Mockingbird Lane</street><city>Bedrock</city></address></kiddie></root>')
        self.assertEquals(2,len(my_model.muppet_addresses))
        address1 = my_model.muppet_addresses[0]
        self.assertEquals(5, address1.number)
        address2 = my_model.muppet_addresses[1]
        self.assertEquals(10, address2.number)
        
    def test_collection_empty_collection_returned_when_xml_not_found(self):
        my_model = MyModel('<root><kiddie><address><number>10</number><street>1st Ave. South</street><city>MuppetVille</city></address><address><number>5</number><street>Mockingbird Lane</street><city>Bedrock</city></address></kiddie></root>')
        self.assertEquals([], my_model.muppet_addresses[0].foobars)
        
    def test_use_a_default_namespace(self):
        nsModel = NsModel("<root xmlns='urn:test:namespace'><name>Finbar</name><age>47</age></root>")
        self.assertEquals('Finbar', nsModel.name)
        self.assertEquals(47, nsModel.age)
        
    def test_model_fields_are_settable(self):
        my_model = MyModel('<root><kiddie><value>Gonzo</value><address><number>10</number><street>1st Ave. South</street><city>MuppetVille</city></address><address><number>5</number><street>Mockingbird Lane</street><city>Bedrock</city></address></kiddie></root>')
        my_model.muppet_name = 'Fozzie'
        self.assertEquals('Fozzie', my_model.muppet_name)
        
    def test_collection_fields_can_be_appended_to(self):
        my_model = MyModel('<root><kiddie><value>Gonzo</value><address><number>10</number><street>1st Ave. South</street><city>MuppetVille</city></address><address><number>5</number><street>Mockingbird Lane</street><city>Bedrock</city></address></kiddie></root>')
        my_model.muppet_names.append('Fozzie')
        self.assertTrue('Fozzie' in my_model.muppet_names)
        self.assertTrue('Gonzo' in my_model.muppet_names)

if __name__=='__main__':
    unittest.main()