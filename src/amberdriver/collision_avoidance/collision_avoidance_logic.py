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


def points_radians(points):
    return map(lambda (angle, distance): (math.radians(angle), distance), points)


def points_degrees(points):
    return map(lambda (angle, distance): (math.degrees(angle), distance), points)


def get_min_distance(scan, current_angle, scanner_dist_offset, angle_range):
    points = points_radians(scan.get_points())
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
    points = points_radians(scan.get_points())
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