import unittest
from xml.dom import minidom

class MultipleNodesReturnedException(Exception):
	pass
	
lxml_available = False
try:
	from lxml import etree, objectify
	lxml_available = True
except:
	import xpath

def find_unique(xml, expression, namespace=None):
	if lxml_available:
		return _lxml_xpath()
	else:
		return _pydom_xpath(xml, expression, namespace)
	
def _lxml_xpath():
	pass

def domify(xml):
	if lxml_available:
		return lxml.objectify.fromstring(xml)
	else:
		return minidom.parseString(xml)

def _pydom_xpath(xml, expression, namespace):
	if namespace:
		pass
	else:		
		nodelist = xpath.find(expression, xml)
		if len(nodelist) > 1:
			raise MultipleNodesReturnedException
		node = nodelist[0].firstChild
		if node.nodeType == minidom.Node.TEXT_NODE:
			return node.nodeValue
		else:
			return None
			
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

class XPathTest(unittest.TestCase):
	
	def test_xpath_returns_expected_element_value(self):
		#setup
		xml = minidom.parseString("<foo><baz>dcba</baz><bar>abcd</bar></foo>")
		#execute
		val = find_unique(xml, "/foo/bar")
		#assert
		self.assertEquals("abcd", val)
		
	def test_xpath_returns_expected_attribute_value(self):
		#setup
		xml = minidom.parseString('<foo><baz name="Arthur">dcba</baz><bar>abcd</bar></foo>')
		#execute
		val = find_unique(xml, "/foo/baz/@name")
		#assert
		self.assertEquals("Arthur", val)
		
if __name__=='__main__':
    unittest.main()