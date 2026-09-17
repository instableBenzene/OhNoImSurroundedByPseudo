# likai_test

最小可运行的示例包（`dlc/README.md` 里提到的那个）——拿它当"照着改就能用"的参照：

- `characters/likai.py`：一个房客（`CHARACTER` + 一个被动），外加一条专属**全局事件**定义。
- `items/painting.py`：一件物资 + `ITEM_HOOKS`（放在屋主物品栏时每回合给全员回理智）。

注意它是**测试包**：数值不参与平衡，只为把"角色 / 物资 / 全局事件"三条路子走通。
