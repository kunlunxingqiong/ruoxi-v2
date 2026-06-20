"""
🌸 若曦V2 - 语音管理器
支持语音对话和合成
"""
from typing import Optional, BinaryIO, Dict, List
from dataclasses import dataclass
from enum import Enum, auto
from pathlib import Path
import asyncio
from datetime import datetime


class VoiceProvider(Enum):
    """语音服务商"""
    GOOGLE_TTS = auto()
    ELEVENLABS = auto()
    AZURE_TTS = auto()
    OPENAI_TTS = auto()
    LOCAL = auto()


class VoiceGender(Enum):
    """声音性别"""
    FEMALE = "female"
    MALE = "male"
    NEUTRAL = "neutral"


@dataclass
class VoiceProfile:
    """声音配置"""
    provider: VoiceProvider
    voice_id: str
    name: str
    gender: VoiceGender
    language: str
    style: str  # e.g., "warm", "professional", "gentle"
    pitch: float = 1.0  # 音调
    speed: float = 1.0  # 语速
    volume: float = 1.0  # 音量


@dataclass
class TTSRequest:
    """文本转语音请求"""
    text: str
    profile: VoiceProfile
    format: str = "mp3"
    quality: str = "high"
    cache_key: Optional[str] = None


@dataclass
class TTSResponse:
    """文本转语音响应"""
    audio_data: bytes
    format: str
    duration_ms: int
    character_count: int
    provider: VoiceProvider
    cached: bool = False


