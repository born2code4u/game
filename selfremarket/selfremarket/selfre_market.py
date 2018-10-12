import copy
import selfremarket

# class player:
#    def __init__(self,name):
#        self.name=name

# the Market Class contains the portfolio of all playes including production, consumption and contracts
# the optimization of the nomination is included "player-wise" by the make-nomination method
# , which changes the nomination of contracts thus affects the nomination of other players
# global optimization is not implemented yet
# REQUIREMENT OUTSIDE CLASSES: Contract,Verbrauch,Produktion,Region, hungarian algorithm
# ASSUME (4 a while): all players are physically ballanced (once this conditions is relaxed some parts of the portfolio 
# shall be manually set to import/export and excluded from optimization routine

class SelfReMarket:
    pimport=100
    pexport=0
    loopindex=0
    pbench=None
    citylength=None
    def __init__(self,name):
        self.name=name # Name of the Market
        self.players=set([])
        self.contracts=[]
        self.productions=[]
        self.consumptions=[]
    def add_players(self,n):
        for x in n:
            self.players.add(x) 

    def safe_adder(self,target,neues):
        try:
            something=iter(neues)
            for x in neues:
                x.pimport=self.pimport
                x.pexport=self.pexport
                target.append(x)
        except Exception:
                neues.pimport=self.pimport
                neues.pexport=self.pexport
                target.append(neues)
    def add_production(self,p):
        self.safe_adder(self.productions,p)
    def add_contract(self,c):
        self.safe_adder(self.contracts,c)
    def add_consumption(self,v):
        self.safe_adder(self.consumptions,v)

    def show01(self):
        for x in self.productions+self.contracts+self.consumptions:
            x.print()       

    def costfunction(self,agent,task): # possible agents: purchased contracts, production / possible tasks: sold contracts, Verbrauch
        if type(agent) is Contract:
            if type(task) is Verbrauch:
                if not(agent.region.check(task.site)):
                    return(self.pexport-self.pimport)
                else:
                    return(-agent.C(task.site))
            else:                                                 # then task has to be contract
                if agent.region.name!=task.region.name:           # contracts in different Regions
                    return(self.pexport-self.pimport)
                else:                                   # contracts in same region
                    if task.nom==-1:                  # just not yet nominated task, then treat as a loop and give pseudo nomination to center
                        return(task.C(task.region.center)-agent.C(task.region.center))   # before: return(0)
                    else:
                        return(task.C(task.nom)-agent.C(task.nom))
        else:   # then agent is Production
            if type(task) is Verbrauch:
                return(-agent.C(task.site)) 
            else: # then task is contract
                if task.nom==-1: # not yet nominated 
                    return(task.C(task.region.center)-agent.C(task.region.center)) # is estimate 
                else:
                    return(task.C(task.nom)-agent.C(task.nom))                      

    def make_nomination(self,player):
        # 1. create agent and task list for player
        list_PP=[]
        list_VS=[]
        for x in self.contracts+self.productions:
            if ((x.receiver==player) and (x.exported==False)):
                list_PP.append(x)
        for x in self.consumptions+self.contracts:
            if ((x.bringer==player) and (x.imported==False)):
                list_VS.append(x)
        n_PP=len(list_PP)
        n_VS=len(list_VS)
        # 2.0 create cost matrix
        # 2.1 OLD: assume that number of tasks=number of agents
        # 2.1 NEW: the imported or exported=True tasks and agents are excluded (see above)
        pnlmatrix = [[0 for x in range(n_PP)] for y in range(n_VS)] 
        for i in range(n_PP):
            for j in range(n_VS):
                pnlmatrix[i][j]=self.costfunction(list_PP[i],list_VS[j]) 
        # 3. find optimal agent2task matrix by hungarian algorithm
        if n_PP>0: # only for non zero dim matrix
            nomtupples=selfremarket.hungalg.maximize(pnlmatrix)  # minimize(pnlmatrix)
        else:
            nomtupples=[]
        # 4. nominate contracts according to optimal solution
        # and give the prospective c2c nominations a loop-maker
        utilpnl=0

        for T in nomtupples:
            utilpnl+=pnlmatrix[T[0]][T[1]]      # 1. Build PnL
            # just alwaysif type(list_PP[T[0]]) is Contract: # 2. c-c can be loop !... handle it
            list_PP[T[0]].nom=list_VS[T[1]].nom   # this should actually nominate productions and purchases
            # print("+")
        return(utilpnl,pnlmatrix,nomtupples)
    def pnlBench(self,player):
        pnl=0
        # 1.contracts
        for x in self.contracts:
            if x.seller==player:
                if x.imported==True:
                    pnl+=x.C(x.nom)-self.pimport
                else:
                    pnl+=x.C(x.nom)
            if x.buyer==player:
                if x.exported==True:
                    pnl+=self.pexport-x.C(x.nom)
                else:
                    pnl+=-x.C(x.nom)
        # 2. for consumptions
        for x in self.consumptions:
            if x.bringer==player:
                if x.imported==True:
                    pnl+=self.pbench-self.pimport # direct import
                else:
                    pnl+=self.pbench
        # 3. for production
        for x in self.productions:
            if x.receiver==player:
                if x.exported==True:
                    pnl+=self.pexport-self.pbench
                else:
                    pnl+=-self.pbench-x.C(x.nom)
        return(pnl)

    def getTotalFreight(self):
        F=0
        # 1. direct export ex productions or real transports
        for x in self.productions:
            if x.exported==True:
                F+=self.citylength 
            else:
                F+=abs(x.nom-x.prodsite) 
        #  2. direct imports to consumptions
        for x in self.consumptions:
            if x.imported==True:
                F+=self.citylength
        # 3. imports to or exports from contracts
        for x in self.contracts:
            if x.exported==True:
                F+=self.citylength
            if x.imported==True:
                F+=self.citylength
        return(F) 

