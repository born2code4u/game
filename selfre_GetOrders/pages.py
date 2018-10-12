from . import models
from ._builtin import Page, WaitPage
from .models import Constants
from otree.api import Currency as c 
import random

import selfremarket.selfre_market
from selfremarket.selfre_market import Produktion, Verbrauch
from .models import Constants, Orderapi, Player
from django import forms
from django.forms import modelformset_factory, formset_factory, BaseFormSet
from django.core.exceptions import ValidationError
from django.forms.utils import ErrorList
from .forms import ImportForm, BaseImportFormSet

from django.core import validators
from django.utils.translation import gettext_lazy as _, ngettext, ungettext

class commonWPrep(WaitPage):
    def after_all_players_arrive(self):
        self.subsession.session.vars['AllOrders']={}
        for x in self.group.get_players():
            x.name=x.id_in_group
            x.description=self.subsession.session.vars['selfremarket'].description[str(x.name)]

class OrderAPIPrepWPage(Page):
    pass

class CaptchaForm(forms.Form):
    def validate_positive(value):
        if value < 0:
            raise ValidationError(
                _('%(value)s is not a positive number'),
                params={'value': value},
            )
    region = "Region X"
    book = None
    alltrades = None
    lasttrades = None
    Mypurch = None
    Mysales = None
    # fields :
    bid = forms.IntegerField(initial=0, required=True,validators=[validate_positive])
    # bidvol = forms.IntegerField(initial=0, required=True,validators=[validate_positive])
    offer = forms.IntegerField(initial=0, required=True,validators=[validate_positive])
    # offervol = forms.IntegerField(initial=0, required=True,validators=[validate_positive])
    bidvol = forms.ChoiceField(choices=[(x,int(x)) for x in range(10)])
    offervol = forms.ChoiceField(choices=[(x,int(x)) for x in range(10)])
    NetDeals = None

class OrderAPIPage(Page):
    timeout_seconds = 8 
    def vars_for_template(self):
        CaptchaFormSetCC = formset_factory(CaptchaForm, extra=len(self.player.subsession.session.vars['selfremarket'].regions))
        CaptchaFormSet=CaptchaFormSetCC()
        books,Dall,DallLast,DmyB,DmyS = ({} for i in range(5))
        # create user specific Order Books per region!
        for r in self.player.subsession.session.vars['selfremarket'].regions:
            Nbid,Noff = (0,0)
            books[r.name],blist,olist,Dall[r.name],DallLast[r.name],DmyB[r.name],DmyS[r.name] = ([] for i in range(7))
            for key,x in self.player.subsession.session.vars['AllOrders'].items():
                if(x.status=='old' and x.region==r.name):
                    if(x.typus=="Bid"):
                        Nbid+=1
                        if(x.player==str(self.player.name)):
                            blist.append((x.price,'*'))  # make tuples
                        else:
                            blist.append((x.price,' '))
                    else:
                        Noff+=1
                        if(x.player==str(self.player.name)):
                            olist.append((x.price,'*'))  # make tuples
                        else:
                            olist.append((x.price,' '))
                if(x.typus=="Bid" and x.status=='exec' and x.region==r.name):
                    Dall[r.name].append((x.filled_price,x.timestamp))
                    if(x.timestamp==(self.player.subsession.session.vars['TRound']-1)):
                        DallLast[r.name].append((x.filled_price,x.timestamp))
                if(x.player==str(self.player.name) and x.status=='exec' and x.region==r.name):
                    if(x.typus=="Bid"):
                        DmyB[r.name].append((x.filled_price,x.timestamp))
                    if(x.typus=="Offer"):
                        DmyS[r.name].append((x.filled_price,x.timestamp))
            # order the lists
            blist.sort(key=lambda tup: tup[0],reverse=True)
            olist.sort(key=lambda tup: tup[0],reverse=False)
            # if more offers than bids, fill them up with empty - vice versa...
            if Nbid<Noff:
                for n in range(Noff-Nbid):
                   blist.append((" "," "))
            if Noff<Nbid:
                for n in range(Nbid-Noff):
                   olist.append((" ","  "))
            books[r.name]=zip(blist,olist)
            # alldeals[r.name]=Dall
            # alllastdeals[r.name]=DallLast  # difficult to distringuish ? timestamp !!
            # mydeals[r.name]=Dmy
            # mylastdeals[r.namme]=DmyLast
        i=0
        for f in CaptchaFormSet:
            f.region=self.player.subsession.session.vars['selfremarket'].regions[i]
            f.book=books[f.region.name]
            f.alltrades=Dall[f.region.name]
            f.lasttrades=DallLast[f.region.name]
            f.Mypurch=DmyB[f.region.name]
            f.Mysales=DmyS[f.region.name]
            f.NetDeals=len(f.Mypurch)-len(f.Mysales)
            i+=1
        return {
            'ordertaker_formset': CaptchaFormSet }
    def before_next_page(self):
        CasFS=formset_factory(CaptchaForm,extra=len(self.player.subsession.session.vars['selfremarket'].regions))
        orderformset=CasFS(self.request.POST)
        # test formset validation
        i=0
        for f in orderformset: # loop over regions
            f.is_valid()
            rgName=self.player.subsession.session.vars['selfremarket'].regions[i].name # using that form order is same as region order !!
            p=self.player
        # === fill now the propperly formatted orders into the AllOrders list ===
            if ('bidvol' in f.cleaned_data and 'bid' in f.cleaned_data):
                for n in range(int(f.cleaned_data['bidvol'])):
                    last_bid = models.Order(p.name,self.subsession.session.vars['TRound'],f.cleaned_data['bid'],"Bid",rgName)
                    dictLaenge = len(self.subsession.session.vars['AllOrders'])
                    self.subsession.session.vars['AllOrders'][dictLaenge] = last_bid
            if ('offervol' in f.cleaned_data and 'offer' in f.cleaned_data):
                for n in range(int(f.cleaned_data['offervol'])):
                    last_offer = models.Order(p.name,self.subsession.session.vars['TRound'],f.cleaned_data['offer'],"Offer",rgName)
                    dictLaenge = len(self.subsession.session.vars['AllOrders'])
                    self.subsession.session.vars['AllOrders'][dictLaenge] = last_offer
            i+=1
        # print("Selfemarket TESTx TRound %s "%(self.subsession.session.vars['TRound']))
        # self.subsession.session.vars['selfremarket'].selfremarket.show01()

