from artificer import Artificer, Artifact, rule

@rule([], ['A'])
def a(artifact):
    artifact.add_tag('A')

@rule([], ['B'])
def b(artifact):
    artifact.add_tag('B')

@rule(['A', 'B'], ['C'])
def c(artifact):
    artifact.add_tag('C')

artificer = Artificer([a, b, c], [Artifact([])])
artificer.build()

print(artificer.artifacts)
