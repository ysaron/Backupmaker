import os
import shutil
import yaml
import sys

with open('bu_paths.yaml', encoding='utf-8') as f:
    raw_paths = yaml.safe_load(f)


class NoBackupError(Exception):
    msg = 'Не определено никаких файлов для копирования'

    def __init__(self):
        self.message = NoBackupError.msg
        super().__init__(self.message)


class YamlListError(Exception):
    msg = 'Один или более списков путей в YAML не соответствуют типу list'

    def __init__(self):
        self.message = YamlListError.msg
        super().__init__(self.message)


class BackupPaths:

    def __init__(self):
        self.__targets = []
        self.__elems_to_backup = {}
        self.__backup_size: int = 0
        self.problems = {'nonstr_paths': [],
                         'nonabs_paths': [],
                         'nonexistent_paths': [],
                         'failed_targets': []}

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
        if not to_backup:
            raise NoBackupError
        for path_list in to_backup.values():
            self.__validate_path_list(path_list)  # если что-то не так - здесь возникнут исключения
        self.__calc_backup_size(to_backup)
        self.__elems_to_backup = to_backup

    def __validate_path_list(self, path_list: list[str]):
        if not path_list:
            raise NoBackupError
        if not isinstance(path_list, list):
            raise YamlListError

        for path in path_list:
            if not isinstance(path, str):
                self.problems['nonstr_paths'].append(path)
        if self.problems['nonstr_paths']:
            raise TypeError('Не все пути являются строками')

        for path in path_list:
            if not os.path.isabs(path):
                self.problems['nonabs_paths'].append(path)
            if not os.path.exists(path):
                self.problems['nonexistent_paths'].append(path)
        if self.problems['nonabs_paths']:
            raise ValueError(f'Не все пути являются абсолютными')
        if self.problems['nonexistent_paths']:
            raise FileNotFoundError(f'Не все пути в списке существуют')

    def __calc_backup_size(self, to_backup: dict[list]):
        size = 0
        for path_list in to_backup.values():
            size += sum([os.stat(path).st_size for path in path_list])
        self.__backup_size = size
        print(f'Копируемые файлы занимают {self.__backup_size} байт')

    @staticmethod
    def __calc_free_memory(directory: str):
        total_bytes, used_bytes, free_bytes = shutil.disk_usage(directory[:2])
        return free_bytes

    def make_backup(self):
        for dir_ in self.__targets:
            free_mem = BackupPaths.__calc_free_memory(dir_)
            if free_mem <= self.__backup_size:
                self.problems['failed_targets'].append(dir_)
                continue
            for key, value in self.__elems_to_backup.items():
                subdir = self.__make_backup_subdir(name=key, root_dir=dir_)
                self.__copy_to_subdir(subdir=subdir, pathlist=value)

    @staticmethod
    def __make_backup_subdir(name: str, root_dir: str):
        """ Создает в папке подпапку с заданным именем """
        subdir = os.path.join(root_dir, name)
        if not os.path.exists(subdir):
            os.mkdir(path=subdir)
        return subdir

    @staticmethod
    def __copy_to_subdir(subdir: str, pathlist: list):
        """ Копирует каждый файл/папку в списке путей в заданную папку """
        for path in pathlist:
            if os.path.isfile(path):
                shutil.copy2(path, subdir)
            else:
                destination = os.path.join(subdir, os.path.split(path)[-1])
                if not os.path.exists(destination):
                    os.mkdir(destination)
                shutil.copytree(src=path, dst=destination, dirs_exist_ok=True)


def main():
    bp = BackupPaths()
    farewell_msg = 'Enter - закрыть окно\n'
    try:
        bp.target = raw_paths['backup_dir']
        del raw_paths['backup_dir']
        bp.paths = raw_paths
    except KeyError:
        print('Папки, в которые выполняется резервное копирование, должны быть заданы в YAML-файле списком под ключом '
              'backup_dir')
        input(farewell_msg)
        sys.exit()
    except NoBackupError:
        print(NoBackupError.msg)
        input(farewell_msg)
        sys.exit()
    except YamlListError:
        print(YamlListError.msg)
        input(farewell_msg)
        sys.exit()
    except TypeError:
        print('Не все пути являются строками:')
        for path in bp.problems['nonstr_paths']:
            print(path)
        input(farewell_msg)
        sys.exit()
    except ValueError:
        print('Не все пути являются абсолютными:')
        for path in bp.problems['nonabs_paths']:
            print(path)
        input(farewell_msg)
        sys.exit()
    except FileNotFoundError:
        print('Не все пути из указанных существуют:')
        for path in bp.problems['nonexistent_paths']:
            print(path)
        input(farewell_msg)
        sys.exit()

    bp.make_backup()


if __name__ == '__main__':
    main()
