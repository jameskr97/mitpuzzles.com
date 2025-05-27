import logging
import time
import typing
from functools import wraps

from channels.generic.websocket import JsonWebsocketConsumer
from django.utils import timezone

from puzzles.engines import get_puzzle_engine, PuzzleEngineBase
from puzzles.models import ActivePuzzleSession
from puzzles.monitor import get_admin_monitor
from utils.auth import get_current_actor


def ensure_session_loaded(func):
    """
    Decorator to ensure the puzzle session is loaded in memory.
    If the session is not loaded, it will attempt to load it from the database.
    If the session is not found, it will send an error message.

    This is only to load existing sessions, not to create new ones. `handle_create` should be used for that.
    """
    @wraps(func)
    def wrapper(self, data=None, session_id=None):
        if not session_id:
            return self.send_error("Missing session_id")
        if not self.ensure_puzzle_in_memory(session_id):
            return self.send_error(f"Session {session_id} not found", session_id=session_id)
        return func(self, data, session_id)
    return wrapper


class PuzzleConsumer(JsonWebsocketConsumer):
    logger = logging.getLogger(__name__)

    def __init__(self, *args, **kwargs):
        super().__init__(args, kwargs)
        self.actor = None
        self.active_sessions: typing.Dict[str, typing.Tuple[ActivePuzzleSession, PuzzleEngineBase]] = {}
        self.puzzle_type_sessions = {}
        self.group_name = None
        self.admin_monitor = None

    def connect(self):
        self.admin_monitor = get_admin_monitor(self.channel_layer)
        self.actor = get_current_actor(self.scope)
        self.is_admin = getattr(self.actor, "is_staff", False)
        if not self.is_admin: # Only register non-admins as users initially
            self.admin_monitor.register_user(self.actor.id)
        self.accept()
        self.logger.info(f"User {getattr(self.actor, 'id', 'Unknown')} connected.")

    def disconnect(self, code):
        if self.is_admin:
            self.admin_monitor.unregister_admin(self.channel_name)
        # Always attempt to unregister the user from game playing perspective
        self.admin_monitor.unregister_user(self.actor.id)
        self.logger.info(f"User {getattr(self.actor, 'id', 'Unknown')} disconnected.")

    def receive_json(self, content, **kwargs):
        message_type = content.get("type", "")
        data = content.get("data", {})
        session_id = content.get("session_id")

        if message_type.startswith("cmd:admin:"):
            command = message_type[10:]
            handler_map = {
                "monitor": self.handle_admin_monitor,
                "unmonitor": self.handle_admin_unmonitor,
            }

            handler = handler_map.get(command)
            if handler:
                handler()
            else:
                self.send_error(f"Unknown admin command: {command}")
            return None

        if message_type.startswith("cmd:"):
            command = message_type[4:]
            handler_map = {
                "create": self.handle_create,
                "resume": self.handle_resume,
                "reset": self.handle_reset,
                "action": self.handle_action,
                "submit": self.handle_submit,
            }

            handler = handler_map.get(command)
            if handler:
                handler(data, session_id)
                if session_id in self.active_sessions:
                    session, engine = self.active_sessions[session_id]
                    print(session.move_history)
            else:
                self.send_error(f"Unknown command: {command}")
        else:
            self.send_error(f"Invalid message type: {message_type}")
            return None
        return None

    ################################################################################
    #### Event Senders
    def send_state(self, session_id):
        """Send the current puzzle state"""
        if session_id not in self.active_sessions:
            return self.send_error(f"Session {session_id} not found")

        puzzle_session, engine = self.active_sessions[session_id]

        state = engine.serialize_gamedata()
        state["puzzle_id"] = puzzle_session.puzzle.id
        state["session_id"] = session_id
        state["puzzle_type"] = puzzle_session.puzzle.puzzle_type
        state["puzzle_size"] = puzzle_session.puzzle.puzzle_size
        state["puzzle_difficulty"] = puzzle_session.puzzle.puzzle_difficulty
        state["is_solved"] = puzzle_session.is_solved

        self.send_json({"type": "event:state", "data": state, "session_id": session_id})

        # If the current user is an admin and is now playing (sending state),
        # ensure they are registered in the monitor as an active user.
        if self.is_admin:
            self.admin_monitor.register_user(str(self.actor.id))

        # Broadcast state to admin monitor (now includes admins who are playing)
        self.admin_monitor.broadcast_state(str(self.actor.id), str(session_id), state)
        return None

    def send_error(self, message, details=None, session_id=None):
        """Send an error message"""
        response = {"type": "event:error", "data": {"message": message}}
        if details:
            response["data"]["details"] = details
        if session_id:
            response["session_id"] = session_id
        self.send_json(response)

    ################################################################################
    #### Event Handlers
    def handle_create(self, data, session_id=None):
        """Create a new puzzle session/Request a new puzzle for an existing session"""
        self.logger.info(f"User {getattr(self.actor, 'id', 'Unknown')} executed handle_create with data: {data}")
        puzzle_type = data.get("puzzle_type")
        if not puzzle_type:
            return self.send_error("Missing puzzle_type")
        size = data.get("puzzle_size", None)
        difficulty = data.get("puzzle_difficulty", None)
        try:
            # create a new puzzle session
            engine = ActivePuzzleSession.create_puzzle_engine(self.actor, puzzle_type, size, difficulty)

            # store the session in the active sessions
            session_id = str(engine.puzzle_session.id)
            self.active_sessions[session_id] = (engine.puzzle_session, engine)

            solution = engine.get_solution_board_string()
            self.logger.info(f"Solution for puzzle {session_id}: {solution}")

            self.send_state(session_id)
        except Exception as e:
            self.send_error(f"Failed to create puzzle: {str(e)}")
        return None

    def handle_resume(self, data, session_id=None):
        """Resume an existing puzzle session"""
        self.logger.info(
            f"User {getattr(self.actor, 'id', 'Unknown')} executed handle_resume with session_id: {session_id}"
        )
        if self.ensure_puzzle_in_memory(session_id):
            return self.send_state(session_id)
        # invariant: session_id does not exist in-memory or in-database.
        # this would only happen if a session the user previously accessed was deleted from the database.
        # manual deletion? either way, just send then a new puzzle.
        return self.handle_create(data, None)

    @ensure_session_loaded
    def handle_action(self, data, session_id=None):
        """Process a puzzle action for a specific session"""
        self.logger.info(
            f"User {getattr(self.actor, 'id', 'Unknown')} executed handle_action with session_id: {session_id} and data: {data}"
        )

        try:
            session, engine = self.active_sessions[session_id]
            success = engine.handle_input_event(data)
            if success:
                board = list(engine.get_board_state())
                session.move_history.append(
                    {
                        "timestamp": time.time(),
                        "board": board
                    }
                )
                engine.save_active_puzzle()
                self.send_state(session_id)
        except Exception as e:
            self.send_error(f"Failed to process action: {str(e)}", session_id=session_id)
        return None

    @ensure_session_loaded
    def handle_reset(self, data, session_id=None):
        self.logger.info(
            f"User {getattr(self.actor, 'id', 'Unknown')} executed handle_reset with session_id: {session_id}"
        )
        """Reset a puzzle session"""
        try:
            _, engine = self.active_sessions[session_id]
            engine.board_clear()
            engine.save_active_puzzle()
            self.send_state(session_id)
        except Exception as e:
            self.send_error(f"Failed to reset puzzle: {str(e)}", session_id=session_id)
        return None

    @ensure_session_loaded
    def handle_submit(self, data, session_id=None):
        self.logger.info(
            f"User {getattr(self.actor, 'id', 'Unknown')} executed handle_submit with session_id: {session_id}"
        )
        try:
            puzzle_session, engine = self.active_sessions[session_id]
            payload = {
                "type": "event:submit_result",
                "data": {"is_solved": True},
                "session_id": session_id,
            }

            solved = engine.is_solved()
            puzzle_session.is_solved = solved
            payload["data"]["is_solved"] = solved
            self.send_json(payload)
            puzzle_session.save()

            if solved:
                puzzle_session.convert_to_game_recording()

        except Exception as e:
            self.send_error(f"Failed to validate puzzle: {str(e)}", session_id=session_id)
        return None

    ################################################################################
    #### Admin Monitoring Commands
    def handle_admin_monitor(self):
        """Handle admin monitoring commands"""
        self.logger.info(f"Admin {getattr(self.actor, 'id', 'Unknown')} executed handle_admin_monitor.")
        if self.is_admin:
            self.admin_monitor.register_admin(self.channel_name)
        return None

    def handle_admin_unmonitor(self):
        """Handle admin unmonitoring commands"""
        self.logger.info(f"Admin {getattr(self.actor, 'id', 'Unknown')} executed handle_admin_unmonitor.")
        if self.is_admin:
            self.admin_monitor.unregister_admin(self.channel_name)
        return None

    ################################################################################
    #### Helpers
    def store_active_sessions(self, session: ActivePuzzleSession) -> (ActivePuzzleSession, PuzzleEngineBase):
        """Store the active sessions in the database"""
        engine = get_puzzle_engine(session)
        session_id = str(session.id)
        self.active_sessions[session_id] = (session, engine)
        return session, engine

    def ensure_puzzle_in_memory(self, session_id) -> bool:
        """
        Ensure the puzzle session is in memory.
        :param session_id: session_id to load in memory
        :return: true if the session is in memory, false otherwise
        """
        if session_id in self.active_sessions:
            return True

        puzzle_session = ActivePuzzleSession.fetch_for_actor(session_id, self.actor)
        if puzzle_session:
            self.store_active_sessions(puzzle_session)
            return True
        return False

    ################################################################################
    #### Channel Layer Group Handlers
    def receive_user_gamestate(self, event):
        self.send_json(
            {
                "type": "event:monitor:state",
                "session_id": event["session_id"],
                "actor_id": event["actor_id"],
                "data": event["data"],
            }
        )

    def receive_user_count_update(self, event):
        self.send_json({"type": "event:monitor:user_count", "data": {"user_count": event["user_count"]}})

    def receive_user_disconnect(self, event):
        self.send_json(
            {
                "type": "event:monitor:disconnect",
                "actor_id": event["actor_id"],
            }
        )
