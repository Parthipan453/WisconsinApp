import time
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import TemplateView, ListView, CreateView, UpdateView
from django.views.generic.edit import FormView
from .forms import ForgotPasswordForm, OTPVerifyForm, SetNewPasswordForm, AnnouncementForm
from .models import PasswordResetOTP, Announcement, Notification
from .utils import send_otp_email, get_admin_pages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.urls import reverse_lazy
from django.views import View
from PermissionAccess.mixins import PermissionRequiredMixin, PageAccessMixin
from django.db import models as db_models
from django.utils import timezone
from django.views.decorators.http import require_GET
from Admin.models import UserRole
from django.db.models import Q
from django.urls import reverse
from Admin.bela_admin.models import Department

User = get_user_model()

# Password Reset
SESSION_EMAIL_KEY = "pwd_reset_email"
SESSION_USER_ID_KEY = "pwd_reset_user_id"
SESSION_OTP_ID_KEY = "pwd_reset_otp_id"
SESSION_VERIFIED_KEY = "pwd_reset_verified"
SESSION_VERIFIED_AT_KEY = "pwd_reset_verified_at"
SESSION_LAST_SENT_KEY = "pwd_reset_last_sent"

RESET_WINDOW_SECONDS = 10 * 60

class ForgotPasswordView(FormView):
    template_name = "Dominic/forgot_password.html"
    form_class = ForgotPasswordForm
    success_url = reverse_lazy("Password:verify_otp")

    def form_valid(self, form):
        email = form.cleaned_data["email"]
        session = self.request.session

        last_sent = session.get(SESSION_LAST_SENT_KEY, 0)
        same_email_pending = session.get(SESSION_EMAIL_KEY) == email
        if same_email_pending and (time.time() - last_sent) < PasswordResetOTP.RESEND_COOLDOWN_SECONDS:
            messages.info(
                self.request,
                "A code was already sent recently. Please check your inbox, "
                "or wait a moment before requesting another.",
            )
            return redirect(self.success_url)

        user = User.objects.filter(email__iexact=email, is_active=True).first()
        
        if user is None:
            form.add_error("email", "No account found with this email address.")
            return self.form_invalid(form)

        otp_instance, raw_otp = PasswordResetOTP.generate_for_user(user)
        send_otp_email(user, raw_otp)

        session[SESSION_USER_ID_KEY] = user.pk
        session[SESSION_OTP_ID_KEY] = otp_instance.pk
        session[SESSION_EMAIL_KEY] = email
        session[SESSION_LAST_SENT_KEY] = time.time()
        session.pop(SESSION_VERIFIED_KEY, None)

        messages.success(self.request, "A verification code has been sent to your email.")
        return super().form_valid(form)

class VerifyOTPView(FormView):
    template_name = "Dominic/verify_otp.html"
    form_class = OTPVerifyForm
    success_url = reverse_lazy("Password:reset_password")

    def dispatch(self, request, *args, **kwargs):
        if not request.session.get(SESSION_EMAIL_KEY):
            messages.error(request, "Please start the password reset process again.")
            return redirect("Password:forgot_password")
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["email"] = self.request.session.get(SESSION_EMAIL_KEY)
        return context

    def form_valid(self, form):
        session = self.request.session
        otp_id = session.get(SESSION_OTP_ID_KEY)
        user_id = session.get(SESSION_USER_ID_KEY)
        entered_otp = form.cleaned_data["otp"]

        otp_instance = None
        if otp_id and user_id:
            otp_instance = PasswordResetOTP.objects.filter(pk=otp_id, user_id=user_id).first()

        if otp_instance is None or not otp_instance.verify(entered_otp):
            form.add_error("otp", "Invalid or expired code. Please try again.")
            return self.form_invalid(form)

        session[SESSION_VERIFIED_KEY] = True
        session[SESSION_VERIFIED_AT_KEY] = time.time()
        return super().form_valid(form)

