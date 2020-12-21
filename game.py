import math
import pgzrun
import time

# TODO 只是为了vscode不报warning，没有别的用处
from pgzero.actor import Actor
from pgzero.rect import Rect, ZRect
from pgzero.loaders import sounds, images
from pgzero import music, tone
from pgzero.clock import clock
from pgzero.builtins import keymods
from pgzero.constants import mouse
from pgzero.animation import animate
from pgzero.keyboard import keys, Keyboard
from pgzero.screen import Screen
keyboard: Keyboard
screen: Screen


TITLE = "燕园云战役"
WIDTH = 1000
HEIGHT = 700


class Game:
    def __init__(self):
        self.begin_time = time.time()
        self.status = "begin"
        self.level = 1
        self.buying = 0
        self.mouse_down_pos = (0, 0)
        self.mouse_move_pos = (0, 0)
        self.lives = 3
        self.money = 500
        self.enemies = []
        self.enemy_count = 0
        self.last_enemy_time = 0
        self.towers = []

        # 音乐
        music.set_volume(0.4)
        music.play("start.wav")

        # 共用界面
        self.back_button = Actor("back_button", (50, 50))
        # 开始界面
        self.begin_button = Actor("begin_button", (500, 425))
        # 帮助界面
        self.help_button = Actor("help_button", (500, 550))
        # 升级界面
        self.egg_button = Actor("egg_button", (100, 400))
        # 游戏中
        self.buy_tower1 = Actor("tower1", (450, 650))
        self.buy_tower2 = Actor("tower2", (625, 650))
        self.buy_tower3 = Actor("tower3", (825, 650))
        self.hint = Actor("tower1", (0, 0))
        self.pause_button = Actor("pause_button", (100, 200))
        self.start_button = Actor("start_button", (100, 300))
        self.next_button = Actor("next_button", (100, 400))
        # 彩蛋
        self.buy_pkuer = Actor("pkuer2", (700, 650))

    def run(self):
        # 开始界面
        if self.status == "begin":
            if self.begin_button.collidepoint(self.mouse_down_pos):
                self.status = "playing"
                sounds.starta.play(loops = 0)
                music.set_volume(0.2)
            elif self.help_button.collidepoint(self.mouse_down_pos):
                self.status = "help"
                sounds.starta.play(loops = 0)
        # 帮助界面
        elif self.status == "help":
            if self.back_button.collidepoint(self.mouse_down_pos):
                sounds.starta.play(loops = 0)
                self.status = "begin"
        # 暂停状态
        elif self.status == "pause":
            if self.start_button.collidepoint(self.mouse_down_pos):
                if self.level <= 3:
                    self.status = "playing"
                elif self.level == 4:
                    self.status = "egg"
        # 游戏中
        elif self.status == "playing":
            self.run_playing()
        # 下一关
        elif self.status == "level up":
            self.run_level_up()
        # 彩蛋
        elif self.status == "egg":
            self.run_egg()
        # 胜利
        elif self.status == "win":
            if self.back_button.collidepoint(self.mouse_down_pos):
                self.restart()
                self.status = "begin"
        # 失败
        elif self.status == "lose":
            if self.back_button.collidepoint(self.mouse_down_pos):
                self.restart()
                self.status = "begin"

    def run_playing(self):
        # 检测游戏结果
        result = self.get_result()
        if result == 1:             # 胜利
            music.stop()
            self.level += 1
            self.status = "level up"
            sounds.levelup.play(loops = 0)
        elif result == -1:          # 失败
            self.status = "lose"
            music.set_volume(0.5)
            music.play_once("lose.wav")

        # 返回到开始界面
        if self.back_button.collidepoint(self.mouse_down_pos):
            self.restart()
            self.status = "begin"

        # 暂停游戏
        if self.pause_button.collidepoint(self.mouse_down_pos):
            self.status = "pause"

        # 购买状态
        if self.buying:
            if self.tower_in_range(self.mouse_move_pos):
                self.buy_tower()

        # 按下购买按钮，并更改状态
        if self.buy_tower1.collidepoint(self.mouse_down_pos) and self.money - 50 >= 0:
            self.buying = 1
        elif self.buy_tower2.collidepoint(self.mouse_down_pos) and self.money - 100 >= 0:
            self.buying = 2
        elif self.buy_tower3.collidepoint(self.mouse_down_pos) and self.money - 200 >= 0:
            self.buying = 3

        # 更新
        self.update_actor()

    def run_egg(self):
        # 返回按钮
        if self.back_button.collidepoint(self.mouse_down_pos):
            self.restart()
            self.status = "begin"

        # 暂停游戏
        if self.pause_button.collidepoint(self.mouse_down_pos):
            self.status = "pause"

        # 塔攻击
        for tower in self.towers:
            if tower.type == 1:
                tower.attack(self.enemies)
            elif tower.type == 2:
                tower.frozen(self.enemies)
            elif tower.type == 3:
                tower.boom(self.enemies)

        # 病毒更新
        for enemy in self.enemies:
            enemy.move(self.level)                          # 行走
            enemy.hurt(self.towers)                         # 受伤
            if enemy.type == 4:                             # boss生成病毒
                enemy.boss_born(self.enemies)
            if enemy.health <= 0:                           # 检测病毒是否死亡
                self.money += enemy.type * 10
                sounds.coin.play(loops = 0)
                self.enemies.remove(enemy)
            if enemy.pos == (925, 325):                     # 检测是否胜利
                self.status = "win"
                music.set_volume(0.5)
                music.play_once("youwin.wav")

        # 购买北大学生
        if self.buy_pkuer.collidepoint(self.mouse_down_pos):
            self.enemies.append(Enemy("pkuer", (200, 75), 5))
            self.mouse_down_pos = (0, 0)

    def run_level_up(self):
        # 若处于前三关
        if self.level <= 3:
            self.buying = 0
            self.enemies.clear()
            self.enemy_count = 0
            self.last_enemy_time = 0
            self.towers.clear()
            if self.next_button.collidepoint(self.mouse_down_pos):
                sounds.starta.play(loops = 0)
                music.set_volume(0.2)
                music.play("start.wav")
                self.begin_time = time.time()
                self.status = "playing"

        # 若处于彩蛋关卡
        elif self.level == 4:
            self.buying = 0
            self.enemies.clear()
            self.enemy_count = 0
            self.last_enemy_time = 0
            self.towers.clear()
            self.towers.append(Tower("virus4_1", (400, 325), 1))
            self.towers.append(Tower("virus4_0", (500, 200), 2))
            self.towers.append(Tower("virus4_1", (700, 450), 3))
            if self.next_button.collidepoint(self.mouse_down_pos):
                sounds.starta.play(loops = 0)
                music.set_volume(0.2)
                music.play("start.wav")
                self.begin_time = time.time()
                self.status = "egg"

    def restart(self):
        sounds.starta.play(loops = 0)
        music.set_volume(0.4)
        music.play("start.wav")
        self.level = 1
        self.buying = 0
        self.lives = 3
        self.money = 50
        self.enemies.clear()
        self.enemy_count = 0
        self.last_enemy_time = 0
        self.towers.clear()

    def menu(self):
        # 绘制游戏菜单

        # 开始界面
        if self.status == "begin":
            screen.blit("begin_bg", (0, 0))
            self.begin_button.draw()
            self.help_button.draw()
        # 帮助界面
        elif self.status == "help":
            screen.blit("help_bg", (0, 0))
            self.back_button.draw()
        # 游戏中
        elif self.status == "playing":
            self.draw_playing_menu()
            self.draw_actor()
        # 彩蛋
        elif self.status == "egg":
            screen.blit("playing_bg_thu", (0, 0))
            screen.blit("money", (225, 620))
            screen.draw.text(str(self.money), topright = (350, 640), color = (0, 0, 0), fontsize = 50)
            self.back_button.draw()
            self.pause_button.draw()
            self.start_button.draw()
            self.buy_pkuer.draw()
            self.draw_actor()
        # 胜利
        elif self.status == "win":
            screen.blit("win", (200, 0))
        # 升级
        elif self.status == "level up":
            if self.level <= 3:
                screen.blit("level up", (200, 0))
                self.next_button.draw()
            if self.level == 4:
                screen.blit("win_but", (200, 0))
                self.egg_button.draw()
        # 失败
        elif self.status == "lose":
            screen.blit("lose", (200, 0))
            self.back_button.draw()

    def draw_playing_menu(self):
        # 绘制游戏中菜单

        # 背景
        screen.blit("playing_bg_pku", (0, 0))
        # 金币
        screen.blit("money", (225, 620))
        screen.draw.text(str(self.money), topright = (350, 640), color = (0,0,0), fontsize = 50)
        # 生命
        screen.blit("lives", (50, 90))
        screen.draw.text(str(self.lives), topright=(130, 100), color = (0,0,0), fontsize = 50)
        # 按钮
        self.back_button.draw()
        self.pause_button.draw()
        self.start_button.draw()
        self.next_button.draw()
        # 塔的价格
        screen.blit("little_money", (500, 650))
        screen.draw.text("50", topright = (575, 650), color = (0,0,0), fontsize = 30)
        screen.blit("little_money", (675, 650))
        screen.draw.text("100", topright = (750, 650), color = (0,0,0), fontsize = 30)
        screen.blit("little_money", (875, 650))
        screen.draw.text("200", topright = (950, 650), color = (0,0,0), fontsize = 30)
        # 塔的购买按钮
        self.buy_tower1.draw()
        self.buy_tower2.draw()
        self.buy_tower3.draw()
        # 游戏进度条
        rect = Rect((25, 475), (150, 10))
        screen.draw.filled_rect(rect, (0, 255, 0))
        rect = Rect((25, 475), (self.enemy_count / (self.level * 10) * 150, 10))
        screen.draw.filled_rect(rect, (255, 0, 0))
        screen.blit("virus2_2", (self.enemy_count / (self.level * 10) * 150, 465))

    def update_actor(self):
        # 更新所有移动图像

        # 购买提示图像坐标
        self.hint.pos = self.mouse_move_pos

        # 添加病毒
        self.add_virus()

        # 病毒更新
        for enemy in self.enemies:
            enemy.move(self.level)                          # 行走
            enemy.hurt(self.towers)                         # 受伤
            if enemy.type == 4:                             # boss生成病毒
                enemy.boss_born(self.enemies)
            if enemy.health <= 0:                           # 检测病毒是否死亡
                self.money += enemy.type * 10
                sounds.coin.play(loops = 0)
                self.enemies.remove(enemy)
            if int(enemy.x) == 600 and int(enemy.y) == 275: # 检测病毒是否到达终点
                self.lives -= 1
                self.enemies.remove(enemy)

        # 塔的攻击
        for tower in self.towers:
            if tower.type == 1:
                tower.attack(self.enemies)
            elif tower.type == 2:
                tower.frozen(self.enemies)
            elif tower.type == 3:
                tower.boom(self.enemies)

    def draw_actor(self):
        # 绘制所有移动图像

        # 如果在购买状态，绘制位置提示
        if self.buying:
            if self.tower_in_range(self.mouse_move_pos):
                self.hint.image = "tower" + str(self.buying)
            else:
                self.hint.image = "out_of_range"
            self.hint.draw()

        # 绘制病毒和塔，还有塔发射的子弹
        for enemy in self.enemies:
            enemy.draw()
        for tower in self.towers:
            tower.draw()
            for shoot in tower.shoots:
                shoot.draw()

    def add_virus(self):
        # 增加新病毒
        tamp = time.time()

        # 根据游戏关卡，确定病毒开始位置
        if self.level == 1:
            begin_pos = (1000, 325)
        elif self.level == 2:
            begin_pos = (700, 575)
        elif self.level == 3:
            begin_pos = (200, 75)
        elif self.level == 4:
            begin_pos = (200, 75)

        # 每隔5秒，病毒出场
        enemy_sum = self.level * 10
        if tamp - self.last_enemy_time > 5 and self.enemy_count < enemy_sum:
            if self.enemy_count < enemy_sum / 2:
                # 0 - 1/2 为低级病毒
                self.enemies.append(Enemy("virus1_1", begin_pos, 1))
            elif enemy_sum / 2 <= self.enemy_count < enemy_sum * 3 / 4:
                # 1/2 - 3/4 为中级病毒
                self.enemies.append(Enemy("virus2_1", begin_pos, 2))
            elif enemy_sum * 3 / 4 <= self.enemy_count < enemy_sum - 1:
                # 3/4 - 1 为高级病毒
                self.enemies.append(Enemy("virus3_1", begin_pos, 3))
            elif self.enemy_count == enemy_sum - 1:
                # 最后一个为Boss
                self.enemies.append(Enemy("virus4_1", begin_pos, 4))
            self.enemy_count += 1
            self.last_enemy_time = tamp


    def get_result(self):
        # 获取游戏结果
        tamp = time.time()
        if len(self.enemies) == 0 and self.enemy_count == self.level * 10:
            if self.lives > 0:
                return 1        # 胜利
        if self.lives <= 0:
            return -1           # 失败
        else:
            return 0            # 游戏中

    def buy_tower(self):
        # 购买塔

        # 如果选择的位置不合法，则停止本次购买
        in_range = self.tower_in_range(self.mouse_down_pos)
        if not in_range:
            self.buying = 0

        # 如果选择的位置合法，根据塔的种类放置塔，并播放音效
        if self.buying > 0:
            tower_name = "tower" +str(self.buying)
            sounds.starta.play(loops = 0)
            self.towers.append(Tower(tower_name, self.mouse_down_pos, self.buying))
            self.money -= self.towers[-1].cost

        # 结束购买状态
        self.buying = 0

    def tower_in_range(self, pos):
        # 判断塔的位置是否合法

        # 塔不能重叠
        for tower in self.towers:
            if tower.collidepoint(pos):
                return False

        # 只有空白区域可以放置塔，道路和建筑物上不能放置
        if 200 < pos[0] < 350 and 0 < pos[1] < 50:
            return True
        elif 200 < pos[0] < 300 and 200 < pos[1] < 300:
            return True
        elif 200 < pos[0] < 300 and 350 < pos[1] < 500:
            return True
        elif 200 < pos[0] < 400 and 550 < pos[1] < 600:
            return True
        elif 350 < pos[0] < 400 and 100 < pos[1] < 450:
            return True
        elif 350 < pos[0] < 400 and 300 < pos[1] < 350:
            return True
        elif 450 < pos[0] < 550 and 150 < pos[1] < 250:
            return True
        elif 525 < pos[0] < 575 and 350 < pos[1] < 375:
            return True
        elif 650 < pos[0] < 750 and 400 < pos[1] < 500:
            return True
        elif 725 < pos[0] < 750 and 250 < pos[1] < 500:
            return True
        elif 725 < pos[0] < 800 and 500 < pos[1] < 600:
            return True
        elif 800 < pos[0] < 900 and 300 < pos[1] < 450:
            return True
        elif 850 < pos[0] < 1000 and 100 < pos[1] < 200:
            return True
        elif 500 < pos[0] < 700 and 0 < pos[1] < 100:
            return True
        elif 600 < pos[0] < 650 and 550 < pos[1] < 600:
            return True
        elif 950 < pos[0] < 1000 and 350 < pos[1] < 500:
            return True
        else:
            return False

