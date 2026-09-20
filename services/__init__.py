"""Service package marker.

Service modules are imported explicitly by their callers.  Keeping this package
initializer empty prevents eager imports and circular-import side effects.
"""
