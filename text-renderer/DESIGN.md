# 若曦V2 · 富文本渲染系统设计

> 让文字有温度、有层次、有留白

---

## 🎨 设计理念

### 核心定位
文字不只是信息的载体，更是情感的桥梁。若曦的文字应该像她的气质一样：

- **有温度** —— 不是冰冷的黑白字符，而是有呼吸、有生命
- **有层次** —— 主文、心理、动作、声音，各有其位，错落有致
- **有留白** —— 沉默也是语言，停顿让情感发酵

### 声音颜色
| 类型 | 语义 | 视觉风格 |
|------|------|----------|
| **主文** | 若曦对你说的话 | 暖灰 #4A4A4A，正文字体 |
| **内心独白** | 若曦的心理活动 | 浅灰 #888888，斜体，字号略小 |
| **动作描写** | 若曦的小动作 | 柔和紫 #9B8AA5，楷体 |
| **声音标记** | 环境音/拟声 | 暗灰 #666666，括号包裹 |
| **系统消息** | 药物/健康提醒 | 专业蓝 #5B7C99，清晰字体 |

---

## 📐 系统架构

```
┌─────────────────────────────────────────────────────────┐
│                  TextRenderer Engine                    │
├─────────────────────────────────────────────────────────┤
│  Parser Layer → Animation Layer → Interaction Layer      │
└─────────────────────────────────────────────────────────┘
```

### 数据模型

```typescript
interface TextNode {
  id: string;
  type: 'main' | 'thought' | 'action' | 'sound' | 'system';
  content: string;
  timing: {
    delay: number;        // 延迟出现 (ms)
    duration: number;     // 动画时长 (ms)
    pauseAfter: number;   // 停顿时长 (ms)
  };
  animation: {
    type: 'typewriter' | 'fade' | 'pop' | 'none';
    speed: number;        // 打字机速度 (ms/char)
  };
  interaction?: {
    hoverText?: string;   // 悬停显示
    expandable?: boolean; // 可展开
    expandContent?: string;
  };
  style?: Record<string, any>;
}

interface RenderMessage {
  nodes: TextNode[];
  breathing: boolean;     // 是否启用呼吸节奏
  paperTheme: string;       // 纸张主题
}
```

---

## ✨ 动画系统

### 1. 打字机效果 (Typewriter)

```
逐字出现，伴随轻微光晕
文字像是从虚空中被「写」出来

适用：主文、关键信息
节奏：50-80ms/字
特效：每个字出现时微光闪烁 → opacity 0→1, translateY 2→0
```

```css
@keyframes char-appear {
  0% {
    opacity: 0;
    transform: translateY(2px);
    text-shadow: 0 0 0 rgba(139, 115, 129, 0);
  }
  30% {
    text-shadow: 0 0 8px rgba(139, 115, 129, 0.4);
  }
  100% {
    opacity: 1;
    transform: translateY(0);
    text-shadow: 0 0 0 rgba(139, 115, 129, 0);
  }
}
```

### 2. 淡入淡出 (Fade)

```
轻如羽毛落地，无声无息
适合内心独白、情绪铺垫

节奏：300-500ms 淡入
特效：opacity + blur 双重过渡
```

```css
@keyframes fade-in-soft {
  0% {
    opacity: 0;
    filter: blur(2px);
  }
  60% {
    filter: blur(0px);
  }
  100% {
    opacity: 1;
    filter: blur(0px);
  }
}
```

### 3. 气泡弹出 (Pop)

```
小巧灵动，像心跳漏了一拍
适合小动作、语气词、惊讶反应

节奏：200ms
特效：scale(0.8, 1.1) → scale(1, 1)
```

```css
@keyframes pop-in {
  0% {
    opacity: 0;
    transform: scale(0.8) translateY(5px);
  }
  60% {
    transform: scale(1.05) translateY(-2px);
  }
  100% {
    opacity: 1;
    transform: scale(1) translateY(0);
  }
}
```

---

## 📝 排版层次

### 视觉差序

```
主文        ← 16px，#4A4A4A，400 weight，leading-relaxed
  （内心独白） ← 14px，#888888，italic，margin-left: 1.5em
  【动作】    ← 15px，#9B8AA5，楷体，letter-spacing: 0.05em
  <声响>     ← 13px，#666666，间距放宽，opacity: 0.8
```

