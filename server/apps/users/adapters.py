from typing import Any

from allauth.headless.adapter import DefaultHeadlessAdapter

from .serializers import UserSerializer


class HeadlessAdapter(DefaultHeadlessAdapter):
    def serialize_user(self, user) -> dict[str, Any]:
        return UserSerializer(user, context={"request": self.request}).data
