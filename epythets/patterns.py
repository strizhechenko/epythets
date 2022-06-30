""" Словарь шаблонов словосочетаний """

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
adjf_adjf_noun = [
    {
        'TAG': {
            'OR': ['ADJF', 'PRTF'],
        },
        'COMMON': {
            'WITH': 1,
            'TAG': {
                'AND': [
                    'nomn',
                    {'OR': ['ADJF', 'PRTF']}
                ]
            }
        },
        'NOT': 'IGNORED',
    },
    {
        'NOT': 'IGNORED'
    },
    {
        'TAG': ['NOUN', 'nomn']
    }
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


def load_patterns() -> dict:
    _p = dict()
    for pattern in [adjf_adjf_noun, adjf_noun_noun, noun_adjf_noun, adjf_noun]:
        if len(pattern) not in _p:
            _p[len(pattern)] = []
        _p[len(pattern)].append(pattern)
    return _p


patterns = load_patterns()
