from artificer import *

class A(ArtifactRule):
    def __init__(self):
        super().__init__([], ['A'])

    def apply(self, artifacts):
        for artifact in artifacts:
            artifact['A'] = True

class B(ArtifactRule):
    def __init__(self):
        super().__init__([], ['B'])

    def apply(self, artifacts):
        for artifact in artifacts:
            artifact['B'] = True

class C(ArtifactRule):
    def __init__(self):
        super().__init__(['A', 'B'], ['C'])

    def apply(self, artifacts):
        for artifact in artifacts:
            artifact['C'] = True

artificer = Artificer([A(), B(), C()])

artifacts = [Artifact('C')]

artificer.build(artifacts)

print(artifacts)