class ResetPasswordView(FormView):
    template_name = "Dominic/reset_password.html"
    form_class = SetNewPasswordForm
    success_url = reverse_lazy("Password:reset_complete")

    def dispatch(self, request, *args, **kwargs):
        session = request.session
        verified = session.get(SESSION_VERIFIED_KEY)
        verified_at = session.get(SESSION_VERIFIED_AT_KEY, 0)

        if not verified or (time.time() - verified_at) > RESET_WINDOW_SECONDS:
            messages.error(request, "Your verification has expired. Please verify the code again.")
            return redirect("Password:forgot_password")

        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        session = self.request.session
        user = User.objects.filter(pk=session.get(SESSION_USER_ID_KEY)).first()

        if user is None:
            messages.error(self.request, "Something went wrong. Please try again.")
            return redirect("Password:forgot_password")

        user.set_password(form.cleaned_data["new_password"])
        user.save(update_fields=["password"])

        for key in (
            SESSION_EMAIL_KEY,
            SESSION_USER_ID_KEY,
            SESSION_OTP_ID_KEY,
            SESSION_VERIFIED_KEY,
            SESSION_VERIFIED_AT_KEY,
            SESSION_LAST_SENT_KEY,
        ):
            session.pop(key, None)

        messages.success(self.request, "Your password has been reset. You can now log in.")
        return super().form_valid(form)

class ResetCompleteView(TemplateView):
    template_name = "Dominic/reset_complete.html"
    
# Announcement
class AnnouncementListView(LoginRequiredMixin, PermissionRequiredMixin, PageAccessMixin, ListView):
    permission_required = "announcement_read"
    page_key = 'announcement_list'
    user_types = ["faculty"]
    model = Announcement
    template_name = 'Dominic/announcements/announcement_list.html'
    context_object_name = 'announcements'
    paginate_by = 10

    def get_queryset(self):
        qs = Announcement.objects.select_related('created_by')
        visibility = self.request.GET.get('visibility')
        if visibility in ('website', 'dashboard', 'both'):
            qs = qs.filter(visibility=visibility)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['visibility_filter'] = self.request.GET.get('visibility', '')

        all_qs = Announcement.objects.all()
        now = timezone.now()
        context['stats'] = {
            'total': all_qs.count(),
            'active': all_qs.filter(
                is_active=True, start_date__lte=now
            ).filter(
                db_models.Q(end_date__isnull=True) | db_models.Q(end_date__gte=now)
            ).count(),
            'scheduled': all_qs.filter(is_active=True, start_date__gt=now).count(),
            'disabled': all_qs.filter(is_active=False).count(),
        }
        return context
    
class AnnouncementCreateView(LoginRequiredMixin, PermissionRequiredMixin, PageAccessMixin, CreateView):
    permission_required = "announcement_create"
    page_key = "create_announcement"
    model = Announcement
    form_class = AnnouncementForm
    template_name = 'Dominic/announcements/announcement_form.html'
    success_url = reverse_lazy('Password:announcement_list')

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, f'Announcement "{form.instance.title}" created successfully.')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_edit'] = False
        return context
    
class AnnouncementUpdateView(LoginRequiredMixin, PermissionRequiredMixin, PageAccessMixin, UpdateView):
    permission_required = "announcement_update"
    page_key = "edit_announcement"
    model = Announcement
    form_class = AnnouncementForm
    template_name = 'Dominic/announcements/announcement_form.html'
    success_url = reverse_lazy('Password:announcement_list')

    def form_valid(self, form):
        messages.success(self.request, f'Announcement "{form.instance.title}" updated successfully.')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_edit'] = True
        return context
    
class AnnouncementToggleStatusView(LoginRequiredMixin, PageAccessMixin, View):

    def post(self, request, pk):
        announcement = get_object_or_404(Announcement, pk=pk)
        announcement.is_active = not announcement.is_active
        announcement.save(update_fields=['is_active'])

        state = 'enabled' if announcement.is_active else 'disabled'

        return JsonResponse({
            'success': True,
            'is_active': announcement.is_active,
            'status': announcement.status,
        })
        
