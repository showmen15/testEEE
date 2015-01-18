import mock

from amberdriver.drive_to_point import drive_to_point_pb2
from amberdriver.drive_to_point.drive_to_point import DriveToPoint
from amberdriver.drive_to_point.drive_to_point_controller import DriveToPointController


__author__ = 'paoolo'

import unittest


class DriveToPointControllerTestCase(unittest.TestCase):
    def setUp(self):
        self.mocked_stdin, self.mocked_stdout = mock.Mock(), mock.Mock()
        self.mocked_amber_pipes = mock.Mock()
        self.mocked_drive_to_point = mock.Mock()

        self.controller = DriveToPointController(self.mocked_stdin, self.mocked_stdout, self.mocked_drive_to_point)
        self.controller._MessageHandler__amber_pipes = self.mocked_amber_pipes


class HandleDataMessageTestCase(DriveToPointControllerTestCase):
    def runTest(self):
        header, message = mock.Mock(), mock.Mock()

        message.HasExtension = mock.Mock(side_effect=lambda ext: ext is drive_to_point_pb2.setTargets)
        mocked_handle_set_targets = mock.Mock()
        self.controller._DriveToPointController__handle_set_targets = mocked_handle_set_targets
        self.controller.handle_data_message(header, message)
        mocked_handle_set_targets.assert_called_once_with(header, message)
        self.assertEqual(message.HasExtension.call_count, 1)

        message.HasExtension = mock.Mock(side_effect=lambda ext: ext is drive_to_point_pb2.getNextTarget)
        mocked_handle_get_next_target = mock.Mock()
        self.controller._DriveToPointController__handle_get_next_target = mocked_handle_get_next_target
        self.controller.handle_data_message(header, message)
        mocked_handle_get_next_target.assert_called_once_with(header, message)
        self.assertEqual(message.HasExtension.call_count, 2)

        message.HasExtension = mock.Mock(side_effect=lambda ext: ext is drive_to_point_pb2.getNextTargets)
        mocked_handle_get_next_targets = mock.Mock()
        self.controller._DriveToPointController__handle_get_next_targets = mocked_handle_get_next_targets
        self.controller.handle_data_message(header, message)
        mocked_handle_get_next_targets.assert_called_once_with(header, message)
        self.assertEqual(message.HasExtension.call_count, 3)

        message.HasExtension = mock.Mock(side_effect=lambda ext: ext is drive_to_point_pb2.getVisitedTarget)
        mocked_handle_get_visited_target = mock.Mock()
        self.controller._DriveToPointController__handle_get_visited_target = mocked_handle_get_visited_target
        self.controller.handle_data_message(header, message)
        mocked_handle_get_visited_target.assert_called_once_with(header, message)
        self.assertEqual(message.HasExtension.call_count, 4)

        message.HasExtension = mock.Mock(side_effect=lambda ext: ext is drive_to_point_pb2.getVisitedTargets)
        mocked_handle_get_visited_targets = mock.Mock()
        self.controller._DriveToPointController__handle_get_visited_targets = mocked_handle_get_visited_targets
        self.controller.handle_data_message(header, message)
        mocked_handle_get_visited_targets.assert_called_once_with(header, message)
        self.assertEqual(message.HasExtension.call_count, 5)

        message.HasExtension = mock.Mock(side_effect=lambda ext: ext is drive_to_point_pb2.getConfiguration)
        mocked_handle_get_configuration = mock.Mock()
        self.controller._DriveToPointController__handle_get_configuration = mocked_handle_get_configuration
        self.controller.handle_data_message(header, message)
        mocked_handle_get_configuration.assert_called_once_with(header, message)
        self.assertEqual(message.HasExtension.call_count, 6)

        message.HasExtension = mock.Mock(side_effect=lambda ext: False)
        self.controller.handle_data_message(header, message)
        self.assertEqual(message.HasExtension.call_count, 6)


class HandleSetTargetsTestCase(DriveToPointControllerTestCase):
    def runTest(self):
        header, message = mock.Mock(), mock.Mock()

        targets = mock.Mock()
        message.Extensions = {drive_to_point_pb2.targets: targets}
        targets.longitudes, targets.latitudes, targets.radiuses = list(), list(), list()

        self.controller._DriveToPointController__handle_set_targets(header, message)
        self.mocked_drive_to_point.set_targets.assert_called_once_with(list())


