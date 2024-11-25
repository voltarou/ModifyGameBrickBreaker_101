import tkinter as tk
import random


class GameObject(object):
    def __init__(self, canvas, item):
        self.canvas = canvas
        self.item = item

    def get_position(self):
        return self.canvas.coords(self.item)

    def move(self, x, y):
        self.canvas.move(self.item, x, y)

    def delete(self):
        self.canvas.delete(self.item)


class Ball(GameObject):
    def __init__(self, canvas, x, y):
        self.radius = 10
        self.direction = [1, -1]
        self.speed = 15
        item = canvas.create_oval(x - self.radius, y - self.radius,
                                  x + self.radius, y + self.radius,
                                  fill='white')
        super(Ball, self).__init__(canvas, item)

    def update(self):
        coords = self.get_position()
        width = self.canvas.winfo_width()
        height = self.canvas.winfo_height()

        if coords[0] <= 0 or coords[2] >= width:
            self.direction[0] *= -1

        if coords[1] <= 0:
            self.direction[1] *= -1

        if coords[3] >= height:
            return False  # Ball fell off screen, game over

        x = self.direction[0] * self.speed
        y = self.direction[1] * self.speed
        self.move(x, y)
        return True

    def collide(self, game_objects):
        coords = self.get_position()
        x = (coords[0] + coords[2]) * 0.5
        if len(game_objects) > 1:
            self.direction[1] *= -1
        elif len(game_objects) == 1:
            game_object = game_objects[0]
            coords = game_object.get_position()
            if x > coords[2]:
                self.direction[0] = 1
            elif x < coords[0]:
                self.direction[0] = -1
            else:
                self.direction[1] *= -1

        for game_object in game_objects:
            if isinstance(game_object, Brick):
                game_object.hit()
                self.speed += 1  # Increase speed when hitting a brick


class Paddle(GameObject):
    def __init__(self, canvas, x, y):
        self.width = 80
        self.height = 10
        self.ball = None
        item = canvas.create_rectangle(x - self.width / 2,
                                       y - self.height / 2,
                                       x + self.width / 2,
                                       y + self.height / 2,
                                       fill='#FFB643')
        super(Paddle, self).__init__(canvas, item)

    def set_ball(self, ball):
        self.ball = ball

    def move(self, offset):
        coords = self.get_position()
        width = self.canvas.winfo_width()
        if coords[0] + offset >= 0 and coords[2] + offset <= width:
            super(Paddle, self).move(offset, 0)
            if self.ball is not None:
                self.ball.move(offset, 0)

    def increase_size(self):
        self.width += 20
        self.canvas.coords(self.item, self.get_position()[0] - 10,
                           self.get_position()[1], self.get_position()[2] + 10,
                           self.get_position()[3])


class Brick(GameObject):
    COLORS = {1: '#4535AA', 2: '#ED639E', 3: '#8FE1A2'}

    def __init__(self, canvas, x, y, hits):
        self.width = 75
        self.height = 20
        self.hits = hits
        color = Brick.COLORS[hits]
        item = canvas.create_rectangle(x - self.width / 2,
                                       y - self.height / 2,
                                       x + self.width / 2,
                                       y + self.height / 2,
                                       fill=color, tags='brick')
        super(Brick, self).__init__(canvas, item)

    def hit(self):
        self.hits -= 1
        if self.hits == 0:
            self.delete()
        else:
            self.canvas.itemconfig(self.item,
                                   fill=Brick.COLORS[self.hits])


class PowerUp(GameObject):
    def __init__(self, canvas, x, y):
        self.type = random.choice(['increase_paddle', 'extra_life', 'slow_ball'])
        self.width = 20
        self.height = 20
        color = 'yellow'  # Power-ups are yellow
        item = canvas.create_oval(x - self.width / 2, y - self.height / 2,
                                  x + self.width / 2, y + self.height / 2,
                                  fill=color, tags='powerup')
        super(PowerUp, self).__init__(canvas, item)

    def apply(self, game):
        if self.type == 'increase_paddle':
            game.paddle.increase_size()
        elif self.type == 'extra_life':
            game.lives += 1
            game.update_lives_text()
        elif self.type == 'slow_ball':
            game.ball.speed = max(5, game.ball.speed - 5)  # Slow down the ball


