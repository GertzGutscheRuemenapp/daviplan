from rest_framework import routers
from datentool_backend.user.views import UserViewSet

router = routers.SimpleRouter()
router.register(r'users', UserViewSet, basename='user')

urlpatterns = router.urls