class HandleGetNextTargetTestCase(DriveToPointControllerTestCase):
    def runTest(self):
        header, message = mock.Mock(), mock.Mock()
        longitude, latitude, radius = mock.Mock(spec=int), mock.Mock(spec=int), mock.Mock(spec=int)
        x, y, p, alfa, time_stamp = mock.Mock(spec=int), mock.Mock(spec=int), mock.Mock(spec=int), \
                                    mock.Mock(spec=int), mock.Mock(spec=int)
        next_target, current_location = [longitude, latitude, radius], [x, y, p, alfa, time_stamp]

        message.synNum = int()
        header.clientIDs = list()

        self.mocked_drive_to_point.get_next_target_and_location = mock.Mock(
            return_value=(next_target, current_location))

        def write_to_pipe(hdr, msg):
            self.assertTrue(longitude in msg.Extensions[drive_to_point_pb2.targets].longitudes)
            self.assertTrue(latitude in msg.Extensions[drive_to_point_pb2.targets].latitudes)
            self.assertTrue(radius in msg.Extensions[drive_to_point_pb2.targets].radiuses)
            self.assertEqual(msg.Extensions[drive_to_point_pb2.location].x, x)
            self.assertEqual(msg.Extensions[drive_to_point_pb2.location].y, y)
            self.assertEqual(msg.Extensions[drive_to_point_pb2.location].p, p)
            self.assertEqual(msg.Extensions[drive_to_point_pb2.location].alfa, alfa)
            self.assertEqual(msg.Extensions[drive_to_point_pb2.location].timeStamp, time_stamp)
            self.assertTrue(msg.Extensions[drive_to_point_pb2.getNextTarget])

        self.mocked_amber_pipes.write_header_and_message_to_pipe = mock.Mock(side_effect=write_to_pipe)

        self.controller._DriveToPointController__handle_get_next_target(header, message)


class HandleGetNextTargetsTestCase(DriveToPointControllerTestCase):
    def runTest(self):
        header, message = mock.Mock(), mock.Mock()
        longitude, latitude, radius = mock.Mock(spec=int), mock.Mock(spec=int), mock.Mock(spec=int)
        x, y, p, alfa, time_stamp = mock.Mock(spec=int), mock.Mock(spec=int), mock.Mock(spec=int), \
                                    mock.Mock(spec=int), mock.Mock(spec=int)
        next_targets, current_location = [(longitude, latitude, radius)], [x, y, p, alfa, time_stamp]

        message.synNum = int()
        header.clientIDs = list()

        self.mocked_drive_to_point.get_next_targets_and_location = mock.Mock(
            return_value=[next_targets, current_location])

        def write_to_pipe(hdr, msg):
            self.assertTrue(longitude in msg.Extensions[drive_to_point_pb2.targets].longitudes)
            self.assertTrue(latitude in msg.Extensions[drive_to_point_pb2.targets].latitudes)
            self.assertTrue(radius in msg.Extensions[drive_to_point_pb2.targets].radiuses)
            self.assertEqual(msg.Extensions[drive_to_point_pb2.location].x, x)
            self.assertEqual(msg.Extensions[drive_to_point_pb2.location].y, y)
            self.assertEqual(msg.Extensions[drive_to_point_pb2.location].p, p)
            self.assertEqual(msg.Extensions[drive_to_point_pb2.location].alfa, alfa)
            self.assertEqual(msg.Extensions[drive_to_point_pb2.location].timeStamp, time_stamp)
            self.assertTrue(msg.Extensions[drive_to_point_pb2.getNextTargets])

        self.mocked_amber_pipes.write_header_and_message_to_pipe = mock.Mock(side_effect=write_to_pipe)

        self.controller._DriveToPointController__handle_get_next_targets(header, message)


class HandleGetGetVisitedTargetTestCase(DriveToPointControllerTestCase):
    def runTest(self):
        header, message = mock.Mock(), mock.Mock()
        longitude, latitude, radius = mock.Mock(spec=int), mock.Mock(spec=int), mock.Mock(spec=int)
        x, y, p, alfa, time_stamp = mock.Mock(spec=int), mock.Mock(spec=int), mock.Mock(spec=int), \
                                    mock.Mock(spec=int), mock.Mock(spec=int)
        visited_target, current_location = [longitude, latitude, radius], [x, y, p, alfa, time_stamp]

        message.synNum = int()
        header.clientIDs = list()

        self.mocked_drive_to_point.get_visited_target_and_location = mock.Mock(
            return_value=(visited_target, current_location))

        def write_to_pipe(hdr, msg):
            self.assertTrue(longitude in msg.Extensions[drive_to_point_pb2.targets].longitudes)
            self.assertTrue(latitude in msg.Extensions[drive_to_point_pb2.targets].latitudes)
            self.assertTrue(radius in msg.Extensions[drive_to_point_pb2.targets].radiuses)
            self.assertEqual(msg.Extensions[drive_to_point_pb2.location].x, x)
            self.assertEqual(msg.Extensions[drive_to_point_pb2.location].y, y)
            self.assertEqual(msg.Extensions[drive_to_point_pb2.location].p, p)
            self.assertEqual(msg.Extensions[drive_to_point_pb2.location].alfa, alfa)
            self.assertEqual(msg.Extensions[drive_to_point_pb2.location].timeStamp, time_stamp)
            self.assertTrue(msg.Extensions[drive_to_point_pb2.getVisitedTarget])

        self.mocked_amber_pipes.write_header_and_message_to_pipe = mock.Mock(side_effect=write_to_pipe)

        self.controller._DriveToPointController__handle_get_visited_target(header, message)


