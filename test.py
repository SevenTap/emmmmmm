import tkinter as tk
import guaiwu as gw
import xiaodui
# ==================================================
# ==================================================
class BattleModel:
    def __init__(self):
        self.global_turn = 0
        self.level = 1  # 当前关卡等级
        self.round = 0  # 当前轮数

        self.enemies = gw.generate_monsters(self.level, 4)

        # 使用 xiaodui 生成初始队伍
        self.party = xiaodui.generate_party(4)
        self.recruit_candidates = None
        self.max_turns = sum(m["total_turns"] for m in self.party)
        self.pending_actions = {}
        self.victory = False  # 是否胜利
        self.recruit_used = False  # 本轮是否已招募
        self.damage_multipliers = {}  # 存储伤害倍率，key为成员id
    def can_act(self, member):
        return (
                self.global_turn < self.max_turns
                and member["used_turns"] < member["total_turns"]
                and not member["acted"]
        )

    def check_victory(self):
        return all(e["hp"] == 0 for e in self.enemies)

    def next_round(self):
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
        self.recruit_candidates = None
        self.pending_actions.clear()
        self.victory = False
        self.recruit_used = False  # 重置招募状态
        self.damage_multipliers.clear()  # 重置伤害倍率
        
    def commit_turn(self):
        if not self.pending_actions:
            return

        import math
        
        # 先处理所有伤害倍率技能，确保倍率在伤害结算前生效
        for pa in self.pending_actions.values():
            if pa["attr"] == "damage_multiplier":
                target_id = id(pa["target"])
                self.damage_multipliers[target_id] = self.damage_multipliers.get(target_id, 1) * pa["value"]
                pa["member"]["used_turns"] += 1
                pa["member"]["acted"] = True

        # 再处理所有伤害/治疗技能
        for pa in self.pending_actions.values():
            attr = pa["attr"]
            member = pa["member"]

            if attr == "hp":
                # 普通伤害/治疗技能
                damage = pa["value"]
                # 如果有伤害倍率，应用倍率
                member_id = id(member)
                if member_id in self.damage_multipliers:
                    damage = math.floor(damage * self.damage_multipliers[member_id])
                    del self.damage_multipliers[member_id]  # 重置倍率
                pa["target"]["hp"] += damage
                member["used_turns"] += 1
                member["acted"] = True
            
            elif attr == "hp_div":
                # 除法伤害技能 - 对敌人造成 HP/除数（向上取整）
                target = pa["target"]
                damage = math.ceil(target["hp"] / pa["value"])
                target["hp"] = damage
                member["used_turns"] += 1
                member["acted"] = True

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
        return all(e["hp"] == 0 for e in self.enemies)
# ==================================================
# ==================================================
class BattleApp:
    def __init__(self, root):
        self.root = root
        self.root.geometry("480x600")
        self.model = BattleModel()
        container = tk.Frame(root)
        container.pack(fill="both", expand=True)
        self.start_view = StartView(container, self)
        self.battle_view = BattleView(container, self)
        self.skill_view = SkillView(container, self)
        self.recruit_view = xiaodui.RecruitView(container, self, self.model.party)
        self.battle_view.place(in_=container, x=0, y=0, relwidth=1, relheight=1)
        self.skill_view.place(in_=container, x=0, y=0, relwidth=1, relheight=1)
        self.recruit_view.place(in_=container, x=0, y=0, relwidth=1, relheight=1)
        self.start_view.place(in_=container, x=0, y=0, relwidth=1, relheight=1)
        self.show_start()
    def show_start(self):
        self.start_view.lift()
    def start_game(self):
        """开始游戏"""
        self.model = BattleModel()
        self.recruit_view = xiaodui.RecruitView(
            self.battle_view.master, self, self.model.party
        )
        self.recruit_view.place(in_=self.battle_view.master, x=0, y=0, relwidth=1, relheight=1)
        self.show_battle()
    def show_battle(self):
        self.battle_view.refresh()
        self.battle_view.lift()

    def show_skill(self, member):
        self.skill_view.refresh(member)
        self.skill_view.lift()

    def show_recruit(self):
        model = self.model
        if model.recruit_candidates is None:
            model.recruit_candidates = xiaodui.recruit_candidates(model.party)
        if model.recruit_used:
            # 本轮已招募，显示提示
            self.battle_view.action_log.config(text="本回合只能招募一个！")
            return

        self.recruit_view.refresh(model.recruit_candidates)
        self.recruit_view.lift()

    def next_round(self):
        self.model.next_round()
        self.show_battle()
