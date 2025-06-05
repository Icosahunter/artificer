from toposort import toposort_flatten
from collections.abc import Mapping, Iterable
from pathlib import Path
from urllib.parse import urlparse
import re
from itertools import chain

def _resolve_tag(tag):
    tags = ['']
    for t in tag.split('.'):
        tags.append(tags[-1] + t)
    tags.remove('')
    return set(tags)

def _resolve_tags(tags):
    return set(chain.from_iterable((_resolve_tag(x) for x in tags)))

def _str_is_pathlike(string):
    if Path(string).exists():
        return True
    if re.match(string, r"(?:\.|~)?[a-zA-Z0-9 \-_()&/]+(?:\.[a-zA-Z0-9]{2,3})+$"):
        return True
    if re.match(string, r"(?:\.|~)?[a-zA-Z0-9 \-_()&/]+$") and string.count('/') > 1:
        return True
    return False

class Artifact:
    def __init__(self, obj, tags = []):
        self.obj = obj
        self.tags = _resolve_tags(tags)
        self._set_type_tags()

    def __repr__(self):
        tags = list(self.tags)
        tags.sort()
        tags = ', '.join(tags)
        return f'<{type(self).__name__} obj:{self.obj.__repr__()} tags:{{{tags}}}>'

    def _set_type_tags(self):
        self.tags.add(f'py:{type(self.obj).__name__}')
        if isinstance(self.obj, Mapping):
            self.tags.add('std:mapping')
        if isinstance(self.obj, Iterable) and not isinstance(self.obj, str):
            self.tags.add('std:iterable')
        if isinstance(self.obj, str) and urlparse(self.obj).scheme:
            self.tags.add('std:url')
        if isinstance(self.obj, Path) or (isinstance(self.obj, str) and _str_is_pathlike(self.obj)):
            self.tags.add('std:path')
            # If dir/file not specified by tags argument, try to figure it out
            if not ('std:path.dir' in self.tags or 'std:path.file' in self.tags):
                path = Path(self.obj)
                if path.exists():
                    if path.is_dir():
                        self.tags.add('std:path.dir')
                    else:
                        self.tags.add('std:path.file')
                elif path.suffix:
                    self.tags.add('std:path.file')
                elif isinstance(self.obj, str):
                    if self.obj[-1] in ['/', '\\']:
                        self.tags.add('std:path.dir')

class AttrArtifact(Artifact):
    def __init__(self, obj, attr, tags = []):
        self._obj = obj
        self._attr = attr
        self.tags = _resolve_tags(tags)
        self._set_type_tags()

    @property
    def obj(self):
        return getattr(self._obj, self._attr)

    @obj.setter
    def obj(self, value):
        setattr(self._obj, self._attr, value)

def rule(src_tags, tar_tags):
    def rule_decorator(func):
        return Rule(func, src_tags, tar_tags)
    return rule_decorator

class Rule:
    def __init__(self, func, src_tags, tar_tags):
        self.func = func
        self.src_tags = set(src_tags)
        self.tar_tags = set(tar_tags)

    def depends_on(self, other_rule):
        return self.src_tags & other_rule.tar_tags

    def __call__(self, artificer):
        filtered_artifacts = artificer.filter(self.src_tags)

        for artifact in filtered_artifacts:
            result = self.func(artifact)
            if result is not None:
                if issubclass(type(result), Artifact):
                    artificer.artifacts.append(result)
                else:
                    try:
                        for artifact in result:
                            if issubclass(type(artifact), Artifact):
                                artificer.artifacts.append(result)
                            else:
                                break
                    except TypeError:
                        pass

class Artificer:
    def __init__(self, rules = [], artifacts = []):
        self.rules = rules
        self.artifacts = artifacts
        self.build_steps

    def filter(self, tags):
        tags = set(tags)
        return [x for x in self.artifacts if x.tags >= tags]

    def build(self):
        self._build_dep_graph()

    def _build_dep_graph(self):
        self.dep_graph = {}
        for rule in self.rules:
            rule_deps = set(
                [x for x in self.rules if rule.depends_on(x)]
            )
            self.dep_graph[rule] = rule_deps
        self.build_steps = toposort_flatten(self.dep_graph, False)
