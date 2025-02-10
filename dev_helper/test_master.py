import unittest
from unittest.mock import patch, MagicMock
import image_processing_pb2
import master


class TestMaster(unittest.TestCase):

    def setUp(self):
        """Set up any necessary resources for tests"""
        self.worker_address = "localhost:50052"
        self.image_data = b"test_image_data"
        self.mock_insecure_channel = patch("master.grpc.insecure_channel").start()
        self.mock_popen = patch("master.subprocess.Popen").start()
        self.mock_check_worker_ready = patch("master.MasterServiceServicer.check_worker_ready").start()
        self.mock_image_open = patch("master.Image.open").start()
        self.mock_send_image_to_worker = patch("master.MasterServiceServicer.send_image_to_worker").start()

    def tearDown(self):
        """Clean up after each test"""
        patch.stopall()  # Stop all active patches to ensure no leftover mocks

    @patch("master.generate_descriptions")
    def test_generate_descriptions(self, mock_generate_descriptions):
        # Mock inputs
        detections = [
            {"class": "cat", "bounding_box": [50, 50, 100, 100], "confidence": 0.95},
            {"class": "dog", "bounding_box": [150, 150, 200, 200], "confidence": 0.88},
        ]
        image_width, image_height = 300, 300

        # Expected descriptions
        mock_generate_descriptions.return_value = [
            "cat detected at the top left of the image with 0.95 confidence.",
            "dog detected at the middle center of the image with 0.88 confidence.",
        ]

        # Call the method
        descriptions = master.generate_descriptions(detections, image_width, image_height)

        # Verify
        self.assertEqual(len(descriptions), 2)
        self.assertIn("cat detected at the top left", descriptions[0])

    def test_send_image_to_worker(self):
        # Mock worker response with a valid JSON string
        mock_stub = MagicMock()
        mock_stub.ProcessChunk.return_value = MagicMock(
            result='[{"class": "car", "bounding_box": [10, 20, 30, 40], "confidence": 0.9}]'  # Correct JSON string
        )
        self.mock_insecure_channel.return_value = mock_stub

        # Call the method
        servicer = master.MasterServiceServicer()
        detections = servicer.send_image_to_worker(self.worker_address, self.image_data)

        # Verify
        self.assertEqual(len(detections), 1)
        self.assertEqual(detections[0]["class"], "car")

    def test_start_worker(self):
        self.mock_check_worker_ready.return_value = True
        self.mock_popen.return_value = MagicMock()

        # Call the method
        master.MasterServiceServicer().start_worker(50052)

        # Verify worker registry updates
        self.assertIn(self.worker_address, master.worker_registry)

    def test_stop_worker(self):
        # Mock worker registry with a mock process
        master.worker_registry[self.worker_address] = {"process": MagicMock()}

        # Call the method
        master.MasterServiceServicer().stop_worker(self.worker_address)

        # Verify process termination
        master.worker_registry[self.worker_address]["process"].terminate.assert_called_once()
        self.assertNotIn(self.worker_address, master.worker_registry)

    def test_process_image(self):
        # Mock image and detections
        mock_image = MagicMock()
        mock_image.size = (300, 300)
        self.mock_image_open.return_value = mock_image
        self.mock_send_image_to_worker.return_value = [
            {"class": "car", "bounding_box": [10, 20, 30, 40], "confidence": 0.9}]  # Mock response

        # Create a request
        request = image_processing_pb2.ImageRequest(image_data=self.image_data)
        servicer = master.MasterServiceServicer()

        # Call the method
        response = servicer.ProcessImage(request, None)

        # Verify response
        self.assertEqual(len(response.worker_responses), 1)
        self.assertIn("car detected", response.worker_responses[0].result)


if __name__ == "__main__":
    unittest.main()
