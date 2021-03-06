from otree.api import (
    models, widgets, BaseConstants, BaseSubsession, BaseGroup, BasePlayer,
    Currency as c, currency_range
)

author = 'Eddi'

doc = """
Your app description
"""

class Constants(BaseConstants):
    name_in_url = 'Game020201'
    players_per_group = None
    num_rounds = 1
    region_number = 5


class Subsession(BaseSubsession):
    pass

class Group(BaseGroup):
    pass

class Player(BasePlayer):
    name = models.StringField(initial='SurName')
    firstname = models.StringField(initial='FirstName')
