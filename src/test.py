from artificer import Artificer, Artifact, rule, filter

@rule([], ['A'])
def a(artifacts):
    for artifact in artifacts:
        artifact.add_tag('A')

@rule([], ['B'])
def b(artifacts):
    for artifact in artifacts:
        artifact.add_tag('B')

@rule(['A', 'B'], ['C'])
def c(artifacts):
    for artifact in filter(artifacts, ['A', 'B']):
        artifact.add_tag('C')

artificer = Artificer([a, b, c])
artifacts = [Artifact([])]
artificer.build(artifacts)

print(artifacts)
