import os

from ansible import constants
from ansible.module_utils._text import to_text
from ansible.plugins.vars import BaseVarsPlugin


class VarsModule(BaseVarsPlugin):

    def get_vars(self, loader, path, entities):
        super().get_vars(loader, path, entities)

        result = {}
        lab_templates_dir = os.path.join(path, 'user-data', 'topologies')
        lab_templates = {}
        if os.path.isdir(lab_templates_dir):
            for dir_path, subdirs, files in os.walk(lab_templates_dir):
                for filename in files:
                    base_filename, extension = os.path.splitext(filename)
                    if base_filename == 'topology' and to_text(extension) in constants.YAML_FILENAME_EXTENSIONS:
                        full_path = os.path.join(dir_path, filename)
                        dir_name = os.path.basename(os.path.dirname(full_path))
                        lab_templates[dir_name] = loader.load_from_file(
                            full_path,
                            cache=True,
                            unsafe=False
                        )
        result['topologies'] = lab_templates
        return result
