/**
 * 若曦V2 富文本渲染React组件
 * TextRenderer.jsx - React Component
 */

import React, { useState, useEffect, useRef, useCallback } from 'react';
import './TextRenderer.css';

// ==================== 类型定义 (JSDoc) ====================

/**
 * @typedef {Object} TextNode
 * @property {string} id
 * @property {'main'|'thought'|'action'|'sound'|'system'} type
 * @property {string} content
 * @property {Object} timing
 * @property {Object} animation
 * @property {Object} [interaction]
 */

// ==================== 常量配置 ====================

const TYPE_STYLES = {
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
    letterSpacing: '0.05em',
    display: 'block',
    margin: '0.6em 0'
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
    fontFamily: 'system-ui, sans-serif',
    background: 'rgba(91, 124, 153, 0.06)',
    padding: '12px 18px',
    borderRadius: '10px',
    borderLeft: '3px solid #5B7C99',
    display: 'block',
    margin: '12px 0'
  }
};

const ANIMATION_TYPES = {
  main: 'typewriter',
  thought: 'fade',
  action: 'pop',
  sound: 'fade',
  system: 'none'
};

const THEMES = {
  morning: '#FFFEF9',
  afternoon: '#FDFCF8',
  dusk: '#FBF8F4',
  night: '#F8F6F3'
};

// ==================== 工具函数 ====================

/**
 * 解析消息文本为节点数组
 */
export const parseMessage = (text, options = {}) => {
  const segments = [];
  const parts = text.split(/(\[[^\]]+\]|（[^）]+）|「[^」]+」)/g);
  
  parts.forEach((part, index) => {
    if (!part || !part.trim()) return;
    
    let type = 'main';
    let content = part;
    let interaction = null;
    
    // 检测类型
    if (part.startsWith('[') && part.endsWith(']')) {
      type = 'action';
      content = part.slice(1, -1);
    } else if (part.startsWith('（') && part.endsWith('）')) {
      type = 'sound';
      content = part.slice(1, -1);
    } else if (part.startsWith('「') && part.endsWith('」')) {
      type = 'thought';
      content = part.slice(1, -1);
    }
    
    // 检测交互标记 [data-hover="xxx"]
    const hoverMatch = content.match(/\(hover:\s*([^)]+)\)/);
    if (hoverMatch) {
      interaction = { hoverText: hoverMatch[1] };
      content = content.replace(hoverMatch[0], '');
    }
    
    // 检测展开标记 [expand:xxx]
    const expandMatch = content.match(/\(expand:\s*([^)]+)\)/);
    if (expandMatch) {
      interaction = { ...interaction, expandable: true, expandContent: expandMatch[1] };
      content = content.replace(expandMatch[0], '');
    }
    
    // 检测停顿
    const pauseMatch = content.match(/(…|……|\.{3,}|\n\n)$/);
    const pauseAfter = pauseMatch ? 600 : 0;
    
    segments.push({
      id: `node-${Date.now()}-${index}`,
      type,
      content: content.trim(),
      timing: {
        delay: (options.delay || 0) + segments.length * 80,
        pauseAfter
      },
      animation: {
        type: ANIMATION_TYPES[type],
        speed: options.speed || 55
      },
      interaction
    });
  });
  
  return segments;
};

// ==================== 子组件 ====================

/**
 * 打字机效果组件
 */
