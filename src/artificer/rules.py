from artificer import Artifact, rule, filter
from pathlib import Path

def pandoc_convert(source_fmt, target_fmt):
    import pypandoc
    @rule([f'std:path.file.{source_fmt}'], [f'std:path.file.{target_fmt}'])
    def _pandoc_convert(artifacts):
        for artifact in filter(artifacts, [f'std:path.file.{source_fmt}']):
            pypandoc.convert_file(artifact.obj, target_fmt)
            output = Path(artifact.obj).with_suffix('.'+target_fmt)
            if output.exists():
                artifacts.add(Artifact(output))
    return _pandoc_convert

def pil_convert(source_fmt, target_fmt):
    from PIL import Image
    @rule([f'std:path.file.{source_fmt}'], [f'std:path.file.{target_fmt}'])
    def _pil_convert(artifacts):
        for artifact in filter(artifacts, [f'std:path.file.{source_fmt}']):
            try:
                img = Image.open(artifact.obj)
                output = Path(artifact.obj).with_suffix('.'+target_fmt)
                img.save(output)
                if output.exists():
                    artifacts.add(Artifact(output))
            except:
                pass
    return _pil_convert

@rule(['std:path.file.json'], ['std:mapping', 'std:sequence'])
def load_json(artifacts):
    import json
    for artifact in filter(artifacts, ['std:path.file.json']):
        try:
            with open(artifact.obj, 'r') as f:
                artifacts.add(Artifact(json.load(f)))
        except:
            pass

@rule(['std:path.file.toml'], ['std:mapping'])
def load_toml(artifacts):
    import tomllib
    for artifact in filter(artifacts, ['std:path.file.toml']):
        try:
            with open(artifact.obj, 'rb') as f:
                artifacts.add(Artifact(tomllib.load(f)))
        except:
            pass

@rule(['std:path.file.yml'], ['std:mapping', 'std:sequence'])
def load_yaml(artifacts):
    import yaml
    for artifact in filter(artifacts, ['std:path.file.yml']):
        try:
            with open(artifact.obj, 'r') as f:
                artifacts.add(Artifact(yaml.safe_load(f)))
        except:
            pass

@rule(['std:path.file'], ['std:mapping', 'std:sequence'])
def load_conf(artifacts):
    from configparser import ConfigParser
    for artifact in filter(artifacts, ['std:path.file']):
        if 'std:path.file.toml' not in artifact.tags:
            config = ConfigParser()
            try:
                config.read(artifact.obj)
                conf_dict = {s:dict(config.items(s)) for s in config.sections()}
                artifacts.Add(Artifact(conf_dict))
            except:
                pass

@rule(['std:path.dir'], ['std:path.file'])
def iter_dirs(artifacts):
    for artifact in filter(artifacts, ['std:path.dir']):
        for file in Path(artifact.obj).glob('**/*'):
            artifacts.add(Artifact(file))