class Enemy(Actor):
    def __init__(self, image, pos, enemy_type, path_index = 0, anchor = None, **kwargs):
        Actor.__init__(self, image, pos, anchor, **kwargs)
        self.path1 = [(1000, 325), (925, 325), (925, 475), (775, 475), (775, 225),
        (675, 225), (675, 350), (600, 350), (600, 275)]
        self.path2 = [(700, 575), (700, 525), (425, 525), (425, 375), (450, 375),
        (450, 275), (400, 275), (400, 125), (600, 125), (600, 275)]
        self.path3 = [(200, 75), (325, 75), (325, 525), (400, 525), (400, 375),
        (450, 375), (450, 275), (400, 275), (400, 125), (600, 125), (600, 275)]
        self.path4 =  [(200, 75), (325, 75), (325, 525), (400, 525), (400, 375),
        (450, 375), (450, 275), (400, 275), (400, 125), (600, 125), (600, 275),
        (600, 350), (675, 350), (675, 225), (775, 225), (775, 475),(925, 475),
        (925, 325), (1000, 325)]
        self.path_index = path_index
        self.type = enemy_type
        self.speed_list = [0.2, 0.5, 1, 0.2, 1]
        self.speed = self.speed_list[self.type - 1]
        self.health_list = [20, 50, 50, 100, 100]
        self.health = self.health_list[self.type - 1]
        self.appear_time = time.time()
        self.boss_born_time = 0
        self.frozen = False
        self.frozen_time = 0

    def draw(self):
        # 绘制病毒图片
        tamp = time.time()

        # 实现非冰冻和冰冻状态下的动画效果。
        if not self.frozen:
            # 非冰冻状态下，每隔0.1秒更换一次image，从而实现动画效果
            temp = int((tamp - self.appear_time) * 10)
            if self.type == 5:
                # 彩蛋关卡图片
                self.image = "pkuer" + str(temp % 2 + 1)
            else:
                self.image = "virus" + str(self.type) + "_" + str(temp % 3 + 1)
        elif self.frozen:
            # 冰冻状态下，image固定为冰冻效果图片
            if self.type == 5:
                self.image = "pkuer0"
            else:
                self.image = "virus" + str(self.type) + "_0"

        Actor.draw(self)        # 绘制病毒
        self.health_bar()       # 绘制血量条

    def health_bar(self):
        # 绘制血量条

        if self.type == 5:
            bar_len = 60      # 彩蛋中角色的图片更大
        else:
            bar_len = 50

        # 绘制总血量
        rect = Rect((self.x - bar_len / 2, self.y - bar_len), (bar_len, 10))
        screen.draw.filled_rect(rect, (255, 0, 0))

        # 绘制剩余血量
        remain_len = self.health / self.health_list[self.type - 1] * bar_len
        rect = Rect((self.x - bar_len / 2, self.y - bar_len), (remain_len, 10))
        screen.draw.filled_rect(rect, (0, 255, 0))


    def move(self, level):
        tamp = time.time()

        # 检查冰冻时间，若冰冻超过三秒，则解冻，从而正常移动
        if self.frozen == True and tamp - self.frozen_time > 3:
            self.frozen = False

        # 根据关卡确定路径
        if level == 1:
            path = self.path1
        elif level == 2:
            path = self.path2
        elif level == 3:
            path = self.path3
        elif level == 4:
            path = self.path4

        # 若不处于冰冻状态，则移动
        if not self.frozen:
            if path[self.path_index][0] == path[self.path_index + 1][0]:
                if self.y < path[self.path_index + 1][1]:
                    self.y += self.speed
                elif int(self.y) == path[self.path_index + 1][1]:
                    if self.path_index + 2 < len(path):
                        self.path_index += 1
                elif self.y > path[self.path_index + 1][1]:
                    self.y -= self.speed

            if path[self.path_index][1] == path[self.path_index + 1][1]:
                if self.x < path[self.path_index + 1][0]:
                    self.x += self.speed
                elif int(self.x) == path[self.path_index + 1][0]:
                    if self.path_index + 2 < len(path):
                        self.path_index += 1
                elif self.x > path[self.path_index + 1][0]:
                    self.x -= self.speed

    def hurt(self, towers):
        # 对所有子弹，检测是否击中病毒
        for tower in towers:
            for shoot in tower.shoots:
                if self.collidepoint(shoot.x, shoot.y):
                    sounds.beat4.play(loops = 0)
                    self.health -= 5
                    tower.shoots.remove(shoot)

    def boss_born(self, enemies):
        # 每隔8秒，boss病毒诞生一个中等病毒，其位置同Boss病毒，但不继承冰冻状态。
        tamp = time.time()
        if tamp - self.boss_born_time > 8 and self.frozen == False:
            enemies.append(Enemy("virus2_1", (self.x, self.y), 2, self.path_index))
            self.boss_born_time = tamp

