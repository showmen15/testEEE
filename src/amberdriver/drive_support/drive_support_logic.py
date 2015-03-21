import math

import os

from amberdriver.tools import config


__author__ = 'paoolo'

pwd = os.path.dirname(os.path.abspath(__file__))
config.add_config_ini('%s/collision_avoidance.ini' % pwd)

ROBO_WIDTH = float(config.ROBO_WIDTH)

MAX_SPEED = float(config.MAX_SPEED)
MAX_ROTATING_SPEED = float(config.MAX_ROTATING_SPEED)
SOFT_LIMIT = float(config.SOFT_LIMIT)
HARD_LIMIT = float(config.HARD_LIMIT)

SCANNER_DIST_OFFSET = float(config.SCANNER_DIST_OFFSET)
ANGLE_RANGE = float(config.ANGLE_RANGE)

DISTANCE_ALPHA = float(config.DISTANCE_ALPHA)
RODEO_SWAP_ALPHA = float(config.RODEO_SWAP_ALPHA)


def get_angle(left, right, robo_width):
    return math.atan2(left - right, float(robo_width))


def get_speed(left, right):
    return (left + right) / 2.0


def get_max_speed(distance, soft_limit, hard_limit, max_speed):
    return max_speed / (soft_limit - hard_limit) * float(distance) - \
           (max_speed * hard_limit) / (soft_limit - hard_limit)


def get_soft_limit(current_speed, max_speed, soft_limit, hard_limit, alpha):
    return alpha * soft_limit * (current_speed / max_speed) + hard_limit + 50.0


def convert_angles_to_radians(points):
    return map(lambda (angle, distance): (math.radians(angle), distance), points)


def convert_angles_to_degrees(points):
    return map(lambda (angle, distance): (math.degrees(angle), distance), points)


def get_min_distance(scan, current_angle, scanner_dist_offset, angle_range):
    points = convert_angles_to_radians(scan)
    min_distance = None
    min_distance_angle = None

    for angle, distance in points:
        if distance > scanner_dist_offset \
                and current_angle - angle_range < angle < current_angle + angle_range:
            if min_distance is None or distance < min_distance:
                min_distance = distance
                min_distance_angle = angle

    return min_distance, min_distance_angle


def get_max_distance(scan, current_angle, scanner_dist_offset, angle_range):
    points = convert_angles_to_radians(scan)
    max_distance = None
    max_distance_angle = None
    max_diff_angle = 0.0

    for angle, distance in points:
        if (distance > scanner_dist_offset or distance == 0) \
                and current_angle - angle_range < angle < current_angle + angle_range:
            diff_angle = abs(current_angle - angle)
            if (max_distance is None or distance > max_distance or distance == 0) and diff_angle > max_diff_angle:
                max_distance = distance
                max_distance_angle = angle
                max_diff_angle = diff_angle

    return max_distance, max_distance_angle


def analyze_scan(scan):
    points = convert_angles_to_radians(scan)
    for angle, distance in points:
        x, y = distance * math.cos(angle), distance * math.sin(angle)


def simple_importance_angle_level(angle):
    if math.fabs(angle) < math.pi / 2.0:
        return 1.0 - 2.0 * math.fabs(angle) / math.pi
    return 0.0


def simple_distance_level(distance, max_distance=5000.0):
    """ max_distance in [mm] """
    return distance / max_distance


def average(values):
    return reduce(lambda x, y: x + y, values) / len(values)


def distance_danger_level(scan,
                          importance_angle_level_func=simple_importance_angle_level,
                          distance_level_func=simple_distance_level,
                          compute_level_func=average):
    points = convert_angles_to_radians(scan)
    levels = []
    for angle, distance in points:
        importance_angle_level = importance_angle_level_func(angle)
        distance_level = distance_level_func(distance)
        levels.append(importance_angle_level * distance_level)
    return compute_level_func(levels)


def find_continuities(scan, max_continuity_interval=10):
    """ max_continuity_interval in [mm] for distance 100 [mm] """
    points = convert_angles_to_radians(scan)
    continuities = []
    old_x, old_y = None, None
    first_x, first_y = None, None
    for angle, distance in sorted(points.items()):
        x, y = distance * math.cos(angle), distance * math.sin(angle)
        if old_x is None and old_y is None:
            old_x, old_y = x, y
            first_x, first_y = x, y
        else:
            limit = math.pow(distance * max_continuity_interval * 0.01, 2)
            if math.pow(old_x - x, 2) > limit or math.pow(old_y - y, 2) > limit:
                first = (first_x, first_y)
                last = (old_x, old_y)
                continuities.append((first, last))
                first_x, first_y = x, y
            else:
                old_x, old_y = x, y
    return continuities


