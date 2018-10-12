from otree.api import (
    models, widgets, BaseConstants, BaseSubsession, BaseGroup, BasePlayer,
    Currency as c, currency_range
)

from django.db import models



class Question(models.Model):
    question_text = models.StringField(max_length=200)
    pub_date = models.DateTimeField('date published')
    def __str__(self):
        return self.question_text

class Choice(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    choice_text = models.StringField(max_length=200)
    votes = models.IntegerField(default=0)
    def __str__(self):
        return self.choice_text

doc = """
Your app description
"""


class Constants(BaseConstants):
    name_in_url = 'djTest'
    players_per_group = None
    num_rounds = 1


class Subsession(BaseSubsession):
    pass


class Group(BaseGroup):
    pass


class Player(BasePlayer):
    pass
