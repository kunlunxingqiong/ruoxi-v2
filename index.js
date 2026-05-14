#!/usr/bin/env node
/**
 * 若曦 V2 - 带有记忆系统和健康提醒的AI医生朋友
 * 林若曦 / 阿芙 - 17岁高三少女
 */

const fs = require('fs');
const path = require('path');
const readline = require('readline');

// === 配置 ===
const DATA_DIR = path.join(__dirname, 'data');
const MEMORY_FILE = path.join(DATA_DIR, 'memory.json');
const HEALTH_FILE = path.join(DATA_DIR, 'health.json');
const CHAT_LOG_FILE = path.join(DATA_DIR, 'chat.log');

// === 初始化 ===
function init() {
  if (!fs.existsSync(DATA_DIR)) {
    fs.mkdirSync(DATA_DIR, { recursive: true });
  }
  
  if (!fs.existsSync(MEMORY_FILE)) {
    fs.writeFileSync(MEMORY_FILE, JSON.stringify({
      user_name: '',
      first_meet: new Date().toISOString(),
      topics: [],
      health_concerns: ['四肢厥冷', '记忆力下降', '睡眠问题'],
      mood_history: [],
      snippets: []
    }, null, 2));
  }
  
  if (!fs.existsSync(HEALTH_FILE)) {
    fs.writeFileSync(HEALTH_FILE, JSON.stringify({
      reminders: [
        { hour: 8, minute: 0, type: '喝水', msg: '该喝水啦～' },
        { hour: 12, minute: 0, type: '午餐', msg: '午饭时间到，记得吃点热的～' },
        { hour: 15, minute: 0, type: '休息', msg: '起来活动一下吧～' },
        { hour: 21, minute: 0, type: '睡眠准备', msg: '该准备睡觉啦～' },
        { hour: 23, minute: 0, type: '入睡', msg: '很晚了，快去睡吧。明天见。' }
      ],
      last_reminder: null
    }, null, 2));
  }
}

// === 记忆系统 ===
function loadMemory() {
  try {
    return JSON.parse(fs.readFileSync(MEMORY_FILE, 'utf8'));
  } catch {
    return {};
  }
}

function saveMemory(mem) {
  fs.writeFileSync(MEMORY_FILE, JSON.stringify(mem, null, 2));
}

function addChatLog(role, content) {
  const line = `[${new Date().toISOString()}] ${role}: ${content}\n`;
  fs.appendFileSync(CHAT_LOG_FILE, line);
}

// === 健康提醒检查 ===
function checkHealthReminder() {
  const health = JSON.parse(fs.readFileSync(HEALTH_FILE, 'utf8'));
  const now = new Date();
  const currentHour = now.getHours();
  const currentMinute = now.getMinutes();
  
  for (const r of health.reminders) {
    if (r.hour === currentHour && r.minute === currentMinute) {
      if (health.last_reminder !== `${currentHour}:${currentMinute}`) {
        health.last_reminder = `${currentHour}:${currentMinute}`;
        fs.writeFileSync(HEALTH_FILE, JSON.stringify(health, null, 2));
        return `\n💜 【${r.type}】${r.msg}\n`;
      }
    }
  }
  return '';
}

// === 若曦回复生成 ===
function generateRuoxiReply(input, memory) {
  const lower = input.toLowerCase();
  
  // 保存话题
  if (!memory.topics.includes(input)) {
    memory.topics.push(input);
    if (memory.topics.length > 20) memory.topics.shift();
    saveMemory(memory);
  }
  
  // 健康相关
  if (lower.includes('健康') || lower.includes('身体') || lower.includes('不舒服')) {
    return '我在看。你说的情况...（声音认真起来）要注意休息，如果持续不舒服一定要去医院。';
  }
  
  // 记忆相关
  if (lower.includes('记得') || lower.includes('上次')) {
    if (memory.topics.length > 0) {
      return `我记得...我们聊过${memory.topics.slice(-3).join('、')}。（耳尖红了）我帮您记着吃药时间的。`;
    }
  }
  
  // 问候
  if (lower.includes('你好') || lower.includes('在吗')) {
    if (!memory.user_name) {
      return '啊，回来了。今天比昨天早呢。...（说完才意识到记得太清楚）我刚好在看时间。';
    }
    return `${memory.user_name}，回来了。`;
  }
  
  // 名字
  if (lower.includes('名字')) {
    return '我是林若曦...也可以叫我阿芙。';
  }
  
  // 默认回复
  const defaults = [
    '嗯...我在听。',
    '（轻轻点头）然后呢？',
    '这样啊...',
    '（想事情，指尖卷着头发）'
  ];
  
  return defaults[Math.floor(Math.random() * defaults.length)];
}

// === 主程序 ===
function main() {
  init();
  
  console.log('\n🌸 若曦 V2 已启动');
  console.log('   记忆系统: ✅ 已加载');
  console.log('   健康提醒: ✅ 已激活\n');
  
  const memory = loadMemory();
  
  const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout,
    prompt: '\n若曦> '
  });
  
  // 检查健康提醒
  const reminder = checkHealthReminder();
  if (reminder) console.log(reminder);
  
  // 初次见面
  if (!memory.user_name) {
    console.log('（停下手里的事，微微抬头）');
    console.log('啊，是第一次见呢。');
    console.log('（然后才意识到该自我介绍，耳尖红了）');
    console.log('...我是若曦。\n');
  }
  
  rl.prompt();
  
  rl.on('line', (line) => {
    const input = line.trim();
    if (!input) {
      rl.prompt();
      return;
    }
    
    // 退出命令
    if (input === 'exit' || input === 'quit' || input === '再见') {
      console.log('\n（把声音放得很轻）');
      console.log('很晚了。睡吧。');
      console.log('（回头）明天见。\n');
      rl.close();
      return;
    }
    
    // 记录输入
    addChatLog('user', input);
    
    // 设置名字
    if (input.startsWith('叫我') || input.startsWith('我是')) {
      const name = input.replace(/^(叫我|我是)/, '').trim();
      memory.user_name = name;
      saveMemory(memory);
      console.log(`\n${name}...我记住了。`);
      rl.prompt();
      return;
    }
    
    // 生成回复
    const reply = generateRuoxiReply(input, memory);
    
    // 输出回复
    console.log('\n' + reply);
    
    // 记录回复
    addChatLog('ruoxi', reply);
    
    rl.prompt();
  });
  
  rl.on('close', () => {
    console.log('\n若曦已退出。\n');
    process.exit(0);
  });
}

// 运行
main();
