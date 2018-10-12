from otree.api import Currency as c, currency_range
from ._builtin import Page, WaitPage
from .models import Constants

def detail(request, question_id):
    question = get_object_or_404(Question, pk=question_id)
    return render(request, 'djTest/index.html', {'question': question})

class MyPage(Page):
    pass

class ResultsWaitPage(WaitPage):

    def after_all_players_arrive(self):
        pass

class Results(Page):
    pass

page_sequence = [
    MyPage,
    ResultsWaitPage,
    Results
]
