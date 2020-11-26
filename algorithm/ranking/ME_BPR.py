from baseclass.MetaRecommender import MetaRecommender
from tool import config
from random import shuffle, choice
from collections import defaultdict
import numpy as np
from tool.qmath import sigmoid, cosine
from math import log
import gensim.models.word2vec as w2v
import traceback



class ME_BPR(MetaRecommender):
    def __init__(self, conf, trainingSet=None, testSet=None, relation=None, inform1=None , inform2=None , fold='[1]'):
        MetaRecommender.__init__(self, conf=conf, trainingSet=trainingSet, testSet=testSet, relation=relation , inform1=inform1 , inform2=inform2 ,fold=fold)

    def readConfiguration(self):
        super(ME_BPR, self).readConfiguration()
        options = config.LineConfig(self.config['ME_BPR'])
        self.walkCount = int(options['-T'])
        self.walkLength = int(options['-L'])
        #self.walkMetaLength = int(options['-L1'])
        self.walkDim = int(options['-l'])
        self.winSize = int(options['-w'])
        self.topK = int(options['-k'])
       #self.topK-I = int(options['-k1'])
        self.alpha = float(options['-a'])
        self.epoch = int(options['-ep'])
        self.neg = int(options['-neg'])
        self.rate = float(options['-r'])

    def printAlgorConfig(self):
        super(ME_BPR, self).printAlgorConfig()
        print 'Specified Arguments of', self.config['recommender'] + ':'
        print 'Walks count per user', self.walkCount
        print 'Length of each walk', self.walkLength
        #print 'Length of each Meta walk', self.walkMetaLength
        print 'Dimension of user embedding', self.walkDim
        print '=' * 80

    def readNegativeFeedbacks(self):
        self.negative = defaultdict(list)
        self.nItems = defaultdict(list)
        filename = self.config['ratings'][:-4]+'.txt'
        with open(filename) as f:
            for line in f:
                items = line.strip().split()
                self.negative[items[0]].append(items[1])
                self.nItems[items[1]].append(items[0])
                if items[0] not in self.data.user:
                    self.data.user[items[0]]=len(self.data.user)
                    self.data.id2user[self.data.user[items[0]]] = items[0]

    def initModel(self):
        super(ME_BPR, self).initModel()
        self.positive = defaultdict(list)
        self.pItems = defaultdict(list)
        for user in self.data.trainSet_u:
            for item in self.data.trainSet_u[user]:
                self.positive[user].append(item)
                self.pItems[item].append(user)
        self.readNegativeFeedbacks()
        self.P = np.ones((len(self.data.user), self.embed_size))*0.1  # latent user matrix
        
        self.threshold = {}
        self.avg_sim = {}
        self.thres_d = dict.fromkeys(self.data.user.keys(),0) #derivatives for learning thresholds
        self.thres_count = dict.fromkeys(self.data.user.keys(),0)

        print 'Preparing item sets...'
        self.PositiveSet = defaultdict(dict)
        self.NegSets = defaultdict(dict)

       
        for user in self.data.user:
            if user in self.data.trainSet_u:
                for item in self.data.trainSet_u[user]:
                    self.PositiveSet[user][item] = 1

        for user in self.data.user:
            if user in self.data.trainSet_i:
                for item in self.negative[user]:
                    if self.data.item.has_key(item):
                        self.NegSets[user][item] = 1

    def randomWalks(self):
        print 'Kind Note: This method will probably take much time.'
        # build U-F-NET
        print 'Building weighted user-friend network...'
        # filter isolated nodes and low ratings
        # Definition of Meta-Path
        #
        p1 = 'UIU'
        p2 = 'UFU'
        p3 = 'UTU'
        p4 = 'UFIU'
        p5 = 'UFUIU'
        p6 = 'UIAIU'
        p7 = 'UIDIU'
        mPaths = [p1,p6,p7]
        print 'length of positive1:', len(self.positive)

        self.G = np.random.rand(self.data.trainingSize()[0], self.walkDim) * 0.1
        self.W = np.random.rand(self.data.trainingSize()[0], self.walkDim) * 0.1

        self.UFNet = defaultdict(list) # a -> b #a trusts b
        for u in self.social.followees:
            s1 = set(self.social.followees[u])
            for v in self.social.followees[u]:
                if v in self.social.followees:  # make sure that v has out links
                    if u <> v:
                        s2 = set(self.social.followees[v])
                        weight = len(s1.intersection(s2))
                        self.UFNet[u] += [v] * (weight + 1)

        self.UTNet = defaultdict(list) # a <- b #a is trusted by b
        for u in self.social.followers:
            s1 = set(self.social.followers[u])
            for v in self.social.followers[u]:
                if self.social.followers.has_key(v):  # make sure that v has out links
                    if u <> v:
                        s2 = set(self.social.followers[v])
                        weight = len(s1.intersection(s2))
                        self.UTNet[u] += [v] * (weight + 1)

        print 'Generating random meta-path random walks... (Positive)'
        self.pWalks = []
        # self.usercovered = {}

        # positive
        for user in self.data.user:
            for mp in mPaths:
                if mp == p1:
                    self.walkCount = 10
                if mp == p2:
                    self.walkCount = 8
                if mp == p3:
                    self.walkCount = 8                            
                if mp == p6:
                    self.walkCount = 5
                if mp == p7:
                    self.walkCount = 5
                for t in range(self.walkCount):
                    path = ['U' + user]
                    lastNode = user
                    nextNode = user
                    lastType = 'U'
                    #print 'length of positive2:', len(self.positive)
                    for i in range(self.walkLength / len(mp[1:])):
                        #print 'length of positive1:', len(self.positive)
                        for tp in mp[1:]:
                            #print 'length of positive1.1:', len(self.positive)
                            try:
                                if tp == 'I':
                                    if lastType == 'A':
                                        nextNode = choice(self.meta.act[lastNode])
                                    elif lastType == 'D':
                                        nextNode = choice(self.meta.dm[lastNode])
                                    else:
                                        if lastNode in self.positive:
                                            nextNode = choice(self.positive[lastNode])
                                        else:
                                            raise IndexError
                        
                                #print 'length of positiveI:', len(self.positive)
                                if tp == 'U':
                                    if lastType == 'I':
                                        nextNode = choice(self.pItems[lastNode])
                                    elif lastType == 'F':
                                        nextNode = choice(self.UFNet[lastNode])
                                        while not self.data.user.has_key(nextNode):
                                            nextNode = choice(self.UFNet[lastNode])
                                    elif lastType == 'T':
                                        nextNode = choice(self.UTNet[lastNode])
                                        while not self.data.user.has_key(nextNode):
                                            nextNode = choice(self.UTNet[lastNode])
                                #print 'length of positiveU:', len(self.positive)
                                if tp == 'F':
                                    nextNode = choice(self.UFNet[lastNode])
                                    while not self.data.user.has_key(nextNode):
                                        nextNode = choice(self.UFNet[lastNode])

                                if tp == 'T':
                                    nextNode = choice(self.UFNet[lastNode])
                                    while not self.data.user.has_key(nextNode):
                                        nextNode = choice(self.UFNet[lastNode])

                                if tp == 'A':
                                    i = 0
                                    #print 'length of positiveA1:', len(self.positive)
                                    nextNode = choice(self.meta.actors[lastNode])
                                    while not self.meta.actor.has_key(nextNode) and i > len(self.meta.actors[lastNode]):
                                        nextNode = choice(self.meta.actors[lastNode])
                                        i = i+1
                                #print 'length of positiveA2:', len(self.positive)
                                
                                if tp == 'D':
                                    i = 0
                                    #print 'length of positiveD1:', len(self.positive)
                                    nextNode = choice(self.meta.md[lastNode])
                                    while not self.meta.dire.has_key(nextNode) and i > len(self.meta.md[lastNode]):
                                        nextNode = choice(self.meta.md[lastNode])
                                        i = i+1
                                    #print 'length of positiveD2:', len(self.positive)
                                
                                #print 'length of positive2.1:', len(self.positive)    
                                path.append(tp + nextNode)
                                #print 'length of positive2.2:', len(self.positive)
                                lastNode = nextNode
                                lastType = tp
                                #print 'length of positive2.3:', len(self.positive)
                            except Exception as e:
                                #print 'length of positive:', len(self.positive)
                                path = []
                                #print self.positive['2817'] , self.data.trainSet_u['2817']
                                # print 'str(e):\t\t',str(e)
                                # print 'traceback.print_exc():';
                                # traceback.print_exc()
                                # print 'traceback.format_exc():\n%s' % traceback.format_exc()
                                # print 'tp:',tp
                                # print 'lastNode:',lastNode
                                # print 'length of positive:', len(self.positive)
                                # print 'length of trainset_u',len(self.data.trainSet_u)
                                break

                    if path:
                        #print 'length of positive3:', len(self.positive)
                        self.pWalks.append(path)
                        #print 'length of positive4:', len(self.positive)

        print 'length of positive:', len(self.positive)
        print 'Generating random meta-path random walks... (Negative)'
        self.nWalks = []
        # self.usercovered = {}

        # negative
        for user in self.data.user:
            for mp in mPaths:
                if mp == p1:
                    self.walkCount = 10
                if mp == p2:
                    self.walkCount = 8
                if mp == p3:
                    self.walkCount = 8
                if mp == p4:
                    self.walkCount = 5
                if mp == p5:
                    self.walkCount = 5
                for t in range(self.walkCount):
                    path = ['U' + user]
                    lastNode = user
                    nextNode = user
                    lastType = 'U'
                    for i in range(self.walkLength / len(mp[1:])):
                        for tp in mp[1:]:
                            try:
                                if tp == 'I':
                                    if lastType == 'A':
                                        nextNode = choice(self.meta.act[lastNode])
                                    else:
                                        if lastNode in self.negative:
                                            nextNode = choice(self.negative[lastNode])
                                        else:
                                            raise IndexError

                                if tp == 'U':
                                    if lastType == 'I':
                                        nextNode = choice(self.nItems[lastNode])
                                    elif lastType == 'F':
                                        nextNode = choice(self.UFNet[lastNode])
                                        while not self.data.user.has_key(nextNode):
                                            nextNode = choice(self.UFNet[lastNode])
                                    elif lastType == 'T':
                                        nextNode = choice(self.UTNet[lastNode])
                                        while not self.data.user.has_key(nextNode):
                                            nextNode = choice(self.UTNet[lastNode])

                                if tp == 'F':
                                    nextNode = choice(self.UFNet[lastNode])
                                    while not self.data.user.has_key(nextNode):
                                        nextNode = choice(self.UFNet[lastNode])

                                if tp == 'T':
                                    nextNode = choice(self.UFNet[lastNode])
                                    while not self.data.user.has_key(nextNode):
                                        nextNode = choice(self.UFNet[lastNode])
                                
                                if tp == 'A':
                                    i = 0
                                    nextNode = choice(self.meta.actors[lastNode])
                                    while not self.data.item.has_key(nextNode) and i > len(self.meta.actors[lastNode]):
                                        nextNode = choice(self.meta.actors[lastNode])

                                path.append(tp + nextNode)
                                lastNode = nextNode
                                lastType = tp

                            except (KeyError, IndexError):
                                # print 'tp:',tp
                                # print 'lastNode:',lastNode
                                path = []
                                break

                    if path:
                        self.nWalks.append(path)

        shuffle(self.pWalks)
        print 'length of positive:', len(self.positive)
        print 'pwalks:', len(self.pWalks)
        print 'nwalks:', len(self.nWalks)

    def computeSimilarity(self):
        # Training get top-k friends
        print 'Generating user embedding...'
        print 'length of positive:', len(self.positive)
        print 'length of trainset_u:', len(self.data.trainSet_u)
        self.pTopKSim = {}
        self.nTopKSim = {}
        self.pSimilarity = defaultdict(dict)
        self.nSimilarity = defaultdict(dict)
        pos_model = w2v.Word2Vec(self.pWalks, size=self.walkDim, window=5, min_count=0, iter=10)
        neg_model = w2v.Word2Vec(self.nWalks, size=self.walkDim, window=5, min_count=0, iter=10)
        for user in self.positive:
            uid = self.data.user[user]
            try:
                self.W[uid] = pos_model.wv['U' + user]
            except KeyError:
                continue
        for user in self.negative:
            uid = self.data.user[user]
            try:
                self.G[uid] = neg_model.wv['U' + user]
            except KeyError:
                continue
        print 'User embedding generated.'

        print 'Constructing similarity matrix...'
        i = 0
        for user1 in self.positive:
            uSim = []
            i += 1
            if i % 200 == 0:
                print i, '/', len(self.positive)
            vec1 = self.W[self.data.user[user1]]
            for user2 in self.positive:
                if user1 <> user2:
                    vec2 = self.W[self.data.user[user2]]
                    sim = cosine(vec1, vec2)
                    uSim.append((user2, sim))
            fList = sorted(uSim, key=lambda d: d[1], reverse=True)[:self.topK]
            self.threshold[user1] = fList[self.topK / 2][1]
            for pair in fList:
                self.pSimilarity[user1][pair[0]] = pair[1]
            self.pTopKSim[user1] = [item[0] for item in fList]
            self.avg_sim[user1] = sum([item[1] for item in fList][:self.topK / 2]) / (self.topK / 2)

        i = 0
        for user1 in self.negative:
            uSim = []
            i += 1
            if i % 200 == 0:
                print i, '/', len(self.negative)
            vec1 = self.G[self.data.user[user1]]
            for user2 in self.negative:
                if user1 <> user2:
                    vec2 = self.G[self.data.user[user2]]
                    sim = cosine(vec1, vec2)
                    uSim.append((user2, sim))
            fList = sorted(uSim, key=lambda d: d[1], reverse=True)[:self.topK]
            for pair in fList:
                self.nSimilarity[user1][pair[0]] = pair[1]
            self.nTopKSim[user1] = [item[0] for item in fList]

        self.trueTopKFriends = defaultdict(list)
        for user in self.pTopKSim:
            trueFriends = list(set(self.pTopKSim[user]).intersection(set(self.nTopKSim[user])))
            self.trueTopKFriends[user] = trueFriends
            self.pTopKSim[user] = list(set(self.pTopKSim[user]).difference(set(trueFriends)))

    def updateSets(self):
        self.JointSet = defaultdict(dict)
        self.PS_Set = defaultdict(dict)
        # print 'len of user',len(self.data.user)
        # print 'len of transetu',len(self.data.trainSet_u)
        for user in self.data.user:
            if user in self.trueTopKFriends:
                for friend in self.trueTopKFriends[user]:
                    if friend in self.data.user and self.pSimilarity[user][friend] >= self.threshold[user]:
                        for item in self.positive[friend]:
                            if item not in self.PositiveSet[user] and item not in self.NegSets[user]:
                                self.JointSet[user][item] = friend

            if self.pTopKSim.has_key(user):
                for friend in self.pTopKSim[user][:self.topK]:
                    if friend in self.data.user and self.pSimilarity[user][friend] >= self.threshold[user]:
                        for item in self.positive[friend]:
                            if item not in self.PositiveSet[user] and item not in self.JointSet[user] \
                                    and item not in self.NegSets[user]:
                                self.PS_Set[user][item] = friend

            if self.nTopKSim.has_key(user):
                for friend in self.nTopKSim[user][:self.topK]:
                    try:
                        if user in self.threshold:
                            if friend in self.data.user and self.nSimilarity[user][friend]>=self.threshold[user]:
                                for item in self.negative[friend]:
                                    if item in self.data.item:
                                        if item not in self.PositiveSet[user] and item not in self.JointSet[user] \
                                                and item not in self.PS_Set[user]:
                                            self.NegSets[user][item] = friend
                    except KeyError:
                        self.search(friend)
                    

    def search(self,key):
        if key in self.data.trainSet_u:
            print key
            print self.positive[key]
            print self.data.trainSet_u[key]
            print self.data.user[key]
        else: 
            print key


    def buildModel(self):

        self.randomWalks()
        self.computeSimilarity()

        print 'Decomposing...'
        iteration = 0
        while iteration < self.maxIter:
            self.loss = 0
            self.updateSets()
            itemList = self.data.item.keys()
            for user in self.PositiveSet:
                #itemList = self.NegSets[user].keys()
                kItems = self.JointSet[user].keys()
                pItems = self.PS_Set[user].keys()
                nItems = self.NegSets[user].keys()

                u = self.data.user[user]

                for item in self.PositiveSet[user]:
                    i = self.data.item[item]
                    selectedItems = [i]
                    #select items from different sets
                    if len(kItems) > 0:
                        item_k = choice(kItems)                        
                        uf = self.JointSet[user][item_k]
                        k = self.data.item[item_k]
                        selectedItems.append(k)
                        self.optimization_thres(u,i,k,user,uf)
                    if len(pItems)>0:
                        item_p = choice(pItems)
                        p = self.data.item[item_p]
                        selectedItems.append(p)

                    item_r = choice(itemList)
                    while item_r in self.PositiveSet[user] or item_r in self.JointSet[user]\
                        or item_r in self.PS_Set[user] or item_r in self.NegSets[user]:
                        item_r = choice(itemList)
                    r = self.data.item[item_r]
                    selectedItems.append(r)

                    if len(nItems)>0:
                        item_n = choice(nItems)
                        n = self.data.item[item_n]
                        selectedItems.append(n)

                    #optimization
                    for ind,item in enumerate(selectedItems[:-1]):
                        self.optimization(u,item,selectedItems[ind+1])


                if self.thres_count[user]>0:
                    self.threshold[user] -= self.lRate * self.thres_d[user] / self.thres_count[user]
                    self.thres_d[user]=0
                    self.thres_count[user]=0
                    li = [sim for sim in self.pSimilarity[user].values() if sim>=self.threshold[user]]
                    if len(li)==0:
                        self.avg_sim[user] = self.threshold[user]
                    else:
                        self.avg_sim[user]= sum(li)/(len(li)+0.0)

                for friend in self.trueTopKFriends[user]:
                    if self.pSimilarity[user][friend]>self.threshold[user]:
                        u = self.data.user[user]
                        f = self.data.user[friend]
                        self.P[u] -= self.alpha*self.lRate*(self.P[u]-self.P[f])

            self.loss += self.regU * (self.P * self.P).sum() + self.regI * (self.Q * self.Q).sum()
            iteration += 1
            if self.isConverged(iteration):
                 break
            print self.foldInfo,'iteration:',iteration
        self.ranking_performance()


    def optimization(self, u, i, j):
        s = sigmoid(self.P[u].dot(self.Q[i]) - self.P[u].dot(self.Q[j]))
        self.P[u] += self.lRate * (1 - s) * (self.Q[i] - self.Q[j])
        self.Q[i] += self.lRate * (1 - s) * self.P[u]
        self.Q[j] -= self.lRate * (1 - s) * self.P[u]
        self.loss += -log(s)
        self.P[u] -= self.lRate * self.regU * self.P[u]
        self.Q[i] -= self.lRate * self.regI * self.Q[i]
        self.Q[j] -= self.lRate * self.regI * self.Q[j]

    def optimization_thres(self, u, i, j,user,friend):
        #print 'inner', (self.pSimilarity[user][friend]-self.threshold[user])/(self.avg_sim[user]-self.threshold[user])
        try:
            g_theta = sigmoid((self.pSimilarity[user][friend]-self.threshold[user])/(self.avg_sim[user]-self.threshold[user]))
        except OverflowError:
            print 'threshold',self.threshold[user],'smilarity',self.pSimilarity[user][friend],'avg',self.avg_sim[user]
            print (self.pSimilarity[user][friend]-self.threshold[user]),(self.avg_sim[user]-self.threshold[user])
            print (self.pSimilarity[user][friend]-self.threshold[user])/(self.avg_sim[user]-self.threshold[user])
            exit(-1)
        #print 'g_theta',g_theta

        s = sigmoid((self.P[u].dot(self.Q[i]) - self.P[u].dot(self.Q[j]))/(1+g_theta))
        self.P[u] += self.lRate * (1 - s) * (self.Q[i] - self.Q[j])
        self.Q[i] += self.lRate * (1 - s) * self.P[u]
        self.Q[j] -= self.lRate * (1 - s) * self.P[u]
        self.loss += -log(s)
        self.P[u] -= self.lRate * self.regU * self.P[u]
        self.Q[i] -= self.lRate * self.regI * self.Q[i]
        self.Q[j] -= self.lRate * self.regI * self.Q[j]
        t_derivative = -g_theta*(1-g_theta)*(1-s)*(self.P[u].dot(self.Q[i]) - self.P[u].dot(self.Q[j]))\
                       *(self.pSimilarity[user][friend]-self.avg_sim[user])/(self.avg_sim[user]-
                       self.threshold[user])**2/(1+g_theta)**2 + 0.005*self.threshold[user]
        #print 'derivative', t_derivative
        self.thres_d[user] += t_derivative
        self.thres_count[user] += 1

    def predictForRanking(self, u):
        'invoked to rank all the items for the user'
        if self.data.containsUser(u):
            u = self.data.getUserId(u)
            return self.Q.dot(self.P[u])
        else:
            return [self.data.globalMean] * self.num_items