class OrderProcessWPage(WaitPage):
    def after_all_players_arrive(self):
        del self.subsession.session.vars['OrderKeys'][:]
        for x in self.subsession.session.vars['AllOrders']:
            self.subsession.session.vars['OrderKeys'].append(x)            # funktioniert
        for r in self.subsession.session.vars['selfremarket'].regions:
            self.matcher=models.OrderMatcher(r.name)
            while True:
                x=self.matcher.bestmatch(self.subsession.session.vars['AllOrders'])
                if x!=True:
                    break
        for x in self.subsession.session.vars['OrderKeys']:
            self.subsession.session.vars['AllOrders'][x].age_me()          # funktioniert
        self.subsession.session.vars['TRound']+=1
# on TransferWPage1 the executed orders get collectd and selfremarket.contract
# objects are formed, they are stored into selfremarket unmatchables are set to im/export
# on next website TransferPage2
# on TransferPage3 the nomination is performed
class TransferWPage1(WaitPage):
    def after_all_players_arrive(self):
        # 1) transfer executed orders to Contracts in the selfre model
        for region in self.subsession.session.vars['selfremarket'].regions:
            for k,x in self.subsession.session.vars['AllOrders'].items():
                if (x.status=='exec' and x.region==region.name):
                    x.status='postpro'
                    y=self.subsession.session.vars['AllOrders'][x.filled_against]
                    y.status='postpro'
                    if x.typus=='Bid':
                        buyer=next((z for z in self.subsession.session.vars['selfremarket'].selfremarket.players if z == x.player),None) # match  by name
                        seller=next((z for z in self.subsession.session.vars['selfremarket'].selfremarket.players if z == y.player),None) # match  by name
                        c=selfremarket.Contract(seller,buyer,x.filled_price,region)  # eler,buyer,p,region)
                        # print("foo56 CREATE CONTRACT for players %s, %s"%(x.player,y.player))
                        
                        c.print()
                        self.subsession.session.vars['selfremarket'].selfremarket.add_contract(c)
                    else:
                        seller=next((z for z in self.subsession.session.vars['selfremarket'].selfremarket.players if z == x.player),None) # match  by name
                        buyer=next((z for z in self.subsession.session.vars['selfremarket'].selfremarket.players if z == y.player),None) # match  by name
                        c=selfremarket.Contract(seller,buyer,x.filled_price,region)
                        print("foo57 CREATE CONTRACT")
                        c.print()
                        self.subsession.session.vars['selfremarket'].selfremarket.add_contract(c)
        # check if all contracts got inserted...
        print("SelfreMarket - after deals and before nomination:")
        self.subsession.session.vars['selfremarket'].selfremarket.show01()

