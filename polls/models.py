import datetime

from django.db import models
from django.utils import timezone


class Question(models.Model):
    """
    Define el modelo para una pregunta de la encuesta.
    """
    question_text = models.CharField(max_length=200)
    pub_date = models.DateTimeField("date published")

    def __str__(self):
        """Representación en texto del objeto (útil en el admin)."""
        return self.question_text

    def was_published_recently(self):
        """Método helper para saber si se publicó recientemente."""
        now = timezone.now()
        return now - datetime.timedelta(days=1) <= self.pub_date <= now


class Choice(models.Model):
    """
    Define el modelo para una opción de respuesta.
    Está vinculada a una Pregunta (Question).
    """
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    choice_text = models.CharField(max_length=200)
    votes = models.IntegerField(default=0)

    def __str__(self):
        """Representación en texto del objeto."""
        return self.choice_text
