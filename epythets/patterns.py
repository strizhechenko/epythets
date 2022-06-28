""" Словарь шаблонов словосочетаний """
patterns = dict()

adjf_noun_noun = [
    {
        'TAG': {'OR': ['PRTF', 'ADJF']},
        'NOT': 'IGNORED',
        'COMMON': {
            'WITH': 1,
            'TAG': {
                'AND': [
                    {'OR': ['plur', 'sing']},
                    'nomn'
                ]
            }
        }
    },
    {'COMMON': {'WITH': 2, 'TAG': 'NOUN'}},
    {
        'TAG': 'gent',
        'NOT': {
            'TAG': 'ADJS'
        }
    }
]
noun_adjf_noun = [
    {
        'TAG': 'nomn',
        'COMMON': {'WITH': 2, 'TAG': 'NOUN'}
    },
    {
        'TAG': {'OR': ['PRTF', 'ADJF']},
        'NOT': 'IGNORED',
        'COMMON': {
            'WITH': 2,
            'TAG': 'gent'
        }
    },
    {}
]
adjf_noun = [
    {
        'TAG': {'OR': ['PRTF', 'ADJF']},
        'NOT': 'IGNORED',
        'COMMON': {
            'WITH': 1,
            'TAG': 'nomn'
        }
    },
    {'TAG': 'NOUN'}
]

for pattern in adjf_noun_noun, noun_adjf_noun, adjf_noun:
    if len(pattern) not in patterns:
        patterns[len(pattern)] = []
    patterns[len(pattern)].append(pattern)
