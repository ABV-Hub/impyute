""" impyute.util.wrapper """
from functools import wraps
import numpy as np
from impyute.util import BadInputError
from impyute.util import find_null

## Hacky way to handle python2 not having `ModuleNotFoundError`
# pylint: disable=redefined-builtin, missing-docstring
try:
    raise ModuleNotFoundError
except NameError:
    class ModuleNotFoundError(Exception):
        pass
except ModuleNotFoundError:
    pass
# pylint: enable=redefined-builtin, missing-docstring

def execute_fn_with_args_and_or_kwargs(fn, args, kwargs):
    """ If args + kwargs aren't accepted only args are passed in"""
    try:
        return fn(*args, **kwargs)
    except TypeError:
        return fn(*args)

def get_pandas_df():
    """ Gets pandas DataFrame if we can import it """
    try:
        import pandas as pd
        df = pd.DataFrame
    except (ModuleNotFoundError, ImportError):
        df = None
    return df

def handle_df(fn):
    """ Decorator to handle pandas Dataframe object as input

    If the first arg is a pandas dataframe, convert it to a numpy array
    otherwise don't do anything. Cast back to a pandas Dataframe after
    the imputation function has run
    """
    @wraps(fn)
    def wrapper(*args, **kwargs):
        postprocess_fn = None
        ## convert tuple to list so args can be modified
        args = list(args)
        ## Either make a copy or use a pointer to the original
        if kwargs.get('inplace'):
            args[0] = args[0]
        else:
            args[0] = args[0].copy()

        ## If input data is a dataframe then cast the input to an np.array
        ## and set an indicator flag before continuing
        pd_DataFrame = get_pandas_df()
        if pd_DataFrame and isinstance(args[0], pd_DataFrame):
            postprocess_fn = pd_DataFrame
            args[0] = args[0].values

        ## function invokation
        results = execute_fn_with_args_and_or_kwargs(fn, args, kwargs)

        ## cast the output back to a DataFrame.
        if postprocess_fn is not None:
            results = postprocess_fn(results)

        return results
    return wrapper

def inplace(fn):
    """ Decorator for inplace option

    Functions wrapped by this can have an `inplace` kwarg to use either a copy of
    data or reference """
    @wraps(fn)
    def wrapper(*args, **kwargs):
        """ Run input checks"""
        ## convert tuple to list so args can be modified
        args = list(args)
        ## Either make a copy or use a pointer to the original
        if kwargs.get('inplace'):
            args[0] = args[0]
        else:
            args[0] = args[0].copy()

        ## function invokation
        return execute_fn_with_args_and_or_kwargs(fn, args, kwargs)
    return wrapper

def preprocess(fn):
    return inplace(handle_df(fn))

def _shape_2d(data):
    """ True if array is 2D"""
    return len(np.shape(data)) == 2

def _shape_3d(data):
    """ True if array is 3D"""
    return len(np.shape(data)) == 3

def _is_ndarray(data):
    """ True if the array is an instance of numpy's ndarray"""
    return isinstance(data, np.ndarray)

def _dtype_float(data):
    """ True if the values in the array are floating point"""
    return data.dtype == np.float

def _nan_exists(data):
    """ True if there is at least one np.nan in the array"""
    null_xy = find_null(data)
    return len(null_xy) > 0

def checks(fn):
    """ Throw exception if error runs"""
    @wraps(fn)
    def wrapper(*args, **kwargs):
        data = args[0]
        if len(np.shape(data)) != 2:
            raise BadInputError("No support for arrays that aren't 2D yet.")
        elif not _shape_2d(data):
            raise BadInputError("Not a 2D array.")
        elif not _is_ndarray(data):
            raise BadInputError("Not a np.ndarray.")
        elif not _dtype_float(data):
            raise BadInputError("Data is not float.")
        elif not _nan_exists(data):
            raise BadInputError("No NaN's in given data")
        return execute_fn_with_args_and_or_kwargs(fn, args, kwargs)
    return wrapper
