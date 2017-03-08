#import os
#import sys

import gsapi

# Choose folder to crawl
midiFolder = "../corpora/drums"

# Generate a Dataset with all the midi files in midiFolder
# All events will have tags corresponding to generalMIDI mapping (see definitions.generalMidiMap)

dataset = gsapi.gspattern.Dataset(midiFolder=midiFolder,
                            midiGlob="*.mid",
                            midiMap=gsapi.gsdefs.generalMidiMap,
                            checkForOverlapped=True)

# gspattern.Dataset is nothing integration than a class containing a list of datasets.
# Lets say we want to retrieve every 16 beat long slice from this dataset

allPatternsSliced = []
sizeOfSlice = 16
for midiPattern in dataset.patterns:
    for sliced in midiPattern.splitInEqualLengthPatterns(4):
        allPatternsSliced += [sliced]

print(allPatternsSliced)


markovStyle = gsapi.styles.MarkovStyle(order=3, numSteps=32, loopDuration=sizeOfSlice)
markovStyle.generateStyle(allPatternsSliced)
newPattern = markovStyle.generatePattern()

allTags = allPatternsSliced[0].getAllTags()
tagToSearch = allTags[0]

densityDescriptor = descriptors.Density()

for p in allPatternsSliced:
    p = p.getPatternWithTags(tags="kick")
    densityDescriptor.getDescriptorForPattern(p)


#exit()

#for p in self.dataset.patterns:
#    allTags = p.getAllTags()
#    density = descriptor.getDescriptorForPattern(p)