from django.contrib import admin
from django.urls import path
from inventory.views import VendingMachineList,landing_page,dashboard_home,sync_machine_stock,add_machine,add_store,edit_machine,edit_store,add_storage,edit_storage,add_product,edit_product
from django.conf import settings
from django.conf.urls.static import static
urlpatterns = [
    path('', landing_page, name='home'),
    path('dashboard/', dashboard_home, name='dashboard'),
    path('admin/', admin.site.urls),
    path('api/machines/', VendingMachineList.as_view()),
    path('api/sync-stock/', sync_machine_stock),
    path('add-machine/', add_machine, name='add_machine'),
    path('edit-machine/', edit_machine, name='edit_machine'),
    path('add-store/', add_store, name='add_store'),
    path('edit-store/', edit_store, name='edit_store'),
    path('add-storage/', add_storage, name='add_storage'),
    path('edit-storage/', edit_storage, name='edit_storage'),
    path('add-product/', add_product, name='add_product'),
    path('edit-product/', edit_product, name='edit_product'),

]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
