import random, datetime, config
from utils import baseNarratives, transitions, log5, weightedChoice
from league import leagueMeans

class Matchup(object):

	def __init__(self, batting, pitching):
		
		lgAvg = leagueMeans()
		
		for key in config.RESULT_TYPES:
		
			resultProb = log5(pitching[key], batting[key], lgAvg[key])
			
			setattr(self, key, resultProb)
			
	def genResult(self):
	
		return weightedChoice(self.__dict__)
		

class Event(object):

	def __init__(self, type):
	
		self.type = type
		
		if type in ['strikeout', 'inPlayOut', 'sacrifice', 'GDP']:
			self.batterOut = True
			
		else:
			self.batterOut = False
			
		if type in ['single', 'double', 'triple', 'HR']:
			self.isHit = True
			
		else:
			self.isHit = False
			
		if type in ['BB', 'HBP', 'sacrifice']:
			self.isAB = False
			
		else:
			self.isAB = True

class BaseOutState(object):

	def __init__(self, first=None, second=None, third=None, outs=0):
	
		self.first = first
		self.second = second
		self.third = third
		self.outs = outs
		
	def getState(self):
		
		firstBase, secondBase, thirdBase = '', '', ''
		
		if self.first:
			firstBase = '1'
			
		if self.second:
			secondBase = '2'
			
		if self.third:
			thirdBase = '3'
			
		state = '{0}{1}{2}'.format(firstBase, secondBase, thirdBase)
		
		if state == '':
			state = '0'
		
		return (int(state), self.outs)
			
	def __str__(self):
		
		narr = baseNarratives[self.getState()[0]]
		
		return "{0} and {1} outs".format(narr, self.outs)
	
	def queue(self):
	
		runners = []
		
		for runner in [self.first, self.second, self.third]:
		
			if runner:
			
				runners.append(runner)
				
		return runners
		
class PlateAppearance(object):
	
	def __init__(self, top, inning, baseState, batter, pitcher):
		
		self.top = top
		self.inning = inning
		self.baseState = baseState
		self.batter = batter
		self.pitcher = pitcher
		
		if baseState.outs == 3:
			self.transitions = [None,]
		
		else:
			self.transitions = transitions[baseState.getState()]
			
		self.matchup = Matchup(batter.ratings.batting, pitcher.ratings.pitching)
		self.event = Event(self.matchup.genResult())
	
	def advanceRunners(self, newBases, runs):
		
		oldState = self.baseState
		newState = BaseOutState()
		runners = oldState.queue()
		
		if self.event.type == 'HR':
			runners += [self.batter]
		
		for i in range(0, runs):
			
			runners.pop()
		
		if len(runners) > 0:
		
			if '3' in str(newBases):
			
				newState.third = runners.pop()
				
		if len(runners) > 0:
		
			if '2' in str(newBases):
			
				newState.second = runners.pop()
				
		if len(runners) > 0:
		
			if '1' in str(newBases):
			
				newState.first = runners.pop()	
				
		if not self.event.batterOut:
		
			newState.first = self.batter
			
		return newState
	
	def endState(self):
	
		states = random.sample(self.transitions, len(self.transitions))
		
		for i in states:
		
			if self.event.type in i[1]:
			
				choice = i
				break
				
		runs = choice[2]
		newBases = self.advanceRunners(choice[0][0], runs)
		newBases.outs = choice[0][1]
		
		return (runs, newBases)
	
class Game(object):

	def __init__(self, homeTeam, awayTeam):
	
		self.homeTeam = homeTeam
		self.awayTeam = awayTeam
		self.homeScore = 0
		self.awayScore = 0
		self.PAs = []
		self.inning = 1
		self.top = True
		self.startTime = datetime.datetime.now()
		self.complete = False
		
	def iterate(self, currentPA):
	
		self.PAs.append(currentPA)
		
		if self.top:
		
			self.awayScore += currentPA.endState()[0]
			batter = self.awayTeam.lineup.newBatter()
			pitcher = self.homeTeam.lineup.currentPitcher
			
			return PlateAppearance(self.inning, self.top, currentPA.endState()[1], batter, pitcher)
			
		elif not self.top:
		
			self.homeScore += currentPA.endState()[0]
			batter = self.homeTeam.lineup.newBatter()
			pitcher = self.awayTeam.lineup.currentPitcher
			
			return PlateAppearance(self.inning, self.top, currentPA.endState()[1], batter, pitcher)
			
	def playInning(self):
		
		if self.inning >= 10 and self.top:
		
			if self.awayScore > self.homeScore:
			
				self.complete = True
				return True
		
		if self.top:

			batter = self.awayTeam.lineup.newBatter()
			pitcher = self.homeTeam.lineup.currentPitcher
		
		elif not self.top:
		
			batter = self.homeTeam.lineup.newBatter()
			pitcher = self.awayTeam.lineup.currentPitcher
		
		currentPA = PlateAppearance(self.inning, self.top, BaseOutState(), batter, pitcher)
		
		while True:
		
			currentPA = self.iterate(currentPA)
			
			if self.inning >=9 and not self.top:
				
				if self.homeScore > self.awayScore:
				
					self.complete = True
					return True
			
			if currentPA.baseState.outs == 3:
			
				if not self.top:
					self.inning += 1
					self.top = not self.top
					
				elif self.top:
					self.top = not self.top
					
				return True
				
	def play(self):
		pass