from django.contrib import admin
from django.urls import path
from inventory.views import VendingMachineList,landing_page,dashboard_home,add_machine,add_store,edit_machine,edit_store
from django.conf import settings
from django.conf.urls.static import static
urlpatterns = [
    path('', landing_page, name='home'),
    path('dashboard/', dashboard_home, name='dashboard'),
    path('admin/', admin.site.urls),
    path('api/machines/', VendingMachineList.as_view()), 
    path('add-machine/', add_machine, name='add_machine'),
    path('edit-machine/', edit_machine, name='edit_machine'),
    path('add-store/', add_store, name='add_store'),
    path('edit-store/', edit_store, name='edit_store'),
    

]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
