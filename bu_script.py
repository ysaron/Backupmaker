import os
import shutil
import yaml
import re
from pprint import pprint

with open('bu_paths.yaml', encoding='utf-8') as f:
    raw_paths = yaml.safe_load(f)


class BackupPaths:

    def __init__(self):
        self.__targets = []
        self.__elems_to_backup = {}
        self.__backup_size: int = 0
        self.__problems = {'nonstr_paths': [],
                           'nonabs_paths': [],
                           'nonexistent_paths': [],
                           'failed_targets': [],
                           'other': []}

    @property
    def target(self):
        return self.__targets

    @target.setter
    def target(self, path_list):
        """ Задание списка целевых папок для копий """
        self.__validate_path_list(path_list)
        self.__targets = path_list

    @property
    def paths(self):
        return self.__elems_to_backup

    @paths.setter
    def paths(self, to_backup: dict[list]):
        """ Задание путей к резервируемым файлам """
        for path_list in to_backup.values():
            self.__validate_path_list(path_list)    # если что-то не так - здесь возникнут исключения
        self.__calc_backup_size(to_backup)
        self.__elems_to_backup = to_backup

    def __validate_path_list(self, path_list: list[str]):
        if not path_list:
            self.__problems['other'].append('no dirs')
            raise Exception
        if not isinstance(path_list, list):
            self.__problems['other'].append('dirs is not list')
            raise Exception

        for path in path_list:
            if not isinstance(path, str):
                self.__problems['nonstr_paths'].append(path)
        if self.__problems['nonstr_paths']:
            raise TypeError('Все пути должны быть строками!')

        for path in path_list:
            if not os.path.isabs(path):
                self.__problems['nonabs_paths'].append(path)
            if not os.path.exists(path):
                self.__problems['nonexistent_paths'].append(path)
        if self.__problems['nonabs_paths']:
            raise ValueError(f'Все пути должны быть абсолютными')
        if self.__problems['nonexistent_paths']:
            raise FileNotFoundError(f'Несуществующие пути')

        for path in path_list:
            print(f'FILE SIZE: {os.stat(path).st_size} bytes')

    def __calc_backup_size(self, to_backup: dict[list]):
        size = 0
        for path_list in to_backup.values():
            size += sum([os.stat(path).st_size for path in path_list])
        self.__backup_size = size
        print(self.__backup_size)

    @staticmethod
    def __calc_free_memory(directory: str):
        total_bytes, used_bytes, free_bytes = shutil.disk_usage(directory[:2])
        return free_bytes

    def make_backup(self):
        for dir_ in self.__targets:
            free_mem = BackupPaths.__calc_free_memory(dir_)
            if free_mem <= self.__backup_size:
                self.__problems['failed_targets'].append(dir_)
                continue
            for key, value in self.__elems_to_backup.items():
                subdir = self.__make_backup_subdir(name=key, root_dir=dir_)
                self.__copy_to_subdir(subdir=subdir, filelist=value)

    @staticmethod
    def __make_backup_subdir(name: str, root_dir: str):
        """ Создает в папке подпапку с заданным именем """
        subdir = os.path.join(root_dir, name)
        if not os.path.exists(subdir):
            os.mkdir(path=subdir)
        return subdir

    @staticmethod
    def __copy_to_subdir(subdir: str, filelist: list):
        """ Копирует каждый файл в списке в заданную папку """
        for file in filelist:
            shutil.copy2(file, subdir)


def main():
    pprint(raw_paths)
    bp = BackupPaths()
    bp.target = raw_paths['backup_dir']     # проверять, есть ли такой ключ
    del raw_paths['backup_dir']
    bp.paths = raw_paths
    pprint(bp.target)
    bp.make_backup()

    total_bytes, used_bytes, free_bytes = shutil.disk_usage('F:')
    mb = 10 ** 6
    print(f'Всего:\t\t{total_bytes / mb} МБ')
    print(f'Занято:\t\t{used_bytes / mb} МБ')
    print(f'Свободно:\t{free_bytes / mb} МБ')


if __name__ == '__main__':
    main()