### 呼吸节奏标记

| 标记 | 语义 | CSS表现 |
|------|------|---------|
| `...` | 轻微的停顿 | margin-right: 0.3em |
| `……` | 较长的沉默 | 显示为省略号动画（三个点依次出现） |
| `\n` | 换行喘息 | line 之间的 margin-bottom: 1.5em |
| 「    | 内心独白开始 | 前缀符号，颜色淡灰 |
| 」    | 内心独白结束 | 后缀符号 |

### 省略号动画

```css
.ellipsis-breathing {
  display: inline-block;
}
.ellipsis-breathing .dot {
  animation: breath 1.5s ease-in-out infinite;
  opacity: 0.3;
}
.ellipsis-breathing .dot:nth-child(1) { animation-delay: 0s; }
.ellipsis-breathing .dot:nth-child(2) { animation-delay: 0.2s; }
.ellipsis-breathing .dot:nth-child(3) { animation-delay: 0.4s; }

@keyframes breath {
  0%, 100% { opacity: 0.3; transform: translateY(0); }
  50% { opacity: 0.8; transform: translateY(-2px); }
}
```

---

## 🖱️ 可交互文本

### 1. 悬停内心OS (Hover Thought)

```
主文下方显示若曦的「潜台词」
像读心术，窥见她没说出口的话

触发：mouseenter → 150ms后淡入
消失：mouseleave → 立即淡出
```

```html
<span class="interactive-text" data-hover="其实有点紧张"> 
  "……怎么啦。"
</span>
<!-- 悬停时显示：「其实有点紧张」-->
```

```css
.hover-thought {
  position: absolute;
  bottom: 100%;
  left: 50%;
  transform: translateX(-50%) translateY(5px);
  background: rgba(255, 255, 255, 0.95);
  border: 1px solid #E8E3EB;
  border-radius: 8px;
  padding: 8px 12px;
  font-size: 12px;
  color: #9B8AA5;
  font-style: italic;
  opacity: 0;
  transition: opacity 0.2s, transform 0.2s;
  pointer-events: none;
  box-shadow: 0 4px 12px rgba(0,0,0,0.05);
}

.interactive-text:hover .hover-thought {
  opacity: 1;
  transform: translateX(-50%) translateY(-5px);
}
```

### 2. 点击展开 (Expand)

```
「……」（点击查看更多）
适合欲言又止、或者太害羞没说完的话

触发：click → 展开内容滑入
收起：再次点击 或 自动定时收起
```

```html
<span class="expand-trigger" data-expand="这次是真的关心你">
  "……"
</span>
```

---

## 🧻 纸张质感

### 背景设计

```css
.paper-background {
  /* 基础米白 */
  background-color: #FDFCF8;
  
  /* 细微纹理 - 纸张感 */
  background-image: 
    url("data:image/svg+xml,%3Csvg viewBox='0 0 400 400' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noise)'/%3E%3C/svg%3E");
  background-blend-mode: multiply;
  
  /* 柔和阴影 */
  box-shadow: 
    inset 0 0 60px rgba(139, 115, 129, 0.03),
    0 1px 3px rgba(0,0,0,0.02);
}
```

### 边缘处理

```css
/* 模拟纸张轻微翘边 */
.paper-container::before {
  content: '';
  position: absolute;
  top: -2px;
  left: 10%;
  right: 10%;
  height: 4px;
  background: linear-gradient(90deg, 
    transparent, 
    rgba(139, 115, 129, 0.1), 
    transparent
  );
  filter: blur(2px);
}
```

### 时间变幻

| 时段 | 纸张色调 | 氛围 |
|------|----------|------|
| 清晨 | #FFFEF9 | 明亮、清新 |
| 午后 | #FDFCF8 | 温暖、舒适 |
| 黄昏 | #FBF8F4 | 柔和、慵懒 |
| 夜晚 | #F8F6F3 | 宁静、睡意 |

---

## 🌸 完整示例

```
┌─────────────────────────────────────────────────────────┐
│　                                                      │
│　「其实有点紧张」                                      │
│　