from baseclass.IterativeRecommender import IterativeRecommender
from data.social import SocialDAO
from data.meta_actor import MetaDAO
from tool import config
from os.path import abspath
class MetaRecommender(IterativeRecommender):
    def __init__(self,conf,trainingSet,testSet,relation,inform1,inform2,fold='[1]'):
        super(MetaRecommender, self).__init__(conf,trainingSet,testSet,fold)
        self.social = SocialDAO(self.config,relation) #social relations access control
        self.meta = MetaDAO(self.config,inform1,inform2)

        # data clean
        cleanList = []
        cleanPair = []
        for user in self.social.followees:
            if not self.data.user.has_key(user):
                cleanList.append(user)
            for u2 in self.social.followees[user]:
                if not self.data.user.has_key(u2):
                    cleanPair.append((user, u2))
        for u in cleanList:
            del self.social.followees[u]

        for pair in cleanPair:
            if self.social.followees.has_key(pair[0]):
                del self.social.followees[pair[0]][pair[1]]

        cleanList = []
        cleanPair = []
        for user in self.social.followers:
            if not self.data.user.has_key(user):
                cleanList.append(user)
            for u2 in self.social.followers[user]:
                if not self.data.user.has_key(u2):
                    cleanPair.append((user, u2))
        for u in cleanList:
            del self.social.followers[u]

        for pair in cleanPair:
            if self.social.followers.has_key(pair[0]):
                del self.social.followers[pair[0]][pair[1]]

        idx = []
        for n,pair in enumerate(self.social.relation):
            if pair[0] not in self.data.user or pair[1] not in self.data.user:
                idx.append(n)

        for item in reversed(idx):
            del self.social.relation[item]

        cleanList = []
        cleanPair = []
        for movie in self.meta.actors:
            if not self.data.item.has_key(movie):
                cleanList.append(movie)
            for actor in self.meta.actors[movie]:
                if not self.meta.actor.has_key(actor):
                    cleanPair.append((movie,actor))
        for m in cleanList:
            del self.meta.actors[m]
        
        for pair in cleanPair:
            if self.meta.actors.has_key(pair[0]):
                del self.meta.actors[pair[0]][pair[1]]

        cleanList = []
        cleanPair = []
        for actor in self.meta.act:
            if not self.meta.actor.has_key(actor):
                cleanList.append(actor)
            for movie in self.meta.act[actor]:
                if not self.meta.item.has_key(movie):
                    cleanPair.append((actor,movie))
        for a in cleanList:
            del self.meta.act[a]
        
        for pair in cleanPair:
            if self.meta.act.has_key(pair[0]):
                del self.meta.act[pair[0]][pair[1]]

        
        idx = []
        for n,pair in enumerate(self.meta.inform1):
            if pair[0] not in self.meta.item or pair[1] not in self.meta.actor:
                idx.append(n)

        for item in reversed(idx):
            del self.meta.inform1[item]


        cleanList = []
        cleanPair = []
        for movie in self.meta.md:
            if not self.data.item.has_key(movie):
                cleanList.append(movie)
            for dire in self.meta.md[movie]:
                if not self.meta.dire.has_key(dire):
                    cleanPair.append((movie,dire))
        for m in cleanList:
            del self.meta.md[m]
        
        for pair in cleanPair:
            if self.meta.md.has_key(pair[0]):
                del self.meta.md[pair[0]][pair[1]]

        cleanList = []
        cleanPair = []
        for dire in self.meta.dm:
            if not self.meta.dire.has_key(dire):
                cleanList.append(dire)
            for movie in self.meta.dm[dire]:
                if not self.meta.item.has_key(movie):
                    cleanPair.append((dire,movie))
        for d in cleanList:
            del self.meta.dm[d]
        
        for pair in cleanPair:
            if self.meta.dm.has_key(pair[0]):
                del self.meta.dm[pair[0]][pair[1]]

        
        idx = []
        for n,pair in enumerate(self.meta.inform2):
            if pair[0] not in self.meta.item or pair[1] not in self.meta.dire:
                idx.append(n)

        for item in reversed(idx):
            del self.meta.inform2[item]

    def readConfiguration(self):
        super(MetaRecommender, self).readConfiguration()
        regular = config.LineConfig(self.config['reg.lambda'])
        self.regS = float(regular['-s'])

    def printAlgorConfig(self):
        super(MetaRecommender, self).printAlgorConfig()
        print 'Social dataset:',abspath(self.config['social'])
        print 'Social size ','(User count:',len(self.social.user),'Trust statement count:'+str(len(self.social.relation))+')'
        print 'Social Regularization parameter: regS %.3f' % (self.regS)
        print '=' * 80
        print 'Actor dataset:',abspath(self.config['actor'])
        print 'Actor size ','(Actor count:',len(self.meta.actor),'Actor statement count:'+str(len(self.meta.inform1))+')'
        print '=' * 80
        print 'Director dataset:',abspath(self.config['dire'])
        print 'Director size ','(Director count:',len(self.meta.dire),'Director statement count:'+str(len(self.meta.inform2))+')'
        print '=' * 80