class ImportFormPage(Page):
    def vars_for_template(self):
        self.player.participant.vars['importexport'] = { 'Nunballanced' : 0, 'Ntask' : None, 'Nunderlyings': 0, 'Nagent' : None , 'msg' : None, 'negNunballanced': 0 } 
        impex=self.player.participant.vars['importexport']
        prods=[x for x in self.subsession.session.vars['selfremarket'].selfremarket.productions if x.receiver==self.player.name]
        cons=[x for x in self.subsession.session.vars['selfremarket'].selfremarket.consumptions if x.bringer==self.player.name]
        purchs=[x for x in self.subsession.session.vars['selfremarket'].selfremarket.contracts if x.buyer==self.player.name]
        sales=[x for x in self.subsession.session.vars['selfremarket'].selfremarket.contracts if x.seller==self.player.name]

        impex['Nagent']=len(prods)+len(purchs)
        impex['Ntask']=len(cons)+len(sales)
        impex['Nunderlyings']=0
        impex['Nunballanced']=impex['Nagent']-impex['Ntask']       # IF <0 then import necessary if 0 not thing and if >0 export necessry
        impex['negNunballanced']=impex['Ntask']-impex['Nagent']
        self.player.participant.vars['unerlyings']=[] 
        # extract the underlyings to be displayed in form
        if impex['Nunballanced']!=0:
            description=[]
            if impex['Nunballanced']>0: # export necessary
                underlyings = prods+purchs
                for x in underlyings:
                   if type(x) is Produktion: 
                       description.append("Production,Location="+str(x.prodsite))
                   else:
                       description.append("Purchase,"+str(x.region.name)+", P="+str(x.P))
                ImpFormSetX = formset_factory(ImportForm, formset=BaseImportFormSet, extra=len(underlyings), validate_max=True, validate_min=True)
            else:
                underlyings = cons+sales
                for x in underlyings:
                   if type(x) is Verbrauch: 
                       description.append("Consumption,Location="+str(x.site))
                   else:
                       description.append("Sale, "+str(x.region.name)+", P="+str(x.P))
                ImpFormSetX = formset_factory(ImportForm, formset=BaseImportFormSet, extra=len(underlyings), validate_max=True, validate_min=True)         
            impex['Nunderlyings']=len(underlyings)
            ImpFormSet=ImpFormSetX()
            ImpFormSet.is_valid()
            i=0
            for f in ImpFormSet.forms:
                f.underlyingDesc=description[i]
                i+=1
            return {
                'import_formset': ImpFormSet
            }
    def before_next_page(self):
        if self.participant.vars['importexport']['Nunderlyings']!=0:
            ImpFSC=formset_factory(ImportForm,formset=BaseImportFormSet, extra=self.participant.vars['importexport']['Nunderlyings'])
            impformset=ImpFSC(self.request.POST)
            impformset.is_valid()
            impex=self.player.participant.vars['importexport']
            # start ugly, that this code is here again (like in loop befoe) but I was not able to hand over list of references
            prods=[x for x in self.subsession.session.vars['selfremarket'].selfremarket.productions if x.receiver==self.player.name]
            cons=[x for x in self.subsession.session.vars['selfremarket'].selfremarket.consumptions if x.bringer==self.player.name]
            purchs=[x for x in self.subsession.session.vars['selfremarket'].selfremarket.contracts if x.buyer==self.player.name]
            sales=[x for x in self.subsession.session.vars['selfremarket'].selfremarket.contracts if x.seller==self.player.name]
            # end ugly
            if impex['Nunballanced']!=0:
                if impex['Nunballanced']>0: # export necessary
                    counter=0
                    underlyings=prods+purchs
                    for f in impformset.forms: # test if the right number of exported got selected
                        try:
                            if f.cleaned_data['yes']==True:
                                counter+=1
                        except KeyError:
                            print("SELFRAISE(1): %s"%(KeyError))
                    if counter==impex['Nunballanced']: # propperly choosen thus mark right agents for export... 
                        subcounter=0
                        for x in underlyings: 
                            try:
                                if impformset.forms[subcounter].cleaned_data['yes']==True:
                                    x.exported=True
                            except KeyError:
                                print("SELFRAISE(2): %s"%(KeyError))
                            subcounter+=1
                    else:                             # not propperly choosen, thus choose arbitrarily
                        subcounter=0
                        for x in underlyings: 
                            if subcounter<impex['Nunballanced']:
                                x.exported=True
                            subcounter+=1
                else:                                 # impoert necessary
                    counter=0
                    underlyings=cons+sales
                    for f in impformset.forms:        # test if the right number of imports got selected
                        try:
                            if f.cleaned_data['yes']==True:
                                counter+=1
                        except KeyError:
                            print("SELFRAISE(3): %s"%(KeyError))
                    if counter==-impex['Nunballanced']: # right number of imports got selected
                        subcounter=0
                        for x in underlyings: 
                            try:
                                if impformset.forms[subcounter].cleaned_data['yes']==True:
                                    x.imported = True
                            except KeyError:
                                print("SELFRAISE(4): %s"%(KeyError))
                            subcounter+=1
                    else:                              # wrong number of imports choosen-> choose arbitrary right ones
                        subcounter=0
                        for x in underlyings: 
                            if subcounter<-impex['Nunballanced']:
                                x.imported = True
                            subcounter+=1
        print("Selfre Market after imp/exp")
        self.subsession.session.vars['selfremarket'].selfremarket.show01()
 
 
        # mark import/export in selfremarket objects:
        
