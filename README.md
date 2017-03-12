gsapi
=====

The GS-API is a Python/C++ library for manipulating musical symbolic data.

###Overview

The GS-API (GiantSteps API) provides Python and C++ classes and an interface 
for dealing with musical data. Its main features are:

* flexible input/output from/to JSON/MIDI
* Rhythm generation, both agnostic and based on styles.
* Style and music-theoretical based harmony progression generation.
* More to come.


###Installing the library
Installing the latests stable release can be done via pip:
```
pip install gsapi
```

**Python**

The python modules reside in the **gsapi** subfolder:

* Build and install:
```
cd gsapi
python setup.py build
python setup.py install
```

###Basic Use Examples

The following lines will create a *Pattern* p with two events: one event tagged as "Kick" starting at time 0, with a duration of 1, a Midi Note Number 64 and a Midi 
velocity of 127; and a second event tagged "Snare" starting at time 1, with a duration of 3, Midi Note Number 62 and Midi velocity of 51.

```python
from gsapi import *
p = gspattern.Pattern()
p.addEvent(gspattern.Event(startTime=0, duration=1, pitch=64, velocity=127, tag="Kick")
p.addEvent(gspattern.Event(1, 3, 62, 51, "Snare"))
```

Now, let us get all files in a specified folder:
```python
from gsapi import *
# we select a folder containing midi files:
dataset = gsdataset.Dataset(midiFolder="your/folder",midiGlob="*.mid", midiMap=gsdefs.generalMidiMap)
allPatternsSliced = []


# And we split all files into Patterns of 16 beat each:
for midiPattern in dataset.patterns:
	for sliced in midiPattern.splitInEqualLengthPatterns(16):
		allPatternsSliced+=[sliced]

print(allPatternsSliced)
```

We can use gsapi to characterise a pattern with any given descriptor.
Continuing the previous example, we could estimate the rhythmic density of the
 patterns:

```python
from gsapi import *
density = descriptors.Density()

for pattern in dataset.patterns:
	kickPattern = pattern.getPatternWithTags(tagToLookFor="kick")
	densityOfKick = density.getDescriptorForPattern(kickPattern)
```

More advanced usages create transition probabilities from corpora of music in 
order to generate music in that style: 

```python
from gsapi import *
markovchain = styles.MarkovStyle(order=3, numSteps=32, loopDuration=16)
MarkovStyle.generateStyle(allPatternsSliced)
newPattern = MarkovStyle.generatePattern()
```

### API Philosophies

**JSON and MIDI**

We encourage the use of JSON to be able to work with consistent and reusable 
datasets, as midi files tend to have different MIDI mappings, structures, or 
even suspicious file format implementations.
Thus we provide a flexible MIDI i/o module *gsio* for tagging events with 
respect to their pitch, channel and trackName.
Note to tag mapping is reppresented by dictionaries where keys represent tags
 and values are rules that such tags have to validate.
* Rules are either lists or single *condition* that are OR'ed.
* Each condition is either a tuple with expected pitch number and channel, 
or an integer representing the expected pitch value.

The following snippet will return a list of *Patterns* with events tagged as 
'Kick' if Midi pitch is 30 in any channel; 'Snare' if Midi pitch is 32 and 
channel is 4; and 'ClosedHihat' if MIDI pitch is 33 on whatever channel or MIDI
pitch is 45 on any channel.


```python
from gsapi import *
midiGlobPath = '/path/to/midi/*.mid'
NoteToTagsMap = {"Kick":30, 
                 "Snare":(32,4),
                 "ClosedHihat":[(33,'*'),45]}

listOfGSPatterns = gsio.fromMidiCollection(midiGlobPath, NoteToTagsMap)
```

### Obtaining Help
All submodules within the GS-API provide help by typing help(moduleName)

```python
help(gspattern.Pattern)
help(gsdataset.Dataset)
```

In the *examples* folder you can find more detailed documentation, turorials 
and integration examples.
