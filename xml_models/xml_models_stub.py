from xml_models import Model, NoRegisteredFinderError, DoesNotExist

class XmlModelStubManager(object):
    """Handles what can be queried for, and acts as the entry point for querying.  There is an instance per model that is used
    in the django style of Model.objects.get(attr1=value, attr2=value2) for single results, or 
    Model.objects.filter(attr1=value1,attr2=value2) for multiple results.  As with Django, you can chain filters together, i.e.
    Model.objects.filter(attr1=value1).filter(attr2=value2)  Filter is not evaluated until you try to iterate over the results or
    get a count of the results."""
    def __init__(self, model, finders):
        self.model = model
        self._stubs = []
        
    def _stub(self):
        exp = Expectation(self.model)
        self._stubs.append(exp)
        return exp
        
    def filter(self, **kw):
        for exp in self._stubs:
            if exp.args == kw:
                return exp.called()
        
    def filter_custom(self, url):
         raise NoRegisteredFinderError("foo")

    def count(self):
        raise NoRegisteredFinderError("foo")
        
    def get(self, **kw):
        for exp in self._stubs:
            if exp.args == kw:
                return exp.called()
        raise DoesNotExist(self.model, kw)

class Expectation(object):

    def __init__(self, model):
        self.model = model

    def get(self, **kw):
        self.args = kw
        self.method = 'get'
        return self

    def returns(self, *params, **kw):
        if params and self.method == 'filter':
            self.result = []
            for args in params:
                item = self.model()
                for key, value in args.items():
                    setattr(item, key, value)
                self.result.append(item)
        elif kw and self.method == 'get':
            self.result = self.model()
            for key, value in kw.items():
                setattr(self.result, key, value)
        else:
            if self.method == 'get':
                raise Exception("get methods return single items, call returns(arg_name='name', arg_age='age' ...)")
            else:
                raise Exception("filter methods return multiple items, call returns(dict(arg_name='name', arg_age='age' ...), dict(.....))")

    def filter(self, **kw):
        self.args = kw
        self.method = 'filter'
        return self
        
    def called(self):
        return self.result
        
        
# Decorator for use in tests
def stub(model):
    def wrapper(func):
        def patched(*args, **keywargs):
            old = model.objects
            model.objects = XmlModelStubManager(model, None)
            setattr(model, 'stub', model.objects._stub)
            try:
                return func(*args, **keywargs)
            finally:
                model.objects = old
                delattr(model, 'stub')
        return patched
        
    return wrapper
