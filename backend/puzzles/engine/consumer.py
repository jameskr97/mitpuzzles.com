"""
Modern event-driven puzzle consumer using Blueprint system.

This consumer publishes events to registered blueprints, providing a clean
and modular architecture for handling puzzle operations.
"""

import logging
import typing
from channels.generic.websocket import JsonWebsocketConsumer
from django.conf import settings

from puzzles.engine.events.decorators import on_event
from puzzles.engine.games import get_puzzle_engine, PuzzleEngineBase
from puzzles.models import ActivePuzzleSession
from utils.auth import get_current_actor

# Import event system
from puzzles.engine.events.bus import event_bus
from puzzles.engine.events.event import Event


def ensure_session_loaded(event):
    """Helper to ensure session exists and is loaded"""
    if not event.session_id:
        event.consumer.send_error("Missing session_id")
        return False

    if not event.consumer.ensure_puzzle_in_memory(event.session_id):
        event.consumer.send_error(f"Session {event.session_id} not found", session_id=event.session_id)
        return False

    return True


class PuzzleConsumer(JsonWebsocketConsumer):
    """
    Event-driven puzzle consumer with Blueprint support.
    
    This consumer publishes all incoming messages as events to the event bus,
    which are then handled by registered blueprints. This provides a clean
    separation of concerns and makes it easy to add new functionality.
    """
    
    logger = logging.getLogger(__name__)

    def __init__(self, *args, **kwargs):
        super().__init__(args, kwargs)
        self.actor = None
        self.active_sessions: typing.Dict[str, typing.Tuple[ActivePuzzleSession, PuzzleEngineBase]] = {}

    def connect(self):
        """Handle WebSocket connection"""
        self.actor = get_current_actor(self.scope)
        self.accept()
        
        self.logger.info(f"User {getattr(self.actor, 'id', 'Unknown')} connected.")

    def disconnect(self, code):
        """Handle WebSocket disconnection"""
        self.logger.info(f"User {getattr(self.actor, 'id', 'Unknown')} disconnected.")

    def receive_json(self, content, **kwargs):
        """Handle incoming JSON messages by publishing to event bus"""
        message_type = content.get("type", "")
        data = content.get("data", {})
        session_id = content.get("session_id")

        event = Event(
            type=message_type, 
            data=data, 
            session_id=session_id, 
            consumer=self
        )
        
        self.logger.debug(f"Publishing event: {message_type}")
        event_bus.publish(event)

    def send_state(self, session_id):
        """Send current puzzle state"""
        if session_id not in self.active_sessions:
            return self.send_error(f"Session {session_id} not found")

        puzzle_session, engine = self.active_sessions[session_id]

        # Build state data
        state = engine.serialize_gamedata()
        state["puzzle_id"] = puzzle_session.puzzle.id
        state["session_id"] = session_id
        state["puzzle_type"] = puzzle_session.puzzle.puzzle_type
        state["puzzle_size"] = puzzle_session.puzzle.puzzle_size
        state["puzzle_difficulty"] = puzzle_session.puzzle.puzzle_difficulty
        state["is_solved"] = puzzle_session.is_solved
        state["is_tutorial"] = puzzle_session.is_tutorial
        state["violations"] = [v.to_dict() for v in engine.validate()] if puzzle_session.is_tutorial else []

        self.send_json({
            "type": "event:state", 
            "data": state, 
            "session_id": session_id
        })
        
        return None

    def send_error(self, message, details=None, session_id=None):
        """Send error message"""
        response = {"type": "event:error", "data": {"message": message}}
        if details:
            response["data"]["details"] = details
        if session_id:
            response["session_id"] = session_id
        self.send_json(response)

    def ensure_puzzle_in_memory(self, session_id) -> bool:
        """Ensure puzzle session is loaded in memory"""
        if session_id in self.active_sessions:
            return True

        # Try to fetch from database
        puzzle_session = ActivePuzzleSession.fetch_for_actor(session_id, self.actor)
        if puzzle_session:
            # Load into memory
            engine = get_puzzle_engine(puzzle_session)
            self.active_sessions[session_id] = (puzzle_session, engine)
            return True

        return False

    # Saving and Loading Active Sessions
    def save_active_puzzle(self, session_id) -> bool:
        """Save current puzzle state to database"""
        if session_id not in self.active_sessions:
            self.send_error(f"Session {session_id} not found")
            return True

        puzzle_session, engine = self.active_sessions[session_id]
        try:
            puzzle_session.save()
            self.logger.info(f"Puzzle session {session_id} saved successfully")
            return True
        except Exception as e:
            self.logger.error(f"Failed to save puzzle session {session_id}: {str(e)}")
            self.send_error(f"Failed to save puzzle: {str(e)}", session_id=session_id)
            return False

    # Channel Layer Group Handlers (for admin monitoring)
    def receive_user_gamestate(self, event):
        """Handle user gamestate updates from channel layer"""
        self.send_json({
            "type": "event:monitor:state",
            "session_id": event["session_id"],
            "actor_id": event["actor_id"],
            "data": event["data"],
        })

    def receive_user_count_update(self, event):
        """Handle user count updates from channel layer"""
        self.send_json({
            "type": "event:monitor:user_count", 
            "data": {"user_count": event["user_count"]}
        })

    def receive_user_disconnect(self, event):
        """Handle user disconnect notifications from channel layer"""
        self.send_json({
            "type": "event:monitor:disconnect",
            "actor_id": event["actor_id"],
        })


