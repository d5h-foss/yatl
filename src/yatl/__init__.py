import yaml

from yatl.render import JsonType, render_from_obj


def load(str_or_file, params) -> JsonType:
    obj = yaml.safe_load(str_or_file)
    return render_from_obj(obj, params)
