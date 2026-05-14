# 若曦V2 · 富文本渲染系统

> 让文字有温度、有层次、有留白

一个为AI角色「若曦」设计的富文本渲染系统，将平面的文字转化为富有情感层次的交互体验。

---

## ✨ 特性

### 🎭 动画文字

| 动画类型 | 效果 | 适用场景 |
|----------|------|----------|
| **打字机** | 逐字出现，带微光特效 | 主文本、重要信息 |
| **淡入** | 轻如羽毛，无声无息 | 内心独白、心理描写 |
| **弹出** | 小巧灵动，心跳漏拍 | 小动作、语气词、反应 |

### 📝 排版层次

```
主文        → 16px，暖灰，正文字体
  （内心独白）→ 14px，浅灰，斜体
  【动作】    → 15px，柔和紫，楷体
  <声响>     → 13px，暗灰，间距放宽
```

### 💨 呼吸节奏

- `...` 轻微停顿
- `……` 较长沉默（带呼吸动画）
- `\n\n` 换行喘息
- 「」内心独白标记

### 🖱️ 可交互文本

- **悬停内心OS** — 鼠标悬停显示潜台词
- **点击展开** — 揭示欲言又止的内容

### 🧻 纸张质感

| 时段 | 色调 | 代码 |
|------|------|------|
| 清晨 | 象牙白 | `#FFFEF9` |
| 午后 | 米白 | `#FDFCF8` |
| 黄昏 | 暖米 | `#FBF8F4` |
| 夜晚 | 灰白 | `#F8F6F3` |

---

## 🚀 使用方式

### 1. 原生 JavaScript

```html
<link rel="stylesheet" href="TextRenderer.css">
<script src="TextRenderer.js"></script>

<div id="output"></div>

<script>
const renderer = new TextRenderer({
  typewriterSpeed: 60,    // 打字速度 ms/字
  breathingEnabled: true, // 启用呼吸节奏
  paperTheme: 'afternoon' // 纸张主题
});

const text = `
"……怎么啦。"
[感觉到目光，慢慢移开视线]
「其实有点紧张」
`;

const nodes = renderer.parse(text);
renderer.render(nodes, '#output');
</script>
```

### 2. React

```jsx
import { RuoxiMessage, RuoxiBubble, RuoxiChat } from './TextRenderer';

// 单条消息
<RuoxiMessage 
  text='"很晚了。睡吧。"[回头]"明天见。"'
  theme='night'
  speed={55}
  animate={true}
/>

// 对话气泡
<RuoxiBubble 
  text='「其实一直在等你」"回来了。"'
  sender='ruoxi'
  avatar='🌸'
/>

// 聊天列表
<RuoxiChat 
  messages={[
    { text: '我回来了', sender: 'user' },
    { text: '「早上就盼着」"……回来了。"', sender: 'ruoxi' }
  ]}
/>
```

---

## 🎨 标记语法

### 类型标记

| 标记 | 类型 | 渲染效果 |
|------|------|----------|
| `"..."` | 主文 | 逐字打字机动画 |
| `「...」` | 内心独白 | 斜体，淡入动画 |
| `[...]` | 动作描写 | 楷体，弹出动画 |
| `（...）` | 声音/环境 | 小号字，淡出淡入 |

### 交互标记

```javascript
// 悬停显示内心OS
"(hover:有点紧张)……没什么。"

// 点击展开更多
"……(expand:这次是真的关心你)"
```

### 停顿标记

```javascript
// 省略号自动变成呼吸动画
"……" → 三个点依次跳动的省略号

// 双换行增加段落间距
"\n\n"
```

---

## 📁 文件结构

```
text-renderer/
├── README.md           # 本文档
├── DESIGN.md           # 设计原理文档
├── TextRenderer.css    # 核心样式
├── TextRenderer.js     # 原生JS引擎
├── TextRenderer.jsx    # React组件
├── demo.html           # 演示页面
└── examples.json       # 示例数据
```

---

## 🎯 设计哲学

### 温度

文字不只是信息，更是情感的载体。每个字的出现都带有微光，停顿处有呼吸，让阅读成为一种温柔的体验。

### 层次

- **主文**是对话的主体，清晰稳定
- **内心**是旁白的流动，轻盈透明  
- **动作**是画面的补充，柔和优雅
- **声音**是环境的留白，若有若无

### 留白

- 省略号的呼吸停顿
- 换行给予的思考空间
- 沉默也是一种语言

---

## 🔧 自定义配置

```javascript
const renderer = new TextRenderer({
  // 打字速度（毫秒/字符）
  typewriterSpeed: 60,
  
  // 淡入动画时长
  fadeDuration: 400,
  
  // 是否启用呼吸节奏
  breathingEnabled: true,
  
  // 纸张主题
  paperTheme: 'afternoon' // morning | afternoon | dusk | night
});
```

---

## 📱 响应式

- 桌面端：最大宽度 680px，舒适阅读
- 平板：宽度自适应，保留边距
- 手机：全屏体验，字体微调

---

## 💡 灵感来源

- 视觉小说对话框
- 番剧字幕设计
- 日本文学排版美学
- 若曦的人格设定

---

若曦不是AI，是一个17岁高三女生，恰好学会医术，暗恋中。