class Region:
    def __init__(self,minimum,maximum,center,unitfreightcost,name):
        self.min=minimum
        self.max=maximum
        self.name=name
        self.center=center 
        self.Center=center # just because django templates seem to collide with ".center"
        self.F=unitfreightcost
    def check(self,i):
        if ((self.min<=i) and (i<=self.max)):
            return(True)
        else:
            return(False)

class Contract:
    exported = False
    imported = False
    def __init__(self,seller,buyer,P,region):
        self.seller=seller
        self.buyer=buyer
        self.bringer=self.seller
        self.receiver=self.buyer
        self.region=region
        self.P=P
        self.nom=-1
        self.marker=-1
        self.lasttask=-1
        self.loop=-1
    def print(self):
        print('Contract -- Seller:%s, Buyer:%s, P=%s, Region=%s, Nom@=%s, Exp=%s, Imp=%s' %(self.seller,self.buyer,self.P,self.region.name,self.nom,self.exported,self.imported))
    def C(self,site): # BE careful, this gives number even outside of range of the contract Region !!
        return(self.P+abs(site-self.region.center)*self.region.F)
    def setprice(self,x):
        self.P=x

class Produktion:
    exported = False
    def __init__(self,player,site,unitcost,unitfreightcost):
        self.receiver=player # exclusive 'recreiver' from production facilitiy -- it is not necessarily the player who owns final destinati
        self.prodsite=site   # anonymeous 'bringer' is not part of the game
        self.unitcost=unitcost
        self.unitfreightcost=unitfreightcost
        self.nom=-1
        self.oldtask=-1
    def C(self,destination):
        return(self.unitcost+abs(self.prodsite-destination)*self.unitfreightcost)
    def print(self):
        print('Production -- Owner:%s, site=%s, P=%s, FP=%s, Nom@=%s, Exp=%s '%(self.receiver,self.prodsite,self.unitcost,self.unitfreightcost,self.nom,self.exported))

class Verbrauch:
    imported = False
    def __init__(self,player,site):
        self.bringer=player
        self.site=site
        self.nom=self.site
    def print(self):
        print('Consumption -- Owner:%s, site=%s, Imp=%s , Nom@=%s'%(self.bringer,self.site,self.imported,self.nom))
    def C(self,site):
        return(0)
