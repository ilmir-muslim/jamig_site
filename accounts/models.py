from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils.translation import gettext_lazy as _
from django.core.validators import RegexValidator


class UserManager(BaseUserManager):
    """Кастомный менеджер для модели User без username"""
    
    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        """Создает и сохраняет пользователя с email и паролем"""
        if not email:
            raise ValueError('The Email must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        """Создает обычного пользователя"""
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        """Создает суперпользователя"""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self._create_user(email, password, **extra_fields)


class User(AbstractUser):
    """Кастомная модель пользователя с разными типами"""
    
    USER_TYPES = (
        ('user', 'Обычный пользователь'),
        ('employee', 'Сотрудник'),
        ('author', 'Автор'),
    )
    
    user_type = models.CharField(
        max_length=20,
        choices=USER_TYPES,
        default='user',
        verbose_name="Тип пользователя"
    )
    email = models.EmailField(
        unique=True, 
        verbose_name="Email адрес",
        error_messages={
            'unique': _("Пользователь с таким email уже существует."),
        }
    )
    phone_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message="Номер телефона должен быть в формате: '+79999999999'. Максимум 15 цифр."
    )
    phone_number = models.CharField(
        validators=[phone_regex],
        max_length=17,
        blank=True,
        null=True,
        verbose_name="Номер телефона"
    )
    avatar = models.ImageField(
        upload_to='avatars/',
        blank=True,
        null=True,
        verbose_name="Аватар"
    )
    bio = models.TextField(
        max_length=500,
        blank=True,
        verbose_name="О себе"
    )
    is_verified = models.BooleanField(
        default=False,
        verbose_name="Подтвержденный аккаунт"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата регистрации"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Дата обновления"
    )
    
    # Убираем обязательность поля username, используем email для входа
    username = None
    EMAIL_FIELD = 'email'
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']
    
    # Используем кастомный менеджер
    objects = UserManager()
    
    # Добавляем related_name чтобы избежать конфликтов
    groups = models.ManyToManyField(
        'auth.Group',
        verbose_name='groups',
        blank=True,
        help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.',
        related_name='accounts_user_set',
        related_query_name='accounts_user',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        verbose_name='user permissions',
        blank=True,
        help_text='Specific permissions for this user.',
        related_name='accounts_user_set',
        related_query_name='accounts_user',
    )
    
    def get_full_name(self):
        """Возвращает полное имя пользователя"""
        return f"{self.first_name} {self.last_name}".strip()
    
    def get_short_name(self):
        """Возвращает короткое имя (имя)"""
        return self.first_name
    
    @property
    def is_employee(self):
        return self.user_type == 'employee'
    
    @property
    def is_author(self):
        return self.user_type == 'author'
    
    @property
    def is_regular_user(self):
        return self.user_type == 'user'
    
    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.get_full_name()} ({self.email})"

class Employee(models.Model):
    """Профиль сотрудника (связь 1-к-1 с User)"""
    
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='employee_profile',
        verbose_name="Пользователь"
    )
    # Убираем full_name, так как есть в User
    position = models.CharField(max_length=100, verbose_name="Должность")
    work_place = models.CharField(max_length=200, verbose_name="Мечеть")
    
    # Контактная информация
    phone_number = models.CharField(
        max_length=50, 
        verbose_name="Номер телефона", 
        null=True, 
        blank=True
    )
    telegram = models.CharField(
        max_length=100, 
        verbose_name="Telegram", 
        null=True, 
        blank=True,
        help_text="Username в Telegram"
    )
    whatsapp = models.CharField(
        max_length=100, 
        verbose_name="WhatsApp", 
        null=True, 
        blank=True,
        help_text="Номер для WhatsApp"
    )
    
    # Дополнительные поля
    department = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Отдел"
    )
    work_schedule = models.TextField(
        blank=True,
        verbose_name="График работы"
    )
    is_active_employee = models.BooleanField(
        default=True,
        verbose_name="Активный сотрудник"
    )
    hire_date = models.DateField(
        null=True,
        blank=True,
        verbose_name="Дата приема на работу"
    )
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.position}"
    
    class Meta:
        verbose_name = "Сотрудник"
        verbose_name_plural = "Сотрудники"


class SiteUser(models.Model):
    """Профиль обычного пользователя сайта (связь 1-к-1 с User)"""
    
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='site_user_profile',
        verbose_name="Пользователь"
    )
    
    # Дополнительные поля для обычного пользователя
    date_of_birth = models.DateField(
        null=True,
        blank=True,
        verbose_name="Дата рождения"
    )
    location = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Город"
    )
    interests = models.TextField(
        blank=True,
        verbose_name="Интересы"
    )
    email_notifications = models.BooleanField(
        default=True,
        verbose_name="Email уведомления"
    )
    
    def __str__(self):
        return self.user.get_full_name()
    
    class Meta:
        verbose_name = "Пользователь сайта"
        verbose_name_plural = "Пользователи сайта"


class Authors(models.Model):
    """Профиль автора контента (связь 1-к-1 с User)"""
    
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='author_profile',
        verbose_name="Пользователь"
    )
    
    # Специфичные поля для автора
    specialization = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="Специализация",
        help_text="Например: Исламское право, Коран, История ислама и т.д."
    )
    qualifications = models.TextField(
        blank=True,
        verbose_name="Квалификация и образование"
    )
    social_media_links = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="Ссылки на социальные сети",
        help_text="JSON с ссылками на соцсети"
    )
    is_verified_author = models.BooleanField(
        default=False,
        verbose_name="Проверенный автор"
    )
    show_in_authors_list = models.BooleanField(
        default=True,
        verbose_name="Показывать в списке авторов"
    )
    
    # Статистика
    content_published = models.PositiveIntegerField(
        default=0,
        verbose_name="Опубликованных материалов"
    )
    total_views = models.PositiveIntegerField(
        default=0,
        verbose_name="Всего просмотров"
    )

    @property
    def videos(self):
        return self.videocontent_set.all()
    
    @property
    def audios(self):
        return self.audiocontent_set.all()
    
    @property
    def texts(self):
        return self.textcontent_set.all()
    
    def __str__(self):
        return self.user.get_full_name()
    
    class Meta:
        verbose_name = "Автор"
        verbose_name_plural = "Авторы"