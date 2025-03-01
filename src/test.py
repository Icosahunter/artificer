from artificer import Artificer, Artifact, SimpleRule, Pattern

a = SimpleRule('', 'A', lambda x: [*x, 'A'])
b = SimpleRule('', 'B', lambda x: [*x, 'B'])
c = SimpleRule('A,B', 'C', lambda x: [*x, 'C'])

artificer = Artificer([a, b, c])
artifacts = [Artifact([])]
artificer.build(artifacts)

print(artifacts)
