from abc import ABC, abstractmethod
import pathlib
import json
import os


class AbstractSaver(ABC):
    @abstractmethod
    def __getattr__(self, attr):
        pass

    @abstractmethod
    def __setattr__(self, *args, **kwargs):
        pass


class AbstractFileObject(ABC):
    @abstractmethod
    def get(self, attr: str):
        pass

    @abstractmethod
    def getAll(self) -> dict:
        pass

    @abstractmethod
    def insert(self, value):
        pass

    @abstractmethod
    def delete(self, attr):
        pass

    @abstractmethod
    def update(self, attr, value):
        pass


def _find(attr, data, handle_func):
    for key in data:
        if type((x := data.get(key))) is dict:
            if attr in x:
                handle_func(attr, x)
                return True
            _find(attr, x, handle_func)


class FileObject(AbstractFileObject):
    def _check_file_exist(self):
        if not os.path.isfile(self.filepath):
            open(self.filepath, 'x')

    def __init__(self, filename):
        self.filename = str(filename)
        self.filepath = self.filename
        self._check_file_exist()

    @property
    def filepath(self):
        return self._filepath

    @filepath.setter
    def filepath(self, filename: str):
        self._filepath = f"{Saver._data_path}{filename}Data.json"

    def insert(self, value):
        with open(self._filepath, 'w') as f:
            json.dump(value, f, indent=4)

    def get(self, attr: str):
        with open(self._filepath, 'r') as f:
            try:
                return json.load(f).get(attr)
            except json.JSONDecodeError:
                return {}

    def getAll(self) -> dict:
        with open(self._filepath, 'r') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {}

    def delete(self, attr, additional_keys=None):
        attr = str(attr)
        with open(self._filepath, 'r+') as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                return False
            else:
                if additional_keys:
                    cut_data = data.copy()
                    if type(additional_keys) is list:
                        for key in additional_keys:
                            cut_data = cut_data[key]
                    else:
                        cut_data = data.copy()[additional_keys]
                if attr in data:
                    data.pop(attr)
                    return True
                else:
                    is_deleted = _find(attr, data, lambda *args: args[1].pop(args[0]))
                f.seek(0)
                json.dump(data, f, indent=4)
                f.truncate()
                return is_deleted

    def update(self, attr, value):
        pass

    def __str__(self):
        return self.filename

    def __eq__(self, other):
        try:
            return self.filename == str(other)
        except TypeError:
            return False


class Saver(AbstractSaver):
    # SAVE_FILE_NAME = "AutoroomData"
    _data_path = f"{pathlib.Path().resolve()}/_Data/"

    def _check_path_exist(self):
        if not os.path.exists(self._data_path):
            os.mkdir(self._data_path)
            print(f'Created directory {self._data_path}')

    def __init__(self):
        self._check_path_exist()

    def __setattr__(self, *args, **kwargs):
        return False

    def __getattr__(self, attr):
        return self._create_file(attr)

    def _create_file(self, filename):
        new_file_object = FileObject(filename)
        setattr(self, filename, new_file_object)
        return new_file_object

    # @classmethod
    # def save(cls, data):
    #     if cls.data_path:
    #         with open(cls.data_path, 'w') as f:
    #             json.dump(data, f)
    #
    # @classmethod
    # def read(cls):
    #     if cls.data_path:
    #         try:
    #             with open(cls.data_path, 'r') as f:
    #                 data = json.load(f)
    #                 return data
    #         except json.JSONDecodeError:
    #             return {}
    #         except FileNotFoundError:
    #             cls.save({})
    #             return cls.read()