# Search
@require_GET
def admin_search(request):
    query = request.GET.get('q', '').strip()
    if not query:
        return JsonResponse({'results': []})
    
    q_lower = query.lower()
    results = []
    
    pages = get_admin_pages()
    results.extend([
        p for p in pages
        if q_lower in p['title'].lower() or q_lower in p['group'].lower()
    ])
    
    users = User.objects.filter(
        Q(first_name__icontains=query) |
        Q(last_name__icontains=query) |
        Q(username__icontains=query) |
        Q(university_id__icontains=query)
    ).distinct()[:10]
    
    for u in users:
        results.append({
            'title': u.full_name,
            'path': reverse('user_view', args=[u.uuid]),
            'group': "Users",
            'icon': "user",
        })
        
    departments = Department.objects.filter(department_name__icontains=query)[:10]
    
    for d in departments:
        results.append({
            'title': d.department_name,
            'path': reverse('department_dashboard'),
            'group': 'Departments',
            'icon': 'building'
        })
    
    return JsonResponse({'results': results[:20]})
 
# Notification
class NotificationListView(LoginRequiredMixin, View):
    def get(self, request):
        self._detect_and_create_notifications()
        own_or_broadcast = Q(recipient__isnull=True) | Q(recipient=request.user)

        notifications = Notification.objects.select_related('announcement').filter(
            own_or_broadcast
        )[:10]
        unread_count = Notification.objects.filter(own_or_broadcast, is_read=False).count()
        
        data = [{
            'id': n.id,
            'event': n.event,
            'message': n.message,
            'is_read': n.is_read,
            'created_at': timezone.localtime(n.created_at).strftime('%d %b %Y, %I:%M %p'),
        } for n in notifications]
        
        return JsonResponse({
            'success': True,
            'unread_count': unread_count,
            'notifications': data,
        })
        
    def _detect_and_create_notifications(self):
        now = timezone.now()
        
        live_qs = Announcement.objects.filter(
            is_active=True,
            start_date__lte=now,
            visibility__in=['dashboard', 'both'],
        ).filter(
            db_models.Q(end_date__isnull=True) | db_models.Q(end_date__gte=now)
        )
        
        for ann in live_qs:
            Notification.objects.get_or_create(
                announcement = ann,
                event = "new",
                defaults = {
                    'message': f'New annoucement posted: "{ann.title}"'
                }
            )
            
        expired_qs = Announcement.objects.filter(
            end_date__isnull=False,
            end_date__lte=now,
            visibility__in=['dashboard', 'both'],
        )
        
        for ann in expired_qs:
            Notification.objects.get_or_create(
                announcement = ann,
                event = 'expired',
                defaults = {
                    'message': f'Announcement expired: "{ann.title}"'
                }
            )
        
class NotificationMarkReadView(LoginRequiredMixin, View):
    def post(self, request):
        own_or_broadcast = Q(recipient__isnull=True) | Q(recipient=request.user)
        Notification.objects.filter(own_or_broadcast, is_read=False).update(is_read=True)
        return JsonResponse({'success': True})


######################### Kali code #################

NOTIF_ICON_MAP = {
    'new': 'megaphone',
    'expired': 'calendar-x',
    'shift_assigned': 'calendar-check',
    'shift_updated': 'calendar-clock',
    'shift_cancelled': 'calendar-off',
    'tournament_applied': 'trophy',
}


class NotificationHistoryView(LoginRequiredMixin, ListView):
    model = Notification
    template_name = 'Dominic/notification_history.html'
    context_object_name = 'notifications'
    paginate_by = 10

    def get_queryset(self):
        own_or_broadcast = Q(recipient__isnull=True) | Q(recipient=self.request.user)
        return Notification.objects.select_related(
            'announcement', 'schedule', 'tournament_application'
        ).filter(own_or_broadcast)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        for notif in context['notifications']:
            notif.icon = NOTIF_ICON_MAP.get(notif.event, 'clock-alert')
        return context

    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)
        own_or_broadcast = Q(recipient__isnull=True) | Q(recipient=request.user)
        Notification.objects.filter(own_or_broadcast, is_read=False).update(is_read=True)
        return response


######################### Kali code  End #################