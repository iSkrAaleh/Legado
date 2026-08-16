from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, View, TemplateView, FormView
from django.urls import reverse_lazy
from django.contrib.auth.forms import UserCreationForm, SetPasswordForm
from django.contrib.auth.views import LoginView
from django.contrib import messages
from django.db.models import Q
from .models import Mensaje, Boveda, Suscripcion, AccesoFamiliar, InteraccionIA
from .utils import generar_embedding, cosine_similarity
from django.utils import timezone
import datetime

LIMITES_PLANES = {
    'TRIAL': {'familiares': 1, 'preguntas': 5},
    'BASIC': {'familiares': 3, 'preguntas': 20},
    'PRO': {'familiares': 10, 'preguntas': 100},
    'PREMIUM': {'familiares': 999999, 'preguntas': 999999},
}

class PlanesView(LoginRequiredMixin, TemplateView):
    template_name = 'legado/planes.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        suscripcion, _ = Suscripcion.objects.get_or_create(usuario=self.request.user)
        context['plan_actual'] = suscripcion.plan
        return context

class LandingPageView(TemplateView):
    template_name = 'legado/landing.html'

    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            if hasattr(request.user, 'acceso_familiar'):
                return redirect('buscador_familiar', username=request.user.acceso_familiar.boveda.usuario.username)
            return redirect('dashboard')
        return super().get(request, *args, **kwargs)

class SimularPagoView(LoginRequiredMixin, View):
    def post(self, request, plan):
        if plan in ['BASIC', 'PRO', 'PREMIUM']:
            suscripcion, _ = Suscripcion.objects.get_or_create(usuario=request.user)
            suscripcion.plan = plan
            suscripcion.es_activa = True
            suscripcion.activa_hasta = None # Plan permanente
            suscripcion.save()
            messages.success(request, f"¡Pago exitoso! Ahora tienes el plan permanente {plan}.")
        return redirect('perfil')

class CustomLoginView(LoginView):
    template_name = 'registration/login.html'

    def get_success_url(self):
        if hasattr(self.request.user, 'acceso_familiar'):
            return reverse_lazy('buscador_familiar', kwargs={'username': self.request.user.acceso_familiar.boveda.usuario.username})
        return reverse_lazy('dashboard')

class RegistroView(CreateView):
    template_name = 'registration/register.html'
    form_class = UserCreationForm
    success_url = reverse_lazy('login')

    def form_valid(self, form):
        user = form.save()
        Boveda.objects.create(usuario=user)
        Suscripcion.objects.create(
            usuario=user, 
            plan='TRIAL',
            activa_hasta=timezone.now() + datetime.timedelta(days=14)
        )
        messages.success(self.request, "Cuenta creada con éxito. Inicia sesión para continuar.")
        return super().form_valid(form)

class PerfilView(LoginRequiredMixin, TemplateView):
    template_name = 'legado/perfil.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        suscripcion, _ = Suscripcion.objects.get_or_create(usuario=self.request.user)
        context['suscripcion'] = suscripcion
        return context

class FamiliaresListView(LoginRequiredMixin, ListView):
    model = AccesoFamiliar
    template_name = 'legado/familiares.html'
    context_object_name = 'familiares'

    def get_queryset(self):
        return AccesoFamiliar.objects.filter(boveda__usuario=self.request.user)

class FamiliarCreateView(LoginRequiredMixin, CreateView):
    template_name = 'legado/familiar_form.html'
    form_class = UserCreationForm
    success_url = reverse_lazy('familiares')

    def dispatch(self, request, *args, **kwargs):
        suscripcion, _ = Suscripcion.objects.get_or_create(usuario=self.request.user)
        limite = LIMITES_PLANES.get(suscripcion.plan, LIMITES_PLANES['TRIAL'])['familiares']
        actuales = AccesoFamiliar.objects.filter(boveda__usuario=self.request.user).count()
        if actuales >= limite:
            messages.error(request, "Has alcanzado el límite de familiares de tu plan actual.")
            return redirect('planes')
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        user = form.save()
        boveda, _ = Boveda.objects.get_or_create(usuario=self.request.user)
        AccesoFamiliar.objects.create(boveda=boveda, usuario=user)
        messages.success(self.request, f"Familiar {user.username} creado con éxito.")
        return super().form_valid(form)

class FamiliarPasswordUpdateView(LoginRequiredMixin, FormView):
    template_name = 'legado/familiar_password.html'
    form_class = SetPasswordForm
    success_url = reverse_lazy('familiares')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        acceso = get_object_or_404(AccesoFamiliar, pk=self.kwargs['pk'], boveda__usuario=self.request.user)
        self.familiar_user = acceso.usuario
        kwargs['user'] = self.familiar_user
        return kwargs

    def form_valid(self, form):
        form.save()
        messages.success(self.request, "Contraseña del familiar actualizada con éxito.")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        acceso = get_object_or_404(AccesoFamiliar, pk=self.kwargs['pk'], boveda__usuario=self.request.user)
        context['familiar_username'] = acceso.usuario.username
        return context

