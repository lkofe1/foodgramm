from djoser.views import UserViewSet
from rest_framework import status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model

from users.models import Follow
from api.serializers import FollowSerializer, AvatarSerializer
from api.pagination import CustomPagination

User = get_user_model()


class CustomUserViewSet(UserViewSet):
    pagination_class = CustomPagination

    @action(detail=False, methods=['get'], permission_classes=[
        permissions.IsAuthenticated])
    def subscriptions(self, request):
        queryset = User.objects.filter(following__user=request.user)
        page = self.paginate_queryset(queryset)
        serializer = FollowSerializer(page, many=True, context={
            'request': request})
        return self.get_paginated_response(serializer.data)

    @action(detail=True, methods=['post', 'delete'], permission_classes=[
        permissions.IsAuthenticated])
    def subscribe(self, request, id):
        author = get_object_or_404(User, id=id)
        if request.method == 'POST':
            if request.user == author:
                return Response({'errors': 'Нельзя подписаться на себя'},
                                status=status.HTTP_400_BAD_REQUEST)
            if Follow.objects.filter(user=request.user,
                                     author=author).exists():
                return Response({'errors': 'Вы уже подписаны'},
                                status=status.HTTP_400_BAD_REQUEST)

            Follow.objects.create(user=request.user, author=author)
            serializer = FollowSerializer(author, context={'request': request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        follow = Follow.objects.filter(user=request.user, author=author)
        if not follow.exists():
            return Response({'errors': 'Вы не подписаны на этого автора'},
                            status=status.HTTP_400_BAD_REQUEST)
        follow.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['put', 'delete'], url_path='me/avatar',
            permission_classes=[permissions.IsAuthenticated])
    def avatar(self, request):
        user = request.user
        if request.method == 'PUT':
            serializer = AvatarSerializer(user, data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)

        user.avatar.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
