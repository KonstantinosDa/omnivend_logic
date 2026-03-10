from django.contrib import admin
from django.urls import path
from inventory.views import VendingMachineList,landing_page,dashboard_home
from django.conf import settings
from django.conf.urls.static import static
urlpatterns = [
    path('', landing_page, name='home'),
    path('dashboard/', dashboard_home, name='dashboard'),
    path('admin/', admin.site.urls),
    path('api/machines/', VendingMachineList.as_view()), 
]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