const TypewriterText = ({ text, speed = 55, onComplete }) => {
  const [displayText, setDisplayText] = useState('');
  const [currentIndex, setCurrentIndex] = useState(0);
  const containerRef = useRef(null);
  
  useEffect(() => {
    if (currentIndex >= text.length) {
      onComplete?.();
      return;
    }
    
    const char = text[currentIndex];
    const isPunctuation = /[，。！？、；："…]/.test(char);
    const delay = isPunctuation ? speed * 1.8 : speed;
    
    const timer = setTimeout(() => {
      setDisplayText(prev => prev + char);
      setCurrentIndex(prev => prev + 1);
    }, delay);
    
    return () => clearTimeout(timer);
  }, [currentIndex, text, speed, onComplete]);
  
  // 滚动到可见区域
  useEffect(() => {
    if (containerRef.current && displayText.length > 0) {
      const lastChar = containerRef.current.lastElementChild;
      lastChar?.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }
  }, [displayText]);
  
  return (
    <span ref={containerRef} className="typewriter-container">
      {displayText.split('').map((char, i) => (
        <span key={i} className="char-appear" style={{ animationDelay: `${i * 10}ms` }}>
          {char}
        </span>
      ))}
      {currentIndex < text.length && <span className="typewriter-cursor" />}
    </span>
  );
};

/**
 * 流动省略号组件
 */
const BreathingEllipsis = () => (
  <span className="ellipsis-breathing">
    <span className="dot">·</span>
    <span className="dot">·</span>
    <span className="dot">·</span>
  </span>
);

/**
 * 悬停提示组件
 */
const HoverThought = ({ children, hoverText }) => {
  const [showThought, setShowThought] = useState(false);
  
  return (
    <span 
      className="interactive-hover"
      onMouseEnter={() => setShowThought(true)}
      onMouseLeave={() => setShowThought(false)}
      style={{ position: 'relative' }}
    >
      {children}
      {showThought && (
        <span className="hover-thought" style={{ opacity: 1, transform: 'translateX(-50%) translateY(-8px)' }}>
          「{hoverText}」
        </span>
      )}
    </span>
  );
};

/**
 * 可展开文本组件
 */
const ExpandableText = ({ children, expandContent }) => {
  const [expanded, setExpanded] = useState(false);
  
  return (
    <span>
      <span 
        className="interactive-expand" 
        onClick={() => setExpanded(!expanded)}
      >
        {children}
      </span>
      {expanded && (
        <span className="expand-content" style={{ opacity: 1, transform: 'translateY(0)' }}>
          {expandContent}
        </span>
      )}
    </span>
  );
};

/**
 * 单个文本节点组件
 */
const TextNodeComponent = ({ node, animate = true }) => {
  const [isVisible, setIsVisible] = useState(!animate);
  
  useEffect(() => {
    if (!animate) return;
    
    const timer = setTimeout(() => {
      setIsVisible(true);
    }, node.timing.delay);
    
    return () => clearTimeout(timer);
  }, [animate, node.timing.delay]);
  
  const style = {
    ...TYPE_STYLES[node.type],
    opacity: isVisible ? 1 : 0,
    transition: node.animation.type === 'fade' ? 'all 0.4s ease' : 'opacity 0.3s ease'
  };
  
  // 根据动画类型渲染
  const renderContent = () => {
    let content = node.content;
    
    // 处理交互
    if (node.interaction?.hoverText) {
      content = <HoverThought hoverText={node.interaction.hoverText}>{content}</HoverThought>;
    }
    
    if (node.interaction?.expandable) {
      content = <ExpandableText expandContent={node.interaction.expandContent}>{content}</ExpandableText>;
    }
    
    // 处理尾部省略号
    if (content.toString().endsWith('……') || content.toString().endsWith('...')) {
      content = (
        <>
          {content.toString().replace(/…+$/, '')}
          <BreathingEllipsis />
        </>
      );
    }
    
    if (!isVisible) {
      return null;
    }
    
    switch (node.animation.type) {
      case 'typewriter':
        return <TypewriterText text={node.content} speed={node.animation.speed} />;
      case 'fade':
        return <span className="animate-fade">{content}</span>;
      case 'pop':
        return <span className="animate-pop">{content}</span>;
      case 'none':
      default:
        return content;
    }
  };
  
  return (
    <span className={`text-node text-node-${node.type}`} style={style}>
      {renderContent()}
      {node.timing.pauseAfter > 0 && (
        <span className="breathing-pause" style={{ width: '1.5em' }} />
      )}
    </span>
  );
};

// ==================== 主组件 ====================

/**
 * 富文本消息组件
 */
export const RuoxiMessage = ({ 
  text, 
  type = 'main',
  theme = 'afternoon',
  speed = 55,
  animate = true,
  onComplete,
  className = ''
}) => {
  const nodes = React.useMemo(() => parseMessage(text, { speed }), [text, speed]);
  const containerRef = useRef(null);
  
  // 跟踪所有节点动画完成
  const [completedNodes, setCompletedNodes] = useState(new Set());
  
  const handleNodeComplete = useCallback((nodeId) => {
    setCompletedNodes(prev => {
      const newSet = new Set(prev);
      newSet.add(nodeId);
      return newSet;
    });
  }, []);
  
  // 所有节点完成后触发回调
  useEffect(() => {
    if (completedNodes.size === nodes.length && nodes.length > 0) {
      onComplete?.();
    }
  }, [completedNodes, nodes.length, onComplete]);
  
  return (
    <div 
      ref={containerRef}
      className={`ruoxi-paper ${className}`}
      data-theme={theme}
    >
      {nodes.map((node) => (
        <TextNodeComponent 
          key={node.id} 
          node={node} 
          animate={animate}
        />
      ))}
    </div>
  );
};

/**
 * 消息气泡组件 - 对话式布局
 */
export const RuoxiBubble = ({
  text,
  sender = 'ruoxi', // 'ruoxi' | 'user'
  theme = 'afternoon',
  speed = 55,
  animate = true,
  avatar = '🌸',
  timestamp,
  onComplete
}) => {
  const isRuoxi = sender === 'ruoxi';
  
  return (
    <div className={`message-bubble ${isRuoxi ? 'other' : 'own'}`}>
      {isRuoxi && <div className="message-avatar">{avatar}</div>}
      <div className="message-content">
        <RuoxiMessage 
          text={text} 
          theme={theme}
          speed={speed}
          animate={animate}
          onComplete={onComplete}
        />
      </div>
      {timestamp && (
        <div className="message-time">{timestamp}</div>
      )}
    </div>
  );
};

/**
 * 聊天容器组件
 */
export const RuoxiChat = ({ 
  messages = [], 
  theme = 'afternoon',
  onMessageComplete,
  className = ''
}) => {
  const containerRef = useRef(null);
  
  // 自动滚动到底部
  useEffect(() => {
    if (containerRef.current) {
      containerRef.current.scrollTop = containerRef.current.scrollHeight;
    }
  }, [messages]);
  
  return (
    <div 
      ref={containerRef}
      className={`ruoxi-chat-container ${className}`}
      style={{ overflowY: 'auto', maxHeight: '80vh', padding: '20px' }}
    >
      {messages.map((msg, index) => (
        <RuoxiBubble
          key={index}
          text={msg.text}
          sender={msg.sender}
          theme={msg.theme || theme}
          speed={msg.speed}
          animate={msg.animate !== false}
          avatar={msg.avatar}
          timestamp={msg.timestamp}
          onComplete={() => onMessageComplete?.(index)}
        />
      ))}
    </div>
  );
};

// ==================== Hooks ====================

/**
 * 使用若曦文字渲染器的Hook
 */
export const useTextRenderer = (options = {}) => {
  const [theme, setTheme] = useState(options.theme || 'afternoon');
  const [isTyping, setIsTyping] = useState(false);
  
  const parse = useCallback((text) => {
    return parseMessage(text, { speed: options.speed || 55 });
  }, [options.speed]);
  
  const changeTheme = useCallback((newTheme) => {
    setTheme(newTheme);
  }, []);
  
  return {
    theme,
    setTheme: changeTheme,
    parse,
    isTyping,
    setIsTyping,
    themes: Object.keys(THEMES)
  };
};

// ==================== 导出 ====================

export default {
  RuoxiMessage,
  RuoxiBubble,
  RuoxiChat,
  parseMessage,
  useTextRenderer,
  THEMES
};
