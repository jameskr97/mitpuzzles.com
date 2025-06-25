import uuid

from channels.auth import AuthMiddlewareStack
from channels.db import database_sync_to_async
from channels.testing import WebsocketCommunicator
from django.test import TransactionTestCase

from experiments.models import Experiment, ProlificSession
from puzzles.engine.consumer import PuzzleConsumerN as GameConsumer
from puzzles.middleware import CookieMiddleware
from tracking.models import Visitor


class WebSocketAuthTestCase(TransactionTestCase):
    """Test WebSocket authentication flows"""

    def setUp(self):
        # Set up the test environment
        self.CONNECTION_PATH = "/ws/puzzle/"
        self.visitor_id = str(uuid.uuid4())
        self.visitor = Visitor.objects.create(id=self.visitor_id)
        self.get_communicator = lambda with_cookie=True: WebsocketCommunicator(
            CookieMiddleware(AuthMiddlewareStack(GameConsumer.as_asgi())),
            "/ws/puzzle/",
            headers=[(b"cookie", f"visitor_id={self.visitor_id};".encode())] if with_cookie else []
        )

        # Setup Prolific user test data
        self.prolific = {
            "prolific_id": "TEST_PROLIFIC_ID",
            "session_id": "TEST_SESSION_ID",
            "study_id": "require_authenticated",
        }

        # Setup sample experiment data
        self.experiment = Experiment.objects.create(
            name="Test Experiment",
            config={
                "trials": ["puzzle:1234", "puzzle:4567", "puzzle:1289"],
                "comprehension_questions":[
                    {"answer": True, "question": "Answer this question with the value true"},
                    {"answer": False, "question": "Answer this question with the value false"},
                ]
            }
        )
        self.experiment_id = str(self.experiment.id)

    async def helper_auth_prolific(self, communicator, experiment_id, prolific_id, session_id, study_id):
        """A function to get the user a prolific auth session."""

        # Send prolific auth
        await communicator.send_json_to({
            "type": "auth:prolific",
            "experiment_id": experiment_id,
            "prolific_id": prolific_id,
            "session_id": session_id,
            "study_id": study_id
        })

        response = await communicator.receive_json_from()
        self.assertEqual(response["type"], "auth:prolific:success")
        self.assertEqual(response["mode"], "prolific")
        self.assertEqual(response["experiment_id"], self.experiment_id)
        return response

    async def test_connect_no_visitor_cookie(self):
        """Test freeplay auth without visitor cookie"""
        # Create communicator without visitor cookie
        communicator = self.get_communicator(with_cookie=False)
        connected, _ = await communicator.connect()
        self.assertTrue(connected)

        # Receive connection message
        response = await communicator.receive_json_from()
        self.assertEqual(response["type"], "auth:failed")
        self.assertEqual(response["message"], "unable to connect to websocket server")

        await communicator.disconnect()

    async def test_freeplay_auth_success(self):
        """Test successful freeplay authentication"""
        # Create communicator with visitor cookie
        communicator = self.get_communicator()
        connected, _ = await communicator.connect()
        self.assertTrue(connected)

        # Receive connection message
        response = await communicator.receive_json_from()
        self.assertEqual(response["type"], "auth:connection")
        self.assertEqual(response["status"], "connected")

        # Send freeplay auth
        await communicator.send_json_to({"type": "auth:freeplay"})
        response = await communicator.receive_json_from()
        self.assertEqual(response["type"], "auth:freeplay:success")
        self.assertEqual(response["mode"], "freeplay")
        self.assertEqual(response["visitor_id"], self.visitor_id)
        self.assertTrue(response["authenticated"])
        self.assertIsNone(response["user_id"])

        await communicator.disconnect()

    async def test_prolific_auth_success(self):
        """Test successful prolific authentication"""
        communicator = self.get_communicator()
        connected, _ = await communicator.connect()
        self.assertTrue(connected)
        await communicator.receive_json_from() # Skip connection message
        response = await self.helper_auth_prolific(
            communicator,
            self.experiment_id,
            "TEST_PROLIFIC_ID",
            "TEST_SESSION_ID",
            "TEST_STUDY_ID"
        )

        # Verify database record created
        prolific_session = await database_sync_to_async(ProlificSession.objects.select_related('visitor').get)(
            prolific_id=self.prolific["prolific_id"],
            session_id=self.prolific["session_id"],
            experiment_id=self.experiment_id,
        )
        self.assertEqual(prolific_session.prolific_id, self.prolific["prolific_id"])
        self.assertEqual(str(prolific_session.visitor.id), self.visitor_id)
        self.assertEqual(str(prolific_session.id), response["prolific_session_id"])

        await communicator.disconnect()

    async def test_prolific_auth_missing_experiment_id(self):
        """Test prolific auth with missing parameters"""
        communicator = self.get_communicator()
        connected, _ = await communicator.connect()
        self.assertTrue(connected)
        await communicator.receive_json_from() # Skip connection message

        payload = {"type": "auth:prolific", **self.prolific}
        await communicator.send_json_to(payload)

        response = await communicator.receive_json_from()
        self.assertEqual(response["type"], "auth:failed")
        self.assertIn("message", response)

        await communicator.disconnect()

    async def test_prolific_auth_missing_prolific_id(self):
        """Test prolific auth with missing parameters"""
        communicator = self.get_communicator()
        connected, _ = await communicator.connect()
        self.assertTrue(connected)
        await communicator.receive_json_from() # Skip connection message

        payload = {"type": "auth:prolific", **self.prolific}
        del payload["prolific_id"]  # Remove prolific_id to simulate missing parameter
        await communicator.send_json_to(payload)

        response = await communicator.receive_json_from()
        self.assertEqual(response["type"], "auth:failed")
        self.assertIn("message", response)

        await communicator.disconnect()

        async def test_prolific_auth_missing_experiment_id(self):
            """Test prolific auth with missing parameters"""
            communicator = self.get_communicator()
            connected, _ = await communicator.connect()
            self.assertTrue(connected)
            await communicator.receive_json_from()  # Skip connection message

            payload = {"type": "auth:prolific", **self.prolific}
            await communicator.send_json_to(payload)

            response = await communicator.receive_json_from()
            self.assertEqual(response["type"], "auth:failed")
            self.assertIn("message", response)

            await communicator.disconnect()

    async def test_prolific_auth_missing_study_id(self):
        """Test prolific auth with missing parameters"""
        communicator = self.get_communicator()
        connected, _ = await communicator.connect()
        self.assertTrue(connected)
        await communicator.receive_json_from() # Skip connection message

        payload = {"type": "auth:prolific", **self.prolific}
        del payload["study_id"]  # Remove study_id to simulate missing parameter
        await communicator.send_json_to(payload)

        response = await communicator.receive_json_from()
        self.assertEqual(response["type"], "auth:failed")
        self.assertIn("message", response)

        await communicator.disconnect()

    async def test_prolific_auth_missing_session_id(self):
        """Test prolific auth with missing parameters"""
        communicator = self.get_communicator()
        connected, _ = await communicator.connect()
        self.assertTrue(connected)
        await communicator.receive_json_from() # Skip connection message

        payload = {"type": "auth:prolific", **self.prolific}
        del payload["session_id"]  # Remove session_id to simulate missing parameter
        await communicator.send_json_to(payload)

        response = await communicator.receive_json_from()
        self.assertEqual(response["type"], "auth:failed")
        self.assertIn("message", response)

        await communicator.disconnect()

    # async def test_game_action_without_auth(self):
    #     """Test that game actions fail without authentication"""
    #     communicator = WebsocketCommunicator(
    #         GameConsumer.as_asgi(), "/ws/game/", headers=[(b"cookie", f"visitor_id={self.visitor_id}".encode())]
    #     )
    #
    #     connected, _ = await communicator.connect()
    #     await communicator.receive_json_from()  # Skip connection
    #
    #     # Try to start game without auth
    #     await communicator.send_json_to({"type": "game:start", "game_type": "sudoku"})
    #
    #     response = await communicator.receive_json_from()
    #     self.assertEqual(response["type"], "error")
    #     self.assertEqual(response["code"], "AUTH_REQUIRED")
    #
    #     await communicator.disconnect()
    #
    # async def test_game_action_after_auth(self):
    #     """Test that game actions work after authentication"""
    #     communicator = WebsocketCommunicator(
    #         GameConsumer.as_asgi(), "/ws/game/", headers=[(b"cookie", f"visitor_id={self.visitor_id}".encode())]
    #     )
    #
    #     connected, _ = await communicator.connect()
    #     await communicator.receive_json_from()  # Skip connection
    #
    #     # Authenticate first
    #     await communicator.send_json_to({"type": "auth:freeplay"})
    #     await communicator.receive_json_from()  # Skip auth success
    #
    #     # Now try game action
    #     await communicator.send_json_to({"type": "game:start", "game_type": "sudoku"})
    #
    #     response = await communicator.receive_json_from()
    #     self.assertEqual(response["type"], "game:started")
    #     self.assertIn("game_id", response)
    #
    #     await communicator.disconnect()
    #
    # async def test_no_visitor_cookie(self):
    #     """Test connection without visitor cookie"""
    #     communicator = WebsocketCommunicator(GameConsumer.as_asgi(), "/ws/game/")
    #
    #     connected, _ = await communicator.connect()
    #     self.assertTrue(connected)
    #
    #     await communicator.receive_json_from()  # Connection message
    #
    #     # Should still be able to authenticate
    #     await communicator.send_json_to({"type": "auth:freeplay"})
    #
    #     response = await communicator.receive_json_from()
    #     self.assertEqual(response["type"], "auth:success")
    #     self.assertIsNone(response["visitor_id"])  # No visitor ID without cookie
    #
    #     await communicator.disconnect()
    #
    # async def test_prolific_mode_restriction(self):
    #     """Test that prolific-only actions fail in freeplay mode"""
    #     communicator = WebsocketCommunicator(
    #         GameConsumer.as_asgi(), "/ws/game/", headers=[(b"cookie", f"visitor_id={self.visitor_id}".encode())]
    #     )
    #
    #     connected, _ = await communicator.connect()
    #     await communicator.receive_json_from()
    #
    #     # Auth as freeplay
    #     await communicator.send_json_to({"type": "auth:freeplay"})
    #     await communicator.receive_json_from()
    #
    #     # Try prolific-only action
    #     await communicator.send_json_to({"type": "prolific:consent", "consent": True})
    #
    #     response = await communicator.receive_json_from()
    #     self.assertEqual(response["type"], "error")
    #     self.assertEqual(response["code"], "MODE_RESTRICTED")
    #
    #     await communicator.disconnect()


