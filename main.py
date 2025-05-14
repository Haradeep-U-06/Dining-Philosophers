import pygame
import math
import threading
import time
import random
from collections import deque

pygame.init()

# Constants
WIDTH, HEIGHT = 1200, 800
CENTER = (WIDTH // 2, HEIGHT // 2)
RADIUS = 200
NUM_PHILOSOPHERS = 5
TIMEOUT = 5  # seconds for fork pickup timeout

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
FORK_AVAILABLE = (150, 150, 150)
FORK_USED = (0, 255, 0)
FORK_TEXT_COLOR = (255, 255, 0)

# Philosopher states
THINKING = 0
HUNGRY = 1
EATING = 2
DEADLOCK = 3
STATE_NAMES = {
    THINKING: "Thinking",
    HUNGRY: "Hungry",
    EATING: "Eating",
    DEADLOCK: "Deadlock!"
}
STATE_COLORS = {
    THINKING: (0, 0, 255),
    HUNGRY: (255, 165, 0),
    EATING: (0, 255, 0),
    DEADLOCK: (255, 0, 0)
}

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Dining Philosophers Problem")

font = pygame.font.SysFont('Arial', 16)
big_font = pygame.font.SysFont('Arial', 24)
small_font = pygame.font.SysFont('Arial', 12)

class Monitor:
    def __init__(self):
        self.state = [THINKING] * NUM_PHILOSOPHERS
        self.forks_in_use = [None] * NUM_PHILOSOPHERS
        self.condition = threading.Condition()
        self.log = deque(maxlen=20)
        self.log_lock = threading.Lock()
        self.running = True

    def log_event(self, message):
        with self.log_lock:
            self.log.append(f"{time.strftime('%H:%M:%S')}: {message}")

    def test(self, i):
        left = (i + NUM_PHILOSOPHERS - 1) % NUM_PHILOSOPHERS
        right = i
        if (self.state[i] == HUNGRY and
            self.forks_in_use[left] is None and
            self.forks_in_use[right] is None):
            self.state[i] = EATING
            self.forks_in_use[left] = i
            self.forks_in_use[right] = i
            self.condition.notify_all()
            self.log_event(f"P{i} eating (F{left}, F{right})")

    def pickup_forks(self, i):
        with self.condition:
            if not self.running:
                return False
            self.state[i] = HUNGRY
            self.log_event(f"P{i} hungry")
            self.test(i)
            start_time = time.time()
            while self.state[i] != EATING and self.running:
                remaining = TIMEOUT - (time.time() - start_time)
                if remaining <= 0:
                    self.state[i] = DEADLOCK
                    self.log_event(f"P{i} timed out!")
                    return False
                self.condition.wait(remaining)
            return self.running and self.state[i] == EATING

    def putdown_forks(self, i):
        with self.condition:
            left = (i + NUM_PHILOSOPHERS - 1) % NUM_PHILOSOPHERS
            right = i
            self.state[i] = THINKING
            self.forks_in_use[left] = None
            self.forks_in_use[right] = None
            self.log_event(f"P{i} stopped eating")
            self.test((i - 1 + NUM_PHILOSOPHERS) % NUM_PHILOSOPHERS)
            self.test((i + 1) % NUM_PHILOSOPHERS)

    def stop(self):
        with self.condition:
            self.running = False
            self.condition.notify_all()

def philosopher(id, monitor):
    while monitor.running:
        monitor.log_event(f"P{id} thinking")
        time.sleep(random.uniform(1, 3))
        if not monitor.running:
            break
        if monitor.pickup_forks(id):
            time.sleep(random.uniform(1, 3))
            monitor.putdown_forks(id)

def draw_scene(monitor, button_rect):
    screen.fill((25, 25, 25))

    pygame.draw.circle(screen, (139, 69, 19), CENTER, RADIUS + 50)
    positions = []
    for i in range(NUM_PHILOSOPHERS):
        angle = 2 * math.pi * i / NUM_PHILOSOPHERS - math.pi / 2
        x = CENTER[0] + RADIUS * math.cos(angle)
        y = CENTER[1] + RADIUS * math.sin(angle)
        positions.append((int(x), int(y)))

    for i in range(NUM_PHILOSOPHERS):
        p1 = positions[i]
        p2 = positions[(i + 1) % NUM_PHILOSOPHERS]
        fx = (p1[0] + p2[0]) // 2
        fy = (p1[1] + p2[1]) // 2
        used_by = monitor.forks_in_use[i]
        color = FORK_USED if used_by is not None else FORK_AVAILABLE
        pygame.draw.rect(screen, color, (fx - 5, fy - 20, 10, 40))
        fork_label = font.render(f"F{i}", True, WHITE)
        screen.blit(fork_label, (fx - 10, fy + 30))
        if used_by is not None:
            usage = small_font.render(f"P{used_by}", True, FORK_TEXT_COLOR)
            screen.blit(usage, (fx - 10, fy - 40))

    for i, pos in enumerate(positions):
        state = monitor.state[i]
        color = STATE_COLORS[state]
        pygame.draw.circle(screen, color, pos, 40)
        label = big_font.render(f"P{i}", True, BLACK)
        screen.blit(label, (pos[0] - 10, pos[1] - 10))
        pygame.draw.ellipse(screen, WHITE, (pos[0] - 50, pos[1] - 70, 100, 40))
        state_text = font.render(STATE_NAMES[state], True, BLACK)
        screen.blit(state_text, (pos[0] - 40, pos[1] - 60))
        if state == EATING:
            left = (i + NUM_PHILOSOPHERS - 1) % NUM_PHILOSOPHERS
            right = i
            fork_text = small_font.render(f"F{left} & F{right}", True, WHITE)
            screen.blit(fork_text, (pos[0] - 30, pos[1] + 50))

    panel_x = WIDTH // 2 + RADIUS + 80
    pygame.draw.rect(screen, BLACK, (panel_x, 10, 360, HEIGHT - 120))
    log_y = 20
    with monitor.log_lock:
        for msg in list(monitor.log)[-20:]:
            log_text = font.render(msg, True, WHITE)
            screen.blit(log_text, (panel_x + 10, log_y))
            log_y += 20

    btn_text = "Stop" if monitor.running else "Start"
    btn_label = big_font.render(btn_text, True, WHITE)
    button_rect = btn_label.get_rect(center=(WIDTH // 2, HEIGHT - 50))
    pygame.draw.rect(screen, (0, 100, 200), button_rect.inflate(20, 10))
    screen.blit(btn_label, button_rect)

    pygame.display.flip()
    return button_rect

def main():
    monitor = Monitor()
    philosophers = []
    for i in range(NUM_PHILOSOPHERS):
        t = threading.Thread(target=philosopher, args=(i, monitor))
        t.start()
        philosophers.append(t)

    clock = pygame.time.Clock()
    button_rect = None

    try:
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    raise KeyboardInterrupt
                if event.type == pygame.MOUSEBUTTONDOWN and button_rect:
                    if button_rect.collidepoint(event.pos):
                        if monitor.running:
                            monitor.stop()
                        else:
                            monitor.running = True
                            for i in range(NUM_PHILOSOPHERS):
                                if monitor.state[i] == DEADLOCK:
                                    monitor.state[i] = THINKING
                            philosophers = []
                            for i in range(NUM_PHILOSOPHERS):
                                t = threading.Thread(target=philosopher, args=(i, monitor))
                                t.start()
                                philosophers.append(t)

            button_rect = draw_scene(monitor, button_rect)
            clock.tick(30)

    except KeyboardInterrupt:
        monitor.stop()
        for t in philosophers:
            t.join()
        pygame.quit()

if __name__ == "__main__":
    main()