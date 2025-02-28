from lib2to3.fixer_util import FromImport
from setuptools import depends
from toposort import toposort_flatten
from itertools import combinations
from tqdm import tqdm

class ArtifactPattern:
    def __init__(self, *args, **kwargs):
        self.positive_tags = set(kwargs.get('positive_tags', []))
        self.negative_tags = set(kwargs.get('negative_tags', []))
        if len(args) > 0:
            if type(args[0]) is str:
               self.from_string(args[0])
            elif hasattr(args[0], 'positive_tags') and hasattr(args[0], 'negative_tags'):
               self.positive_tags.update(args[0].positive_tags)
               self.negative_tags.update(args[0].negative_tags)

    def from_string(self, string_pattern):
        for tag in string_pattern.split(','):
            tag = tag.strip()
            if tag.startswith('!'):
                self.negative_tags.add(tag[1:])
            else:
                self.positive_tags.add(tag)

    def depends_on(self, pattern):
        if self.positive_tags & pattern.positive_tags:
            return True

        if self.positive_tags & pattern.negative_tags:
            return True

        return False

    def match(self, artifact):
        return self.positive_tags <= artifact.tags and not self.negative_tags & artifact.tags

class Artifact(dict):
    def __init__(self, target_pattern):
        self.target_pattern = ArtifactPattern(target_pattern)

    @property
    def tags(self):
        return [*self.keys(), *[f'{k}={v}' for k, v in self.items()]]

class ArtifactRule:
    def __init__(self, source_patterns=[], target_patterns=[]):
        self.source_patterns = [ArtifactPattern(x) for x in source_patterns]
        self.target_patterns = [ArtifactPattern(x) for x in target_patterns]

    def depends_on(self, rule):
        return any((y.depends_on(x) for x, y in zip(rule.target_patterns, self.source_patterns)))

    # apply to full list of available artifacts. may need to iterate over and find specific artifacts to do stuff to.
    def apply(self, artifacts):
        pass

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
