import pygame
import random
import JumpKingMapMaker as mapMaker
import math
from os.path import exists
import json

from JumpKingMapMaker import SURF_WIDTH, SURF_HEIGHT

pygame.init()
clock = pygame.time.Clock()

GRAVITY = 300
TERMINAL_VELOCITY = 800
AI_BUCKET = 10
AI_COUNT = 50


class Player:
    def __init__(self, x, y, width, height, color, s):
        self.holdingLeft = False
        self.holdingRight = False
        self.isGrounded = False
        self.displayRect = pygame.Rect(0, 0, 0, 0)
        self.yGauge = pygame.Rect(0, 0, 0, 0)  # Just use random values based on the character
        self.xGauge = pygame.Rect(0, 0, 0, 0)
        self.playerColor = (0, 0, 0)
        self.xInput = 0
        self.jumpForce = 0
        self.jumpChargeTime = 500
        self.maxJumpForce = 370
        self.chargeIncrement = 1
        self.playerVelocity = (0, 0)
        self.displayRect.size = (width, height)
        self.displayRect.center = (x, y)
        self.playerPos = (x, y)
        self.playerColor = color
        self.speed = s
        self.hasYVelocity = False
        self.hasXVelocity = False
        self.wallCollision = (False, 0, 0)

    def MoveX(self):
        xPos, yPos = self.playerPos
        self.playerPos = (xPos + self.xInput * self.speed * min(16.7, clock.get_time()) / 1000, yPos)
        xPos, yPos = self.playerPos
        self.displayRect.center = (xPos, yPos)
        self.xInput = 0

    def ChargeJump(self):
        xVelocity, yVelocity = self.playerVelocity
        if self.isGrounded and xVelocity == 0 and yVelocity == 0:
            if not self.hasYVelocity:
                self.jumpForce = 0 if self.jumpForce + self.chargeIncrement * min(16.7,
                                                                                  clock.get_time()) / self.jumpChargeTime < 0 else 1 if self.jumpForce + self.chargeIncrement * min(
                    16.7, clock.get_time()) / self.jumpChargeTime > 1 else self.jumpForce + self.chargeIncrement * min(
                    16.7, clock.get_time()) / self.jumpChargeTime
                self.chargeIncrement = self.chargeIncrement * -1 if self.jumpForce == 0 or self.jumpForce == 1 else self.chargeIncrement
            elif not self.hasXVelocity:
                self.xInput = -1 if self.xInput + self.chargeIncrement * min(16.7,
                                                                             clock.get_time()) / self.jumpChargeTime < -1 else 1 if self.xInput + self.chargeIncrement * min(
                    16.7, clock.get_time()) / self.jumpChargeTime > 1 else self.xInput + self.chargeIncrement * min(
                    16.7, clock.get_time()) / self.jumpChargeTime
                self.chargeIncrement = self.chargeIncrement * -1 if self.xInput == -1 or self.xInput == 1 else self.chargeIncrement

    def SetGauge(self):
        if self.isGrounded:
            if not self.hasYVelocity:
                self.hasYVelocity = True
                self.chargeIncrement = 1
            elif not self.hasXVelocity:
                self.hasXVelocity = True
                self.Jump()

    def Jump(self):
        xVelocity, yVelocity = self.playerVelocity
        xVelocity += self.xInput * self.maxJumpForce
        yVelocity -= self.jumpForce * self.maxJumpForce
        self.jumpForce = 0
        self.xInput = 0
        self.hasXVelocity = False
        self.hasYVelocity = False
        self.playerVelocity = (xVelocity, yVelocity)

    def Gravity(
            self):  # add a safety precaution, so you don't phase through the floor when you drag the window (the game will pause when you do that)
        xVelocity, yVelocity = self.playerVelocity
        yVelocity = TERMINAL_VELOCITY if yVelocity + GRAVITY * min(16.7,
                                                                   clock.get_time()) / 1000 > TERMINAL_VELOCITY else yVelocity + GRAVITY * min(
            16.7, clock.get_time()) / 1000
        yVelocity = 0 if self.isGrounded and yVelocity > 0 else yVelocity
        self.playerVelocity = (xVelocity, yVelocity)

    # make it so that the x can only be inverted when the player stops colliding with the platform you are currently colliding with
    def CheckCollision(self, platforms):
        rects = [p.displayRect for p in platforms]
        indices = self.displayRect.collidelistall(rects)
        currentRect = self.displayRect
        self.isGrounded = False
        xPos, yPos = self.playerPos
        xVelocity, yVelocity = self.playerVelocity
        isCollidingWall, requiredX, direct = self.wallCollision
        if isCollidingWall and direct * requiredX <= direct * xPos:
            isCollidingWall = False
            requiredX = 0
            direct = 0
        for i in indices:
            if platforms[i].endGoal:
                print("You win!")
            else:
                if (currentRect.top - rects[i].top) * (currentRect.bottom - rects[i].top) <= 0 and currentRect.bottom - \
                        rects[i].top <= currentRect.height * 0.15:
                    currentRect.bottom = rects[i].top + 1
                    self.isGrounded = True
                    yPos = currentRect.bottom - currentRect.height / 2
                    if yVelocity >= 0:
                        xVelocity = 0 if abs(xVelocity) - abs(xVelocity * xVelocity / 25 * min(16.7,
                                                                                               clock.get_time()) / 1000) <= 25 else xVelocity - xVelocity * abs(
                            xVelocity) / 25 * min(16.7, clock.get_time()) / 1000
                        yVelocity = 0 if yVelocity * -0.3 > -10 else yVelocity * -0.3
                elif (currentRect.top - rects[i].bottom) * (currentRect.bottom - rects[i].bottom) <= 0 and rects[
                    i].bottom - currentRect.top <= currentRect.height * 0.1:
                    currentRect.top = rects[i].bottom
                    yVelocity = 0
                    yPos = currentRect.top + currentRect.height / 2
                elif (currentRect.left - rects[i].left) * (
                        currentRect.right - rects[i].left) <= 0 and not isCollidingWall:
                    currentRect.right = rects[i].left
                    xPos = currentRect.right - currentRect.width / 2
                    xVelocity *= -0.5
                    isCollidingWall = True
                    requiredX = rects[i].left - currentRect.width / 2
                    direct = - 1
                elif (currentRect.left - rects[i].right) * (
                        currentRect.right - rects[i].right) <= 0 and not isCollidingWall:
                    currentRect.left = rects[i].right
                    xPos = currentRect.left + currentRect.width / 2
                    xVelocity *= -0.5
                    isCollidingWall = True
                    requiredX = rects[i].right + currentRect.width / 2
                    direct = 1
        self.playerPos = (xPos, yPos)
        self.playerVelocity = (xVelocity, yVelocity)
        self.wallCollision = (isCollidingWall, requiredX, direct)

    def Display(self, surface):
        xPos, yPos = self.playerPos
        xVelocity, yVelocity = self.playerVelocity
        self.playerPos = (xPos + xVelocity * min(16.7, clock.get_time()) /
                          1000, yPos + yVelocity * min(16.7, clock.get_time()) / 1000)
        xPos, yPos = self.playerPos
        self.displayRect.center = (xPos, yPos)
        pygame.draw.rect(surface, self.playerColor, self.displayRect)

    def DisplayGauges(self, surface):
        xVelocity, yVelocity = self.playerVelocity
        if self.isGrounded and xVelocity == 0 and yVelocity == 0:
            w, h = surface.get_size()
            x, y = self.playerPos
            if not self.hasYVelocity:
                midX = w / 2
                m = -1 if x - midX == 0 else (x - midX) / abs(x - midX)
                self.yGauge.size = (self.displayRect.width / 5, self.displayRect.height)
                self.yGauge.center = (
                self.displayRect.centerx - m * (self.displayRect.width / 2) * 1.4, self.displayRect.centery)
                pygame.draw.rect(surface, self.playerColor, self.yGauge, 2)
                self.yGauge.size = (self.yGauge.width * 1.5, self.yGauge.height / 10)
                self.yGauge.center = (self.displayRect.centerx - m * (self.displayRect.width / 2) * 1.4,
                                      self.displayRect.bottom - self.jumpForce * self.displayRect.height)
                pygame.draw.rect(surface, self.playerColor, self.yGauge)
            elif not self.hasXVelocity:
                yThresh = h - self.displayRect.height
                m = -1 if y - yThresh == 0 else (y - yThresh) / abs(y - yThresh)
                self.xGauge.size = (self.displayRect.width / 20, self.displayRect.height / 2.5)
                self.xGauge.center = (
                self.displayRect.centerx, self.displayRect.centery - m * self.displayRect.height / 2 * 1.4)
                pygame.draw.rect(surface, self.playerColor, self.xGauge)
                self.xGauge.size = (self.displayRect.width, self.displayRect.height / 5)
                self.xGauge.center = (
                self.displayRect.centerx, self.displayRect.centery - m * self.displayRect.height / 2 * 1.4)
                pygame.draw.rect(surface, self.playerColor, self.xGauge, 2)
                self.xGauge.size = (self.xGauge.width / 10, self.xGauge.height * 1.5)
                self.xGauge.center = (self.displayRect.left + (self.xInput + 1) / 2 * self.displayRect.width,
                                      self.displayRect.centery - m * self.displayRect.height / 2 * 1.4)
                pygame.draw.rect(surface, self.playerColor, self.xGauge)
                self.xGauge


