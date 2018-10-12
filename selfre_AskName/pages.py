from otree.api import Currency as c, currency_range
from . import models
from ._builtin import Page, WaitPage
from .models import Constants

import copy
import selfremarket.hungalg
import selfremarket.selfre_market as sfm

from django.shortcuts import render
from django.http import HttpResponseRedirect
from .forms import NameForm

# this page does not show anything, it just prepares the selfremarket object
class MarketExample:
    selfremarket=sfm.SelfReMarket("Selfre Hub Version 1")
    regions=[]
    pi_name=None
    pi_prodlocs=[]
    pi_conslocs=[]
    description={}
    generaldescription= None
    def __init__(self,x,b1):
        # ====================== Begin AB3_1  =========
        if x=='AB4_1':
            #public info
            self.pi_name="Simple & Tiny - 2 Producers, 1 Consumer"
            self.pi_prodlocs=[1,9]
            self.pi_conslocs=[3,5]
            boundary01=b1 
            regA=sfm.Region(0,boundary01,0,1,'Region A')
            regB=sfm.Region(boundary01,20,20,1,'Region B')
            self.regions=[regA,regB]
            prodA=[sfm.Produktion('1',0,0,1) for x in range(9)] # name of Player 1: 1
            prodB=[sfm.Produktion('3',20,0,1) for x in range(9)]
            verbr=[sfm.Verbrauch('2',1) for x in range(9)]
            verbr.extend([sfm.Verbrauch('4',5) for x in range(2)])
            verbr.extend([sfm.Verbrauch('4',8) for x in range(2)])
            verbr.extend([sfm.Verbrauch('4',12) for x in range(2)]) 
            verbr.extend([sfm.Verbrauch('2',15) for x in range(1)])
            verbr.extend([sfm.Verbrauch('4',19) for x in range(2)])
            
            AB=self.selfremarket
            AB.productions=prodA
            AB.productions.extend(prodB)
            AB.consumptions=verbr
            AB.players={'1','2','3','4'}
            AB.contracts=[]
            self.description={'1': 'You produce 9 units @0.',
                              '2': 'You consume 10 units ( 9@1 and 1@15).',
                              '3': 'You produce 9 units at site 20.',
                              '4': 'You consume 8 units ( 2@5, 2@8, 2@12 and 2@19).'}
            self.generaldescription="The city ranges from 0 to 20. Only each player knows where and how much he is producing or consuming. The overall production equals the consumption inside the city. The city is divided in a left and a right region, A and B."

            # calculation of freight compensation:
            # assume perfect freight and contract structure and spread freight costs per consumption site 50/50 to consumer and optimal producer
            # optimal freight to player 2:14, 3:72
            self.benchmarkcorrection={'1': 5,
                                      '2': 6,
                                      '3': 37,
                                      '4': 38 
                                     }
            self.optimalFreight=86
            # optimal freight: 2: 14, 4: 77, Sum: 91
            # AB.pexport=self.session.config['exportprice']

class IntroWPage(WaitPage):
    def after_all_players_arrive(self):
        b1=copy.deepcopy(self.subsession.session.config['boundary01'])
        market=MarketExample('AB4_1',b1) # SelfReMarket("Mein Bsp Markt")  # SelfReMarket("Beispiel")
        market.selfremarket.pimport=copy.deepcopy(self.session.config['importprice'])
        market.selfremarket.pexport=copy.deepcopy(self.session.config['exportprice'])
        market.selfremarket.pbench=copy.deepcopy(self.session.config['Benchmarkprice'])
        market.selfremarket.citylength=copy.deepcopy(self.session.config['Citylength'])
        self.subsession.session.vars['selfremarket']=market
        print("Initial Selfremarket, Subsession ID=%s"%(self.group.subsession_id))
        self.subsession.session.vars['selfremarket'].selfremarket.show01()
        self.subsession.session.vars['TRound']=1
# this page shows the general big information page 
class IntroPage(Page):
    pass                      

# this page shows the public info for the particular game and the player specific one for each player
class IntroPlayerPage(Page):
    def vars_for_template(self):
        c=[]
        p=[]
        for cons in self.subsession.session.vars['selfremarket'].selfremarket.consumptions:
            if(cons.bringer==str(self.player.id_in_group)):
                c.append(cons.site)
        for prod in self.subsession.session.vars['selfremarket'].selfremarket.productions:
            if(prod.receiver==str(self.player.id_in_group)):
                p.append(prod.prodsite)
        if len(c)==0:
            c2='None'
        else:
            c2=','.join(str(x) for x in c)
     
        if len(p)==0:
            p2='None'
        else:
            p2=','.join(str(x) for x in p)
 
        return { 'productionfacilities': p2, 'consumptionfacilities': c2 }

page_sequence = [IntroWPage,
]
