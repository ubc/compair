from collections import namedtuple
ComparisonResult = namedtuple('ComparisonResult', 
    ['key', 'score', 'total_rounds', 'total_opponents', 'total_wins', 'total_loses']
)