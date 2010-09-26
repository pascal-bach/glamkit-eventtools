import warnings
import functools


def deprecated(func):
    """This is a decorator which can be used to mark functions
    as deprecated. It will result in a warning being emitted
    when the function is used."""

    @functools.wraps(func)
    def new_func(*args, **kwargs):
        warnings.warn(
            "Function %(funcname)s is deprecated." % {
                'funcname': func.__name__,
            },
            category=DeprecationWarning,
            stacklevel=2
        )
        return func(*args, **kwargs)
    return new_func

"""
## Usage examples ##
@deprecated
def my_func():
    pass

@other_decorators_must_be_upper
@deprecated
def my_func():
    pass
    
"""