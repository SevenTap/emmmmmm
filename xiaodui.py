import random
import tkinter as tk
# 角色职业模板库
# 技能数值使用区间元组 (min, max) 表示浮动范围
CHARACTER_TEMPLATES = [
    {"name": "法师", "total_turns": 4, "skills": [("火球", "hp", (-30, -10)),("火焰剑", "damage_multiplier", (2, 4))]},
    {"name": "牧师", "total_turns": 4, "skills": [("圣光洗礼", "hp_div", 3),("圣光加护", "damage_multiplier", -1)]},
    {"name": "刺客", "total_turns": 5, "skills": [("背刺", "hp", (-18, -8))]},
    {"name": "弓箭手", "total_turns": 4, "skills": [("射击", "hp", (-20, -9))]},
    {"name": "圣骑士", "total_turns": 3, "skills": [("盾击", "hp", (-12, -5)),("圣光打击", "hp_div", (1, 4))]},
    {"name": "盗贼", "total_turns": 5, "skills": [("缠绕", "hp", (9, 15))]},
]

# 固定的初始角色
# 固定的初始角色列表
INITIAL_CHARACTERS = [
    {"name": "x战士", "total_turns": 5, "skills": [("猛击", "hp", -15),("羁绊", "hp", +666)]},
    {"name": "神官", "total_turns": 5, "skills": [("神力", "hp", +1),("神力", "hp", +2),("神力", "hp", +3)]}
]

def create_member(template):
    # 处理技能数值，将区间转换为随机数值
    skills = []
    for skill_name, attr, value in template["skills"]:
        if isinstance(value, tuple) and len(value) == 2:
            # 如果是区间元组，随机生成数值
            min_val, max_val = value
            random_value = random.randint(min_val, max_val)
            skills.append((skill_name, attr, random_value))
        else:
            # 如果是固定数值，直接使用
            skills.append((skill_name, attr, value))
    
    return {
        "name": template["name"],
        "total_turns": template["total_turns"],
        "used_turns": 0,
        "acted": False,
        "skills": skills
    }

def generate_party(max_members=4):
    party = []

    # 添加所有初始角色
    for char_template in INITIAL_CHARACTERS:
        party.append(create_member(char_template))
    return party

def recruit_candidates(party):
    candidate_count =3
    candidates = random.sample(CHARACTER_TEMPLATES, candidate_count)

    return [create_member(template) for template in candidates]

def recruit_member(party, candidate_index, max_members=4):
    if candidate_index == -1:
        return party, None, None

    # 获取候选人
    candidates = recruit_candidates(party)
    if candidate_index >= len(candidates):
        return party, None, None

    new_member = candidates[candidate_index]
    removed_member = None

    if len(party) < max_members:
        # 队伍未满，直接加入
        party.append(new_member)
    else:
        # 队伍已满，需要舍1拿1（随机替换一个成员，不替换初始角色）
        # 找出可替换的成员（排除初始角色）
        replaceable_indices = [
            i for i, member in enumerate(party)
            if member["name"] not in [char_template["name"] for char_template in INITIAL_CHARACTERS]
        ]

        if replaceable_indices:
            replace_index = random.choice(replaceable_indices)
            removed_member = party[replace_index]
            party[replace_index] = new_member
        else:
            # 如果所有成员都是初始角色（理论上不可能），则不替换
            return party, None, None

    return party, new_member, removed_member

def replace_member(party, old_member, new_member_template):
    if old_member["name"] in [char_template["name"] for char_template in INITIAL_CHARACTERS]:
        return party, None

    # 查找并替换
    index = party.index(old_member)
    removed_member = party[index]
    party[index] = create_member(new_member_template)

    return party, removed_member


