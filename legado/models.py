from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import datetime

class Suscripcion(models.Model):
    PLANES = (
        ('TRIAL', 'Prueba Gratis (14 días)'),
        ('BASIC', 'Básico'),
        ('PRO', 'Profesional'),
        ('PREMIUM', 'Premium'),
    )
    usuario = models.OneToOneField(User, on_delete=models.CASCADE, related_name='suscripcion')
    plan = models.CharField(max_length=20, choices=PLANES, default='TRIAL')
    activa_hasta = models.DateTimeField(null=True, blank=True)
    es_activa = models.BooleanField(default=True)

    def is_valid(self):
        if not self.es_activa:
            return False
        if self.activa_hasta and timezone.now() > self.activa_hasta:
            return False
        return True

    def __str__(self):
        return f"{self.usuario.username} - {self.plan}"
class Boveda(models.Model):
    usuario = models.OneToOneField(User, on_delete=models.CASCADE, related_name='boveda')
    creado_en = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Bóveda de {self.usuario.username}"

class AccesoFamiliar(models.Model):
    boveda = models.ForeignKey(Boveda, on_delete=models.CASCADE, related_name='accesos_familiares')
    usuario = models.OneToOneField(User, on_delete=models.CASCADE, related_name='acceso_familiar')
    creado_en = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Familiar {self.usuario.username} -> {self.boveda}"

class Mensaje(models.Model):
    boveda = models.ForeignKey(Boveda, on_delete=models.CASCADE, related_name='mensajes')
    pregunta_referencia = models.CharField(max_length=255)
    respuesta_exacta = models.TextField()
    categoria = models.CharField(max_length=100)
    
    # --- CAMPO VECTORIAL PARA IA (Adaptado para SQLite en V2) ---
    embedding = models.JSONField(null=True, blank=True)
    
    es_activo = models.BooleanField(default=True)
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.pregunta_referencia

class InteraccionIA(models.Model):
    boveda = models.ForeignKey(Boveda, on_delete=models.CASCADE, related_name='interacciones')
    creado_en = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Interacción en {self.boveda} a las {self.creado_en}"
