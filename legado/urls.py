from django.urls import path
from . import views

urlpatterns = [
    path('', views.LandingPageView.as_view(), name='landing'),
    path('dashboard/', views.DashboardMensajesView.as_view(), name='dashboard'),
    path('dashboard/nuevo/', views.MensajeCreateView.as_view(), name='mensaje_crear'),
    path('dashboard/editar/<int:pk>/', views.MensajeUpdateView.as_view(), name='mensaje_editar'),
    path('dashboard/eliminar/<int:pk>/', views.MensajeDeleteView.as_view(), name='mensaje_eliminar'),
    path('perfil/', views.PerfilView.as_view(), name='perfil'),
    path('familiares/', views.FamiliaresListView.as_view(), name='familiares'),
    path('familiares/nuevo/', views.FamiliarCreateView.as_view(), name='familiar_crear'),
    path('familiares/<int:pk>/password/', views.FamiliarPasswordUpdateView.as_view(), name='familiar_password'),
    path('boveda/<str:username>/', views.BuscadorFamiliarView.as_view(), name='buscador_familiar'),
    path('registro/', views.RegistroView.as_view(), name='registro'),
    path('planes/', views.PlanesView.as_view(), name='planes'),
    path('planes/simular/<str:plan>/', views.SimularPagoView.as_view(), name='simular_pago'),
]
