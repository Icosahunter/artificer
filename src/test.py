from artificer import Artificer, Artifact, SimpleRule

a = SimpleRule('', 'std:A', lambda x: [*x, 'std:A'])
b = SimpleRule('', 'std:B', lambda x: [*x, 'std:B'])
c = SimpleRule('std:A,std:B', 'std:C', lambda x: [*x, 'std:C'])

artificer = Artificer([a, b, c])
artifacts = [Artifact([])]
artificer.build(artifacts)

print(artifacts)
