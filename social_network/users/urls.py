from django.urls import path
from .views import UserSignupView, UserLoginView, UserSearchView, FriendRequestView, ListFriendsView, ListPendingRequestsView

urlpatterns = [
    path('signup/', UserSignupView.as_view(), name='signup'),
    path('login/', UserLoginView.as_view(), name='login'),
    path('search/', UserSearchView.as_view(), name='search'),
    path('friend-request/', FriendRequestView.as_view(), name='friend_request'),
    path('friends/', ListFriendsView.as_view(), name='list_friends'),
    path('pending-requests/', ListPendingRequestsView.as_view(), name='pending_requests'),
]
