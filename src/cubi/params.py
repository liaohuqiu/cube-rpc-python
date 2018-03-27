def assert_integer(k):
    return assert_param(k, int, long)

def assert_param(k, *types):
    def decor(fn):
        def wrapper(self, params):
            v = params.get(k, None)
            if v != None:
                assert type(v) in types, 'param key <%s> type error expect %s given %s(%s)' % (k, str(types), str(type(v)), v)
            return fn(self, params)
        return wrapper
    return decor

def extract_args(fn):
    def wrapper(self, *args, **kwargs):
        if len(args) == 1 and isinstance(args[0], dict):
            return fn(self, **(args[0]))
        else:
            return fn(self, *args, **kwargs)
    return wrapper

class Params(dict):
    """
    Query Parameters
    @TODO enable async response by using decorator and subclass of Params
    """
    def __init__(self, params):
        super(Params, self).__init__(params)

    def _want_val(self, k, *types):
        v = self[k]
        assert type(v) in types, 'param want key <%s> type error except %s given %s' % (k, str(types), str(type(v)))
        return v

    def _get_val(self, k, *args):
        d = args[-1]
        if k not in self:
            return d
        v = self[k]
        types = args[:-1]
        assert type(v) in types, 'param get key <%s> type error except %s given %s' % (k, str(types), str(type(v)))
        return v

    def want_integer(self, k):
        return self._want_val(k, int, long)

    def want_float(self, k):
        return self._want_val(k, float)

    def want_str(self, k):
        return self._want_val(k, str)

    def want_bool(self, k):
        return self._want_val(k, bool)

    def want_list(self, k):
        return self._want_val(k, list)

    def want_dict(self, k):
        return self._want_val(k, dict)

    def get_int(self, k, d = 0):
        return self._get_val(k, int, long, d)

    def get_float(self, k, d = 0.0):
        return self._get_val(k, float, d)

    def get_str(self, k, d = ''):
        return self._get_val(k, str, d)

    def get_bool(self, k, d = False):
        return self._get_val(k, bool, d)

    def get_list(self, k, d = []):
        return self._get_val(k, list, d)

    def get_dict(self, k, d = {}):
        return self._get_val(k, dict, d)