class VoiceCache:
    """语音缓存"""
    
    def __init__(self, cache_dir: str = "data/voice_cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._memory_cache: Dict[str, bytes] = {}
    
    def _get_cache_key(self, text: str, voice_id: str) -> str:
        import hashlib
        return hashlib.md5(f"{text}:{voice_id}".encode()).hexdigest()[:16]
    
    async def get(self, text: str, voice_id: str) -> Optional[bytes]:
        """获取缓存"""
        key = self._get_cache_key(text, voice_id)
        
        # 内存缓存
        if key in self._memory_cache:
            return self._memory_cache[key]
        
        # 文件缓存
        cache_file = self.cache_dir / f"{key}.{voice_id}.mp3"
        if cache_file.exists():
            with open(cache_file, "rb") as f:
                data = f.read()
                self._memory_cache[key] = data
                return data
        
        return None
    
    async def set(self, text: str, voice_id: str, audio_data: bytes):
        """设置缓存"""
        key = self._get_cache_key(text, voice_id)
        
        # 内存缓存
        self._memory_cache[key] = audio_data
        
        # 文件缓存
        cache_file = self.cache_dir / f"{key}.{voice_id}.mp3"
        with open(cache_file, "wb") as f:
            f.write(audio_data)


class VoiceManager:
    """
    语音管理器
    
    功能:
    - 文本转语音 (TTS)
    - 语音转文本 (STT) placeholder
    - 多服务商支持
    - 智能缓存
    """
    
    def __init__(self):
        self.cache = VoiceCache()
        self._profiles: Dict[str, VoiceProfile] = {}
        self._init_default_profiles()
    
    def _init_default_profiles(self):
        """初始化默认声音配置"""
        self._profiles = {
            "ruoxi_default": VoiceProfile(
                provider=VoiceProvider.GOOGLE_TTS,
                voice_id="zh-CN-Standard-A",
                name="若曦温柔声",
                gender=VoiceGender.FEMALE,
                language="zh-CN",
                style="gentle",
                pitch=1.1,
                speed=0.95
            ),
            "ruoxi_professional": VoiceProfile(
                provider=VoiceProvider.GOOGLE_TTS,
                voice_id="zh-CN-Standard-C",
                name="若曦专业声",
                gender=VoiceGender.FEMALE,
                language="zh-CN",
                style="professional",
                pitch=1.0,
                speed=1.0
            ),
            "ruoxi_narration": VoiceProfile(
                provider=VoiceProvider.GOOGLE_TTS,
                voice_id="zh-CN-Wavenet-A",
                name="若曦讲故事",
                gender=VoiceGender.FEMALE,
                language="zh-CN",
                style="warm",
                pitch=1.15,
                speed=0.9
            )
        }
    
    async def text_to_speech(
        self, 
        text: str,
        profile_name: Optional[str] = None
    ) -> Optional[TTSResponse]:
        """文本转语音"""
        
        profile = self._profiles.get(profile_name or "ruoxi_default")
        if not profile:
            return None
        
        # 检查缓存
        cached = await self.cache.get(text, profile.voice_id)
        if cached:
            return TTSResponse(
                audio_data=cached,
                format="mp3",
                duration_ms=self._estimate_duration(text, profile.speed),
                character_count=len(text),
                provider=profile.provider,
                cached=True
            )
        
        # 调用TTS服务
        audio_data = await self._call_tts_service(text, profile)
        
        if audio_data:
            # 缓存结果
            await self.cache.set(text, profile.voice_id, audio_data)
            
            return TTSResponse(
                audio_data=audio_data,
                format="mp3",
                duration_ms=self._estimate_duration(text, profile.speed),
                character_count=len(text),
                provider=profile.provider,
                cached=False
            )
        
        return None
    
    async def _call_tts_service(
        self, 
        text: str, 
        profile: VoiceProfile
    ) -> Optional[bytes]:
        """调用TTS服务"""
        
        if profile.provider == VoiceProvider.GOOGLE_TTS:
            return await self._google_tts(text, profile)
        
        elif profile.provider == VoiceProvider.ELEVENLABS:
            return await self._elevenlabs_tts(text, profile)
        
        elif profile.provider == VoiceProvider.AZURE_TTS:
            return await self._azure_tts(text, profile)
        
        elif profile.provider == VoiceProvider.LOCAL:
            return await self._local_tts(text, profile)
        
        return None
    
    async def _google_tts(self, text: str, profile: VoiceProfile) -> Optional[bytes]:
        """Google TTS"""
        try:
            from gtts import gTTS
            
            tts = gTTS(
                text=text[:500],  # gTTS有长度限制
                lang=profile.language.replace("-", "_").split("_")[0],
                slow=(profile.speed < 1.0)
            )
            
            import io
            mp3_fp = io.BytesIO()
            tts.write_to_fp(mp3_fp)
            return mp3_fp.getvalue()
            
        except Exception as e:
            print(f"Google TTS失败: {e}")
            return None
    
    async def _elevenlabs_tts(
        self, 
        text: str, 
        profile: VoiceProfile
    ) -> Optional[bytes]:
        """ElevenLabs TTS (高质量)"""
        # 需要API密钥
        return None
    
    async def _azure_tts(
        self, 
        text: str, 
        profile: VoiceProfile
    ) -> Optional[bytes]:
        """Azure TTS"""
        # 需要API密钥
        return None
    
    async def _local_tts(
        self, 
        text: str, 
        profile: VoiceProfile
    ) -> Optional[bytes]:
        """本地TTS (如 pyttsx3)"""
        try:
            import pyttsx3
            engine = pyttsx3.init()
            
            # 设置参数
            engine.setProperty('rate', int(200 * profile.speed))
            engine.setProperty('pitch', profile.pitch)
            
            # 保存到内存
            import tempfile
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                temp_path = f.name
            
            engine.save_to_file(text[:300], temp_path)
            engine.runAndWait()
            
            with open(temp_path, "rb") as f:
                data = f.read()
            
            Path(temp_path).unlink()
            return data
            
        except Exception as e:
            print(f"本地TTS失败: {e}")
            return None
    
    def _estimate_duration(self, text: str, speed: float) -> int:
        """估算语音时长 (ms)"""
        # 中文大约每秒4-5个字
        chars_per_second = 5 * speed
        seconds = len(text) / chars_per_second
        return int(seconds * 1000)
    
    async def stream_text_to_speech(
        self, 
        text_stream: asyncio.Queue,
        audio_queue: asyncio.Queue
    ):
        """流式语音合成"""
        buffer = ""
        
        while True:
            chunk = await text_stream.get()
            
            if chunk is None:  # 结束信号
                if buffer:
                    audio = await self.text_to_speech(buffer)
                    if audio:
                        await audio_queue.put(audio.audio_data)
                await audio_queue.put(None)
                break
            
            buffer += chunk
            
            # 按句子分割
            if any(punct in buffer for punct in ["，", "。", "！", "？", ".", "!", "?"]):
                sentences = buffer
                buffer = ""
                
                audio = await self.text_to_speech(sentences)
                if audio:
                    await audio_queue.put(audio.audio_data)
    
    def get_available_voices(self) -> List[VoiceProfile]:
        """获取可用声音列表"""
        return list(self._profiles.values())
    
    def add_custom_profile(
        self, 
        name: str, 
        profile: VoiceProfile
    ):
        """添加自定义声音"""
        self._profiles[name] = profile


# 若曦默认语音配置
RUOXI_VOICE_PROFILES = {
    "gentle": "ruoxi_default",
    "professional": "ruoxi_professional",
    "story": "ruoxi_narration",
}

# 全局语音管理器
voice_manager = VoiceManager()
