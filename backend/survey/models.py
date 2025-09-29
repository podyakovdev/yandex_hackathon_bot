from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    phone_number = models.CharField(
        max_length=20,
        blank=True,
        verbose_name="Сотовый телефон"
    )

    def __str__(self):
        return self.username

from django.db import models

class Survey(models.Model):
    """
    Модель опроса, содержащая заголовок и описание.
    """
    title = models.CharField(max_length=255, help_text="Название опроса")
    description = models.TextField(blank=True, help_text="Описание опроса")

    def __str__(self):
        return self.title


class Question(models.Model):
    """
    Вопрос, связанный с конкретным опросом.
    Может быть закрытым, открытым или с подсказками.
    """
    survey = models.ForeignKey(Survey, on_delete=models.CASCADE, related_name='questions')
    text = models.TextField(help_text="Текст вопроса")
    type = models.CharField(
        max_length=20,
        choices=[
            ('closed', 'Closed'),    # с вариантами ответа
            ('open', 'Open'),        # свободный ввод
            ('suggest', 'Suggest'),  # выпадающий список
        ],
        help_text="Тип вопроса"
    )
    required = models.BooleanField(default=True, help_text="Обязателен ли вопрос")

    def __str__(self):
        return f"{self.text[:50]}..."


class Option(models.Model):
    """
    Вариант ответа для закрытого вопроса.
    """
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='options')
    text = models.CharField(max_length=255, help_text="Текст варианта ответа")

    def __str__(self):
        return self.text


class Response(models.Model):
    """
    Ответ пользователя на опрос.
    Хранит дату и информацию, был ли опрос пройден через бота.
    """
    survey = models.ForeignKey(Survey, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    filled_by_bot = models.BooleanField(default=False, help_text="Заполнено через чат-бот")

    def __str__(self):
        return f"Response #{self.id} to {self.survey.title}"


class Answer(models.Model):
    """
    Ответ на конкретный вопрос в рамках одного Response.
    """
    response = models.ForeignKey(Response, on_delete=models.CASCADE, related_name='answers')
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    text = models.TextField(help_text="Ответ пользователя")

    def __str__(self):
        return