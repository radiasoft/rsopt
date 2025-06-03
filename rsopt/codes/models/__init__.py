class FormatterRegistry:
    _formatters = {}

    @classmethod
    def register(cls, key):
        """Decorate formatting functions to register."""
        def decorator(func):
            cls._formatters[key] = func
            return func
        return decorator

    @classmethod
    def get_formatter(cls, key):
        return cls._formatters.get(key, cls.default_formatter)

    @staticmethod
    def default_formatter(value):
        return value