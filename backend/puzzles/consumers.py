from asgiref.sync import sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer

from puzzles.engines import get_puzzle_engine
from puzzles.models import ActivePuzzleSession
from utils.auth import get_current_actor


class PuzzleConsumer(AsyncJsonWebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(args, kwargs)
        self.actor = None
        self.active_sessions = {}
        self.puzzle_type_sessions = {}

    async def connect(self):
        self.actor = await sync_to_async(get_current_actor)(self.scope)
        await self.accept()

    async def receive_json(self, content, **kwargs):
        message_type = content.get("type", "")
        data = content.get("data", {})
        session_id = content.get("session_id")
        print(message_type, data)

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
                await handler(data, session_id)
            else:
                await self.send_error(f"Unknown command: {command}")
        else:
            await self.send_error(f"Invalid message type: {message_type}")
        return None

    ################################################################################
    #### Event Senders

    async def send_state(self, session_id):
        """Send the current puzzle state"""
        if session_id not in self.active_sessions:
            return await self.send_error(f"Session {session_id} not found")

        puzzle_session, engine = self.active_sessions[session_id]

        state = engine.serialize_gamedata()
        state["puzzle_id"] = puzzle_session.puzzle.id
        state["session_id"] = session_id
        state["puzzle_type"] = puzzle_session.puzzle.puzzle_type

        await self.send_json({"type": "event:state", "data": state, "session_id": session_id})
        return None

    async def send_error(self, message, details=None, session_id=None):
        """Send an error message"""
        response = {"type": "event:error", "data": {"message": message}}
        if details:
            response["data"]["details"] = details
        if session_id:
            response["session_id"] = session_id
        await self.send_json(response)

    ################################################################################
    #### Event Handlers

    async def handle_create(self, data, session_id=None):
        """Create a new puzzle session"""
        puzzle_type = data.get("puzzle_type")
        difficulty = data.get("puzzle_difficulty", None)
        if not puzzle_type:
            return await self.send_error("Missing puzzle_type")

        try:
            # create a new puzzle session
            puzzle_session = await sync_to_async(ActivePuzzleSession.create_puzzle_session)(
                self.actor, puzzle_type, difficulty
            )
            engine = get_puzzle_engine(puzzle_session)

            # store the session in the active sessions
            session_id = str(puzzle_session.id)
            self.active_sessions[session_id] = (puzzle_session, engine)
            # self.puzzle_type_sessions[puzzle_type] = session_id
            await self.send_state(session_id)
        except Exception as e:
            await self.send_error(f"Failed to create puzzle: {str(e)}")
        return None

    async def handle_resume(self, data, session_id=None):
        """Resume an existing puzzle session"""
        if not session_id:
            return await self.send_error("Missing session_id")

        # if this session is already loaded into this websocket connection, just send the state
        if session_id in self.active_sessions:
            return await self.send_state(session_id)

        try:
            # fetch the puzzle session
            puzzle_session = await sync_to_async(ActivePuzzleSession.fetch_for_actor)(session_id, self.actor)
            if not puzzle_session:
                # the session_id the user provided is invalid or does not belong to them.
                # NOTE: currently not handling if user A has a session_id of user B. that shouldn't happen...
                # return await self.send_error("Invalid or unauthorized session", session_id=session_id)
                puzzle_type = data.get("puzzle_type")
                if not puzzle_type:
                    return await self.send_error("Missing puzzle_type")

                await self.handle_create({"puzzle_type": puzzle_type})
                return None
            # invariant - the puzzle session does exist

            # check if we already have a session for this puzzle type
            engine = get_puzzle_engine(puzzle_session)
            self.active_sessions[session_id] = (puzzle_session, engine)
            await self.send_state(session_id)
        except Exception as e:
            await self.send_error(f"Failed to resume session: {str(e)}", session_id=session_id)

    async def handle_action(self, data, session_id=None):
        """Process a puzzle action for a specific session"""
        if not session_id:
            return await self.send_error("Missing session_id")

        if session_id not in self.active_sessions:
            return await self.send_error(f"Session {session_id} not found", session_id=session_id)

        try:
            _, engine = self.active_sessions[session_id]
            success = engine.handle_input_event(data)

            if success:
                await engine.save_active_puzzle()
                await self.send_state(session_id)

        except Exception as e:
            await self.send_error(f"Failed to process action: {str(e)}", session_id=session_id)
        return None

    async def handle_reset(self, data, session_id=None):
        """Reset a puzzle session"""
        if not session_id:
            return await self.send_error("Missing session_id")

        if session_id not in self.active_sessions:
            return await self.send_error(f"Session {session_id} not found", session_id=session_id)
        try:
            _, engine = self.active_sessions[session_id]
            engine.board_clear()
            await engine.save_active_puzzle()
            await self.send_state(session_id)
        except Exception as e:
            await self.send_error(f"Failed to reset puzzle: {str(e)}", session_id=session_id)
        return None

    async def handle_submit(self, data, session_id=None):
        if not session_id:
            return await self.send_error("Missing session_id")

        if session_id not in self.active_sessions:
            return await self.send_error(f"Session {session_id} not found", session_id=session_id)

        try:
            puzzle_session, engine = self.active_sessions[session_id]
            if engine.is_solved():
                # Mark as submitted in the database
                # puzzle_sessionn.is_submitted = True
                # await sync_to_async(puzzle_session.save)()

                # Send success message
                await self.send_json(
                    {
                        "type": "event:submit_result",
                        "data": {"success": True},
                        "session_id": session_id,
                    }
                )
            else:
                # Send failure message
                await self.send_json(
                    {
                        "type": "event:submit_result",
                        "data": {"success": False},
                        "session_id": session_id,
                    }
                )

            await engine.save_active_puzzle()
            # await self.send_state(session_id)
        except Exception as e:
            await self.send_error(f"Failed to validate puzzle: {str(e)}", session_id=session_id)
        return None
