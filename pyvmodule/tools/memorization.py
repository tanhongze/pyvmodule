__all__ = ['memorized']
def memorized(f):
    result_cache = {}
    def g(*args):
        if args in result_cache:return result_cache[args]
        val = f(*args)
        result_cache[args] = val
        return val
    return g
