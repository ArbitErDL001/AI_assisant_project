const ocean = document.getElementById("ocean");

if (ocean) {
    const scoreDisplay = document.getElementById("score");
    const feeder = document.getElementById("feeder");
    const fishElements = [...ocean.querySelectorAll(".fish")];
    const fishList = [];
    const foods = [];
    let score = 0;
    let animationFrame = null;

    function getOceanSize() {
        return { width: ocean.clientWidth, height: ocean.clientHeight };
    }

    function randomPosition(min, max) {
        return min + Math.random() * Math.max(0, max - min);
    }

    class Fish {
        constructor(element) {
            this.element = element;
            this.speed = 0.6 + Math.random() * 1.2;
            this.direction = Math.random() < 0.5 ? -1 : 1;
            this.isEating = false;
            this.idleTime = 0;
            this.setRandomPosition();
            this.idleTarget = { x: this.x, y: this.y };
            this.element.classList.add("idle");
            this.updatePosition();
        }

        setRandomPosition() {
            const size = getOceanSize();
            this.x = randomPosition(24, size.width - 64);
            this.y = randomPosition(48, size.height - 64);
        }

        updatePosition() {
            this.element.style.left = `${this.x}px`;
            this.element.style.top = `${this.y}px`;
            this.element.style.transform = `scaleX(${this.direction})`;
        }

        findClosestFood() {
            let closestFood = null;
            let closestDistance = Infinity;

            for (const food of foods) {
                if (food.eaten) continue;
                const distance = Math.hypot(food.x - this.x, food.y - this.y);
                if (distance < closestDistance) {
                    closestDistance = distance;
                    closestFood = food;
                }
            }

            return closestFood;
        }

        moveToward(targetX, targetY, speed) {
            const dx = targetX - this.x;
            const dy = targetY - this.y;
            const distance = Math.hypot(dx, dy);

            if (distance <= 4) return true;

            this.x += (dx / distance) * speed;
            this.y += (dy / distance) * speed;
            this.direction = dx >= 0 ? 1 : -1;
            return false;
        }

        update() {
            if (this.isEating) return;

            const food = this.findClosestFood();
            if (food) {
                this.element.classList.remove("idle");
                if (this.moveToward(food.x, food.y, this.speed * 2)) {
                    this.eatFood(food);
                }
            } else {
                this.element.classList.add("idle");
                this.idleTime += 1;
                if (
                    this.idleTime > 120 ||
                    this.moveToward(this.idleTarget.x, this.idleTarget.y, this.speed * 0.4)
                ) {
                    const size = getOceanSize();
                    this.idleTarget = {
                        x: randomPosition(24, size.width - 64),
                        y: randomPosition(48, size.height - 64),
                    };
                    this.idleTime = 0;
                }
            }

            const size = getOceanSize();
            this.x = Math.max(16, Math.min(size.width - 40, this.x));
            this.y = Math.max(28, Math.min(size.height - 40, this.y));
            this.updatePosition();
        }

        eatFood(food) {
            if (food.eaten) return;

            food.eaten = true;
            this.isEating = true;

            const effect = document.createElement("span");
            effect.className = "eat-effect";
            effect.textContent = "😋";
            effect.style.left = `${food.x}px`;
            effect.style.top = `${food.y}px`;
            ocean.appendChild(effect);
            food.element.remove();

            score += 1;
            scoreDisplay.value = String(score);
            scoreDisplay.textContent = String(score);

            window.setTimeout(() => {
                effect.remove();
                this.isEating = false;
                const index = foods.indexOf(food);
                if (index !== -1) foods.splice(index, 1);
            }, 500);
        }
    }

    class Food {
        constructor(x, y) {
            this.x = x;
            this.y = y;
            this.sinkSpeed = 0.35 + Math.random() * 0.35;
            this.wobble = 0;
            this.eaten = false;

            this.element = document.createElement("span");
            this.element.className = "food";
            this.element.textContent = "🍞";
            this.element.setAttribute("aria-hidden", "true");
            this.updatePosition();
            ocean.appendChild(this.element);

            const splash = document.createElement("span");
            splash.className = "splash";
            splash.style.left = `${x - 15}px`;
            splash.style.top = `${y - 15}px`;
            splash.setAttribute("aria-hidden", "true");
            ocean.appendChild(splash);
            window.setTimeout(() => splash.remove(), 500);
        }

        updatePosition() {
            this.element.style.left = `${this.x}px`;
            this.element.style.top = `${this.y}px`;
        }

        update() {
            if (this.eaten) return;

            this.y += this.sinkSpeed;
            this.wobble += 0.12;
            this.x += Math.sin(this.wobble) * 0.6;

            const size = getOceanSize();
            if (this.y >= size.height - 20) {
                this.eaten = true;
                this.element.remove();
                const index = foods.indexOf(this);
                if (index !== -1) foods.splice(index, 1);
                return;
            }

            this.updatePosition();
        }
    }

    function gameLoop() {
        if (ocean.closest(".offline-game").hidden) {
            animationFrame = null;
            return;
        }

        fishList.forEach((fish) => fish.update());
        foods.forEach((food) => food.update());
        animationFrame = window.requestAnimationFrame(gameLoop);
    }

    function startGame() {
        if (fishList.length === 0) {
            fishElements.forEach((element) => fishList.push(new Fish(element)));
        }
        if (animationFrame === null) {
            animationFrame = window.requestAnimationFrame(gameLoop);
        }
    }

    ocean.addEventListener("click", (event) => {
        if (foods.filter((food) => !food.eaten).length >= 12) return;

        const bounds = ocean.getBoundingClientRect();
        const x = event.clientX - bounds.left;
        const y = event.clientY - bounds.top;
        if (y > 20) foods.push(new Food(x, y));
    });

    ocean.addEventListener("pointermove", (event) => {
        const bounds = ocean.getBoundingClientRect();
        feeder.style.left = `${event.clientX - bounds.left}px`;
        feeder.style.top = `${event.clientY - bounds.top}px`;
    });

    ocean.addEventListener("pointerenter", () => {
        feeder.style.display = "block";
    });

    ocean.addEventListener("pointerleave", () => {
        feeder.style.display = "none";
    });

    window.addEventListener("offline", startGame);
    if (!navigator.onLine) startGame();
}
