import re
from toposort import toposort_flatten
from itertools import chain
from collections.abc import Mapping, Sequence
from pathlib import Path
from urllib.parse import urlparse

def _str_is_pathlike(string):
    if Path(string).exists():
        return True
    if re.match(string, r"(?:\.|~)?[a-zA-Z0-9 \-_()&/]+(?:\.[a-zA-Z0-9]{2,3})+$"):
        return True
    if re.match(string, r"(?:\.|~)?[a-zA-Z0-9 \-_()&/]+$") and string.count('/') > 1:
        return True
    return False

def _resolve_tag(tag):
    tags = ['']
    for t in tag.split('.'):
        tags.append(tags[-1] + t)
    tags.remove('')
    return set(tags)

def _resolve_tags(tags):
    return set(chain.from_iterable((_resolve_tag(x) for x in tags)))

def filter(artifacts, tags):
    tags = set(tags)
    return (x for x in artifacts if tags <= x.tags)

def rule(source_tags, target_tags):
    def rule_decorator(func):
        return Rule(source_tags, target_tags, func)
    return rule_decorator

class Rule:
    def __init__(self, source_tags=[], target_tags=[], function=lambda:()):
        self.source_tags = set(source_tags)
        self.target_tags = set(target_tags)
        self.function = function

    def depends_on(self, rule):
        return True if rule.target_tags & self.source_tags else False

    def __call__(self, artifacts):
        self.function(artifacts)

class Artifact:
    def __init__(self, obj=None, tags=[]):
        self.tags = _resolve_tags(tags)
        self.obj = obj
        self._set_type_tags()

    def add_tag(self, tag):
        self.tags.update(_resolve_tag(tag))

    def remove_tag(self, tag):
        matches = [x for x in self.tags if x.startswith(tag)]
        for match in matches:
            self.tags.remove(match)

    def __repr__(self):
        tags = list(self.tags)
        tags.sort()
        tags = ', '.join(tags)
        return f'<{type(self).__name__} obj:{self.obj} tags:{{{tags}}}>'

    def _set_type_tags(self):
        self.tags.add(f'py:{type(self.obj).__name__}')
        if isinstance(self.obj, Mapping):
            self.tags.add('std:mapping')
            self.tags.update((f'std:mapping.keys.{x}' for x in self.obj.keys()))
        if isinstance(self.obj, Sequence):
            self.tags.add('std:sequence')
        if isinstance(self.obj, str) and urlparse(self.obj).scheme:
            self.tags.add('std:url')
        if isinstance(self.obj, Path) or (isinstance(self.obj, str) and _str_is_pathlike(self.obj)):
            self.tags.add('std:path')
            # If dir/file not specified by tags argument, make try to figure it out
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

class Artificer:
    def __init__(self, rules):
        self.rules = rules
        self._build_dep_graph()

    def _build_dep_graph(self):
        self.dep_graph = {}
        for rule1 in self.rules:
            rule1_deps = set()
            for rule2 in self.rules:
                if rule1.depends_on(rule2):
                    rule1_deps.add(rule2)
            self.dep_graph[rule1] = rule1_deps
        self.build_steps = toposort_flatten(self.dep_graph, False)

    def build(self, artifacts):
        for step in self.build_steps:
            step(artifacts)
