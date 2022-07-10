import pygame
import json
from os.path import exists

pygame.init()
font = pygame.font.SysFont('Times New Roman', 20)
SURF_WIDTH = 400
SURF_HEIGHT = 600
CELL_WIDTH = 20
CELL_HEIGHT = 20

class Platform:
    def __init__(self, left, top, right, bottom, color, endGoal):
        self.displayRect = pygame.Rect(left, top, right - left, bottom - top)
        self.platformColor = color
        self.endGoal = endGoal
    def Display(self, surface):
        pygame.draw.rect(surface, self.platformColor, self.displayRect)
        if self.endGoal:
            pygame.draw.rect(surface, (255, 255, 0), self.displayRect)
    def toDict(self):
        obj = {}
        obj["color"] = self.platformColor
        obj["rect"] = (self.displayRect.left, self.displayRect.top, self.displayRect.right, self.displayRect.bottom)
        obj["endGoal"] = self.endGoal
        return obj
    def __str__(self):
        return json.dumps(self.toDict(), indent = 4)
class Level:
    def __init__(self):
        self.platforms = {}
    def Add(self, platform, gridPos):
        self.platforms[gridPos] = (platform)
    def Add2(self, left, top, right, bottom, color, endGoal, gridPos):
        self.Add(Platform(left, top, right, bottom, color, endGoal), gridPos)
    def Display(self, surface):
        for p in self.platforms.values():
            p.Display(surface)
    def SaveLevel(self):
        obj = {}
        dictList = []
        for k in self.platforms.keys():
            tempObj = self.platforms[k].toDict()
            tempObj["gridPos"] = k
            dictList.append(tempObj)
        #[p.toDict() for p in self.platforms.values()]
        obj["platforms"] = dictList
        return obj

    def LoadLevel(self, level):
        self.platforms = {}
        for p in level["platforms"]:
            left, top, right, bottom = p["rect"]
            self.Add2(left, top, right, bottom, p["color"], p["endGoal"], (p["gridPos"][0], p["gridPos"][1]))


class Stage:
    def __init__(self):
        self.levels = []
        self.bounds = []
        self.curLevel = 0
        self.endGoal = {}
        self.playerSpawn = {}
    def Add(self, level):
        self.levels.append(level)

    def GetLevel(self):
        return self.levels[self.curLevel]

    def SaveStage(self, fileName):
        obj = {}
        obj["levels"] = [l.SaveLevel() for l in self.levels]
        if "gridPos" in self.endGoal:
            obj["endGoal"] = self.endGoal
        if "pos" in self.playerSpawn:
            obj["playerSpawn"] = self.playerSpawn
        with open(fileName, 'w') as f:
            f.write(json.dumps(obj, indent=4))

    def LoadStage(self, fileName, surface):
        f = open(fileName, 'r')
        obj = json.loads(f.read())
        if(obj):
            self.levels = []
            self.curLevel = 0
            for lObj in obj["levels"]:
                l = Level()
                l.LoadLevel(lObj)
                self.Add(l)
            if "endGoal" in obj:
                self.endGoal["gridPos"] = (obj["endGoal"]["gridPos"][0], obj["endGoal"]["gridPos"][1])
                self.endGoal["level"] = obj["endGoal"]["level"]
            if "playerSpawn" in obj:
                self.playerSpawn["pos"] = (obj["playerSpawn"]["pos"][0], obj["playerSpawn"]["pos"][1])
                self.playerSpawn["level"] = obj["playerSpawn"]["level"]
        f.close()
        self.Boundaries(surface)
    def Display(self, surface):
        self.levels[self.curLevel].Display(surface)
    def GetPlatforms(self, surface, player):
        platforms = list(self.levels[self.curLevel].platforms.values()).copy()
        playerW, playerH = player.displayRect.size
        if self.curLevel > 0:
            for p in self.levels[self.curLevel - 1].platforms.values():
                platX, platY = p.displayRect.center
                platW, platH = p.displayRect.size
                if platY <= playerH / 2 + platH / 2:
                    platform = Platform(0, 0, 0, 0, (0, 0, 255), False)
                    platform.displayRect.size = (platW, platH)
                    platform.displayRect.center = (platX, platY + surface.get_height())
                    platforms.append(platform)
        if self.curLevel < len(self.levels) - 1:
            for p in self.levels[self.curLevel + 1].platforms.values():
                platX, platY = p.displayRect.center
                platW, platH = p.displayRect.size
                if platY >= surface.get_width() - (playerH / 2 + platH / 2):
                    platform = Platform(0, 0, 0, 0, (0, 0, 255), False)
                    platform.displayRect.size = (platW, platH)
                    platform.displayRect.center = (platX, platY - surface.get_height())
                    platforms.append(platform)
        platforms.append(self.bounds[0])
        platforms.append(self.bounds[1])
        if self.curLevel == 0:
            platforms.append(self.bounds[3])
        if self.curLevel == len(self.levels) - 1:
            platforms.append(self.bounds[2])
        return platforms
    # def GetPlatformsDict(self, surface, player):
    #     dict = self.levels[self.curLevel].platforms.copy()
    #     playerH = player.displayRect.height
    #     if self.curLevel < len(self.levels) - 1:
    #         for p in self.levels[self.curLevel + 1].platforms.values():
    #             platX, platY = p.displayRect.center
    #             platW, platH = p.displayRect.size
    #             if platY >= surface.get_width() - (playerH / 2 + platH / 2):
    #                 platform = Platform(0, 0, 0, 0, (0, 0, 255), False)
    #                 platform.displayRect.size = (platW, platH)
    #                 platform.displayRect.center = (platX, platY - surface.get_height())
    #                 gX, gY, *extra = StageCreator.ConvertPosToGrid(platform.displayRect.center)
    #                 dict[(gX, gY)] = platform
    #     return dict
    def Boundaries(self, surface):
        surfW, surfH = surface.get_size()
        self.bounds.append(Platform(-surfW, -surfH, 0, surfH * 2, (0, 0, 255), False)) # Left Wall
        self.bounds.append(Platform(surfW, -surfH, surfW * 2, surfH * 2, (0, 0, 255), False)) # Right Wall
        self.bounds.append(Platform(-surfW, -surfH, surfW * 2, 0, (0, 0, 255), False)) # Top Wall
        self.bounds.append(Platform(-surfW, surfH, surfW * 2, surfH * 2, (0, 0, 255), False)) # Bottom Wall
    def CheckPlayerPos(self, player, surface):
        w, h = surface.get_size()
        x, y = player.playerPos
        if y < 0:
            if self.curLevel < len(self.levels) - 1:
                self.curLevel += 1
                y = h + y
        elif y > h:
            if self.curLevel > 0:
                self.curLevel -= 1
                y = y - h
        player.playerPos = (x, y)
