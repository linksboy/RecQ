import numpy as np
from structure import sparseMatrix,new_sparseMatrix
from collections import defaultdict

class MetaDAO(object):
    def __init__(self,conf,inform1=None,inform2=None):
        self.config = conf
        self.item = {} #used to store the order of items in trainingset
        self.actor = {} #used to store the order of actors
        self.dire = {} #used to store the order of directors
        self.inform1 = inform1
        self.inform2 = inform2
        self.actors = defaultdict(dict)
        self.act = defaultdict(dict)
        self.md = defaultdict(dict)
        self.dm = defaultdict(dict)
        self.ActMatrix = self.__generateActSet()
        self.DireMatrix = self.__generateDireSet()

    def __generateActSet(self):
        triple = []
        for line in self.inform1:
            movieId,actorId,weight = line
            #add relations to dict
            if movieId in self.actors:
                self.actors[movieId].append(actorId)
            else :
                self.actors.update({movieId:[actorId]})
        
            if actorId in self.act:
                self.act[actorId].append(movieId)
            else :
                self.act.update({actorId:[movieId]})

            # order the movie
            if movieId not in self.item:
                self.item[movieId] = len(self.item)
            if actorId not in self.actor:
                self.actor[actorId] = len(self.actor)
            triple.append([self.item[movieId], self.actor[actorId], weight])
        return new_sparseMatrix.SparseMatrix(triple)

    def __generateDireSet(self):
        triple = []
        for line in self.inform2:
            movieId,direId,weight = line
            #add relations to dict
            if movieId in self.md:
                self.md[movieId].append(direId)
            else :
                self.md.update({movieId:[direId]})
        
            if direId in self.dm:
                self.dm[direId].append(movieId)
            else :
                self.dm.update({direId:[movieId]})

            # order the movie
            if movieId not in self.item :
                self.item[movieId] = len(self.item)
            if direId not in self.dire:
                self.dire[direId] = len(self.dire)
            triple.append([self.item[movieId], self.dire[direId], weight])
        return new_sparseMatrix.SparseMatrix(triple)

    def row(self,m):
        #return movie m's actors
        return self.ActMatrix.row(self.item[m])

    def col(self,a):
        #return actor a's movies
        return self.ActMatrix.col(self.actor[a])

    def elem(self,m,a):
        return self.ActMatrix.elem(m,a)

    def weight(self,m,a):
        if m in self.actors and a in self.act[m]:
            return self.actors[m][a]
        else:
            return 0

    def ActorSize(self):
        return self.ActMatrix.size

    def getMovies(self,a):
        if self.act.has_key(a):
            return self.act[a]
        else:
            return {}

    def getActors(self,m):
        if self.actors.has_key(m):
            return self.actors[m]
        else:
            return {}

    def hasActor(self,m,a):
        if m in self.actors:
            if a in self.act[m]:
                return True
            else:
                return False
        return False

    def hasMovie(self,m,a):
        if a in self.act:
            if m in self.actors[a]:
                return True
            else:
                return False
        return False

    
    def rowD(self,m):
        #return movie m's directors
        return self.DireMatrix.row(self.item[m])

    def colD(self,d):
        #return actor a's movies
        return self.DireMatrix.col(self.dire[d])

    def elemD(self,m,d):
        return self.DireMatrix.elem(m,d)

    def weightD(self,m,d):
        if m in self.md and d in self.dm[m]:
            return self.md[m][d]
        else:
            return 0

    def DireSize(self):
        return self.DireMatrix.size

    def getMovies1(self,d):
        if self.dm.has_key(d):
            return self.dm[d]
        else:
            return {}

    def getActors1(self,m):
        if self.md.has_key(m):
            return self.md[m]
        else:
            return {}

    def hasDirector(self,m,d):
        if m in self.md:
            if d in self.dm[m]:
                return True
            else:
                return False
        return False

    def hasMovie1(self,m,d):
        if d in self.dm:
            if m in self.md[d]:
                return True
            else:
                return False
        return False

