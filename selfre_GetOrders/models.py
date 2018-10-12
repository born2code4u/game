from otree.api import (
    models, widgets, BaseConstants, BaseSubsession, BaseGroup, BasePlayer,
    Currency as c, currency_range
)
import operator
from otree.db.models import Model, ForeignKey
import random

from django import forms
from django.core.validators import validate_email

author = 'Your name here'

doc = """
Your app description
"""

class Constants(BaseConstants):
    name_in_url = 'ox_GameOneP'
    players_per_group = None
    num_rounds = 1 
    clearingprice = 50
    num_decisions_per_round = 5
    num_regions = 2

class Subsession(BaseSubsession):
    def creating_session(self):
        self.session.vars['orderliste']=[]
        self.session.vars['AllOrders']={}
        self.session.vars['OrderKeys']=[]
        self.session.vars['OrderedBids']=[]
   # def creating_session(self):   # called each round
   #     pass
        # following commented out, because 
        """For each player, create a fixed number of "decision stubs" with random values to be decided upon later."""
        # for p in self.get_players():
        #     p.generate_decision_stubs()
        # for p in self.get_players():
        #     p.generate_ordertaker()

class Order(object):
    key = ""
    player = ""
    timestamp = ""
    price = 0
    typus = ""
    filled_against = ""
    filled_price = None
    status = "fresh"
    region = ""
    def __init__(self,pl,ts,pr,ty,rg):
        self.player=pl
        self.timestamp=ts
        self.price=pr
        self.typus=ty
        self.region=rg
    # def __repr__(self):
    #   return repr(self.player, self.timestamp,self.price,self.typus)
    
    def age_me(self): # fresh->old, old->off, exec->exec
        if self.status=="old":
            self.status="off"
        if self.status=="fresh":
            self.status="old"
    def fill_order(self):
        p.bid_order.set("bla","blub",200,"buh")
    def __str__(self):
        return "Order -- %s/%s/%s/%s/%s/%s"%(self.player, self.timestamp, self.price, self.typus, self.status,self.region)

class OrderMatcher(Order):
    bids={}
    bids_ord=()
    offers={} 
    offers_ord=()
    test=99
    def __init__(self,region):
        self.region=region
    def extract_bids_offers(self,orderdict):
        self.bids.clear()
        self.offers.clear()
        for k,v in orderdict.items():
            if v.typus=="Bid" and (v.status=="fresh" or v.status=="old") and v.region==self.region:
                self.bids[k]=v              # this should hopefully be a copy - despite orderdict is a mutable 
        for k,v in orderdict.items():
            if v.typus=="Offer" and (v.status=="fresh" or v.status=="old") and v.region==self.region:
                self.offers[k]=v       
        def giveorderprice(x):
            return x.price
        self.bids_ord=[]
        for k,v in self.bids.items():
            v.key=k
            self.bids_ord.append(v)
        self.offers_ord=[]
        for k,v in self.offers.items():
            v.key=k
            self.offers_ord.append(v)
        from operator import itemgetter,attrgetter
        self.bids_ord.sort(key=giveorderprice,reverse=True)
        self.offers_ord.sort(key=giveorderprice,reverse=False)
    def give_bids_ord(self):
        return(self.bids_ord)
    def bestmatch(self,orderdict):
        self.extract_bids_offers(orderdict)
        # self.session.vars['test']=self.bids_ord
        for vb in self.bids_ord:
            for vo in self.offers_ord:
                if vb.player!=vo.player and vb.region==vo.region:
                   if vb.price>=vo.price:
                       avprice=0.5*(vb.price+vo.price)
                       orderdict[vb.key].status="exec" # seems to be overwritten later... ?
                       orderdict[vb.key].filled_against=vo.key
                       orderdict[vb.key].filled_price=avprice
                       orderdict[vo.key].status="exec"
                       orderdict[vo.key].filled_against=vb.key
                       orderdict[vo.key].filled_price=avprice
                       return(True)
        return(False)
    def calcposition(self,orderdict,p):
        pos=0
        money=0
        for k,order in orderdict.items():
            if order.status=="exec":
                if order.player==p.name:
                    if order.typus=="Bid":
                        pos+=1
                        money-=order.filled_price
                    else:
                        pos-=1
                        money+=order.filled_price
        return([pos,money])
    def __str__(self):
        s1="".join(str(extorder.price).join("/") for extorder in self.bids_ord)
        s2="".join(str(extorder.price).join("/") for extorder in self.offers_ord)
        return("BidOrder(%s),OfferOrder(%s)"%(s1,s2)) # "Order -- %s/%s/%s/%s/%s"%(self.player, self.timestamp, self.price, self.typus, self.region)

class Group(BaseGroup):
    pass

class Player(BasePlayer):
    name = models.StringField()
    description = models.StringField()
    bid = models.PositiveIntegerField(min=0, max=100, initial=0)
    bidvol = models.PositiveIntegerField(min=0, max=3, initial=0)
    offer = models.PositiveIntegerField(min=0, max=100, initial=100)
    offervol = models.PositiveIntegerField(min=0, max=3, initial=0)
    pos = models.IntegerField(initial=0)
    money = models.CurrencyField(initial=0) 
    pnl = models.CurrencyField(initial=0)
    groupfreight = models.PositiveIntegerField(initial=0) 
    minfreight = models.PositiveIntegerField(initial=0) 

class MultiEmailField(forms.Field):
    def to_python(self, value):
        """Normalize data to a list of strings."""
        # Return an empty list if no input was given.
        if not value:
            return []
        return value.split(',')

    def validate(self, value):
        """Check if value consists only of valid emails."""
        # Use the parent's handling of required fields, etc.
        super().validate(value)
        for email in value:
            validate_email(email)
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

class Orderapi(Model):
    idx = models.IntegerField()    # will be randomly generated
    region = models.StringField(initial='Region X')
    bid = models.PositiveIntegerField(min=0, max=1000,initial=0)
    bidvol = models.IntegerField(min=0,max=3, initial=0)
    offer = models.IntegerField(min=0,max=1000,initial=1000)
    offervol = models.IntegerField(min=0,max=3,initial=0)
    player = ForeignKey(Player)    # creates 1:m relation -> this decision was made by a certain player
     