# # tests/test_websocket_auth_integration.py
# class WebSocketAuthIntegrationTest(TransactionTestCase):
#     """Integration tests for full auth flow"""
#
#     async def test_complete_prolific_flow(self):
#         """Test complete prolific participant flow"""
#         experiment_uuid = str(uuid.uuid4())
#         prolific_id = "INTEGRATION_TEST_ID"
#         visitor_id = str(uuid.uuid4())
#
#         # Create visitor
#         visitor = await database_sync_to_async(Visitor.objects.create)(visitor_id=visitor_id)
#
#         communicator = WebsocketCommunicator(
#             GameConsumer.as_asgi(), "/ws/game/", headers=[(b"cookie", f"visitor_id={visitor_id}".encode())]
#         )
#
#         # Connect and authenticate
#         connected, _ = await communicator.connect()
#         await communicator.receive_json_from()  # Connection
#
#         await communicator.send_json_to(
#             {"type": "auth:prolific", "experiment_uuid": experiment_uuid, "prolific_id": prolific_id}
#         )
#
#         auth_response = await communicator.receive_json_from()
#         self.assertEqual(auth_response["type"], "auth:success")
#
#         # Give consent
#         await communicator.send_json_to({"type": "prolific:consent", "consent": True})
#
#         consent_response = await communicator.receive_json_from()
#         self.assertEqual(consent_response["type"], "prolific:consent_accepted")
#
#         # Request trial
#         await communicator.send_json_to({"type": "prolific:next_trial"})
#
#         # This would return actual trial data in production
#         trial_response = await communicator.receive_json_from()
#
#         await communicator.disconnect()
