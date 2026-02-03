import math
import random
import tkinter as tk
from dataclasses import dataclass


WIDTH = 800
HEIGHT = 600
BG_COLOR = "#101820"
AGENT_COLOR = "#4dd2ff"
GOAL_COLOR = "#ffb347"
OBSTACLE_COLOR = "#ff6b6b"
FPS = 60

AGENT_RADIUS = 8
AGENT_MAX_SPEED = 90.0
NEIGHBOR_DIST = 60.0
AVOID_STRENGTH = 1.4
GOAL_FORCE = 1.0
OBSTACLE_AVOID_DIST = 45.0


@dataclass
class Agent:
    x: float
    y: float
    vx: float
    vy: float
    goal_x: float
    goal_y: float
    radius: float = AGENT_RADIUS


@dataclass
class Obstacle:
    x: float
    y: float
    radius: float


class RVO2Demo:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("RVO2避障演示")
        self.canvas = tk.Canvas(root, width=WIDTH, height=HEIGHT, bg=BG_COLOR, highlightthickness=0)
        self.canvas.pack()
        self.canvas.bind("<Button-1>", self.handle_canvas_click)

        self.status = tk.StringVar(value="暂停")
        self.add_mode = tk.StringVar(value="")
        self.show_velocity = tk.BooleanVar(value=True)
        control_frame = tk.Frame(root)
        control_frame.pack(fill=tk.X, padx=8, pady=6)
        self.start_button = tk.Button(control_frame, text="开始", command=self.toggle)
        self.start_button.pack(side=tk.LEFT)
        tk.Button(control_frame, text="重置", command=self.reset).pack(side=tk.LEFT, padx=6)
        tk.Button(control_frame, text="添加Agent", command=self.set_add_agent).pack(side=tk.LEFT, padx=6)
        tk.Button(control_frame, text="添加障碍物", command=self.set_add_obstacle).pack(side=tk.LEFT)
        tk.Button(control_frame, text="取消添加", command=self.clear_add_mode).pack(side=tk.LEFT, padx=6)
        tk.Checkbutton(
            control_frame,
            text="显示速度",
            variable=self.show_velocity,
            command=self.update_velocity_visibility,
        ).pack(side=tk.LEFT)
        tk.Label(control_frame, textvariable=self.status).pack(side=tk.LEFT, padx=12)

        self.running = False
        self.last_time = None
        self.obstacles = [
            Obstacle(WIDTH * 0.5, HEIGHT * 0.5, 50),
            Obstacle(WIDTH * 0.25, HEIGHT * 0.35, 35),
            Obstacle(WIDTH * 0.75, HEIGHT * 0.65, 35),
        ]
        self.obstacle_shapes = []
        self.agents = []
        self.agent_shapes = []
        self.velocity_shapes = []
        self.goal_shapes = []
        self.reset()
        self.root.after(int(1000 / FPS), self.update)

    def toggle(self) -> None:
        self.running = not self.running
        self.status.set("运行中" if self.running else "暂停")
        self.start_button.config(text="暂停" if self.running else "开始")

    def reset(self) -> None:
        self.agents = []
        self.canvas.delete("all")
        self.obstacle_shapes = []
        self.agent_shapes = []
        self.velocity_shapes = []
        self.goal_shapes = []

        for obstacle in self.obstacles:
            shape = self.canvas.create_oval(
                obstacle.x - obstacle.radius,
                obstacle.y - obstacle.radius,
                obstacle.x + obstacle.radius,
                obstacle.y + obstacle.radius,
                fill=OBSTACLE_COLOR,
                outline="",
            )
            self.obstacle_shapes.append(shape)

        for _ in range(18):
            x, y = self.random_position()
            goal_x, goal_y = self.random_position(avoid=(x, y))
            agent = Agent(x=x, y=y, vx=0.0, vy=0.0, goal_x=goal_x, goal_y=goal_y)
            self.agents.append(agent)
            shape = self.canvas.create_oval(
                x - agent.radius,
                y - agent.radius,
                x + agent.radius,
                y + agent.radius,
                fill=AGENT_COLOR,
                outline="",
            )
            self.agent_shapes.append(shape)
            velocity_shape = self.canvas.create_line(
                x,
                y,
                x + 1,
                y,
                fill=GOAL_COLOR,
                arrow=tk.LAST,
                width=2,
            )
            self.velocity_shapes.append(velocity_shape)
            goal_shape = self.canvas.create_oval(
                goal_x - 4,
                goal_y - 4,
                goal_x + 4,
                goal_y + 4,
                outline=GOAL_COLOR,
                width=2,
            )
            self.goal_shapes.append(goal_shape)

        self.running = False
        self.status.set("暂停")
        self.start_button.config(text="开始")
        self.update_velocity_visibility()

    def set_add_agent(self) -> None:
        self.add_mode.set("agent")

    def set_add_obstacle(self) -> None:
        self.add_mode.set("obstacle")

    def clear_add_mode(self) -> None:
        self.add_mode.set("")

    def update_velocity_visibility(self) -> None:
        state = "normal" if self.show_velocity.get() else "hidden"
        for shape in self.velocity_shapes:
            self.canvas.itemconfigure(shape, state=state)

    def handle_canvas_click(self, event: tk.Event) -> None:
        mode = self.add_mode.get()
        if mode == "agent":
            self.add_agent(float(event.x), float(event.y))
        elif mode == "obstacle":
            self.add_obstacle(float(event.x), float(event.y))

    def add_agent(self, x: float, y: float) -> None:
        if self.is_inside_obstacle(x, y, AGENT_RADIUS + 4):
            return
        goal_x, goal_y = self.random_position(avoid=(x, y))
        agent = Agent(x=x, y=y, vx=0.0, vy=0.0, goal_x=goal_x, goal_y=goal_y)
        self.agents.append(agent)
        shape = self.canvas.create_oval(
            x - agent.radius,
            y - agent.radius,
            x + agent.radius,
            y + agent.radius,
            fill=AGENT_COLOR,
            outline="",
        )
        self.agent_shapes.append(shape)
        velocity_shape = self.canvas.create_line(
            x,
            y,
            x + 1,
            y,
            fill=GOAL_COLOR,
            arrow=tk.LAST,
            width=2,
        )
        self.velocity_shapes.append(velocity_shape)
        goal_shape = self.canvas.create_oval(
            goal_x - 4,
            goal_y - 4,
            goal_x + 4,
            goal_y + 4,
            outline=GOAL_COLOR,
            width=2,
        )
        self.goal_shapes.append(goal_shape)
        self.update_velocity_visibility()

    def add_obstacle(self, x: float, y: float) -> None:
        if self.is_inside_obstacle(x, y, 10):
            return
        obstacle = Obstacle(x=x, y=y, radius=35)
        self.obstacles.append(obstacle)
        shape = self.canvas.create_oval(
            obstacle.x - obstacle.radius,
            obstacle.y - obstacle.radius,
            obstacle.x + obstacle.radius,
            obstacle.y + obstacle.radius,
            fill=OBSTACLE_COLOR,
            outline="",
        )
        self.obstacle_shapes.append(shape)

    def random_position(self, avoid=None) -> tuple[float, float]:
        while True:
            x = random.uniform(40, WIDTH - 40)
            y = random.uniform(40, HEIGHT - 40)
            if avoid and math.hypot(x - avoid[0], y - avoid[1]) < 120:
                continue
            if self.is_inside_obstacle(x, y, AGENT_RADIUS + 10):
                continue
            return x, y

    def is_inside_obstacle(self, x: float, y: float, padding: float = 0.0) -> bool:
        for obstacle in self.obstacles:
            if math.hypot(x - obstacle.x, y - obstacle.y) <= obstacle.radius + padding:
                return True
        return False

    def update(self) -> None:
        if self.running:
            dt = 1.0 / FPS
            self.step(dt)
        self.root.after(int(1000 / FPS), self.update)

    def step(self, dt: float) -> None:
        for idx, agent in enumerate(self.agents):
            goal_dx = agent.goal_x - agent.x
            goal_dy = agent.goal_y - agent.y
            goal_dist = math.hypot(goal_dx, goal_dy)
            if goal_dist < 18:
                agent.goal_x, agent.goal_y = self.random_position()
                self.canvas.coords(
                    self.goal_shapes[idx],
                    agent.goal_x - 4,
                    agent.goal_y - 4,
                    agent.goal_x + 4,
                    agent.goal_y + 4,
                )
                goal_dx = agent.goal_x - agent.x
                goal_dy = agent.goal_y - agent.y
                goal_dist = math.hypot(goal_dx, goal_dy)

            desired_vx = (goal_dx / goal_dist) * AGENT_MAX_SPEED if goal_dist else 0.0
            desired_vy = (goal_dy / goal_dist) * AGENT_MAX_SPEED if goal_dist else 0.0

            avoid_x, avoid_y = 0.0, 0.0
            for j, other in enumerate(self.agents):
                if j == idx:
                    continue
                dx = agent.x - other.x
                dy = agent.y - other.y
                dist = math.hypot(dx, dy)
                if dist < 1e-5 or dist > NEIGHBOR_DIST:
                    continue
                strength = (NEIGHBOR_DIST - dist) / NEIGHBOR_DIST
                avoid_x += (dx / dist) * strength
                avoid_y += (dy / dist) * strength

            for obstacle in self.obstacles:
                dx = agent.x - obstacle.x
                dy = agent.y - obstacle.y
                dist = math.hypot(dx, dy)
                if dist < 1e-5:
                    continue
                min_dist = obstacle.radius + OBSTACLE_AVOID_DIST
                if dist < min_dist:
                    strength = (min_dist - dist) / min_dist
                    avoid_x += (dx / dist) * strength * 1.5
                    avoid_y += (dy / dist) * strength * 1.5

            combined_vx = GOAL_FORCE * desired_vx + AVOID_STRENGTH * AGENT_MAX_SPEED * avoid_x
            combined_vy = GOAL_FORCE * desired_vy + AVOID_STRENGTH * AGENT_MAX_SPEED * avoid_y

            speed = math.hypot(combined_vx, combined_vy)
            if speed > AGENT_MAX_SPEED:
                combined_vx = (combined_vx / speed) * AGENT_MAX_SPEED
                combined_vy = (combined_vy / speed) * AGENT_MAX_SPEED

            agent.vx = combined_vx
            agent.vy = combined_vy

        for idx, agent in enumerate(self.agents):
            agent.x += agent.vx * dt
            agent.y += agent.vy * dt
            agent.x = min(max(agent.x, agent.radius), WIDTH - agent.radius)
            agent.y = min(max(agent.y, agent.radius), HEIGHT - agent.radius)
            self.canvas.coords(
                self.agent_shapes[idx],
                agent.x - agent.radius,
                agent.y - agent.radius,
                agent.x + agent.radius,
                agent.y + agent.radius,
            )
            speed = math.hypot(agent.vx, agent.vy)
            if speed > 1e-3:
                arrow_len = 0.35 * AGENT_MAX_SPEED
                arrow_dx = (agent.vx / speed) * arrow_len
                arrow_dy = (agent.vy / speed) * arrow_len
                self.canvas.coords(
                    self.velocity_shapes[idx],
                    agent.x,
                    agent.y,
                    agent.x + arrow_dx,
                    agent.y + arrow_dy,
                )
            else:
                self.canvas.coords(
                    self.velocity_shapes[idx],
                    agent.x,
                    agent.y,
                    agent.x + 1,
                    agent.y,
                )


if __name__ == "__main__":
    root = tk.Tk()
    root.resizable(False, False)
    demo = RVO2Demo(root)
    root.mainloop()