class StageCreator:
    drawSurface = pygame.Rect(20, 20, SURF_WIDTH, SURF_HEIGHT)
    gridRect = (drawSurface.left, drawSurface.top, drawSurface.width, drawSurface.height)
    gridDimensions = (SURF_WIDTH/CELL_WIDTH, SURF_HEIGHT/CELL_HEIGHT)

    def __init__(self):
        self.running = False
        self.surface = pygame.display.set_mode((SURF_WIDTH+40, SURF_HEIGHT*120))
        self.cursorRect = pygame.Rect(0, 0, 0, 0)
        self.cursorGridPos = (0, 0)
        self.stage = None
        self.curLevel = 0
        self.maxStage = 100
        self.actions = []
        self.undidActions = []
        self.buttons = [] # left, top, right, bottom, color, text, image, method
        self.cursorColor = (150, 150, 150)

    @classmethod
    def ConvertPosToGrid(self, pos):
        x, y = pos
        left, top, width, height = self.gridRect
        xSpaces, ySpaces = self.gridDimensions
        return int((x - left) / width * xSpaces), int((y - top) / height * ySpaces), left, top, int(width / xSpaces), int(height / ySpaces)
    def DisplaySelectionTile(self, rect):
        gridX, gridY, xOffset, yOffset, xLen, yLen = rect
        self.cursorRect.size = (xLen, yLen)
        self.cursorRect.left = xOffset + gridX * xLen
        self.cursorRect.top = yOffset + gridY * yLen
        pygame.draw.rect(self.surface, self.cursorColor, self.cursorRect)
    def IsOverGrid(self):
        left, top, width, height = self.gridRect
        x, y = pygame.mouse.get_pos()
        return left <= x and top <= y and left + width >= x and top + height >= y
    def CanDraw(self, gridPos):
        return not (gridPos in self.stage.levels[self.curLevel].platforms)
    def AddEndGoal(self, gridPos):
        if self.CanDraw(gridPos):
            self.AddPlatform(gridPos)
        alreadyHasGoal = self.stage.levels[self.curLevel].platforms[gridPos].endGoal
        if "gridPos" in self.stage.endGoal:
            self.RemoveEndGoal()
        if not alreadyHasGoal:
            self.stage.levels[self.curLevel].platforms[gridPos].endGoal = True
            self.stage.endGoal["level"] = self.curLevel
            self.stage.endGoal["gridPos"] = gridPos
    def RemoveEndGoal(self):
        if "level" in self.stage.endGoal: #I can remove this later as this is only a temporary fix
            level = self.stage.endGoal["level"]
            lastPos = self.stage.endGoal["gridPos"]
            levels = self.stage.levels
            if level < len(levels) and lastPos in levels[level].platforms:
                self.stage.levels[level].platforms[lastPos].endGoal = False
            self.stage.endGoal.pop("level")
            self.stage.endGoal.pop("gridPos")
    def AddPlayerSpawn(self, gridPos):
        gX, gY = gridPos
        w, h = self.drawSurface.size
        gridXLen, gridYLen = self.gridDimensions
        self.stage.playerSpawn["level"] = self.curLevel
        self.stage.playerSpawn["pos"] = ((w / gridXLen) * (gX + 1.5), (h / gridYLen) * (gY + 1.5))
    def AddPlatform(self, gridPos):
        self.stage.levels[self.curLevel].platforms[gridPos] = (Platform(self.cursorRect.left, self.cursorRect.top, self.cursorRect.right, self.cursorRect.bottom, (0, 0, 255), False))
    def RemovePlatform(self, gridPos):
        if gridPos in self.stage.levels[self.curLevel].platforms:
            if self.stage.levels[self.curLevel].platforms[gridPos].endGoal:
               self.RemoveEndGoal()
            self.stage.levels[self.curLevel].platforms.pop(gridPos)
    def FillPlatforms(self, rect):
        x, y, xOffset, yOffset, xLen, yLen = rect
        maxX, maxY = self.gridDimensions
        add = [[0, 1], [1, 0], [0, -1], [-1, 0]]
        if self.CanDraw((x, y)) and (x >= 0 and x < maxX and y >= 0 and y < maxY):
            self.DisplaySelectionTile(rect)
            self.AddPlatform((x, y))
            for a in add:
                self.FillPlatforms((x + a[0], y + a[1], xOffset, yOffset, xLen, yLen))
    def AddLevel(self):
        if len(self.stage.levels) < self.maxStage:
            if "level" in self.stage.endGoal and self.stage.endGoal["level"] > self.curLevel:
                self.stage.endGoal["level"] = self.stage.endGoal["level"] + 1
            if "level" in self.stage.playerSpawn and self.stage.playerSpawn["level"] > self.curLevel:
                self.stage.playerSpawn["level"] = self.stage.playerSpawn["level"] + 1
            self.stage.levels.insert(self.curLevel + 1, Level())
            self.ChangeCurLevel(self.curLevel + 1)
    def RemoveLevel(self):
        if len(self.stage.levels) > 1:
            self.stage.levels.pop(self.curLevel)
            self.ChangeCurLevel(self.curLevel - 1)
            if "level" in self.stage.endGoal:
                endLevel = self.stage.endGoal["level"]
                if endLevel == self.curLevel:
                    RemoveEndGoal()
                elif endLevel > self.curLevel:
                    self.stage.endGoal["level"] = endLevel - 1
            if "level" in self.stage.playerSpawn:
                spawnLevel = self.stage.playerSpawn["level"]
                if spawnLevel == self.curLevel:
                    gW, gH = self.gridDimensions
                    self.AddPlayerSpawn((gW / 2, gH / 2))
                elif spawnLevel > self.curLevel:
                    self.stage.playerSpawn["level"] = spawnLevel - 1
    def Undo(self):
        self.actions
        print("Undo")
    def Redo(self):
        #Save all the undid actions
        print("Redo")
    def DisplayLevelNum(self, surface, level):
        text = font.render(str(level), True, (0, 0, 0))
        surface.blit(text, (0, 0))
    def ChangeCurLevel(self, newLevel):
        self.curLevel = 0 if newLevel < 0 else len(self.stage.levels) - 1 if newLevel > len(self.stage.levels) - 1 else newLevel
    def EditStage(self, stageName): # use f strings, they are really cool # delegates work, you can pass functions as variables
        self.surface = pygame.display.set_mode((SURF_WIDTH+40, SURF_HEIGHT*120))
        self.stage = Stage()
        if exists(stageName):
            self.stage.LoadStage(stageName, self.surface)
            left = self.drawSurface.left
            top = self.drawSurface.top
            for l in self.stage.levels:
                for p in l.platforms.values():
                    x, y = p.displayRect.center
                    p.displayRect.center = (x + left, y + top)
            spawnX, spawnY = self.stage.playerSpawn["pos"]
            self.stage.playerSpawn["pos"] = (spawnX + left, spawnY + top)
        else:
            self.stage.levels.append(Level())
            self.drawSurface.size
            gW, gH = self.gridDimensions
            self.AddPlayerSpawn((gW / 2, gH / 2))
        self.running = True
        self.curLevel = 0
        self.actions = []
        self.undidActions = []
        self.buttons = []
        self.buttons.append(Button(SURF_WIDTH-10, SURF_HEIGHT+30, SURF_WIDTH+10, SURF_HEIGHT+50, (150, 150, 150), "Add Level", None, self.AddLevel))
        self.buttons.append(Button(SURF_WIDTH-10, SURF_HEIGHT+60, SURF_WIDTH+10, SURF_HEIGHT+80, (150, 150, 150), "Remove Level", None, self.RemoveLevel))
        while self.running:
            x, y = pygame.mouse.get_pos()
            # tempVec = pygame.math.Vector2(x - SURF_WIDTH / 2, y - SURF_HEIGHT / 2)
            # dist, angle = tempVec.as_polar()
            # angle = abs(angle - 180)
            # print("angle is: " + str(angle))
            left, top, width, height = self.gridRect
            x = left if x < left else left + width - 1 if x > left + width - 1 else x
            y = top if y < top else top + height - 1 if y > top + height - 1 else y
            rect = self.ConvertPosToGrid((x, y))
            gridX, gridY, xOffset, yOffset, xLen, yLen = rect
            for event in pygame.event.get():
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE: # can only end the game if there is an end flag and a player spawn
                    self.running = False
                if (event.type == pygame.KEYDOWN and event.key == pygame.K_w) or (event.type == pygame.KEYDOWN and event.key == pygame.K_UP):
                    self.ChangeCurLevel(self.curLevel + 1)
                if (event.type == pygame.KEYDOWN and event.key == pygame.K_s) or (event.type == pygame.KEYDOWN and event.key == pygame.K_DOWN):
                    self.ChangeCurLevel(self.curLevel - 1)
                if event.type == pygame.KEYDOWN and event.key == pygame.K_n:
                    self.AddLevel()
                if event.type == pygame.KEYDOWN and event.key == pygame.K_m:
                    self.RemoveLevel()
                if event.type == pygame.KEYDOWN and event.key == pygame.K_f:
                    self.FillPlatforms(rect)
                if event.type == pygame.MOUSEBUTTONDOWN:
                    [b.CheckClick() for b in self.buttons]
                if event.type == pygame.KEYDOWN and event.key == pygame.K_e:
                    self.AddEndGoal((gridX, gridY))
                if event.type == pygame.KEYDOWN and event.key == pygame.K_p:
                    self.AddPlayerSpawn((gridX, gridY))
            self.surface.fill((200, 200, 200))
            pygame.draw.rect(self.surface, (255, 255, 255), self.drawSurface)
            self.stage.levels[self.curLevel].Display(self.surface)
            self.DisplayLevelNum(self.surface, self.curLevel)
            mouse1, mouse2, mouse3 = pygame.mouse.get_pressed()
            if "pos" in self.stage.playerSpawn and self.stage.playerSpawn["level"] == self.curLevel:
                pygame.draw.circle(self.surface, (0, 255, 0), self.stage.playerSpawn["pos"], 25)
            if self.IsOverGrid():
                self.DisplaySelectionTile(rect)
                if self.CanDraw((gridX, gridY)):
                    if mouse1:
                        self.AddPlatform((gridX, gridY))
                elif mouse3:
                    self.RemovePlatform((gridX, gridY))
            [b.Display(self.surface) for b in self.buttons]

            pygame.display.flip()
        left = self.drawSurface.left
        top = self.drawSurface.top
        for l in self.stage.levels:
            for p in l.platforms.values():
                x, y = p.displayRect.center
                p.displayRect.center = (x - left, y - top)
        spawnX, spawnY = self.stage.playerSpawn["pos"]
        self.stage.playerSpawn["pos"] = (spawnX - left, spawnY - top)
        self.stage.SaveStage(stageName)
class Button:
    def __init__(self, left, top, right, bottom, color, text, image, method):
        self.displayRect = pygame.Rect(left, top, right - left, bottom - top)
        self.color = color
        self.text = text
        self.image = image
        self.method = method
    def Display(self, surface):
        pygame.draw.rect(surface, self.color, self.displayRect)
    def CheckClick(self): #add click priority later, if ever # click priority means that it will click one button if two or more buttons are stacked (it will click the one "on top")
        mX, mY = pygame.mouse.get_pos()
        bX, bY = self.displayRect.topleft
        bW, bH = self.displayRect.size
        if mX >= bX and mY >= bY and mX < bX + bW and mY < bY + bH:
            self.OnClick()
    def OnClick(self):
        self.method()
class Slider:
    def __init__(self, left, top, right, bottom, backgroundColor, sliderColor, maxSliderSize, minSliderSize, alwaysVisible):
        self.displayRect = pygame.Rect(left, top, right - left, bottom - top)
        self.backgroundColor = backgroundColor
        self.sliderColor = sliderColor
        self.maxSize = maxSliderSize
        self.minSize = minSliderSize
        self.alwaysVisible = alwaysVisible
