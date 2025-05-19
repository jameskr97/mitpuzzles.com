from asgiref.sync import sync_to_async, async_to_sync
from channels.generic.websocket import AsyncJsonWebsocketConsumer, JsonWebsocketConsumer

from puzzles.engines import get_puzzle_engine
from puzzles.models import ActivePuzzleSession
from puzzles.monitor import AdminGameMonitor, get_admin_monitor
from utils.auth import get_current_actor


class PuzzleConsumer(JsonWebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(args, kwargs)
        self.actor = None
        self.active_sessions = {}
        self.puzzle_type_sessions = {}
        self.group_name = None
        self.admin_monitor = None

    def connect(self):
        self.admin_monitor = get_admin_monitor(self.channel_layer)
        self.actor = get_current_actor(self.scope)
        self.is_admin = getattr(self.actor, "is_staff", False)
        self.admin_monitor.register_user(self.actor.id)
        self.accept()

    def disconnect(self, code):
        if self.is_admin:
            self.admin_monitor.unregister_admin(self.channel_name)
        else:
            self.admin_monitor.unregister_user(self.actor.id)

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

        self.send_json({"type": "event:state", "data": state, "session_id": session_id})
        if not self.is_admin:
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
        """Create a new puzzle session"""
        puzzle_type = data.get("puzzle_type")
        difficulty = data.get("puzzle_difficulty", None)
        if not puzzle_type:
            return self.send_error("Missing puzzle_type")

        try:
            # create a new puzzle session
            # puzzle_session = await sync_to_async(ActivePuzzleSession.create_puzzle_session)(
            puzzle_session = ActivePuzzleSession.create_puzzle_session(
                self.actor, puzzle_type, difficulty
            )
            engine = get_puzzle_engine(puzzle_session)

            # store the session in the active sessions
            session_id = str(puzzle_session.id)
            self.active_sessions[session_id] = (puzzle_session, engine)
            # self.puzzle_type_sessions[puzzle_type] = session_id
            self.send_state(session_id)
        except Exception as e:
            self.send_error(f"Failed to create puzzle: {str(e)}")
        return None

    def handle_resume(self, data, session_id=None):
        """Resume an existing puzzle session"""
        if not session_id:
            return self.send_error("Missing session_id")

        # if this session is already loaded into this websocket connection, just send the state
        if session_id in self.active_sessions:
            return self.send_state(session_id)

        try:
            # fetch the puzzle session
            # puzzle_session = await sync_to_async(ActivePuzzleSession.fetch_for_actor)(session_id, self.actor)
            puzzle_session = ActivePuzzleSession.fetch_for_actor(session_id, self.actor)
            if not puzzle_session:
                # the session_id the user provided is invalid or does not belong to them.
                # NOTE: currently not handling if user A has a session_id of user B. that shouldn't happen...
                # return await self.send_error("Invalid or unauthorized session", session_id=session_id)
                puzzle_type = data.get("puzzle_type")
                if not puzzle_type:
                    return self.send_error("Missing puzzle_type")

                self.handle_create({"puzzle_type": puzzle_type})
                return None
            # invariant - the puzzle session does exist

            # check if we already have a session for this puzzle type
            self.store_active_sessions(puzzle_session)
            self.send_state(session_id)
        except Exception as e:
            self.send_error(f"Failed to resume session: {str(e)}", session_id=session_id)
        return None

    def handle_action(self, data, session_id=None):
        """Process a puzzle action for a specific session"""
        if not session_id:
            return self.send_error("Missing session_id")

        if session_id not in self.active_sessions:
            # attempt to look up the session
            puzzle_session = ActivePuzzleSession.fetch_for_actor(session_id, self.actor)
            if not puzzle_session:
                return self.send_error("Invalid or unauthorized session", session_id=session_id)
            self.store_active_sessions(puzzle_session)

        try:
            _, engine = self.active_sessions[session_id]
            success = engine.handle_input_event(data)

            if success:
                engine.save_active_puzzle()
                self.send_state(session_id)

        except Exception as e:
            self.send_error(f"Failed to process action: {str(e)}", session_id=session_id)
        return None

    def handle_reset(self, data, session_id=None):
        """Reset a puzzle session"""
        if not session_id:
            return self.send_error("Missing session_id")

        if session_id not in self.active_sessions:
            return self.send_error(f"Session {session_id} not found", session_id=session_id)
        try:
            _, engine = self.active_sessions[session_id]
            engine.board_clear()
            engine.save_active_puzzle()
            self.send_state(session_id)
        except Exception as e:
            self.send_error(f"Failed to reset puzzle: {str(e)}", session_id=session_id)
        return None

    def handle_submit(self, data, session_id=None):
        if not session_id:
            return self.send_error("Missing session_id")

        if session_id not in self.active_sessions:
            return self.send_error(f"Session {session_id} not found", session_id=session_id)

        try:
            puzzle_session, engine = self.active_sessions[session_id]
            if engine.is_solved():
                # Mark as submitted in the database
                # puzzle_sessionn.is_submitted = True
                # await sync_to_async(puzzle_session.save)()

                # Send success message
                self.send_json(
                    {
                        "type": "event:submit_result",
                        "data": {"success": True},
                        "session_id": session_id,
                    }
                )
            else:
                # Send failure message
                self.send_json(
                    {
                        "type": "event:submit_result",
                        "data": {"success": False},
                        "session_id": session_id,
                    }
                )

            engine.save_active_puzzle()
            # await self.send_state(session_id)
        except Exception as e:
            self.send_error(f"Failed to validate puzzle: {str(e)}", session_id=session_id)
        return None

    ################################################################################
    #### Admin Monitoring Commands
    def handle_admin_monitor(self):
        """Handle admin monitoring commands"""
        if self.is_admin:
            self.admin_monitor.register_admin(self.channel_name)
        return None

    def handle_admin_unmonitor(self):
        """Handle admin unmonitoring commands"""
        if self.is_admin:
            self.admin_monitor.unregister_admin(self.channel_name)
        return None

    ################################################################################
    #### Helpers
    def store_active_sessions(self, session: ActivePuzzleSession):
        """Store the active sessions in the database"""
        engine = get_puzzle_engine(session)
        session_id = str(session.id)
        self.active_sessions[session_id] = (session, engine)

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
