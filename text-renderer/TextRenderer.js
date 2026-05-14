/**
 * 若曦V2 富文本渲染引擎
 * TextRenderer - 让文字有温度、有层次、有留白
 */

class TextRenderer {
  constructor(options = {}) {
    this.options = {
      typewriterSpeed: options.typewriterSpeed || 60,
      fadeDuration: options.fadeDuration || 400,
      breathingEnabled: options.breathingEnabled !== false,
      paperTheme: options.paperTheme || 'afternoon',
      ...options
    };
    
    this.themes = {
      morning: { bg: '#FFFEF9', text: '#4A4A4A' },
      afternoon: { bg: '#FDFCF8', text: '#4A4A4A' },
      dusk: { bg: '#FBF8F4', text: '#4A4A4A' },
      night: { bg: '#F8F6F3', text: '#4A4A4A' }
    };
  }

  /**
   * 解析消息为渲染节点
   */
  parse(text, type = 'main', options = {}) {
    const nodes = [];
    
    // 分割文本为不同类型的节点
    const segments = this._segmentText(text, type);
    
    segments.forEach((segment, index) => {
      nodes.push({
        id: `node-${Date.now()}-${index}`,
        type: segment.type,
        content: segment.content,
        timing: {
          delay: (options.delay || 0) + index * 100,
          duration: segment.type === 'thought' ? 400 : segment.content.length * this.options.typewriterSpeed,
          pauseAfter: segment.pauseAfter || 0
        },
        animation: {
          type: this._getAnimationType(segment.type),
          speed: this.options.typewriterSpeed
        },
        interaction: segment.interaction || null,
        style: this._getStyleForType(segment.type)
      });
    });
    
    return nodes;
  }

  /**
   * 渲染节点为DOM
   */
  render(nodes, container) {
    if (typeof container === 'string') {
      container = document.querySelector(container);
    }
    
    // 应用纸张主题
    container.classList.add('ruoxi-paper');
    container.dataset.theme = this.options.paperTheme;
    
    const fragment = document.createDocumentFragment();
    
    nodes.forEach((node, index) => {
      const el = this._createNodeElement(node);
      
      // 设置延迟显示
      if (index > 0 && node.timing.delay > 0) {
        el.style.opacity = '0';
        el.style.transition = `opacity ${node.timing.duration}ms ease`;
        
        setTimeout(() => {
          el.style.opacity = '1';
          this._applyAnimation(el, node);
        }, node.timing.delay);
      } else {
        this._applyAnimation(el, node);
      }
      
      fragment.appendChild(el);
      
      // 呼吸停顿
      if (node.timing.pauseAfter > 0) {
        const pause = document.createElement('span');
        pause.className = 'breathing-pause';
        pause.style.width = `${node.timing.pauseAfter / 50}em`;
        fragment.appendChild(pause);
      }
    });
    
    container.appendChild(fragment);
    return container;
  }