# ==================================================
# Recruit View - 招募窗口
# ==================================================
class RecruitView(tk.Frame):
    def __init__(self, parent, controller, party):
        super().__init__(parent)
        self.controller = controller
        self.party = party  # 引用外部队伍列表
        self.candidates = []
        self.selected_candidate = None

        self.title = tk.Label(self, text="招募队员", font=("微软雅黑", 14, "bold"))
        self.title.pack(pady=10)

        self.current_party_frame = tk.LabelFrame(self, text="当前队伍")
        self.current_party_frame.pack(fill="x", padx=10, pady=5)

        self.candidates_frame = tk.LabelFrame(self, text="招募候选人")
        self.candidates_frame.pack(fill="x", padx=10, pady=5)

        self.replace_frame = tk.LabelFrame(self, text="选择替换队员（队伍已满时）")
        self.replace_frame.pack(fill="x", padx=10, pady=5)
        self.replace_frame.pack_forget()  # 初始隐藏

        self.message_label = tk.Label(self, text="", fg="red")
        self.message_label.pack(pady=5)

        self.back_button = tk.Button(self, text="返回战斗", command=self.on_back)
        self.back_button.pack(pady=10)

    def refresh(self):
        # 清空当前队伍显示
        for w in self.current_party_frame.winfo_children():
            w.destroy()

        # 显示当前队伍
        for member in self.party:
            # 格式化技能显示
            skills_text = ", ".join([f"{skill[0]}({skill[2]})" for skill in member["skills"]])
            lbl = tk.Label(self.current_party_frame, 
                          text=f"{member['name']} (回合数: {member['total_turns']}) | 技能: {skills_text}")
            lbl.pack(anchor="w", padx=5, pady=2)

        # 获取候选人
        self.candidates = recruit_candidates(self.party)

        # 清空候选人显示
        for w in self.candidates_frame.winfo_children():
            w.destroy()

        # 显示候选人
        if not self.candidates:
            tk.Label(self.candidates_frame, text="没有可招募的候选人").pack(pady=5)
        else:
            for i, candidate in enumerate(self.candidates):
                # 格式化技能显示
                skills_text = ", ".join([f"{skill[0]}({skill[2]})" for skill in candidate["skills"]])
                btn = tk.Button(self.candidates_frame,
                               text=f"{candidate['name']} (回合数: {candidate['total_turns']})\n技能: {skills_text}",
                               width=40,
                               command=lambda c=candidate: self.select_candidate(c))
                btn.pack(pady=3)

        # 隐藏替换选择框
        self.replace_frame.pack_forget()
        self.message_label.config(text="")
        self.selected_candidate = None

    def select_candidate(self, candidate):
        """选择候选人"""
        self.selected_candidate = candidate

        if len(self.party) < 4:
            # 队伍未满，直接加入
            self.party.append(create_member(candidate))
            self.message_label.config(text=f"成功招募 {candidate['name']}！")
            # 设置招募已使用标志
            if self.controller and hasattr(self.controller, 'model'):
                self.controller.model.recruit_used = True
            # 延迟返回战斗界面，让用户看到招募成功提示
            self.master.after(1500, self.on_back)
        else:
            # 队伍已满，显示替换选择框
            self.show_replace_selection()

    def show_replace_selection(self):
        # 清空替换框
        for w in self.replace_frame.winfo_children():
            w.destroy()

        # 显示可替换的队员（排除初始角色战士）
        replaceable_members = [m for m in self.party if m["name"] not in [char_template["name"] for char_template in INITIAL_CHARACTERS]]

        if not replaceable_members:
            self.message_label.config(text="无法替换，队伍中只有初始角色！")
            return

        self.replace_frame.pack(fill="x", padx=10, pady=5)
        self.message_label.config(text=f"队伍已满！选择要替换的队员：")

        for member in replaceable_members:
            # 格式化技能显示
            skills_text = ", ".join([f"{skill[0]}({skill[2]})" for skill in member["skills"]])
            btn = tk.Button(self.replace_frame,
                           text=f"替换 {member['name']}\n技能: {skills_text}",
                           width=40,
                           command=lambda m=member: self.confirm_replace(m))
            btn.pack(pady=3)

        # 添加取消按钮
        tk.Button(self.replace_frame,
                  text="取消替换",
                  width=30,
                  command=self.cancel_replace).pack(pady=3)

    def confirm_replace(self, old_member):
        # 替换队员
        index = self.party.index(old_member)
        self.party[index] = create_member(self.selected_candidate)

        self.message_label.config(text=f"{old_member['name']} 被替换为 {self.selected_candidate['name']}！")
        self.replace_frame.pack_forget()
        # 设置招募已使用标志
        if self.controller and hasattr(self.controller, 'model'):
            self.controller.model.recruit_used = True
        # 延迟返回战斗界面，让用户看到替换成功提示
        self.master.after(1500, self.on_back)

    def cancel_replace(self):
        self.replace_frame.pack_forget()
        self.message_label.config(text="")
        self.selected_candidate = None

    def on_back(self):
        if self.controller:
            self.controller.show_battle()
class RecruitApp:
    def __init__(self, root):
        self.root = root
        self.root.title("招募系统")
        self.root.geometry("680x700")
        # 创建初始队伍
        self.party = generate_party(4)
        # 创建招募界面
        self.recruit_view = RecruitView(root, self, self.party)
        self.recruit_view.pack(fill="both", expand=True)
        self.recruit_view.refresh()
    def show_battle(self):
        # 这里只是简单显示队伍状态
        print("当前队伍：")
        for member in self.party:
            print(f"  - {member['name']}")
if __name__ == "__main__":
    root = tk.Tk()
    app = RecruitApp(root)
    root.mainloop()
def main():
    party = generate_party()