# ==================================================
# ==================================================
class StartView(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        start_btn = tk.Button(
            self,
            text="开始游戏",
            font=("微软雅黑", 16, "bold"),
            width=20,
            height=2,
            command=self.controller.start_game,
            relief="raised",
            bd=3
        )
        start_btn.pack(pady=40)
        notice_frame = tk.LabelFrame(
            self,
            text="公告",
            font=("微软雅黑", 12, "bold"),
            bd=2,
        )
        notice_frame.pack(fill="x", padx=30, pady=10)
        notice_text = ("游戏就是简单rpg小游戏\n值得注意是的怪物血量必须等于0才算是杀死\n"
                       "更新内容：\n")
        notice_label = tk.Label(
            notice_frame,
            text=notice_text,
            font=("微软雅黑", 10),
            justify="left"
        )
        notice_label.pack(padx=15, pady=10)
# ==================================================
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
        self.recruit_btn = tk.Button(self, text="招募队员", command=self.controller.show_recruit, state="disabled" )
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
            text = f" 胜利！第 {model.round + 1} 轮完成！\n点击招募队员或进入下一轮"
            self.next_turn_btn.config(text="进入下一轮")
            self.recruit_btn.config(state="normal")
        elif model.pending_actions:
            action_lines = []
            for v in model.pending_actions.values():
                if v["attr"] == "hp":
                    action_lines.append(
                    f"{v['member']['name']} → {v['target']['name']} 【{v['skill_name']}】 HP{v['value']}"
                )
                elif v["attr"] == "damage_multiplier":
                    action_lines.append(
                    f"{v['member']['name']} → {v['target']['name']} 【{v['skill_name']}】 伤害x{v['value']}"
                )
                elif v["attr"] == "hp_div":
                    action_lines.append(
                    f"{v['member']['name']} → {v['target']['name']} 【{v['skill_name']}】 HP降至1/{v['value']}倍"
                )
            text = "待提交：\n" + "\n".join(action_lines)
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
# ==================================================
class SkillView(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.member = None
        self.selected_target = None
        self.target_is_enemy = True

        self.title = tk.Label(self, font=("微软雅黑", 12))
        self.title.pack(pady=10)

        self.content = tk.Frame(self)
        self.content.pack()

        tk.Button(self, text="返回战斗", command=self.controller.show_battle).pack(pady=10)

    def refresh(self, member):
        self.member = member
        self.selected_skill = None  # 重置选中的技能
        self.title.config(
            text=f"{member['name']}（{member['used_turns']}/{member['total_turns']}）"
        )

        for w in self.content.winfo_children():
            w.destroy()

        # 先显示技能选择
        tk.Label(self.content, text="选择技能").pack(pady=5)
        for name, attr, val in member["skills"]:
            if attr == "damage_multiplier":
                btn_text = f"{name} (伤害x{val})"
            elif attr == "hp_div":
                btn_text = f"{name} (HP/{val})"
            else:
                btn_text = f"{name} (HP{val})"

            tk.Button(
                self.content,
                text=btn_text,
                width=25,
                command=lambda n=name, a=attr, v=val: self.select_skill(n, a, v),
            ).pack(pady=3)

    def select_skill(self, skill_name, attr, value):
        """选择技能后，根据技能类型显示目标选择"""
        self.selected_skill = {
            "name": skill_name,
            "attr": attr,
            "value": value
        }

        for w in self.content.winfo_children():
            w.destroy()

        # 根据技能类型显示目标
        if attr == "damage_multiplier":
            # 增幅技能，选择队友
            tk.Label(self.content, text=f"选择要增强的队友【{skill_name}】").pack(pady=5)
            for m in self.controller.model.party:
                if m != self.member:
                    multiplier_info = f" (倍率{self.controller.model.damage_multipliers[id(m)]})" if id(m) in self.controller.model.damage_multipliers else ""
                    tk.Button(
                        self.content,
                        text=f"{m['name']}{multiplier_info}",
                        width=25,
                        command=lambda x=m: self.confirm_target(x),
                    ).pack(pady=3)
        else:
            # 攻击/治疗技能，选择敌人
            tk.Label(self.content, text=f"选择目标敌人【{skill_name}】").pack(pady=5)
            for e in self.controller.model.enemies:
                tk.Button(
                    self.content,
                    text=e["name"],
                    width=25,
                    command=lambda x=e: self.confirm_target(x),
                ).pack(pady=3)
        
        # 添加返回按钮
        tk.Button(
            self.content,
            text="返回选择技能",
            width=20,
            command=lambda: self.refresh(self.member),
        ).pack(pady=5)

    def confirm_target(self, target):
        """确认目标后使用技能"""
        model = self.controller.model
        if not model.can_act(self.member):
            return

        skill = self.selected_skill
        
        # 特殊技能：hp+666 直接获胜
        if skill["attr"] == "hp" and skill["value"] == 666:
            model.victory = True
            self.controller.show_battle()
            return

        model.pending_actions[id(self.member)] = {
            "member": self.member,
            "target": target,
            "target_is_enemy": skill["attr"] != "damage_multiplier",
            "skill_name": skill["name"],
            "attr": skill["attr"],
            "value": skill["value"],
        }

        self.controller.show_battle()
# ==================================================
if __name__ == "__main__":
    i=0
    root = tk.Tk()
    BattleApp(root)
    root.mainloop()
    print("c")