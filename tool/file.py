import os.path
from os import makedirs,remove
from re import compile,findall,split
from config import LineConfig
class FileIO(object):
    def __init__(self):
        pass

    # @staticmethod
    # def writeFile(filePath,content,op = 'w'):
    #     reg = compile('(.+[/|\\\]).+')
    #     dirs = findall(reg,filePath)
    #     if not os.path.exists(filePath):
    #         os.makedirs(dirs[0])
    #     with open(filePath,op) as f:
    #         f.write(str(content))

    @staticmethod
    def writeFile(dir,file,content,op = 'w'):
        if not os.path.exists(dir):
            os.makedirs(dir)
        with open(dir+file,op) as f:
            f.writelines(content)

    @staticmethod
    def deleteFile(filePath):
        if os.path.exists(filePath):
            remove(filePath)

    @staticmethod
    def loadDataSet(conf, file, bTest=False,binarized = False, threshold = 3.0):
        trainingData = []
        testData = []
        ratingConfig = LineConfig(conf['ratings.setup'])
        if not bTest:
            print 'loading training data...'
        else:
            print 'loading test data...'
        with open(file) as f:
            ratings = f.readlines()
        # ignore the headline
        if ratingConfig.contains('-header'):
            ratings = ratings[1:]
        # order of the columns
        order = ratingConfig['-columns'].strip().split()
        delim = ' |,|\t'
        if ratingConfig.contains('-delim'):
            delim=ratingConfig['-delim']
        for lineNo, line in enumerate(ratings):
            items = split(delim,line.strip())
            if not bTest and len(order) < 2:
                print 'The rating file is not in a correct format. Error: Line num %d' % lineNo
                exit(-1)
            try:
                userId = items[int(order[0])]
                itemId = items[int(order[1])]
                if len(order)<3:
                    rating = 1 #default value
                else:
                    rating  = items[int(order[2])]
                if binarized:
                    if float(items[int(order[2])])<threshold:
                        continue
                    else:
                        rating = 1
            except ValueError:
                print 'Error! Have you added the option -header to the rating.setup?'
                exit(-1)
            if not bTest:
                trainingData.append([userId, itemId, float(rating)])
            else:
                if binarized:
                    if rating==1:
                        testData.append([userId, itemId, float(rating)])
                    else:
                        continue
                testData.append([userId, itemId, float(rating)])
        if not bTest:
            return trainingData
        else:
            return testData

    @staticmethod
    def loadRelationship(conf, filePath):
        socialConfig = LineConfig(conf['social.setup'])
        relation = []
        print 'loading social data...'
        with open(filePath) as f:
            relations = f.readlines()
            # ignore the headline
        if socialConfig.contains('-header'):
            relations = relations[1:]
        # order of the columns
        order = socialConfig['-columns'].strip().split()
        if len(order) <= 2:
            print 'The social file is not in a correct format.'
        for lineNo, line in enumerate(relations):
            items = split(' |,|\t', line.strip())
            if len(order) < 2:
                print 'The social file is not in a correct format. Error: Line num %d' % lineNo
                exit(-1)
            userId1 = items[int(order[0])]
            userId2 = items[int(order[1])]
            if len(order) < 3:
                weight = 1
            else:
                weight = float(items[int(order[2])])
            relation.append([userId1, userId2, weight])
        return relation

    @staticmethod
    def loadInformation1(conf, filePath):
        metaConfig = LineConfig(conf['actor.setup'])
        inform1 = []
        print 'loading actor data...'
        with open(filePath) as f:
            informs = f.readlines()
            # ignore the headline
        if metaConfig.contains('-header'):
            informs = informs[1:]
        # order of the columns
        order = metaConfig['-columns'].strip().split()
        if len(order) <= 2:
            print 'The actor file is not in a correct format.'
        for lineNo, line in enumerate(informs):
            items = split(' |,|\t', line.strip())
            if len(order) < 2:
                print 'The actor file is not in a correct format. Error: Line num %d' % lineNo
                exit(-1)
            movieId = items[int(order[0])]
            actorId = items[int(order[1])]
            if len(order) < 3:
                weight = 1
            else:
                weight = float(items[int(order[2])])
            inform1.append([movieId, actorId, weight])
        return inform1

    @staticmethod
    def loadInformation2(conf, filePath):
        metaConfig = LineConfig(conf['dire.setup'])
        inform2 = []
        print 'loading director data...'
        with open(filePath) as f:
            informs = f.readlines()
            # ignore the headline
        if metaConfig.contains('-header'):
            informs = informs[1:]
        # order of the columns
        order = metaConfig['-columns'].strip().split()
        if len(order) <= 2:
            print 'The director file is not in a correct format.'
        for lineNo, line in enumerate(informs):
            items = split(' |,|\t', line.strip())
            if len(order) < 2:
                print 'The actor file is not in a correct format. Error: Line num %d' % lineNo
                exit(-1)
            movieId = items[int(order[0])]
            direId = items[int(order[1])]
            if len(order) < 3:
                weight = 1
            else:
                weight = float(items[int(order[2])])
            inform2.append([movieId, direId, weight])
        return inform2
