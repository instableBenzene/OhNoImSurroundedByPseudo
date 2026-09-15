# locations/

每文件暴露 `LOCATIONS`；需要让**新分组**进入开局地点池时，再声明：

```python
MAP_GROUPS = {"my_group": {"weight": 20, "label": "我的分组", "icon": "i-gate",
                           "required": False}}
```