def find_locals_min_max(scan, interval=50, min_distance=100.0, max_distance=5000.0):
    """ interval in 50 [mm] """
    points = convert_angles_to_radians(scan)
    local_mini, local_maxi = None, None
    local_minis, local_maxis = [], []
    prev_distance = None
    for angle, distance in sorted(points.items()):
        if min_distance < distance < max_distance:
            if prev_distance is None:
                prev_distance = distance
            else:
                if distance - prev_distance > interval:
                    local_maxi = (angle, distance)
                    if local_mini is not None:
                        local_minis.append(local_mini)
                        local_mini = None
                elif distance - prev_distance < -interval:
                    local_mini = (angle, distance)
                    if local_maxi is not None:
                        local_maxis.append(local_maxi)
                        local_maxi = None
                prev_distance = distance
    return local_minis, local_maxis


def limit_due_to_distance(left, right, scan):
    if left > 0 or right > 0:
        current_angle = get_angle(left, right, ROBO_WIDTH)
        current_speed = get_speed(left, right)

        if scan is not None:
            min_distance, _ = get_min_distance(scan, current_angle,
                                               SCANNER_DIST_OFFSET, ANGLE_RANGE)

            if min_distance is not None:
                soft_limit = get_soft_limit(current_speed, MAX_SPEED,
                                            SOFT_LIMIT * 1.3, HARD_LIMIT * 1.3, DISTANCE_ALPHA)

                if HARD_LIMIT * 1.3 < min_distance < soft_limit:
                    max_speed = get_max_speed(min_distance, soft_limit, HARD_LIMIT * 1.3, MAX_SPEED)
                    if current_speed > max_speed:
                        left, right = __calculate_new_left_right(left, right,
                                                                 max_speed, current_speed)

                elif min_distance <= HARD_LIMIT * 1.3:
                    left, right = 0, 0

        else:
            print 'distance: no scan!'
            left, right = 0.0, 0.0

    return left, right


def __calculate_new_left_right(left, right, max_speed, current_speed):
    if current_speed > 0:
        divide = max_speed / current_speed
        return left * divide, right * divide
    else:
        return left, right


def limit_to_max_speed(left, right):
    left = __limit_to_max_speed(left)
    right = __limit_to_max_speed(right)

    return left, right


def __limit_to_max_speed(value):
    max_speed = MAX_SPEED
    return max_speed if value > max_speed \
        else -max_speed if value < -max_speed \
        else value


def limit_due_to_reverse_direction(left, right):
    max_speed = MAX_SPEED

    if (left + right) / 2.0 < 0:

        if left < 0 and right < 0:
            left = left if left > -max_speed else -max_speed
            right = right if right > -max_speed else -max_speed

        elif left < 0 < right:
            right = right if right < max_speed else max_speed
            left = -right

        elif left > 0 > right:
            left = left if left < max_speed else max_speed
            right = -left

    return left, right


def rodeo_swap(left, right, scan):
    current_angle = get_angle(left, right, ROBO_WIDTH)
    current_speed = get_speed(left, right)

    min_distance, min_distance_angle = get_min_distance(scan, current_angle,
                                                        SCANNER_DIST_OFFSET, ANGLE_RANGE)

    if min_distance is not None:
        soft_limit = get_soft_limit(current_speed, MAX_SPEED,
                                    SOFT_LIMIT, HARD_LIMIT, RODEO_SWAP_ALPHA)

        if min_distance < soft_limit:
            if min_distance_angle < current_angle:
                if left > 0:
                    left = left if left < MAX_ROTATING_SPEED else MAX_ROTATING_SPEED
                    right = -left
                else:
                    if right > 0:
                        _t = left
                        left = right
                        right = _t

            else:
                if right > 0:
                    right = right if right < MAX_ROTATING_SPEED else MAX_ROTATING_SPEED
                    left = -right
                else:
                    if left > 0:
                        _t = right
                        right = left
                        left = _t

        elif min_distance < soft_limit * 0.4:
            left = -left
            right = -right

    return left, right


def low_pass_filter(left, right):
    # TODO implement low pass filter
    return left, right


def scan_trust(scan_timestamp, current_timestamp):
    val = scan_timestamp / 1000.0 - current_timestamp
    return math.pow(4.0 / 3.0, val)


def command_trust(command_timestamp, current_timestamp):
    val = command_timestamp - current_timestamp
    return math.pow(4.0 / 3.0, val)