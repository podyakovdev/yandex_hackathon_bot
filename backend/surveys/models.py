from django.db import models


class User(models.Model):
    GENDER_CHOICES = [
        ('M', 'Мужской'),
        ('F', 'Женский'),
        ('O', 'Другой'),
    ]

    tg_nickname = models.CharField(max_length=255, unique=True)
    name = models.CharField(max_length=255)
    surname = models.CharField(max_length=255)
    age = models.PositiveIntegerField()
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"User {self.tg_nickname}: {self.name} {self.surname}"


class Survey(models.Model):
    """
    Опрос, загруженный из внешнего источника (Яндекс Формы).
    """
    # Внешний идентификатор формы (из Яндекс Форм)
    external_id = models.CharField(max_length=128, db_index=True)
    title = models.CharField(max_length=255, help_text="Название опроса")
    description = models.TextField(blank=True, help_text="Описание опроса")

    # Вопросы анкеты как список строк
    questions = models.JSONField(default=list)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"[{self.id}] {self.title}"


class SurveyResponse(models.Model):
    """Ответы пользователя на конкретный опрос."""
    survey = models.ForeignKey(
        Survey, on_delete=models.CASCADE, related_name="responses"
    )
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="responses", 
        null=True, blank=True
    )
    # Произвольные ответы в виде списка строк (по порядку вопросов)
    answers = models.JSONField(default=list)

    # Необязательная информация о пользователе (для совместимости)
    telegram_user_id = models.CharField(max_length=128, blank=True, default="")
    telegram_username = models.CharField(max_length=128, blank=True, default="")

    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Response to survey #{self.survey_id} at {self.submitted_at:%Y-%m-%d %H:%M}"

