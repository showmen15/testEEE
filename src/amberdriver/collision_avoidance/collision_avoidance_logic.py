import math


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