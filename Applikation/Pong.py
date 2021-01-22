import numpy as np
import cv2
import rtmidi
import mido

#MIDI-Port
midiOutput = mido.open_output("LoopBe Internal MIDI 1")

#cap = cv2.VideoCapture("PongV3.mp4")
cap = cv2.VideoCapture(0)

ret, frame = cap.read()
frameCount = 0
height, width = frame.shape[:2]
halfwidth = (int)(width/2)

# halbe Schlägergröße
racketX = 15
racketY = 100

# Ballinitialisierung
ballSpeedX = 10
ballSpeedY = 0
ballSize = 10

# Ballposition
ballPosX = (int)(width/2)
ballPosY = (int)(height/2)
ballPosX_LastFrame = 0
ballPosY_LastFrame = 0

# Schwerpunkt linke Hand
leftHandX = width-10-racketY
leftHandY = (int)(height/2)
leftHandX_LastFrame = 0
leftHandY_LastFrame = 0

# Schwerpunkt rechte Hand
rightHandX = 10+racketY
rightHandY = (int)(height/2)
rightHandX_LastFrame = 0
rightHandY_LastFrame = 0

gameIsActiv = False
rightHitBall = False
leftHitBall = False
leftHandDetected = False
rightHandDetected = False
ballCrossedMid = False
gameOver = False

# Opacity of the winnig message
winOpactiy = 0

# Text variable of "no racket visible" message
handText = 0

# Values for each Container (audio configuration takes place at effects.js)
gainNum = 1.0
panNum = 0.0
distNum = 10
threshNum = -20

# These strings prevent multiple additions/subtractions for one moment
ballMidPos = ""

# Draw Containers
font = cv2.FONT_ITALIC
fontScale = 0.6
fontColor = (0,0,0)
thickness = 2
winText = ''
winColor = (255,0,0)
winScale = 0.6

def sendMIDIMessage(val1, val2):
	midiOutput.send(mido.Message('control_change', control=val1, value=val2))

def gameEnd(string):
	global winText, winOpactiy, ballSpeedX, ballSpeedY, gameOver
	
	if (string == 'lGain'):
		winText = 'Right Player has won with reaching the minimum Gain'
	elif (string == 'lPan'):
		winText = 'Right Player has won with reaching the minimum Panning'
	elif (string == 'lDist'):
		winText = 'Right Player has won with reaching the minimum Distortion'
	elif (string == 'lThresh'):
		winText = 'Right Player has won with reaching the minimum Threshold'
	elif (string == 'rGain'):
		winText = 'Left Player has won with reaching the maximum Gain'
	elif (string == 'rPan'):
		winText = 'Left Player has won with reaching the maximum Panning'
	elif(string == 'rDist'):
		winText = 'Left Player has won with reaching the maximum Distortion'
	elif(string == 'rThresh'):
		winText = 'Left Player has won with reaching the maximum Threshold'
	sendMIDIMessage(4, 4)
	winOpactiy = 1
	ballSpeedX = 0
	ballSpeedY = 0
	gameOver = True

