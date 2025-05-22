from asgiref.sync import async_to_sync
from datetime import datetime, timedelta
import threading
import time

class AdminGameMonitor:
    def __init__(self, channel_layer):
        self.channel_layer = channel_layer
        # user + admin sessions
        self.user_sessions = set()
        self.monitoring_admins = set()

        # game + connection state
        self.latest_user_states = {} # actor_id -> gamedata
        self.last_seen = {} # actor_id -> last seen time
        self._start_cleanup_loop()

    ################################################################################
    #### Stale User Pruning
    def _start_cleanup_loop(self):
        def loop():
            while True:
                self._remove_stale_users()
                time.sleep(30)

        threading.Thread(target=loop, daemon=True).start()

    def _remove_stale_users(self):
        now = datetime.now()
        cutoff = now - timedelta(minutes=5)

        stale = [aid for aid, seen in self.last_seen.items() if seen < cutoff]
        for actor_id in stale:
            self.unregister_user(actor_id)
            self.last_seen.pop(actor_id, None)

    def register_user(self, actor_id):
        self.user_sessions.add(str(actor_id))
        self.last_seen[str(actor_id)] = datetime.now()
        self._broadcast_user_count()

    def unregister_user(self, actor_id):
        self.user_sessions.discard(str(actor_id))
        self._broadcast_user_count()

        self.latest_user_states.pop(str(actor_id), None)
        self.last_seen.pop(str(actor_id), None)
        for channel in self.monitoring_admins:
            async_to_sync(self.channel_layer.send)(
                channel,
                {
                    "type": "receive_user_disconnect",
                    "actor_id": str(actor_id),
                },
            )

    def register_admin(self, channel_name):
        self.monitoring_admins.add(channel_name)
        self._broadcast_user_count()
        
        for actor_id, data in self.latest_user_states.items():
            async_to_sync(self.channel_layer.send)(
                channel_name,
                {
                    "type": "receive_user_gamestate",
                    "actor_id": actor_id,
                    "session_id": data.get("session_id", None),  # optional
                    "data": data,
                    "user_count": self.get_user_count(),
                },
            )

    def unregister_admin(self, channel_name):
        self.monitoring_admins.discard(channel_name)

    def broadcast_state(self, actor_id, session_id, data):
        key = str(actor_id)
        self.latest_user_states[key] = data
        self.last_seen[key] = datetime.now()

        for channel in self.monitoring_admins:
            async_to_sync(self.channel_layer.send)(channel, {
                "type": "receive_user_gamestate",
                "actor_id": actor_id,
                "session_id": session_id,
                "data": data,
            })

    def get_user_count(self):
        return len(self.user_sessions)

    def _broadcast_user_count(self):
        for channel in self.monitoring_admins:
            async_to_sync(self.channel_layer.send)(channel, {
                "type": "receive_user_count_update",
                "user_count": self.get_user_count()
            })

_shared_monitor = None
def get_admin_monitor(channel_layer):
    global _shared_monitor
    if _shared_monitor is None:
        _shared_monitor = AdminGameMonitor(channel_layer)
    return _shared_monitor