class AI(Player):
    jumpDB = {}

    def InitJumpRecords(self):
        self.jumpRecord = {}
        self.LoadJumpDB("AI_Brain.txt")

    def SaveJumpDB(self, fileName):
        with open(fileName, 'w') as f:
            f.write(json.dumps(AI.jumpDB, indent=4))

    def LoadJumpDB(self, fileName):
        if exists(fileName):
            f = open(fileName, 'r')
            obj = json.loads(f.read())
            if (obj):
                AI.jumpDB = obj

    def SaveJumpRecord(self):
        if "goalPlat" in self.jumpRecord:
            xPos, yPos = self.displayRect.midbottom
            goalX, goalY = self.jumpRecord["goalPlat"]
            endDeltaVec = pygame.math.Vector2(abs(xPos - goalX), yPos - goalY)
            startDeltaVec = pygame.math.Vector2(self.jumpRecord["startDelta"][0], self.jumpRecord["startDelta"][1])
            roundX = math.floor(startDeltaVec.x / AI_BUCKET)
            roundY = math.floor(startDeltaVec.y / AI_BUCKET)

            self.jumpRecord["endDelta"] = [endDeltaVec.x, endDeltaVec.y]
            if startDeltaVec.x != 0:
                self.jumpRecord["xScore"] = min(1, max(-1, 1.0 - abs(endDeltaVec.x / startDeltaVec.x)))
            else:
                self.jumpRecord["xScore"] = 0
            if startDeltaVec.y != 0:
                self.jumpRecord["yScore"] = min(1, max(-1, 1.0 - abs(endDeltaVec.y / startDeltaVec.y)))
            else:
                self.jumpRecord["yScore"] = 0

            self.jumpRecord["avgScore"] = (self.jumpRecord["xScore"] + self.jumpRecord["yScore"]) / 2.0
            print(self.jumpRecord["xScore"])
            print(self.jumpRecord["yScore"])

            if self.jumpRecord["avgScore"] > 0:
                if str((roundX, roundY)) in AI.jumpDB:
                    AI.jumpDB[str((roundX, roundY))].append(self.jumpRecord)
                else:
                    AI.jumpDB[str((roundX, roundY))] = [(self.jumpRecord)]

            self.SaveJumpDB("AI_Brain.txt")
            self.jumpRecord = {}

    def isSettled(self):
        xVelocity, yVelocity = self.playerVelocity
        return self.isGrounded and xVelocity == 0 and yVelocity == 0

    def ChargeJump(self, goalPlat):

        if self.isSettled():  # Settled
            if "goalPlat" in self.jumpRecord:
                self.SaveJumpRecord()
            xPos, yPos = self.displayRect.midbottom
            goalX, goalY = goalPlat.displayRect.midtop if goalPlat else (0, 0)
            xMod = 1 if goalX > xPos else -1
            minX, maxX = (0, 1)
            minY, maxY = (0, 1)

            # Load
            deltaVec = pygame.math.Vector2(abs(xPos - goalX), yPos - goalY)
            roundX = math.floor(deltaVec.x / AI_BUCKET)
            roundY = math.floor(deltaVec.y / AI_BUCKET)
            recList = []
            if str((roundX, roundY)) in AI.jumpDB:
                recList = AI.jumpDB[str((roundX, roundY))].copy()
            else:
                for i in range(1, 3):
                    tempList = []
                    if str((roundX + i, roundY)) in AI.jumpDB:
                        tempList.extend(AI.jumpDB[str((roundX + i, roundY))].copy())
                    if str((roundX - i, roundY)) in AI.jumpDB:
                        tempList.extend(AI.jumpDB[str((roundX - i, roundY))].copy())
                    # for t in tempList:
                    #    t["xScore"] *= pow(0.8, i)
                    #    t["yScore"] *= pow(0.95, i)
                    recList.extend(tempList)
            print("Loading " + str(len(recList)) + " jump records...")

            rLen = len(recList)
            if (rLen > 0):
                bestJumpX = max(recList, key=lambda r: r["avgScore"])
                bestJumpY = max(recList, key=lambda r: r["avgScore"])
                xPerc, yPerc = (1 - bestJumpX["xScore"], 1 - bestJumpY["yScore"])
                minX = max(0, bestJumpX["xInput"] - (0.5 * xPerc))
                maxX = min(1, bestJumpX["xInput"] + (0.5 * xPerc))
                minY = max(0, bestJumpY["yInput"] - (0.5 * yPerc))
                maxY = min(1, bestJumpY["yInput"] + (0.5 * yPerc))

                for r in recList:
                    xEffect, yEffect = (0, 0)
                    if r["xScore"] > 0:
                        xEffect = r["xInput"]
                    else:
                        xEffect = r["xInput"] / (2 - r["xScore"])
                    if r["yScore"] > 0.1:
                        yEffect = r["yInput"]
                    elif r["yScore"] >= 0:
                        yEffect = 1 - r["yInput"]

                    if xEffect < maxX and xEffect > minX:
                        maxX = ((maxX * (rLen - 1)) + xEffect) / (rLen)
                        # elif xEffect > minX:
                        minX = ((minX * (rLen - 1)) + xEffect) / (rLen)
                    if yEffect < maxY and yEffect > minY:
                        maxY = ((maxY * (rLen - 1)) + yEffect) / (rLen)
                        # elif yEffect < minY:
                        minY = ((minY * (rLen - 1)) + yEffect) / (rLen)

                    # else:
                    #     if r["yInput"] > maxY:
                    #         maxY = ((maxY * (rLen - 1)) + (r["yInput"])) / (rLen)
                    #     elif r["yInput"] < minX:
                    #         minY = ((minY * (rLen - 1)) + (r["yInput"])) / (rLen)
                # minX /= len(recList)+1
                # maxX /= len(recList)+1
                # minY /= len(recList)+1
                # maxY /= len(recList)+1

            # Learn

            # Execute

            # More complex AI logic incoming

            print(str(minX) + ", " + str(maxX) + " | " + str(minY) + ", " + str(maxY))
            self.xInput = min(1, max(-1, random.uniform(minX, maxX) * xMod))
            self.jumpForce = min(1, max(0, random.uniform(minY, maxY)))
            self.jumpRecord = {"goalPlat": (goalX, goalY), "startDelta": [deltaVec.x, deltaVec.y],
                               "xInput": abs(self.xInput), "yInput": self.jumpForce}
            print("-------------------------  " + str(self.xInput) + " | " + str(
                self.jumpForce) + "  -------------------------")
            self.Jump()

    def SetGoal(self, platforms):
        playX, playY = self.playerPos
        playW, playH = self.displayRect.size
        minDist = 9999
        goalPlat = None
        for p in platforms:
            pX, pY = p.displayRect.center
            pL = p.displayRect.left
            pR = p.displayRect.right
            dist = math.sqrt(pow(playX - pX, 2) + pow(playY - pY, 2))
            if dist < minDist and (pR < playX - playW * 0.5 or pL > playX + playW / 2):
                goalPlat = p
                minDist = dist
        return goalPlat

    def SetPossiblePlatforms(self, stage, surface):
        platforms = stage.GetLevel().platforms
        gW, gH = mapMaker.StageCreator.gridDimensions
        pList = []
        for k, p in platforms.items():
            gX, gY = k
            gXPixels = gX * p.displayRect.width
            gYPixels = gY * p.displayRect.height
            rightBlanks = [not (gX + (i + 1), gY) in platforms and gX + (i + 1) < gW for i in range(3)]
            leftBlanks = [not (gX - (i + 1), gY) in platforms and gX - (i + 1) >= 0 for i in range(3)]
            if not (gX, gY - 1) in platforms and gYPixels <= self.playerPos[1] and (
                    all(rightBlanks) or all(leftBlanks)):
                pList.append(p)
        # Only platforms that don't have an above neighbor
        return self.SetGoal(pList)


