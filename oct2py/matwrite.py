"""
.. module:: _h5write
   :synopsis: Write Python values into an MAT file for Octave.
              Strives to preserve both value and type in transit.

.. moduleauthor:: Steven Silvester <steven.silvester@ieee.org>

"""
from __future__ import absolute_import, print_function, division

from scipy.io import savemat
import numpy as np

from .utils import Oct2PyError


def write_file(obj, path, oned_as='row', convert_to_float=True):
    """Save a Python object to an Octave file on the given path.
    """
    obj['nargin'] = len(obj['func_args'])
    data = putval(obj, convert_to_float=convert_to_float)
    try:
        savemat(path, data, appendmat=False, oned_as=oned_as,
                long_field_names=True)
    except KeyError:  # pragma: no cover
        raise Exception('could not save mat file')


def putval(data, convert_to_float=False):
    """Convert the Python values to values suitable to sent to Octave.
    """

    # Extract the values from dict and Struct objects.
    if isinstance(data, dict):
        for (key, value) in data.items():
            data[key] = putval(value, convert_to_float)

    # Send None as nan.
    if data is None:
        return np.NaN

    # See if it should be an array, otherwise treat is as a tuple.
    if isinstance(data, list):
        try:
            test = np.array(data)
            if test.dtype.kind in 'uicf':
                return putval(test, convert_to_float)
        except Exception:
            pass
        return putval(tuple(data))

    # Make a cell array.
    if isinstance(data, (tuple, set)):
        data = [putval(o, convert_to_float) for o in data]
        if len(data) == 1:
            return data[0]
        else:
            return np.array(data, dtype=object)

    # Clean up nd arrays.
    if isinstance(data, np.ndarray):
        return clean_array(data, convert_to_float)

    # Leave all other content alone.
    return data


def clean_array(data, convert_to_float=False):
    """Handle data type considerations."""
    dstr = data.dtype.str
    if 'c' in dstr and dstr[-2:] == '24':
        raise Oct2PyError('Datatype not supported: {0}'.format(data.dtype))
    elif 'f' in dstr and dstr[-2:] == '12':
        raise Oct2PyError('Datatype not supported: {0}'.format(data.dtype))
    elif 'V' in dstr and not hasattr(data, 'classname'):
        raise Oct2PyError('Datatype not supported: {0}'.format(data.dtype))
    elif dstr == '|b1':
        data = data.astype(np.int8)
    elif dstr == '<m8[us]' or dstr == '<M8[us]':
        data = data.astype(np.uint64)
    elif '|S' in dstr or '<U' in dstr:
        data = data.astype(np.object)
    elif '<c' in dstr and np.alltrue(data.imag == 0):
        data.imag = 1e-9
    if data.dtype.name in ['float128', 'complex256']:
        raise Oct2PyError('Datatype not supported: {0}'.format(data.dtype))
    if data.dtype == 'object' and len(data.shape) > 1:
        data = data.T
    if convert_to_float and data.dtype.kind in 'uib':
        data = data.astype(float)

    return data