class DashboardMensajesView(LoginRequiredMixin, ListView):
    model = Mensaje
    template_name = 'legado/dashboard.html'
    context_object_name = 'mensajes'

    def get_queryset(self):
        boveda, _ = Boveda.objects.get_or_create(usuario=self.request.user)
        return Mensaje.objects.filter(boveda=boveda, es_activo=True).order_by('-creado_en')
        
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        suscripcion, _ = Suscripcion.objects.get_or_create(usuario=self.request.user)
        context['suscripcion_valida'] = suscripcion.is_valid()
        context['suscripcion'] = suscripcion
        return context

class MensajeCreateView(LoginRequiredMixin, CreateView):
    model = Mensaje
    template_name = 'legado/mensaje_form.html'
    fields = ['pregunta_referencia', 'respuesta_exacta', 'categoria']
    success_url = reverse_lazy('dashboard')

    def dispatch(self, request, *args, **kwargs):
        suscripcion, _ = Suscripcion.objects.get_or_create(usuario=self.request.user)
        if not suscripcion.is_valid():
            messages.error(request, "Tu suscripción ha expirado. No puedes crear más memorias.")
            return redirect('dashboard')
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        boveda, _ = Boveda.objects.get_or_create(usuario=self.request.user)
        form.instance.boveda = boveda
        
        texto_a_vectorizar = form.instance.pregunta_referencia
        vector = generar_embedding(texto_a_vectorizar)
        if vector:
            form.instance.embedding = vector
            
        return super().form_valid(form)

class MensajeUpdateView(LoginRequiredMixin, UpdateView):
    model = Mensaje
    template_name = 'legado/mensaje_form.html'
    fields = ['pregunta_referencia', 'respuesta_exacta', 'categoria']
    success_url = reverse_lazy('dashboard')

    def get_queryset(self):
        return Mensaje.objects.filter(boveda__usuario=self.request.user)

    def form_valid(self, form):
        if 'pregunta_referencia' in form.changed_data:
            vector = generar_embedding(form.instance.pregunta_referencia)
            if vector:
                form.instance.embedding = vector
        return super().form_valid(form)

class MensajeDeleteView(LoginRequiredMixin, DeleteView):
    model = Mensaje
    template_name = 'legado/mensaje_confirm_delete.html'
    success_url = reverse_lazy('dashboard')

    def get_queryset(self):
        return Mensaje.objects.filter(boveda__usuario=self.request.user)
        
    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.es_activo = False
        self.object.save()
        return redirect(self.success_url)

class BuscadorFamiliarView(View):
    template_name = 'legado/buscador.html'

    def get(self, request, username):
        return render(request, self.template_name, {'username': username})

    def post(self, request, username):
        query = request.POST.get('q', '').strip()
        resultado = None
        error_limite = None

        if query:
            # Check limits
            boveda = get_object_or_404(Boveda, usuario__username=username)
            suscripcion, _ = Suscripcion.objects.get_or_create(usuario=boveda.usuario)
            limite_preguntas = LIMITES_PLANES.get(suscripcion.plan, LIMITES_PLANES['TRIAL'])['preguntas']
            
            hoy_inicio = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
            preguntas_hoy = InteraccionIA.objects.filter(boveda=boveda, creado_en__gte=hoy_inicio).count()

            if preguntas_hoy >= limite_preguntas:
                error_limite = f"El creador de esta bóveda ha alcanzado su límite diario de preguntas ({limite_preguntas}). Vuelve mañana."
            else:
                # Add Interaction
                InteraccionIA.objects.create(boveda=boveda)

                query_embedding = generar_embedding(query)
                
                if query_embedding:
                    memorias = Mensaje.objects.filter(
                        boveda__usuario__username=username,
                        es_activo=True
                    )
                    
                    mejor_similitud = -1.0
                    mejor_memoria = None
                    
                    for memoria in memorias:
                        if memoria.embedding:
                            similitud = cosine_similarity(query_embedding, memoria.embedding)
                            if similitud > mejor_similitud:
                                mejor_similitud = similitud
                                mejor_memoria = memoria
                    
                    if mejor_memoria and mejor_similitud >= 0.80:
                        resultado = mejor_memoria
                else:
                    resultado = Mensaje.objects.filter(
                        boveda__usuario__username=username,
                        es_activo=True
                    ).filter(
                        Q(pregunta_referencia__icontains=query) | Q(categoria__icontains=query)
                    ).first()

        context = {
            'username': username,
            'query': query,
            'resultado': resultado,
            'error_limite': error_limite
        }
        return render(request, self.template_name, context)
