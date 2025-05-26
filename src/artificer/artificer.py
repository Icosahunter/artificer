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
        for artifact in filter(artifacts, self.source_tags):
            self.function(artifact)

class Artifact:
    def __init__(self, obj=None, tags=[]):
        self.tags = _resolve_tags(tags)
        self.obj = obj

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

class AttrArtifact(Artifact):

    class AttrArtifactDescriptor:
        def __init__(self, obj, attr):
            self.obj = obj
            self.attr = attr

        def __get__(self, obj, objtype=None):
            return self.obj[self.attr]

        def __set__(self, obj, value):
            self.obj[self.attr] = value

    def __init__(self, obj=None, attr='', tags=[]):
        super().__init__(self.AttrArtifactDescriptor(obj, attr), tags)

class DefaultArtifactLoader:

    def supports_obj(self, obj):
        return True

    def load(self, obj):
        artifact = Artifact(obj)
        self._set_type_tags(artifact)
        return [artifact]

    def _set_type_tags(self, artifact):
        artifact.tags.add(f'py:{type(artifact.obj).__name__}')
        if isinstance(artifact.obj, Mapping):
            artifact.tags.add('std:mapping')
            artifact.tags.update((f'std:mapping.keys.{x}' for x in artifact.obj.keys()))
        if isinstance(artifact.obj, Sequence):
            artifact.tags.add('std:sequence')
        if isinstance(artifact.obj, str) and urlparse(artifact.obj).scheme:
            artifact.tags.add('std:url')
        if isinstance(artifact.obj, Path) or (isinstance(artifact.obj, str) and _str_is_pathlike(artifact.obj)):
            artifact.tags.add('std:path')
            # If dir/file not specified by tags argument, try to figure it out
            if not ('std:path.dir' in artifact.tags or 'std:path.file' in artifact.tags):
                path = Path(artifact.obj)
                if path.exists():
                    if path.is_dir():
                        artifact.tags.add('std:path.dir')
                    else:
                        artifact.tags.add('std:path.file')
                elif path.suffix:
                    artifact.tags.add('std:path.file')
                elif isinstance(artifact.obj, str):
                    if artifact.obj[-1] in ['/', '\\']:
                        artifact.tags.add('std:path.dir')

class Artificer:

    default_artifact_loaders = [DefaultArtifactLoader()]

    def __init__(self, rules, artifact_loaders = None):
        self.rules = rules
        if artifact_loaders:
            self.artifact_loaders = artifact_loaders
        else:
            self.artifact_loaders = Artificer.default_artifact_loaders
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

    def _load_artifacts(self, objs):
        artifacts = []
        for obj in objs:
            for loader in self.artifact_loaders:
                if loader.supports_obj(obj):
                    artifacts += loader.load(obj)
                    break

    def build(self, objs):
        artifacts = self._load_artifacts(objs)
        for step in self.build_steps:
            step(artifacts)