class Wait4impexpWPage(WaitPage):
    pass

class NominationWPage(WaitPage):
    def after_all_players_arrive(self):
        for n in range(3): # nunber of optimization rounds
            print("NomRound %s"%(n))
            for x in self.group.get_players(): #  self.subsession.session.vars['selfremarket'].selfremarket.players:
                print("..for player %s"%(x.name))
                print(self.subsession.session.vars['selfremarket'].selfremarket.make_nomination(x.name))
        print("SelfeMarket -- after all nominations:")
        self.subsession.session.vars['selfremarket'].selfremarket.show01()
        print("Session finished.")

class FinishWPage(WaitPage):
    def after_all_players_arrive(self):
        # group results: F, all display orders/deals
        
        F=self.subsession.session.vars['selfremarket'].selfremarket.getTotalFreight()
        bench=self.subsession.session.vars['selfremarket'].selfremarket.pbench
        printorders={}
        for region in self.subsession.session.vars['selfremarket'].regions:
            printorders[region.name] = { 'Bids': [], 'Offers': [], 'Deals': [], 'Benchmark': bench, 'Average': 0 }
        for region in self.subsession.session.vars['selfremarket'].regions:
            dealaverage=0
            dealnumber=0
            for key,x in self.subsession.session.vars['AllOrders'].items():
                if x.typus=='Bid' and x.region==region.name:
                    printorders[x.region]['Bids'].append([x.timestamp,x.price])
                    if x.status=='postpro':
                        printorders[x.region]['Deals'].append([x.timestamp,x.filled_price])
                        dealnumber+=1
                        dealaverage+=x.filled_price
                if x.typus=='Offer' and x.region==region.name:
                    printorders[x.region]['Offers'].append([x.timestamp,x.price])
            if dealnumber>0:
                dealaverage/=dealnumber
            else:
                dealaverage=bench
            printorders[region.name]['Average']=dealaverage
        # 2) individual reults:
        pnl={}
        for p in self.group.get_players():
            pnl[p.name]=self.subsession.session.vars['selfremarket'].selfremarket.pnlBench(p.name)
            pnl[p.name]+=self.subsession.session.vars['selfremarket'].benchmarkcorrection[p.name] 
            p.pnl=pnl[p.name] # necessary so that operator can see all results
            p.groupfreight=F        # ''

        self.group.subsession.session.vars['pnl']=pnl
        self.group.subsession.session.vars['F']=F
        self.group.subsession.session.vars['Fopt']=self.subsession.session.vars['selfremarket'].optimalFreight
        self.group.subsession.session.vars['Printorders']=printorders
        

class FinishPage(Page):
    def vars_for_template(self):
        pnl=self.group.subsession.session.vars['pnl']
        F=self.group.subsession.session.vars['F']
        Fopt=self.group.subsession.session.vars['Fopt']
        printorders=self.group.subsession.session.vars['Printorders']
        print("Printorders for Player %s: %s"%(self.player.name,printorders))
        pairlines=[]
        for x in self.subsession.session.vars['selfremarket'].selfremarket.productions:
            if x.nom!=-1:
                pairlines.append([x.prodsite,x.nom])
        return {'pnl': pnl, 'F': F , 'Fopt': Fopt, 'Printorders': printorders, 'lines': pairlines}

# class chartPage(Page):
#    def vars_for_template(self):
#        x=[43900,43900,43900,43900,43900,43900,43900,43900]
#        return {'testdata': x}

page_sequence = [commonWPrep,
                 OrderAPIPrepWPage,
                 OrderAPIPage,OrderProcessWPage,
                 OrderAPIPage,OrderProcessWPage,
                 OrderAPIPage,OrderProcessWPage,
                 OrderAPIPage,OrderProcessWPage,
                 OrderAPIPage,OrderProcessWPage,
                 OrderAPIPage,OrderProcessWPage,
                 TransferWPage1,  
                 ImportFormPage,  
                 Wait4impexpWPage, 
                 NominationWPage,
                 FinishWPage,
                 FinishPage
                ]
