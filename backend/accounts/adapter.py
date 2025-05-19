from typing import Dict, Any

from allauth.headless.adapter import DefaultHeadlessAdapter


class CustomHeadlessAdapter(DefaultHeadlessAdapter):

    def serialize_user(self, user) -> Dict[str, Any]:
        res = super().serialize_user(user)
        res["is_admin"] = user.is_staff
        return res
