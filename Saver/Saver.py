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
    def insert(self, value):
        pass

    @abstractmethod
    def delete(self, attr):
        pass

    @abstractmethod
    def update(self, attr, value):
        pass


def _find(data, attr, handle_func, *args):
    # if type((found_data_dict := data.get(attr))) is dict:
    if type(data) is dict:
        if attr in data:
            return result if (result := handle_func(data, attr, *args)) else True
        for key in data:
            _find(data[key], attr, handle_func, *args)


class FileObject(AbstractFileObject):
    def _check_file_exist(self):
        if not os.path.isfile(self.filepath):
            with open(self.filepath, 'w') as f:
                json.dump({}, f, indent=4)

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

    def insert(self, value: dict):
        with open(self._filepath, 'r+') as f:
            data = json.load(f)
            for key in value.keys():
                data[key] = value[key]
            f.seek(0)
            json.dump(data, f, indent=4)
            f.truncate()
            return True

    def get(self, attr=None):
        with open(self._filepath, 'r') as f:
            try:
                data = json.load(f)
                if attr:
                    data = _find(data, attr, lambda *args: args[0][args[1]])
                return data
            except json.JSONDecodeError:
                return {}

    def delete(self, attr):
        attr = str(attr)
        with open(self._filepath, 'r+') as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                return False
            else:
                is_deleted = True if _find(data, attr, lambda *args: args[0].pop(args[1])) else False
                f.seek(0)
                json.dump(data, f, indent=4)
                f.truncate()
                return is_deleted

    @staticmethod
    def _update_value(data, attr, value):
        data[attr] = value
        return True

    def update(self, attr, value):
        data = self.get()
        is_updated = True if _find(data, attr, self._update_value, value) else False
        self.insert(data)
        return is_updated

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

    def __setattr__(self, name, value):
        return False

    def __getattr__(self, attr):
        return self._create_file(attr)

    def _create_file(self, filename):
        new_file_object = FileObject(filename)
        setattr(self, filename, new_file_object)
        return new_file_object
