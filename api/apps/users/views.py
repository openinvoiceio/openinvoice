from drf_spectacular.utils import extend_schema
from rest_framework import generics, status
from rest_framework.response import Response

from .models import User
from .serializers import UserSerializer, UserUpdateSerializer


class ProfileRetrieveUpdateAPIView(generics.GenericAPIView):
    queryset = User.objects.none()
    serializer_class = UserSerializer

    @extend_schema(
        operation_id="retrieve_profile",
        responses={200: UserSerializer},
    )
    def get(self, _):
        serializer = UserSerializer(self.request.user, context=self.get_serializer_context())
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        operation_id="update_profile",
        request=UserUpdateSerializer,
        responses={200: UserSerializer},
    )
    def put(self, request, **__):
        user = self.request.user
        serializer = UserUpdateSerializer(data=request.data, context=self.get_serializer_context())
        serializer.is_valid(raise_exception=True)

        user.update_profile(
            name=serializer.validated_data.get("name"),
            avatar=serializer.validated_data.get("avatar"),
        )

        serializer = UserSerializer(user, context=self.get_serializer_context())
        return Response(serializer.data, status=status.HTTP_200_OK)
