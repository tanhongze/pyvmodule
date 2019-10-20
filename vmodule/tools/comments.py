class SynopsysComments:
    base = '//synopsys'
    @classmethod
    def async_set_reset(cls,w):
        return cls.base + ' async_set_reset "%s"'%str(w)
    @classmethod
    def sync_set_reset(cls,w):
        return cls.base + ' sync_set_reset "%s"'%str(w)
    @classmethod
    def translate_on(cls):
        raise NotImplementedError('Forbidden synthesis directive.')
    @classmethod
    def translate_off(cls):
        raise NotImplementedError('Forbidden synthesis directive.')
    @classmethod
    def full_case(cls):
        raise NotImplementedError('Forbidden synthesis directive.')
    @classmethod
    def parallel_case(cls):
        raise NotImplementedError('Forbidden synthesis directive.')
