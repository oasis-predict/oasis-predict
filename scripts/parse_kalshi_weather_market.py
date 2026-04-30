import re


CITY_PATTERNS = [
    ('Los Angeles', [r'\bin la\b', r'\blos angeles\b', r'\bla,? us\b']),
    ('New York', [r'\bin nyc\b', r'\bnew york\b', r'\bin ny\b']),
    ('Chicago', [r'\bchicago\b']),
    ('Miami', [r'\bmiami\b']),
]

DATE_PATTERN = re.compile(r'on ([a-z]{3,9}) (\d{1,2}), (\d{4})', re.IGNORECASE)
GREATER_PATTERN = re.compile(r'be >(\d+(?:\.\d+)?)°', re.IGNORECASE)
LESS_PATTERN = re.compile(r'be <(\d+(?:\.\d+)?)°', re.IGNORECASE)
RANGE_PATTERN = re.compile(r'be (\d+(?:\.\d+)?)\-(\d+(?:\.\d+)?)°', re.IGNORECASE)


def detect_city(question_lower):
    for city, patterns in CITY_PATTERNS:
        for pattern in patterns:
            if re.search(pattern, question_lower):
                return city
    return None


def parse_kalshi_question(question: str):
    q = question.strip()
    q_lower = q.lower()

    result = {
        'raw_question': q,
        'city': detect_city(q_lower),
        'date': None,
        'market_type': None,
        'comparison': None,
        'threshold_low': None,
        'threshold_high': None,
        'unit': 'F',
        'mode': 'binary',
    }

    date_match = DATE_PATTERN.search(q_lower)
    if date_match:
        month = date_match.group(1).title()
        day = int(date_match.group(2))
        year = int(date_match.group(3))
        result['date'] = f'{month} {day}, {year}'

    if 'high temp' in q_lower or 'highest temperature' in q_lower:
        result['market_type'] = 'daily_high_temperature'

    greater_match = GREATER_PATTERN.search(q)
    less_match = LESS_PATTERN.search(q)
    range_match = RANGE_PATTERN.search(q)

    if greater_match:
        result['comparison'] = 'greater_than'
        result['threshold_low'] = float(greater_match.group(1))
    elif less_match:
        result['comparison'] = 'less_than'
        result['threshold_high'] = float(less_match.group(1))
    elif range_match:
        result['comparison'] = 'between'
        result['threshold_low'] = float(range_match.group(1))
        result['threshold_high'] = float(range_match.group(2))

    return result


def test():
    examples = [
        'Will the high temp in LA be >89° on Mar 18, 2026?',
        'Will the high temp in New York be <82° on Mar 18, 2026?',
        'Will the high temp in Chicago be 84-85° on Mar 18, 2026?',
    ]

    for question in examples:
        parsed = parse_kalshi_question(question)
        print('=' * 70)
        for key, value in parsed.items():
            print(f'{key}: {value}')


if __name__ == '__main__':
    test()