class StagePlayer:
    def __init__(self):
        self.players = [
            AI(200, 0, 50, 50, (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)), 150) for i in
            range(AI_COUNT)]
        for p in self.players: p.InitJumpRecords()
        self.running = False
        self.surface = pygame.display.set_mode(size=(SURF_WIDTH, SURF_HEIGHT))
        self.stage = mapMaker.Stage()

    def PlayStage(self, stageName):
        self.surface = pygame.display.set_mode(size=(SURF_WIDTH, SURF_HEIGHT))
        self.stage.LoadStage(stageName, self.surface)
        for p in self.players:
            p.playerPos = (0, 0)
        if "pos" in self.stage.playerSpawn:
            self.stage.curLevel = self.stage.playerSpawn["level"]
            for p in self.players:
                p.playerPos = self.stage.playerSpawn["pos"]
                p.displayRect.center = p.playerPos
        self.running = True
        clock.tick()
        goalPlat = None
        while self.running:
            clock.tick()

            self.surface.fill((255, 255, 255))
            for p in self.players:
                for event in pygame.event.get():
                    if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                        self.running = False
                    if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                        p.SetGauge()
                if p.isSettled():
                    # temp = p.SetPossiblePlatforms(self.stage, self.surface)
                    goalPlat = p.SetPossiblePlatforms(self.stage,
                                                      self.surface)  # temp if temp is not None else goalPlat
                    if (goalPlat):
                        p.ChargeJump(goalPlat)
                    else:
                        p.SaveJumpRecord()
                p.Gravity()
                p.CheckCollision(self.stage.GetPlatforms(self.surface, p))
                self.stage.CheckPlayerPos(p, self.surface)
                p.Display(self.surface)
            self.stage.Display(self.surface)
            if goalPlat:
                goalPlat.platformColor = (255, 255, 0)
                goalPlat.Display(self.surface)
                goalPlat.platformColor = (0, 0, 255)
            # self.player.DisplayGauges(self.surface)
            pygame.display.flip()


