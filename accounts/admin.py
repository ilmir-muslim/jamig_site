### BEGIN: accounts/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from .models import User, Employee, SiteUser, Authors


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Админ-панель для кастомной модели пользователя"""
    
    list_display = [
        'email', 'first_name', 'last_name', 'user_type', 
        'is_verified', 'is_staff', 'is_active', 'created_at'
    ]
    list_filter = [
        'user_type', 'is_verified', 'is_staff', 'is_active', 
        'is_superuser', 'created_at'
    ]
    search_fields = ['email', 'first_name', 'last_name', 'phone_number']
    ordering = ['-created_at']
    readonly_fields = ['created_at', 'updated_at', 'last_login']
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (_('Personal info'), {
            'fields': (
                'first_name', 'last_name', 'phone_number', 
                'avatar', 'bio', 'user_type'
            )
        }),
        (_('Permissions'), {
            'fields': (
                'is_verified', 'is_active', 'is_staff', 'is_superuser',
                'groups', 'user_permissions'
            ),
        }),
        (_('Important dates'), {
            'fields': ('last_login', 'created_at', 'updated_at')
        }),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'email', 'password1', 'password2', 'first_name', 
                'last_name', 'user_type'
            ),
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'employee_profile', 'site_user_profile', 'author_profile'
        )


class EmployeeInline(admin.StackedInline):
    """Инлайн для профиля сотрудника"""
    model = Employee
    can_delete = False
    verbose_name_plural = 'Профиль сотрудника'
    fk_name = 'user'
    fields = [
        'position', 'work_place', 'phone_number', 
        'telegram', 'whatsapp', 'department', 
        'work_schedule', 'is_active_employee', 'hire_date'
    ]


class SiteUserInline(admin.StackedInline):
    """Инлайн для профиля обычного пользователя"""
    model = SiteUser
    can_delete = False
    verbose_name_plural = 'Профиль пользователя'
    fk_name = 'user'
    fields = [
        'date_of_birth', 'location', 'interests', 'email_notifications'
    ]


class AuthorsInline(admin.StackedInline):
    """Инлайн для профиля автора"""
    model = Authors
    can_delete = False
    verbose_name_plural = 'Профиль автора'
    fk_name = 'user'
    fields = [
        'specialization', 'qualifications', 'social_media_links',
        'is_verified_author', 'show_in_authors_list',
        'content_published', 'total_views'
    ]


class CustomUserAdmin(UserAdmin):
    """Расширенная админка пользователя с inline профилями"""
    
    inlines = [EmployeeInline, SiteUserInline, AuthorsInline]
    
    def get_inline_instances(self, request, obj=None):
        """Показываем только соответствующий inline для типа пользователя"""
        if not obj:
            return []
        
        inlines = []
        if obj.user_type == 'employee':
            inlines = [EmployeeInline]
        elif obj.user_type == 'author':
            inlines = [AuthorsInline]
        else:
            inlines = [SiteUserInline]
            
        return [inline(self.model, self.admin_site) for inline in inlines]


# Перерегистрируем User с расширенной админкой
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    """Админ-панель для сотрудников"""
    
    list_display = [
        'get_user_email', 'get_full_name', 'position', 
        'work_place', 'is_active_employee', 'hire_date'
    ]
    list_filter = [
        'is_active_employee', 'department', 'position', 'hire_date'
    ]
    search_fields = [
        'user__email', 'user__first_name', 'user__last_name',
        'position', 'work_place', 'department'
    ]
    list_select_related = ['user']
    readonly_fields = ['user_info_display']
    fieldsets = (
        (_('Основная информация'), {
            'fields': ('user', 'user_info_display', 'position', 'work_place')
        }),
        (_('Контактная информация'), {
            'fields': ('phone_number', 'telegram', 'whatsapp')
        }),
        (_('Дополнительная информация'), {
            'fields': ('department', 'work_schedule')
        }),
        (_('Статус'), {
            'fields': ('is_active_employee', 'hire_date')
        }),
    )
    
    def get_user_email(self, obj):
        return obj.user.email
    get_user_email.short_description = 'Email'
    get_user_email.admin_order_field = 'user__email'
    
    def get_full_name(self, obj):
        return obj.user.get_full_name()
    get_full_name.short_description = 'ФИО'
    get_full_name.admin_order_field = 'user__last_name'
    
    def user_info_display(self, obj):
        if obj.user:
            return f"{obj.user.get_full_name()} ({obj.user.email})"
        return "Пользователь не найден"
    user_info_display.short_description = 'Информация о пользователе'


@admin.register(SiteUser)
class SiteUserAdmin(admin.ModelAdmin):
    """Админ-панель для обычных пользователей"""
    
    list_display = [
        'get_user_email', 'get_full_name', 'location', 
        'date_of_birth', 'email_notifications'
    ]
    list_filter = ['email_notifications', 'date_of_birth']
    search_fields = [
        'user__email', 'user__first_name', 'user__last_name', 'location'
    ]
    list_select_related = ['user']
    readonly_fields = ['user_info_display']
    
    def get_user_email(self, obj):
        return obj.user.email
    get_user_email.short_description = 'Email'
    get_user_email.admin_order_field = 'user__email'
    
    def get_full_name(self, obj):
        return obj.user.get_full_name()
    get_full_name.short_description = 'ФИО'
    get_full_name.admin_order_field = 'user__last_name'
    
    def user_info_display(self, obj):
        if obj.user:
            return f"{obj.user.get_full_name()} ({obj.user.email})"
        return "Пользователь не найден"
    user_info_display.short_description = 'Информация о пользователе'


@admin.register(Authors)
class AuthorsAdmin(admin.ModelAdmin):
    """Админ-панель для авторов"""
    
    list_display = [
        'get_user_email', 'get_full_name', 'specialization', 
        'is_verified_author', 'content_published', 'total_views',
        'show_in_authors_list'
    ]
    list_filter = [
        'is_verified_author', 'show_in_authors_list'
    ]
    search_fields = [
        'user__email', 'user__first_name', 'user__last_name', 
        'specialization', 'qualifications'
    ]
    list_select_related = ['user']
    readonly_fields = [
        'user_info_display', 'content_published', 'total_views'
    ]
    fieldsets = (
        (_('Основная информация'), {
            'fields': ('user', 'user_info_display', 'specialization')
        }),
        (_('Квалификация'), {
            'fields': ('qualifications', 'social_media_links')
        }),
        (_('Статус'), {
            'fields': ('is_verified_author', 'show_in_authors_list')
        }),
        (_('Статистика'), {
            'fields': ('content_published', 'total_views')
        }),
    )
    
    def get_user_email(self, obj):
        return obj.user.email
    get_user_email.short_description = 'Email'
    get_user_email.admin_order_field = 'user__email'
    
    def get_full_name(self, obj):
        return obj.user.get_full_name()
    get_full_name.short_description = 'ФИО'
    get_full_name.admin_order_field = 'user__last_name'
    
    def user_info_display(self, obj):
        if obj.user:
            return f"{obj.user.get_full_name()} ({obj.user.email})"
        return "Пользователь не найден"
    user_info_display.short_description = 'Информация о пользователе'
### END: accounts/admin.py