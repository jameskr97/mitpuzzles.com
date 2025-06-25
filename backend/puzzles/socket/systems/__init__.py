from importlib import import_module, resources

# Import every .py under systems/ so @command decorators run exactly once
for name in resources.contents(__name__):
    if name.endswith(".py") and name not in {"__init__.py"}:
        import_module(f"{__name__}.{name[:-3]}")
