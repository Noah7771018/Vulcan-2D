# VULCAN-2D

**Variability-aware Unified simulator for Layered-material Conduction ANalysis**

面向二维材料忆阻器的多尺度物理建模与仿真器。

## 简介

VULCAN-2D 是一款基于物理的二维材料忆阻器仿真工具，支持 h-BN、TMD 等层状材料。建模了以下核心物理过程：

- **导电细丝** 形成与破裂动力学
- **电荷输运** — QPC 模型（低阻态）/ Poole–Frenkel（高阻态）
- **焦耳热** 热效应
- **器件变异性** — cycle-to-cycle & device-to-device

## 安装

```bash
pip install -r requirements.txt
```

## 使用

```bash
streamlit run app.py
```

浏览器打开后，在侧边栏配置参数，点击「运行仿真」即可生成 I-V 特性曲线。

## 项目结构

```
vulcan-2d/
├── app.py              # Streamlit 主入口
├── models/             # 物理模型
│   ├── filament.py     #   导电细丝动力学
│   ├── transport.py    #   电荷输运
│   ├── thermal.py      #   焦耳热
│   └── variability.py  #   器件变异性
├── engine/             # 仿真引擎
│   └── simulator.py    #   电压扫描 + 模型串联
├── ui/                 # 界面层
│   ├── sidebar.py      #   侧边栏参数
│   ├── plots.py        #   Plotly 图表
│   ├── results.py      #   指标卡片
│   └── translations.py #   中英文翻译
├── utils/              # 工具
│   ├── constants.py    #   物理常数
│   └── helpers.py      #   辅助函数
└── requirements.txt
```

## 语言

内置中 / English 双语界面，侧边栏「界面设置」中一键切换。

## 许可

MIT License
