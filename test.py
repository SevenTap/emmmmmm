import tkinter as tk
import guaiwu as gw
import xiaodui

class BattleModel:
    def __init__(self):
        self.global_turn = 0
        self.level = 1  # 当前关卡等级
        self.round = 0  # 当前轮数

        self.enemies = gw.generate_monsters(self.level, 4)

        # 使用 xiaodui 生成初始队伍
        self.party = xiaodui.generate_party(4)

        self.max_turns = sum(m["total_turns"] for m in self.party)
        self.pending_actions = {}
        self.victory = False  # 是否胜利
        self.recruit_used = False  # 本轮是否已招募

    def can_act(self, member):
        return (
                self.global_turn < self.max_turns
                and member["used_turns"] < member["total_turns"]
                and not member["acted"]
        )

    def check_victory(self):
        """检查是否胜利（所有怪物血量为0）"""
        return all(e["hp"] == 0 for e in self.enemies)

    def next_round(self):
        """进入下一轮"""
        self.round += 1
        self.global_turn = 0
        
        # 每5轮level上升1
        if self.round % 5 == 0:
            self.level += 1
        
        # 重新生成敌人
        self.enemies = gw.generate_monsters(self.level, 4)
        
        # 重置队伍状态
        for m in self.party:
            m["used_turns"] = 0
            m["acted"] = False
        
        self.pending_actions.clear()
        self.victory = False
        self.recruit_used = False  # 重置招募状态

    def commit_turn(self):
        if not self.pending_actions:
            return

        for pa in self.pending_actions.values():
            pa["enemy"]["hp"] += pa["value"]
            pa["member"]["used_turns"] += 1
            pa["member"]["acted"] = True

        self.global_turn += 1
        self.pending_actions.clear()
        for m in self.party:
            m["acted"] = False
        
        # 检查是否胜利
        if self.check_victory():
            self.victory = True
    def reset_acted_flags(self):
        for m in self.party:
            m["acted"] = False

    def check_victory(self):
        """检查是否胜利（所有怪物血量等于0）"""
        return all(e["hp"] == 0 for e in self.enemies)


# ==================================================
# App
# ==================================================
class BattleApp:
    def __init__(self, root):
        self.root = root
        self.root.geometry("480x600")

        self.model = BattleModel()

        container = tk.Frame(root)
        container.pack(fill="both", expand=True)

        self.battle_view = BattleView(container, self)
        self.skill_view = SkillView(container, self)
        self.recruit_view = xiaodui.RecruitView(container, self, self.model.party)

        self.battle_view.place(in_=container, x=0, y=0, relwidth=1, relheight=1)
        self.skill_view.place(in_=container, x=0, y=0, relwidth=1, relheight=1)
        self.recruit_view.place(in_=container, x=0, y=0, relwidth=1, relheight=1)

        self.show_battle()

    def show_battle(self):
        self.battle_view.refresh()
        self.battle_view.lift()

    def show_skill(self, member):
        self.skill_view.refresh(member)
        self.skill_view.lift()

    def show_recruit(self):
        model = self.model
        if model.recruit_used:
            # 本轮已招募，显示提示
            self.battle_view.action_log.config(text="⚠️ 本回合只能招募一个！")
            return
        self.recruit_view.refresh()
        self.recruit_view.lift()

    def next_round(self):
        """进入下一轮"""
        self.model.next_round()
        self.show_battle()


