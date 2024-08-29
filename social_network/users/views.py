from django.contrib.auth import authenticate
from django.db.models import Q
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from rest_framework.throttling import UserRateThrottle
from .models import User
from .serializers import UserSerializer

# Pagination class for the user search
class UserPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100

# User signup view
class UserSignupView(APIView):
    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')
        name = request.data.get('name')
        if not email or not password:
            return Response({'error': 'Email and password are required'}, status=status.HTTP_400_BAD_REQUEST)
        if not name:
            return Response({'error': 'Name is required'}, status=status.HTTP_400_BAD_REQUEST)
        user = User.objects.create_user(email=email, password=password, name=name)
        return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)

# User login view
class UserLoginView(APIView):
    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')
        user = authenticate(request, email=email, password=password)
        if user:
            return Response(UserSerializer(user).data, status=status.HTTP_200_OK)
        return Response({'error': 'Invalid credentials'}, status=status.HTTP_400_BAD_REQUEST)

# User search view
class UserSearchView(generics.ListAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = UserPagination

    def get_queryset(self):
        query = self.request.query_params.get('query', '')
        if query:
            return User.objects.filter(Q(email__iexact=query) | Q(name__icontains=query)).distinct()
        return User.objects.none()

# Friend request view
class FriendRequestView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [UserRateThrottle]  # Throttle to limit friend requests

    def post(self, request):
        user = request.user
        target_user_email = request.data.get('email')
        
        if not target_user_email:
            return Response({'error': 'Target user email is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            target_user = User.objects.get(email=target_user_email)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
        
        if target_user == user:
            return Response({'error': 'You cannot send a friend request to yourself'}, status=status.HTTP_400_BAD_REQUEST)

        if user.friends.filter(id=target_user.id).exists():
            return Response({'error': 'You are already friends with this user'}, status=status.HTTP_400_BAD_REQUEST)

        if user.sent_requests.filter(id=target_user.id).exists():
            return Response({'error': 'You have already sent a friend request to this user'}, status=status.HTTP_400_BAD_REQUEST)

        # Send a friend request
        user.sent_requests.add(target_user)
        return Response({'success': 'Friend request sent'}, status=status.HTTP_200_OK)

    def put(self, request):
        user = request.user
        target_user_email = request.data.get('email')
        action = request.data.get('action')  # "accept" or "reject"

        if not target_user_email or not action:
            return Response({'error': 'Target user email and action are required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            target_user = User.objects.get(email=target_user_email)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

        if action == 'accept':
            if user.received_requests.filter(id=target_user.id).exists():
                user.friends.add(target_user)
                user.received_requests.remove(target_user)
                target_user.friends.add(user)
                target_user.sent_requests.remove(user)
                return Response({'success': 'Friend request accepted'}, status=status.HTTP_200_OK)
            else:
                return Response({'error': 'No pending friend request from this user'}, status=status.HTTP_400_BAD_REQUEST)
        
        elif action == 'reject':
            if user.received_requests.filter(id=target_user.id).exists():
                user.received_requests.remove(target_user)
                target_user.sent_requests.remove(user)
                return Response({'success': 'Friend request rejected'}, status=status.HTTP_200_OK)
            else:
                return Response({'error': 'No pending friend request from this user'}, status=status.HTTP_400_BAD_REQUEST)
        
        return Response({'error': 'Invalid action'}, status=status.HTTP_400_BAD_REQUEST)

# List friends view
class ListFriendsView(generics.ListAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return user.friends.all()

# List pending friend requests view
class ListPendingRequestsView(generics.ListAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return user.received_requests.all()