while cap.isOpened():

	ret, frame = cap.read()
	img = frame
	frameCount +=1

	img = cv2.resize(img, (960, 720))
	blk = np.zeros(img.shape, np.uint8)

	height, width = img.shape[:2]
	halfwidth = (int) (width/2)

	# convert image to grayscale image
	gray_image = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

	b,g,r = cv2.split(img)

	r_mask = cv2.inRange(r, 0, 10)
	g_mask = cv2.inRange(g, 0, 25)
	b_mask = cv2.inRange(b, 0, 25)

	mask = r_mask * g_mask * g_mask
	
	# Filter
	mask = cv2.medianBlur(mask, 5)
	kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (15, 15))
	mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

	# convert the grayscale image to binary image
	ret, thresh = cv2.threshold(mask, 235, 255, cv2.THRESH_BINARY_INV)
	invert = cv2.bitwise_not(thresh)

	# Split into left and right half
	leftSide = invert.copy()
	rightSide = invert.copy()
	leftSide[0:height, 0:halfwidth] = (0)
	rightSide[0:height, halfwidth:width] = (0)

	# Find contours:
	contoursLeft, hierarchyLeft = cv2.findContours(leftSide, cv2.CHAIN_APPROX_SIMPLE, cv2.CHAIN_APPROX_SIMPLE)
	contoursRight, hierarchyRight = cv2.findContours(rightSide, cv2.CHAIN_APPROX_SIMPLE, cv2.CHAIN_APPROX_SIMPLE)

	# Draw contours:   
	cv2.drawContours(img, contoursLeft, 0, (0, 255, 0), 2)
	cv2.drawContours(img, contoursRight, 0, (0, 255, 0), 2)


	# Calculate Heavypoint Left
	if(len(contoursLeft) > 0):
		# calculate moments of binary image
		MLeft = cv2.moments(contoursLeft[0])

		# calculate x,y coordinate of center
		if MLeft["m00"] > 2000:
			leftHandX = int(MLeft["m10"] / MLeft["m00"])
			leftHandY = int(MLeft["m01"] / MLeft["m00"])
			leftHandDetected = True
			# draw point in center
			cv2.circle(img, (leftHandX, leftHandY), 3, (255, 255, 255), -1)
		else:
			leftHandDetected = False
		

	# Calculate Heavypoint Right
	if(len(contoursRight) > 0):
		# calculate moments of binary image
		MRight = cv2.moments(contoursRight[0])

		# calculate x,y coordinate of center
		if MRight["m00"] > 2000:
			rightHandX = int(MRight["m10"] / MRight["m00"])
			rightHandY = int(MRight["m01"] / MRight["m00"])
			rightHandDetected = True
			# draw point in center
			cv2.circle(img, (rightHandX, rightHandY), 3, (255, 255, 255), -1)
		else:
			rightHandDetected = False

	
	################
	##### PONG #####
	################

	# Start Game if left and right hand are detected
	if leftHandDetected and rightHandDetected and not gameOver:
		gameIsActiv = True
		sendMIDIMessage(4, 1)
		handText = ""
	
	# Stop Game if just one hand is detected
	if (not leftHandDetected or not rightHandDetected) and not(not leftHandDetected and not rightHandDetected):
		gameIsActiv = False
		sendMIDIMessage(4, 2)
		handText = "A racket is not visible"

	# Reset Game if no hand is detected
	if not leftHandDetected and not rightHandDetected:
		ballPosX = (int)(width/2)
		ballPosY = (int)(height/2)
		leftHandX = width-10-racketY
		leftHandY = (int)(height/2)
		rightHandX = 10+racketY
		rightHandY = (int)(height/2)
		ballSpeedY = 0
		ballSpeedX = 10
		gainNum = 1.0
		panNum = 0.0
		distNum = 10
		threshNum = -20
		winText = ''
		winOpactiy = 0
		sendMIDIMessage(4, 4)
		handText = ""
		gameIsActiv = False
		gameOver = False

	# Start Game
	if gameIsActiv:
		ballPosX += ballSpeedX
		ballPosY += ballSpeedY

		# Y-Speed verringert sich
		if ballSpeedY > 0:
			# alle 10 Frames ballSpeedY-=1
			if frameCount > 5:
				frameCount = 0
				ballSpeedY -= 1

		# Wenn Ball linken Schläger berührt
		if (abs(ballPosX-leftHandX) < (racketX+ballSize) and (ballPosY) < (leftHandY+racketY) and (ballPosY) > (leftHandY-racketY) and
				not(abs(ballPosX_LastFrame-leftHandX_LastFrame) < (racketX+ballSize)) and not leftHitBall):
			ballSpeedX *= -1
			ballSpeedY += (leftHandY - leftHandY_LastFrame)
			ballCrossedMid = False
			rightHitBall = False
			leftHitBall = True

		# Wenn Ball rechten Schläger berührt
		if (abs(rightHandX-ballPosX) < (racketX+ballSize) and (ballPosY) < (rightHandY+racketY) and (ballPosY) > (rightHandY-racketY) and
				not(abs(rightHandX_LastFrame-ballPosX_LastFrame) < (racketX+ballSize))  and not rightHitBall):
			ballSpeedX *= -1
			ballSpeedY += (rightHandY - rightHandY_LastFrame)
			ballCrossedMid = False
			rightHitBall = True
			leftHitBall = False


		# Wenn Ball Rand berührt
		# rechts
		if (ballPosX > width-(ballSpeedX+1)):
			if ballSpeedX > 0:
				ballSpeedX *= -1
				ballCrossedMid = False
				leftHitBall = False
		# links
		if (ballPosX < 0+(ballSpeedX+1)):
			if ballSpeedX < 0:
				ballSpeedX *= -1
				ballCrossedMid = False
				rightHitBall = False
		# oben
		if (ballPosY > height-(ballSpeedY+1)):
			if ballSpeedY > 0:
				ballSpeedY *= -1
		# unten
		if (ballPosY < 0+(ballSpeedY+1)):
			if ballSpeedY < 0:
				ballSpeedY *= -1

	# Get Position from last Frame
	ballPosX_LastFrame = ballPosX
	ballPosY_LastFrame = ballPosY
	leftHandX_LastFrame = leftHandX
	rightHandX_LastFrame = rightHandX
	leftHandY_LastFrame = leftHandY
	rightHandY_LastFrame = rightHandY


	####################
	##### JS STUFF #####
	####################

	containerLeftX = (int) (width/2 - 50)
	containerRightX = (int) (width/2 + 50)
	

	# Requirements for changing the sound values + sending them to JS
	if (ballPosX >= containerLeftX and ballPosX <= containerRightX and not ballCrossedMid):
		ballCrossedMid = True

		if (leftHitBall):
			if (ballPosY <= (height*(1/4))):
				ballMidPos = "LeftGain"
				gainNum = round(gainNum-0.1, 1)
				sendMIDIMessage(5, 1)
				if (gainNum  < 0.09):
					gameEnd('lGain')
			if (ballPosY > (height*(1/4)) and ballPosY <= (height*(2/4))):
				ballMidPos = "LeftPan"
				panNum = round(panNum-0.1, 1)
				sendMIDIMessage(5, 3)
				if (panNum  < -0.91):
					gameEnd('lPan')
			if (ballPosY > (height*(2/4)) and ballPosY <= (height*(3/4))):
				ballMidPos = "LeftDist"
				distNum -= 1
				sendMIDIMessage(5, 5)
				if (distNum  < 0.9):
					gameEnd('lDist')
			if (ballPosY > (height*(3/4))):
				ballMidPos = "LeftThresh"
				threshNum -= 2
				sendMIDIMessage(5, 7)
				if (threshNum  < -39):
					gameEnd('lThresh')

		if (rightHitBall):
			if (ballPosY <= (height*(1/4))):
				ballMidPos = "RightGain"
				gainNum = round(gainNum+0.1, 1)
				sendMIDIMessage(5, 2)
				if (gainNum  > 1.91):
					gameEnd('rGain')
			if (ballPosY > (height*(1/4)) and ballPosY <= (height*(2/4))):
				ballMidPos = "RightPan"
				panNum = round(panNum+0.1, 1)
				sendMIDIMessage(5, 4)
				if (panNum  > 0.91):
					gameEnd('rPan')
			if (ballPosY > (height*(2/4)) and ballPosY <= (height*(3/4))):
				ballMidPos = "RightDist"
				distNum += 1
				sendMIDIMessage(5, 6)
				if (distNum  > 19.1):
					gameEnd("rDist")
			if (ballPosY > (height*(3/4))):
				ballMidPos = "RightThresh"
				threshNum += 2
				sendMIDIMessage(5, 8)
				if (threshNum  > -1):
					gameEnd("rThresh")
	elif ((ballPosX >= containerRightX and ballPosX <= containerRightX+12) or (ballPosX <= containerLeftX and ballPosX >= containerLeftX-12)):
		sendMIDIMessage(4, 3)

	################
	##### Draw #####
	################

	# Gain Container
	cv2.rectangle(img, (containerLeftX,0), (containerRightX,(int)(height*(1/4))), (121,159,247), -1)
	cv2.putText(img, 'Gain', (458,85), font, fontScale, fontColor, thickness)
	cv2.putText(img, '+      -', (437,170), font, fontScale, fontColor, thickness)
	cv2.putText(img, str(gainNum) + ' dB', (448,105), font, fontScale, fontColor, thickness)

	# Panning Container
	cv2.rectangle(img, (containerLeftX,181), (containerRightX,(int)(height*(2/4))), (105,111,91), -1)
	cv2.putText(img, 'Panning', (442,265), font, fontScale, fontColor, thickness)
	cv2.putText(img, '+      -', (437,350), font, fontScale, fontColor, thickness)
	cv2.putText(img, str(panNum) + ' LR', (448,285), font, fontScale, fontColor, thickness)
	
	# Distortion Container
	cv2.rectangle(img, (containerLeftX,361), (containerRightX,(int)(height*(3/4))), (152,123,118), -1)
	cv2.putText(img, 'Distortion', (436,445), font, fontScale, fontColor, thickness)
	cv2.putText(img, '+      -', (437,530), font, fontScale, fontColor, thickness)
	cv2.putText(img, str(distNum), (467,465), font, fontScale, fontColor, thickness)
	
	# Threshold Container
	cv2.rectangle(img, (containerLeftX,541), (containerRightX,height), (149,174,214), -1)
	cv2.putText(img, 'Threshold', (435,625), font, fontScale, fontColor, thickness)
	cv2.putText(img, '+      -', (437,710), font, fontScale, fontColor, thickness)
	cv2.putText(img, str(threshNum) + ' dB', (442,645), font, fontScale, fontColor, thickness)

	# Draw Ball
	img = cv2.circle(img, (ballPosX, ballPosY), ballSize, (0,255,255), -1)
	
	# Draw left Hand
	img = cv2.rectangle(img, (leftHandX-racketX, leftHandY-racketY), (leftHandX+racketX, leftHandY+racketY), (255,0,0), 3)

	# Draw right Hand
	img = cv2.rectangle(img, (rightHandX-racketX, rightHandY-racketY), (rightHandX+racketX, rightHandY+racketY), (0,0,255), 3)

	# Draw text at the end of the game
	cv2.rectangle(blk, (0,340), (width,370), (255,255,255), cv2.FILLED)
	img = cv2.addWeighted(img, 1, blk, winOpactiy, 1.0)
	cv2.putText(img, winText , (200,360), font, winScale, winColor, thickness)

	# Draw text if racket is not visible while game is active
	cv2.putText(img, handText, (300,360), font, 1, (0,191,255), thickness)

	cv2.imshow('AV-Pong', img)

	# Beenden bei Tastendruck
	if cv2.waitKey(25) != -1:
		sendMIDIMessage(4, 4)
		break

cap.release()
cv2.destroyAllWindows()