logger = logging.getLogger(__name__)

@on_event("cmd:create")
def handle_create(event):
    """Create a new puzzle session"""
    logger.info(f"Creating puzzle for user {getattr(event.consumer.actor, 'id', 'Unknown')}")

    puzzle_type = event.data.get("puzzle_type")
    if not puzzle_type:
        return event.consumer.send_error("Missing puzzle_type")

    size = event.data.get("puzzle_size", None)
    difficulty = event.data.get("puzzle_difficulty", None)

    try:
        # Create puzzle engine
        engine = ActivePuzzleSession.create_puzzle_engine(event.consumer.actor, puzzle_type, size, difficulty)
        session_id = str(engine.puzzle_session.id)
        event.consumer.active_sessions[session_id] = (engine.puzzle_session, engine)  # Store in consumer
        event.consumer.send_state(session_id) # Send initial state

    except Exception as e:
        if settings.DEBUG:
            logger.exception(f"Error creating puzzle for user [{getattr(event.consumer.actor, 'id', 'Unknown')}]: {str(e)}")
        event.consumer.send_error(f"Failed to create puzzle: {str(e)}")
    return None

@on_event("cmd:resume")
def handle_resume(event):
    """Resume an existing puzzle session"""
    logger.info(f"Resuming session: {event.session_id}")

    if not event.session_id:
        return event.consumer.send_error("Missing session_id for resume")

    # Try to load session into memory
    if event.consumer.ensure_puzzle_in_memory(event.session_id):
        # Session loaded successfully, send current state
        return event.consumer.send_state(event.session_id)


    # Session not found in database, create a new one instead
    logger.info(f"Session {event.session_id} not found, creating new puzzle")
    return handle_create(event)

@on_event("cmd:action")
def handle_action(event):
    """Process a puzzle action"""
    if not ensure_session_loaded(event):
        return
    logger.info(f"Processing action for session {event.session_id}")

    try:
        session, engine = event.consumer.active_sessions[event.session_id]
        success = engine.handle_input_event(event.data)

        if success:
            # Save move to history
            board = list(engine.get_board_state())
            session.move_history.append({"timestamp": event.timestamp, "board": board})
            session.save()
            event.consumer.send_state(event.session_id) # Send updated state
    except Exception as e:
        if settings.DEBUG:
            logger.exception(f"Error processing action for session [{event.session_id}]: {str(e)}")
        event.consumer.send_error(f"Failed to process action: {str(e)}", session_id=event.session_id)

@on_event("cmd:reset")
def handle_reset(event):
    """Reset puzzle to initial state"""
    if not ensure_session_loaded(event):
        return

    logger.info(f"Resetting session: {event.session_id}")

    try:
        session, engine = event.consumer.active_sessions[event.session_id]
        engine.board_clear()
        session.save()
        event.consumer.send_state(event.session_id)

    except Exception as e:
        if settings.DEBUG:
            logger.exception(f"Error resetting puzzle session [{event.session_id}]: {str(e)}")
        event.consumer.send_error(f"Failed to reset puzzle: {str(e)}", session_id=event.session_id)

@on_event("cmd:submit")
def handle_submit(event):
    """Submit puzzle solution"""
    if not ensure_session_loaded(event):
        return

    logger.info(f"Submitting solution for session: {event.session_id}")

    try:
        puzzle_session, engine = event.consumer.active_sessions[event.session_id]
        solved = engine.is_solved()
        puzzle_session.is_solved = solved
        puzzle_session.save()

        # Send result
        event.consumer.send_json( {
            "type": "event:submit_result",
            "data": {"is_solved": solved},
            "session_id": event.session_id,
        })

        # Convert to recording if solved
        if solved:
            puzzle_session.convert_to_game_recording()

    except Exception as e:
        if settings.DEBUG:
            logger.exception(f"Error submitting solution for session [{event.session_id}]: {str(e)}")
        event.consumer.send_error(f"Failed to validate puzzle: {str(e)}", session_id=event.session_id)

@on_event("cmd:toggle_tutorial")
def handle_toggle_tutorial(event):
    """Toggle tutorial mode for the session"""
    if not ensure_session_loaded(event):
        return

    logger.info(f"Toggling tutorial mode for session: {event.session_id}")

    try:
        puzzle_session, _ = event.consumer.active_sessions[event.session_id]
        puzzle_session.is_tutorial = event.data.get("enabled", False)
        puzzle_session.used_tutorial = True  # Mark as used if toggled
        puzzle_session.save()

        # Send updated state
        event.consumer.send_state(event.session_id)

    except Exception as e:
        event.consumer.send_error(f"Failed to toggle tutorial mode: {str(e)}", session_id=event.session_id)

@on_event("cmd:create")
@on_event("cmd:resume")
@on_event("cmd:action")
@on_event("cmd:submit")
@on_event("cmd:reset")
@on_event("cmd:toggle_tutorial")
def log_command(event):
    """Log all puzzle commands"""
    command = event.get_command()
    user_id = getattr(event.consumer.actor, "id", "Unknown")
    print(f"User: {user_id} | Session: {event.session_id} | Command: {command} =>  {event.data}")
