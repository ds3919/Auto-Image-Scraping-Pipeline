import pandas as pd
from sys import argv
from PIL import Image
import os
import ast

def cropAndResize(filename, imgPath, outDir, dimensions, xoff, yoff, newFilename):
    
    with Image.open(imgPath) as img:
        dim = min(dimensions)

        img.convert("RGB")

        centerPoint = (dimensions[0]/2+xoff, dimensions[1]/2+yoff)
        halfLen = dim/2
        x1 = centerPoint[0]-halfLen
        y1 = centerPoint[1]-halfLen
        x2 = centerPoint[0]+halfLen
        y2 = centerPoint[1]+halfLen
        img = (img.crop((x1, y1, x2, y2)).resize((targetDim, targetDim)))
        
        outputPath = os.path.join(outDir, newFilename)
        print(outputPath)
        img.save(outputPath)
        return outputPath

def calcOff(dimensions, numSamples):
    diff = abs(dimensions[0]-dimensions[1])
    xoffs = [0]
    yoffs = [0]
    stepSize = diff/numSamples
    halfPoint = int(numSamples/2) + 1
    if min(dimensions) == dimensions[0]:
        for i in range(1, halfPoint):
            xoff = -1*i*stepSize
            xoffs.append(xoff)
            yoffs.append(0)
        for i in range(1, halfPoint):
            xoff = i*stepSize
            xoffs.append(xoff)
            yoffs.append(0)
    else:
        for i in range(1, halfPoint):
            yoff = -1*i*stepSize
            yoffs.append(yoff)
            xoffs.append(0)
        for i in range(1, halfPoint):
            yoff = i*stepSize
            yoffs.append(yoff)
            xoffs.append(0)
    
    return xoffs, yoffs

def process(filename, imgPath, dimensions, numSamples, outDir, category):
    xoffs, yoffs = calcOff(dimensions, numSamples)
    print(f'processing {filename} for offsets:')
    for i in range(0, len(xoffs)):
        print(f'xoff:{xoffs[i]} yoff:{yoffs[i]}')
        
        fileList = filename.split('.')
        newFilename = fileList[0]+'_'+str(i+1)+'.'+fileList[1]

        outPath = cropAndResize(filename, imgPath, outDir, dimensions, xoffs[i], yoffs[i], newFilename)
        outputCsv.append([filename, outPath, category, targetDim])


if len(argv) != 7:
    print("Format arguments as <xlsxPath> <diffRange> <upper/lower> <numCrops> <targetDim> <outputDir>")
else:
    excelPath = argv[1]
    diffRange = argv[2]
    limit = ast.literal_eval(argv[3])
    numCrops = int(argv[4])
    targetDim = int(argv[5])
    outputDir = argv[6]
'''
xlsxPath = path to excel file
diffRange = margin of acceptability for image aspect ratio; input as string; "0.8-1.0"
upper/lower = upper and lower limits for the mutable resolutions; input as tuple; (10000, 20000)
numCrops = number of crops performed per image; proportionate to number of processed images output per inputed image
targetDim = target dimension for post processed square iamges
outputDir = output directory
'''

refFile = pd.read_excel(excelPath, sheet_name="synthImageInfo")
outputCsv = []
for r in refFile.itertuples(index=False):
    if r.diffRange == diffRange and limit[0] <= r.resolution <= limit[1]:
        process(r.filename, r.image_path, (r.width, r.height), numCrops, outputDir, r.category)

outputCsv = pd.DataFrame(outputCsv, columns=["filename", "outputPath", "category", "dimensions"])
outputCsv.to_csv(os.path.join(outputDir, "resizedImages.csv"), index=False)