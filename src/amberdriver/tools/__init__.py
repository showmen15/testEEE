__author__ = 'paoolo'


def bound_sleep_interval(value, min_value=0.2, max_value=2.0):
    return value if min_value < value < max_value else max_value if value > max_value else min_value