class HandleGetVisitedTargetsTestCase(DriveToPointControllerTestCase):
    def runTest(self):
        header, message = mock.Mock(), mock.Mock()
        longitude, latitude, radius = mock.Mock(spec=int), mock.Mock(spec=int), mock.Mock(spec=int)
        x, y, p, alfa, time_stamp = mock.Mock(spec=int), mock.Mock(spec=int), mock.Mock(spec=int), \
                                    mock.Mock(spec=int), mock.Mock(spec=int)
        visited_targets, current_location = [(longitude, latitude, radius)], [x, y, p, alfa, time_stamp]

        message.synNum = int()
        header.clientIDs = list()

        self.mocked_drive_to_point.get_visited_targets_and_location = mock.Mock(
            return_value=[visited_targets, current_location])

        def write_to_pipe(hdr, msg):
            self.assertTrue(longitude in msg.Extensions[drive_to_point_pb2.targets].longitudes)
            self.assertTrue(latitude in msg.Extensions[drive_to_point_pb2.targets].latitudes)
            self.assertTrue(radius in msg.Extensions[drive_to_point_pb2.targets].radiuses)
            self.assertEqual(msg.Extensions[drive_to_point_pb2.location].x, x)
            self.assertEqual(msg.Extensions[drive_to_point_pb2.location].y, y)
            self.assertEqual(msg.Extensions[drive_to_point_pb2.location].p, p)
            self.assertEqual(msg.Extensions[drive_to_point_pb2.location].alfa, alfa)
            self.assertEqual(msg.Extensions[drive_to_point_pb2.location].timeStamp, time_stamp)
            self.assertTrue(msg.Extensions[drive_to_point_pb2.getVisitedTargets])

        self.mocked_amber_pipes.write_header_and_message_to_pipe = mock.Mock(side_effect=write_to_pipe)

        self.controller._DriveToPointController__handle_get_visited_targets(header, message)


class HandleGetConfigurationTestCase(DriveToPointControllerTestCase):
    def runTest(self):
        header, message = mock.Mock(), mock.Mock()
        max_speed = mock.Mock(spec=int)

        message.synNum = int()
        header.clientIDs = list()

        self.mocked_drive_to_point.MAX_SPEED = max_speed

        def write_to_pipe(hdr, msg):
            self.assertEqual(msg.Extensions[drive_to_point_pb2.configuration].maxSpeed, max_speed)
            self.assertTrue(msg.Extensions[drive_to_point_pb2.getConfiguration])

        self.mocked_amber_pipes.write_header_and_message_to_pipe = mock.Mock(
            side_effect=write_to_pipe)

        self.controller._DriveToPointController__handle_get_configuration(header, message)


class TerminateTestCase(DriveToPointControllerTestCase):
    def runTest(self):
        self.controller.terminate()
        self.mocked_drive_to_point.terminate.assert_called_once_with()


class DriveToPointTestCase(unittest.TestCase):
    def setUp(self):
        self.mocked_roboclaw_proxy = mock.Mock()
        self.mocked_location_proxy = mock.Mock()
        self.drive_to_point = DriveToPoint(self.mocked_roboclaw_proxy, self.mocked_location_proxy)


class SetTargetsTestCase(DriveToPointTestCase):
    def runTest(self):
        targets = mock.Mock()
        self.drive_to_point.set_targets(targets)
        self.assertEqual(self.drive_to_point._DriveToPoint__next_targets, targets)
        self.assertEqual(self.drive_to_point._DriveToPoint__visited_targets, [])


class TargetAndLocationTestCase(DriveToPointTestCase):
    def setUp(self):
        super(TargetAndLocationTestCase, self).setUp()
        self.mocked_next_target = mock.Mock()
        self.mocked_next_targets = [self.mocked_next_target, ]
        self.mocked_visited_target = mock.Mock()
        self.mocked_visited_targets = [self.mocked_visited_target, ]
        self.mocked_location = mock.Mock(spec=tuple)
        self.drive_to_point._DriveToPoint__next_targets = self.mocked_next_targets
        self.drive_to_point._DriveToPoint__visited_targets = self.mocked_visited_targets
        self.drive_to_point._DriveToPoint__current_location = self.mocked_location


class GetNextTargetsAndLocationTestCase(TargetAndLocationTestCase):
    def runTest(self):
        targets, location = self.drive_to_point.get_next_targets_and_location()
        self.assertTrue(self.mocked_next_target in targets)
        self.assertEqual(self.mocked_location, location)


class GetNextTargetAndLocationTestCase(TargetAndLocationTestCase):
    def runTest(self):
        target, location = self.drive_to_point.get_next_target_and_location()
        self.assertEqual(self.mocked_next_target, target)
        self.assertEqual(self.mocked_location, location)


class GetVisitedTargetsAndLocationTestCase(TargetAndLocationTestCase):
    def runTest(self):
        targets, location = self.drive_to_point.get_visited_targets_and_location()
        self.assertTrue(self.mocked_visited_target in targets)
        self.assertEqual(self.mocked_location, location)


class GetVisitedTargetAndLocationTestCase(TargetAndLocationTestCase):
    def runTest(self):
        target, location = self.drive_to_point.get_visited_target_and_location()
        self.assertEqual(self.mocked_visited_target, target)
        self.assertEqual(self.mocked_location, location)