class Game(tk.Frame):
    def __init__(self, master):
        super(Game, self).__init__(master)
        self.lives = 3
        self.width = 800
        self.height = 500
        self.canvas = tk.Canvas(self, bg='#D6D1F5',
                                width=self.width,
                                height=self.height, )
        self.canvas.pack()
        self.pack()

        self.items = {}
        self.ball = None
        self.paddle = Paddle(self.canvas, self.width / 2, 426)
        self.items[self.paddle.item] = self.paddle
        for x in range(5, self.width - 5, 75):
            self.add_brick(x + 37.5, 50, 3)
            self.add_brick(x + 37.5, 70, 2)
            self.add_brick(x + 37.5, 90, 1)

        self.hud = None
        self.setup_game()
        self.canvas.focus_set()
        self.canvas.bind('<Left>', lambda _: self.paddle.move(-20))  # Move faster
        self.canvas.bind('<Right>', lambda _: self.paddle.move(20))  # Move faster
        self.paused = False
        self.canvas.bind('<p>', lambda _: self.toggle_pause())

    def setup_game(self):
        self.add_ball()
        self.update_lives_text()
        self.text = self.draw_text(400, 250,
                                   'Press Space to start\nPress "P" to pause')
        self.canvas.bind('<space>', lambda _: self.start_game())

    def add_ball(self):
        if self.ball is not None:
            self.ball.delete()
        paddle_coords = self.paddle.get_position()
        x = (paddle_coords[0] + paddle_coords[2]) * 0.5
        self.ball = Ball(self.canvas, x, 426)
        self.paddle.set_ball(self.ball)

    def add_brick(self, x, y, hits):
        brick = Brick(self.canvas, x, y, hits)
        self.items[brick.item] = brick

    def add_powerup(self, x, y):
        powerup = PowerUp(self.canvas, x, y)
        self.items[powerup.item] = powerup

    def draw_text(self, x, y, text, size='40'):
        font = ('Forte', size)
        return self.canvas.create_text(x, y, text=text,
                                       font=font)

    def update_lives_text(self):
        text = 'Lives: %s' % self.lives
        if self.hud is None:
            self.hud = self.draw_text(50, 20, text, 15)
        else:
            self.canvas.itemconfig(self.hud, text=text)

    def toggle_pause(self):
        if self.paused:
            self.paused = False
            self.game_loop()  # Resume game if previously paused
        else:
            self.paused = True
            self.canvas.after(1, self.game_loop)  # Stop updating the game loop

    def start_game(self):
        if self.paused:
            return  # Don't start the game if paused
        self.canvas.unbind('<space>')
        self.canvas.delete(self.text)
        self.paddle.ball = None
        self.game_loop()

    def game_loop(self):
        if self.paused:
            return  # Do not update the game loop if paused

        if not self.ball.update():
            self.lives -= 1
            if self.lives < 0:
                self.draw_text(400, 250, 'You Lose! Game Over!')
                self.canvas.after(2000, self.reset_game)  # Reset game after delay
            else:
                self.after(1000, self.setup_game)
            return

        self.check_collisions()
        num_bricks = len(self.canvas.find_withtag('brick'))
        if num_bricks == 0:
            self.ball.speed = None
            self.draw_text(400, 250, 'You win! You the Breaker of Bricks.')
            self.after(2000, self.reset_game)  # Reset game after delay

        self.after(50, self.game_loop)

    def check_collisions(self):
        ball_coords = self.ball.get_position()
        items = self.canvas.find_overlapping(*ball_coords)
        objects = [self.items[x] for x in items if x in self.items]
        self.ball.collide(objects)

        for obj in objects:
            if isinstance(obj, PowerUp):
                obj.apply(self)
                obj.delete()

    def reset_game(self):
        self.lives = 3
        self.update_lives_text()
        self.setup_game()


if __name__ == '__main__':
    root = tk.Tk()
    root.title('Break those Bricks!')
    game = Game(root)
    game.mainloop()
