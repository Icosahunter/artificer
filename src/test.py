from artificer import Artificer, Artifact, Rule

class A(Rule):
    def __init__(self):
        super().__init__([], ['A'])

    def apply(self, artifacts):
        for artifact in artifacts:
            artifact.tags.add('A')

class B(Rule):
    def __init__(self):
        super().__init__([], ['B'])

    def apply(self, artifacts):
        for artifact in artifacts:
            artifact.tags.add('B')

class C(Rule):
    def __init__(self):
        super().__init__(['A', 'B'], ['C'])

    def apply(self, artifacts):
        for artifact in artifacts:
            artifact.tags.add('C')

artificer = Artificer([A(), B(), C()])

artifacts = [Artifact({}, ['C'])]

artificer.build(artifacts)

print(artifacts)
