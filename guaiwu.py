import random
import time

hp_player = None
def generate_monster_count(max_count):
    return random.randint(1, max_count)
def calculate_monster_hp(level):
    if level >= 10:
        base_hp = random.randint(50, 150) + 5
    else:
        base_hp = random.randint(20, 50) + 5
    return base_hp + level
def generate_monsters(level, max_count):
    monsters = []
    monster_count = generate_monster_count(max_count)
    for i in range(monster_count):
        monster = {
            "id": i + 1,
            "name": f"怪物{i+1}",
            "hp": calculate_monster_hp(level)
        }
        monsters.append(monster)
    return monsters
def main():
    level = 10
    hp = [0, 0, 0, 0]  # 最多4个怪物
    random.seed(time.time())

    monsters = generate_monsters(level, 4)
    print(f"怪物数量: {len(monsters)}")

    for i in range(len(monsters)):
        hp[i] = monsters[i]["hp"]

    print("怪物血量: ", end="")
    for i in range(len(monsters)):
        print(f"{monsters[i]['name']}: {hp[i]}HP ", end="")
    print()
if __name__ == "__main__":
    main()