# level1 = mapMaker.Level()
# level2 = mapMaker.Level()
# level1.Add(mapMaker.Platform(120, 400, 340, 425, (30, 130, 130), False))
# level1.Add(mapMaker.Platform(120, 100, 340, 125, (130, 30, 130), False))
# level1.Add(mapMaker.Platform(0, 200, 150, 225, (130, 130, 30), False))
# level2.Add(mapMaker.Platform(120, 400, 340, 425, (30, 130, 130), False))
# level2.Add(mapMaker.Platform(120, 100, 340, 125, (130, 30, 130), False))
# level2.Add(mapMaker.Platform(0, 200, 150, 225, (130, 130, 30), False))
# stage = mapMaker.Stage()
# stage.Add(level1)
# stage.Add(level2)
# stage.SaveStage("savedLevel.txt")
# level1.Add(mapMaker.Platform(-50, 0, 0, 600, (30, 130, 130), False)) #Left Wall
# level1.Add(mapMaker.Platform(400, 0, 450, 600, (30, 130, 130), False)) #Right Wall
# level1.Add(mapMaker.Platform(0, 600, 400, 650, (30, 130, 130), False)) #Bottom Wall
# level1.Add(mapMaker.Platform(0, -50, 400, 0, (30, 130, 130), False)) #Top Wall
stagePlayer = StagePlayer()
stageCreator = mapMaker.StageCreator()
stageCreator.EditStage("savedLevel3.txt")
stagePlayer.PlayStage("savedLevel3.txt")
pygame.quit()