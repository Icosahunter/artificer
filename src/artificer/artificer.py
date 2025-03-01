import re
from lib2to3.fixer_util import FromImport
from setuptools import depends
from toposort import toposort_flatten
from itertools import combinations
from collections.abc import Mapping, Sequence
from pathlib import Path
from urllib.parse import urlparse

class Pattern:
    def __init__(self, *args, **kwargs):
        self.positive_tags = set(kwargs.get('positive_tags', []))
        self.negative_tags = set(kwargs.get('negative_tags', []))
        if len(args) > 0:
            if type(args[0]) is str and args[0]:
               self.from_string(args[0])
            elif isinstance(args[0], Sequence):
               self.from_sequence(args[0])
            elif hasattr(args[0], 'positive_tags') and hasattr(args[0], 'negative_tags'):
               self.positive_tags.update(args[0].positive_tags)
               self.negative_tags.update(args[0].negative_tags)

    def __repr__(self):
        tag_str = ', '.join([*self.positive_tags, *['!' + x for x in self.negative_tags]])
        return f'<{type(self).__name__} {{{tag_str}}}>'

    def from_string(self, string_pattern):
        self.from_sequence(string_pattern.split(','))

    def from_sequence(self, seq):
        for tag in seq:
            tag = tag.strip()
            if tag.startswith('!'):
                self.negative_tags.add(tag[1:])
            else:
                self.positive_tags.add(tag)

    def match(self, artifact):
        return not self.positive_tags or (self.positive_tags <= artifact.tags and not self.negative_tags & artifact.tags)

def _str_is_pathlike(string):
    if Path(string).exists():
        return True
    if re.match(string, r"(?:\.|~)?[a-zA-Z0-9 \-_()&/]+(?:\.[a-zA-Z0-9]{2,3})+$"):
        return True
    if re.match(string, r"(?:\.|~)?[a-zA-Z0-9 \-_()&/]+$") and string.count('/') > 1:
        return True
    return False

class Artifact:
    def __init__(self, obj=None, tags=[]):
        self.tags = set(tags)
        self.obj = obj
        self._set_type_tags()

    def __repr__(self):
        tags = list(self.tags)
        tags.sort()
        tags = ', '.join(tags)
        return f'<{type(self).__name__} obj:{self.obj} tags:{{{tags}}}>'

    def _set_type_tags(self):
        self.tags.add(f'type-{type(self.obj).__name__}')
        if isinstance(self.obj, Mapping):
            self.tags.add('type-mapping')
        if isinstance(self.obj, Sequence):
            self.tags.add('type-sequence')
        if isinstance(self.obj, str) and urlparse(self.obj).scheme:
            self.tags.add('type-url')
            self.tags.add('type-file')
        if isinstance(self.obj, Path) or (isinstance(self.obj, str) and _str_is_pathlike(self.obj)):
            self.tags.add('type-path')
            # If dir/file not specified by tags argument, make try to figure it out
            if not ('type-dir' in self.tags or 'type-file' in self.tags):
                path = Path(self.obj)
                if path.exists():
                    if path.is_dir():
                        self.tags.add('type-dir')
                    else:
                        self.tags.add('type-file')
                elif path.suffix:
                    self.tags.add('type-file')
                elif isinstance(self.obj, str):
                    if self.obj[-1] in ['/', '\\']:
                        self.tags.add('type-dir')

class Rule:
    def __init__(self, source_patterns=[], target_patterns=[]):
        self.source_patterns = [Pattern(x) for x in source_patterns]
        self.target_patterns = [Pattern(x) for x in target_patterns]

    def depends_on(self, rule):
        return any((x.positive_tags & y.positive_tags for x, y in zip(rule.target_patterns, self.source_patterns))) or \
               any((x.negative_tags & y.positive_tags for x, y in zip(rule.source_patterns, self.source_patterns)))

    # apply to full list of available artifacts. may need to iterate over and find specific artifacts to do stuff to.
    def apply(self, artifacts):
        raise(NotImplementedError)

class SimpleRule(Rule):
    def __init__(self, source_pattern='', target_pattern='', function=lambda x: x, del_ext=False):
        super().__init__([source_pattern], [target_pattern])
        self.function = function
        self.del_ext = del_ext

    def apply(self, artifacts):
        for artifact in (x for x in artifacts if self.source_patterns[0].match(x)):
            artifact.obj = self.function(artifact.obj)
            if self.del_ext:
                artifacts.tags = {x for x in artifact.tags if not x.startswith('.')}
            artifact.tags.update(self.target_patterns[0].positive_tags)

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
            step.apply(artifacts)
