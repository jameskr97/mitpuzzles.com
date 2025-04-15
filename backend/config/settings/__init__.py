import os

DJANGO_ENV = os.environ.get('DJANGO_ENV', 'local')
match DJANGO_ENV:
    case 'local':
        from .local import *
    case 'production':
        from .prod import *
    case _:
        raise ValueError(f"Invalid DJANGO_ENV: {DJANGO_ENV}")