class Tower(Actor):
    def __init__(self, image, pos, tower_type ,anchor = None, **kwargs):
        Actor.__init__(self, image, pos, anchor, **kwargs)
        self.type = tower_type
        self.range = 150
        self.in_range = False
        self.cost_list = [50, 100, 200]
        self.cost = self.cost_list[self.type - 1]
        self.shoots = []
        self.last_attack_time = time.time()
        self.booming = False

    def draw(self):
        Actor.draw(self)
        # 绘制爆炸效果
        if self.type == 3 and self.booming:
            boom1 = Actor("boom", (self.x + 25, self.y - 30))
            boom1.draw()
            boom2 = Actor("boom", (self.x - 25, self.y - 30))
            boom2.draw()

    def attack(self, enemies):
        tamp = time.time()
        min_dis = 100000
        min_dis_enemy = 0
        self.in_range = False

        # 判断病毒是否在范围内，并找到距离最短的病毒
        for enemy in enemies:
            x = enemy.x
            y = enemy.y
            dis = math.sqrt((x - self.x) ** 2 + (y - self.y) ** 2)
            if dis < self.range:
                self.in_range = True
                if dis < min_dis:
                    min_dis = dis
                    min_dis_enemy = enemy

        # 发射子弹
        if self.in_range and tamp - self.last_attack_time > 1:
            self.shoots.append(Actor("shoot", (self.x, self.y)))
            self.shoots[-1].speed_x = (min_dis_enemy.x - self.x) / 20
            self.shoots[-1].speed_y = (min_dis_enemy.y - self.y) / 20
            self.last_attack_time = tamp

        # 子弹运动
        for shoot in self.shoots:
            shoot.x += shoot.speed_x
            shoot.y += shoot.speed_y

    def boom(self, enemies):
        tamp = time.time()
        boom = False

        if tamp - self.last_attack_time > 1:
            self.booming = False

        # 对范围内的病毒，生命值减少25点，并播放音效
        for enemy in enemies:
            x = enemy.x
            y = enemy.y
            dis = math.sqrt((x - self.x) ** 2 + (y - self.y) ** 2)
            if dis < self.range and tamp - self.last_attack_time > 5:
                sounds.boom.play(loops = 0)
                enemy.health -= 25
                self.booming = True
                boom = True
        if boom:
            self.last_attack_time = tamp

    def frozen(self, enemies):
        tamp = time.time()
        froze = False

        # 对范围内的病毒，实现冰冻效果，并记录冰冻时间，播放音效
        for enemy in enemies:
            x = enemy.x
            y = enemy.y
            dis = math.sqrt((x - self.x) ** 2 + (y - self.y) ** 2)
            if dis < self.range and tamp - self.last_attack_time > 5:
                sounds.froz.play(loops = 0)
                enemy.frozen = True
                enemy.frozen_time = tamp
                froze = True
        if froze:
            self.last_attack_time = tamp


def update():
    game.run()

def draw():
    game.menu()

def on_mouse_down(pos):
    game.mouse_down_pos = pos

def on_mouse_move(pos, rel, buttons):
    game.mouse_move_pos = pos

game = Game()

pgzrun.go()