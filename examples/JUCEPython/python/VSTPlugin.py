
import gsapi


def test(s):
	return s+"kklolo"


def setup():
    pass

def onNewTime(time):
    pass

def onGenerateNew():
	pattern = gsapi.GSPattern();
	ev = gsapi.GSPatternEvent(0,1,60,100,["lala"]);
	pattern.addEvent(ev)
	transformPattern(pattern)
	return pattern

def transformPattern(patt):
	i = 0;
	
	print len(patt)
	# for e in patt:
	# 	print patt

	patt.events = l
		
	
	return patt

if __name__ =='__main__':
	patt = onGenerateNew();
	
	for i in patt.events:
		print i
		print i.length