# ==================================================
# Battle View
# ==================================================
class BattleView(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        self.turn_label = tk.Label(self, font=("微软雅黑", 12, "bold"))
        self.turn_label.pack(anchor="nw", padx=10, pady=5)

        self.enemy_frame = tk.LabelFrame(self, text="敌人")
        self.enemy_frame.pack(fill="x", padx=10, pady=5)

        self.enemy_labels = {}
        for e in self.controller.model.enemies:
            lbl = tk.Label(self.enemy_frame, text="")
            lbl.pack(anchor="w")
            self.enemy_labels[e["id"]] = lbl

        self.action_log = tk.Label(self, text="", justify="left", fg="blue")
        self.action_log.pack(anchor="w", padx=10, pady=5)

        self.party_frame = tk.LabelFrame(self, text="小队成员")
        self.party_frame.pack(fill="x", padx=10, pady=5)

        self.member_buttons = {}  # 使用成员对象作为key

        self.next_turn_btn = tk.Button(self, text="下一回合", command=self.next_turn)
        self.next_turn_btn.pack(pady=5)
        self.recruit_btn = tk.Button(self, text="招募队员", command=self.controller.show_recruit, state="disabled")
        self.recruit_btn.pack(pady=5)# 固定的初始角色列表

    def refresh(self):
        model = self.controller.model

        self.turn_label.config(
            text=f"轮数：{model.round + 1} | 等级：{model.level} | 回合：{model.global_turn} / {model.max_turns}"
        )

        # 更新敌人标签（处理新生成的敌人）
        for w in self.enemy_frame.winfo_children():
            w.destroy()
        self.enemy_labels.clear()
        
        for e in model.enemies:
            lbl = tk.Label(self.enemy_frame, text=f"{e['name']} HP:{e['hp']}")
            lbl.pack(anchor="w")
            self.enemy_labels[e["id"]] = lbl

        # 清除所有成员按钮，重新创建
        for btn in self.member_buttons.values():
            btn.destroy()
        self.member_buttons.clear()
        
        for m in model.party:
            btn = tk.Button(
                self.party_frame,
                text=f"{m['name']} ({m['used_turns']}/{m['total_turns']})",
                width=34,
                command=lambda x=m: self.controller.show_skill(x),
                state="normal" if model.can_act(m) else "disabled",
            )
            btn.pack(pady=3)
            self.member_buttons[id(m)] = btn

        if model.victory:
            text = f"🎉 胜利！第 {model.round + 1} 轮完成！\n点击招募队员或进入下一轮"
            self.next_turn_btn.config(text="进入下一轮")
            self.recruit_btn.config(state="normal")
        elif model.pending_actions:
            text = "待提交：\n" + "\n".join(
                f"{v['member']['name']} → {v['enemy']['name']} 【{v['skill_name']}】 HP{v['value']}"
                for v in model.pending_actions.values()
            )
        else:
            text = "本回合尚未选择行动"

        self.action_log.config(text=text)

    def next_turn(self):
        model = self.controller.model
        
        # 如果胜利，进入下一轮
        if model.victory:
            model.next_round()
            self.next_turn_btn.config(text="下一回合")
            self.recruit_btn.config(state="disabled")
        else:
            model.commit_turn()
        
        self.refresh()


# ==================================================
# Skill View
# ==================================================
class SkillView(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.member = None
        self.selected_enemy = None

        self.title = tk.Label(self, font=("微软雅黑", 12))
        self.title.pack(pady=10)

        self.content = tk.Frame(self)
        self.content.pack()

        tk.Button(self, text="返回战斗", command=self.controller.show_battle).pack(pady=10)

    def refresh(self, member):
        self.member = member
        self.title.config(
            text=f"{member['name']}（{member['used_turns']}/{member['total_turns']}）"
        )

        for w in self.content.winfo_children():
            w.destroy()

        for e in self.controller.model.enemies:
            tk.Button(
                self.content,
                text=e["name"],
                width=20,
                command=lambda x=e: self.show_skills(x),
            ).pack(pady=3)

    def show_skills(self, enemy):
        self.selected_enemy = enemy

        for w in self.content.winfo_children():
            w.destroy()

        tk.Label(self.content, text=f"对 {enemy['name']} 使用技能").pack(pady=5)

        for name, attr, val in self.member["skills"]:
            tk.Button(
                self.content,
                text=f"{name} (HP{val})",
                width=20,
                command=lambda n=name, a=attr, v=val: self.use_skill(n, a, v),
            ).pack(pady=3)

    def use_skill(self, skill_name, attr, value):
        model = self.controller.model
        if not model.can_act(self.member):
            return

        # 特殊技能：hp+666 直接获胜
        if attr == "hp" and value == 666:
            model.victory = True
            self.controller.show_battle()
            return

        model.pending_actions[id(self.member)] = {
            "member": self.member,
            "enemy": self.selected_enemy,
            "skill_name": skill_name,
            "attr": attr,
            "value": value,
        }
        self.member["acted"] = True

        self.controller.show_battle()


# ==================================================
if __name__ == "__main__":
    root = tk.Tk()
    BattleApp(root)
    root.mainloop()