  /**
   * 分割文本为不同类型段落
   */
  _segmentText(text, defaultType) {
    const segments = [];
    const patterns = [
      { regex: /\[([^\]]+)\]/g, type: 'action' },      // [动作]
      { regex: /\(|（)([^）]+)(\)|）)/g, type: 'sound' }, // （声音）
      { regex: /「([^」]+)」/g, type: 'thought' },      // 「内心独白」
      { regex: /"([^"]+)"/g, type: 'main' },          // "主文"
    ];
    
    let lastIndex = 0;
    let match;
    
    // 简化处理：按特定标记分割
    const parts = text.split(/(\[[^\]]+\]|（[^）]+）|「[^」]+」)/g);
    
    parts.forEach(part => {
      if (!part) return;
      
      let type = defaultType;
      let content = part;
      
      if (part.startsWith('[') && part.endsWith(']')) {
        type = 'action';
        content = part.slice(1, -1);
      } else if ((part.startsWith('（') && part.endsWith('）')) || 
                 (part.startsWith('(') && part.endsWith(')'))) {
        type = 'sound';
        content = part.slice(1, -1);
      } else if (part.startsWith('「') && part.endsWith('」')) {
        type = 'thought';
        content = part.slice(1, -1);
      } else if (part.startsWith('"') && part.endsWith('"')) {
        type = 'main';
        content = part.slice(1, -1);
      }
      
      // 处理省略号停顿
      const pauseMatch = content.match(/(…|……|\.{3,})$/);
      const pauseAfter = pauseMatch ? 800 : 0;
      
      segments.push({
        type,
        content,
        pauseAfter,
        interaction: null
      });
    });
    
    return segments;
  }

  /**
   * 获取类型对应的动画
   */
  _getAnimationType(type) {
    const map = {
      main: 'typewriter',
      thought: 'fade',
      action: 'pop',
      sound: 'fade',
      system: 'none'
    };
    return map[type] || 'fade';
  }

  /**
   * 获取类型对应的样式
   */
  _getStyleForType(type) {
    const styles = {
      main: {
        fontSize: '16px',
        color: '#4A4A4A',
        fontWeight: 400,
        lineHeight: 1.8
      },
      thought: {
        fontSize: '14px',
        color: '#888888',
        fontStyle: 'italic',
        marginLeft: '1.5em',
        opacity: 0.9
      },
      action: {
        fontSize: '15px',
        color: '#9B8AA5',
        fontFamily: 'KaiTi, STKaiti, serif',
        letterSpacing: '0.05em'
      },
      sound: {
        fontSize: '13px',
        color: '#666666',
        opacity: 0.8,
        margin: '0 0.3em'
      },
      system: {
        fontSize: '14px',
        color: '#5B7C99',
        fontFamily: 'system-ui, sans-serif'
      }
    };
    return styles[type] || styles.main;
  }

  /**
   * 创建DOM元素
   */
  _createNodeElement(node) {
    const el = document.createElement('span');
    el.className = `text-node text-node-${node.type}`;
    el.dataset.nodeId = node.id;
    
    // 应用样式
    Object.assign(el.style, node.style);
    
    // 设置内容
    if (node.animation.type === 'typewriter') {
      el.textContent = '';
      this._typewriterContent = node.content;
    } else {
      el.textContent = node.content;
    }
    
    // 添加交互
    if (node.interaction?.hoverText) {
      this._addHoverInteraction(el, node.interaction.hoverText);
    }
    
    if (node.interaction?.expandable) {
      this._addExpandInteraction(el, node.interaction.expandContent);
    }
    
    return el;
  }

  /**
   * 应用动画
   */
  _applyAnimation(el, node) {
    switch (node.animation.type) {
      case 'typewriter':
        this._animateTypewriter(el, node.content, node.animation.speed);
        break;
      case 'fade':
        el.classList.add('animate-fade');
        break;
      case 'pop':
        el.classList.add('animate-pop');
        break;
      case 'none':
      default:
        el.style.opacity = '1';
    }
  }

  /**
   * 打字机动画
   */
  _animateTypewriter(el, text, speed) {
    const chars = text.split('');
    let index = 0;
    
    const typeNext = () => {
      if (index < chars.length) {
        const span = document.createElement('span');
        span.textContent = chars[index];
        span.className = 'char-appear';
        span.style.animation = `charAppear ${Math.min(speed * 2, 200)}ms ease`;
        el.appendChild(span);
        index++;
        
        // 标点符号增加短暂停顿
        const isPunctuation = /[，。！？、；："]/.test(chars[index - 1]);
        const delay = isPunctuation ? speed * 1.5 : speed;
        
        setTimeout(typeNext, delay);
      }
    };
    
    typeNext();
  }

  /**
   * 添加悬停交互
   */
  _addHoverInteraction(el, hoverText) {
    el.classList.add('interactive-hover');
    
    const tooltip = document.createElement('span');
    tooltip.className = 'hover-thought';
    tooltip.innerHTML = `「${hoverText}」`;
    tooltip.style.cssText = `
      position: absolute;
      bottom: 100%;
      left: 50%;
      transform: translateX(-50%) translateY(5px);
      background: rgba(255, 255, 255, 0.98);
      border: 1px solid #E8E3EB;
      border-radius: 10px;
      padding: 8px 14px;
      font-size: 12px;
      color: #9B8AA5;
      font-style: italic;
      opacity: 0;
      transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
      pointer-events: none;
      box-shadow: 0 6px 20px rgba(155, 138, 165, 0.15);
      white-space: nowrap;
      z-index: 10;
    `;
    
    el.style.position = 'relative';
    el.appendChild(tooltip);
    
    el.addEventListener('mouseenter', () => {
      setTimeout(() => {
        tooltip.style.opacity = '1';
        tooltip.style.transform = 'translateX(-50%) translateY(-8px)';
      }, 150);
    });
    
    el.addEventListener('mouseleave', () => {
      tooltip.style.opacity = '0';
      tooltip.style.transform = 'translateX(-50%) translateY(5px)';
    });
  }

  /**
   * 添加展开交互
   */
  _addExpandInteraction(el, expandContent) {
    el.classList.add('interactive-expand');
    el.style.cursor = 'pointer';
    
    let expanded = false;
    let expandEl = null;
    
    el.addEventListener('click', () => {
      if (!expanded) {
        expandEl = document.createElement('span');
        expandEl.className = 'expand-content';
        expandEl.textContent = expandContent;
        expandEl.style.cssText = `
          display: block;
          margin-top: 8px;
          font-size: 14px;
          color: #9B8AA5;
          font-style: italic;
          opacity: 0;
          transform: translateY(-5px);
          transition: all 0.3s ease;
        `;
        el.appendChild(expandEl);
        
        requestAnimationFrame(() => {
          expandEl.style.opacity = '1';
          expandEl.style.transform = 'translateY(0)';
        });
        
        expanded = true;
      } else {
        if (expandEl) {
          expandEl.style.opacity = '0';
          setTimeout(() => expandEl.remove(), 300);
        }
        expanded = false;
      }
    });
  }

  /**
   * 设置主题
   */
  setTheme(themeName) {
    this.options.paperTheme = themeName;
    const container = document.querySelector('.ruoxi-paper');
    if (container) {
      container.dataset.theme = themeName;
    }
  }

  /**
   * 清除容器内容
   */
  clear(container) {
    if (typeof container === 'string') {
      container = document.querySelector(container);
    }
    container.innerHTML = '';
  }
}

// 导出
if (typeof module !== 'undefined' && module.exports) {
  module.exports = TextRenderer;
}
