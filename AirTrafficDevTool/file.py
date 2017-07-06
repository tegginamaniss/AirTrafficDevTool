from collections import Sequence
from pathlib import PurePath

import yaml
import json
import umsgpack
import pickle
import gzip

binary_mode_table = {
    pickle: True,
    yaml: False,
    umsgpack: True,
    json: False,
}
"""
Dictionary indicating whether the serializers require the file to be opened in binary mode or not.
"""

extension_table = {
    ".pickle": pickle,
    ".yaml": yaml,
    ".msgp": umsgpack,
    ".json": json,
}
"""
Dictionary mapping file extensions to serializers.
"""


class File:
    """
    Class used to (de)serialize files. The serializer is chosen based on
    the file extension. If the file extension is not recognized then the
    default serializer is used. If no default serializer was given, then msgpack
    is used.

    If the file path's last file extension is `.gz`, the files are compressed
    and decompressed using gzip. If the default serializer is being used, then
    `is_gzipped_default` is checked. 'is_gzipped_default' will have no  effect
    if the file path ends with `.gz`, even for unknown file extensions.

    .. note:: Only use standard types (strings, lists, tuples dictionaries,
       floats, etc) to assure compatibility with all serializers.

    .. note:: The file is only opened when loading or dumping data. There
       is no need to explicitly close the file.

    .. list-table:: Supported serializers
       :header-rows: 1

       * - Name
         - Extension

       * - Pickle
         - .pickle

       * - Yaml
         - .yaml

       * - Msgpack
         - .msgp

       * - Json
         - .json


    :param path: Either a string or :class:`pathlib.PurePath` object with the path
       of the file to be loaded or dumped to.
    :param default_serializers: A single or a list of serialization objects. This
       can be any object, module or package with the same load(s) and dump(s)
       methods as the python pickle package.
    :param bool is_gzipped_default: True to compress and decompress files using
       gzip when using the default serializer.
    """

    def __init__(self, file_path, default_serializers=None, is_gzipped_default=False):
        # If the path is a string, create a PurePath object.
        self.file_path = file_path if isinstance(file_path, PurePath) else PurePath(file_path)
        """
        :class:`pathlib.PurePath` object with the path to the file.
        """

        # Get file extensions.
        file_extensions = self.file_path.suffixes

        # Check whether the file is gzipped or not.
        if ".gz" in file_extensions:
            self.__is_gzipped = True
            file_extensions.remove(".gz")
        else:
            self.__is_gzipped = False

        # Get the extension indicating the serializer. If the file is gzipped, it's the
        # one before last extension. If the file is't gzipped it's the last one.
        serializer_extension = file_extensions[-1]
        self.custom_ext_check = serializer_extension

        # print("extension", serializer_extension)

        # Check the file extension.
        serializer = extension_table.get(serializer_extension, None)

        if serializer is None:
            # The file extension was not recognized. Use the first serializer in the serializers list.

            # We'll be using a default serializer, so let's set is_gzipped to is_gzipped_default if
            # is_gzipped is False
            if not self.__is_gzipped:
                self.__is_gzipped = is_gzipped_default

            if default_serializers is None:
                # If no default serializers where given as a parameter, use message pack.
                serializer = umsgpack
            else:
                if isinstance(default_serializers, Sequence):
                    # If a list was given, use the first non-None value in the list.
                    for x in default_serializers:
                        if x is None:
                            continue
                        else:
                            serializer = x
                            break
                else:
                    # If a single default serializer was given, just use that one.
                    serializer = default_serializers

                # If all default serializers are None. Raise an error.
                if serializer is None:
                    raise ValueError("No suitable serializer was found to open file '{}'.".format(file_path))

        self.serializer = serializer  #: Selected serializer

        # Because the serializers require the files to be opened in either text or binary mode.
        self.is_binary = binary_mode_table[self.serializer]

    @property
    def is_gzipped(self):
        """
        True if the file is compressed with gzip.
        """
        return self.__is_gzipped

    def load(self, file):
        """
        Loads in data from a file(-like) object.

        :param file: File(-like) object to load
        :return: Data stored in the file.
        """

        return self.loads(file.read())

    def loads(self, bytes_object):
        """
        Decodes and decompresses a string or bytes object.

        :param bytes_object: Either a bytes or str object to be decompressed and deserialized.
        :return: Data encoded in the byte string.
        """
        # Decompress the data if necessary.
        if self.is_gzipped:
            bytes_object = bytes(bytes_object)
            bytes_object = gzip.decompress(bytes_object)

        # Encodes or decodes the data to binary or string depending what the serializer requires.
        if self.is_binary:
            bytes_object = bytes(bytes_object, "utf8") if isinstance(bytes_object, str) else bytes_object
        else:
            bytes_object = str(bytes_object, "utf8") if isinstance(bytes_object, bytes) else bytes_object

        # Deserialize the bytes_object and return the resulting object.
        if self.custom_ext_check == '.yaml':
            return self.serializer.load(bytes_object)
        else:
            return self.serializer.loads(bytes_object)

    def dump(self, obj, file):
        """
        Dumps data into a file(-like) object.

        :param obj: Object to be encoded and stored.
        :param file: File(-like) where to store the encoded data.
        """
        file.write(self.dumps(obj))

    def dumps(self, obj):
        """
        Encodes and decompresses a python object.

        :param obj: Object to encode.
        :return: String or byte string with the encoded data.
        """

        # Serialize the object to a string or byte string.
        dumped_data = self.serializer.dumps(obj)

        if self.is_gzipped:
            # Encodes the data to a byte string if it's a string.
            dumped_data = bytes(dumped_data, "utf8") if isinstance(dumped_data, str) else dumped_data

            # Compresses data.
            dumped_data = gzip.compress(dumped_data)

        return dumped_data

    def load_data(self):
        """
        Read in and decode the file.

        :return: The python object stored in the file
        """
        # Open the file and return the loaded in data.
        with open(self.file_path, "r" + ("b" if self.is_binary or self.is_gzipped else "")) as f:
            return self.load(f)

    def dump_data(self, obj):
        """
        Dump a python object to the file

        :param obj: Object to be stored.
        """
        # Open the file and dump the object into the file.
        with open(self.file_path, "w" + ("b" if self.is_binary or self.is_gzipped else "")) as f:
            self.dump(obj, f)