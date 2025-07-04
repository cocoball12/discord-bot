import discord
from discord.ext import commands
import os
import asyncio
from datetime import datetime, timedelta
import json
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 환경 변수에서 포트 가져오기
PORT = os.environ.get('PORT', 8080)

# 봇 설정 - 필요한 intents만 활성화
intents = discord.Intents.default()
intents.message_content = True  # 메시지 내용 읽기 권한 (중요!)
intents.guilds = True
intents.guild_messages = True
intents.members = True  # 멤버 정보 접근

bot = commands.Bot(
    command_prefix='!', 
    intents=intents, 
    help_command=None,
    case_insensitive=True
)

# 환경 변수 설정
TOKEN = os.getenv('DISCORD_TOKEN')
DORADORI_ROLE_NAME = "도라도라미"

print(f"=== 봇 시작 정보 ===")
print(f"TOKEN 존재: {'예' if TOKEN else '아니오'}")
print(f"포트: {PORT}")
print("==================")

# 봇 준비 완료 이벤트
@bot.event
async def on_ready():
    print(f"\n✅ {bot.user}이(가) 온라인 상태입니다!")
    print(f"📊 접속한 서버: {len(bot.guilds)}개")
    print(f"🆔 봇 ID: {bot.user.id}")
    print(f"⚡ 지연시간: {round(bot.latency * 1000)}ms")
    
    # 접속한 서버 목록
    for guild in bot.guilds:
        print(f"   🏰 {guild.name} (멤버: {guild.member_count}명)")
    
    # 봇 상태 설정
    await bot.change_presence(
        activity=discord.Game(name="!ping 명령어 테스트"),
        status=discord.Status.online
    )
    print("\n🤖 봇이 완전히 준비되었습니다!")

# 메시지 이벤트 (디버깅용)
@bot.event
async def on_message(message):
    # 봇 자신의 메시지는 무시
    if message.author == bot.user:
        return
    
    # 봇 멘션 시 응답
    if bot.user.mentioned_in(message):
        await message.channel.send(f"안녕하세요 {message.author.mention}! `!ping`을 입력해보세요!")
    
    # 로그 출력
    channel_name = message.channel.name if hasattr(message.channel, 'name') else 'DM'
    guild_name = message.guild.name if message.guild else 'DM'
    logger.info(f"메시지: [{guild_name}#{channel_name}] {message.author}: {message.content}")
    
    # 명령어 처리
    await bot.process_commands(message)

# 명령어 실행 이벤트
@bot.event
async def on_command(ctx):
    logger.info(f"명령어 실행: {ctx.command} - {ctx.author}")

# 기본 명령어들
@bot.command(name='ping', aliases=['핑', 'pong'])
async def ping(ctx):
    """봇 응답 테스트"""
    try:
        latency = round(bot.latency * 1000)
        
        embed = discord.Embed(
            title="🏓 Pong!",
            description=f"지연시간: **{latency}ms**",
            color=0x00ff00,
            timestamp=datetime.now()
        )
        
        try:
            embed.add_field(name="서버", value=ctx.guild.name if ctx.guild else "DM", inline=True)
            embed.add_field(name="채널", value=ctx.channel.name if hasattr(ctx.channel, 'name') else "DM", inline=True)
            embed.add_field(name="사용자", value=ctx.author.display_name, inline=True)
            
            if ctx.author.avatar:
                embed.set_footer(text=f"요청자: {ctx.author}", icon_url=ctx.author.avatar.url)
            else:
                embed.set_footer(text=f"요청자: {ctx.author}")
        except:
            # 추가 정보 설정 실패 시 기본 정보만 유지
            pass
        
        await ctx.send(embed=embed)
        
    except Exception as e:
        # 임베드 생성 실패 시 간단한 메시지로 대체
        await ctx.send(f"🏓 Pong! 지연시간: {round(bot.latency * 1000)}ms")

@bot.command(name='간단테스트', aliases=['simple'])
async def simple_test(ctx):
    """간단한 테스트"""
    await ctx.send("✅ 봇이 정상 작동 중입니다!")

@bot.command(name='정보', aliases=['info'])
async def bot_info(ctx):
    """봇 기본 정보"""
    info_text = f"""
**봇 정보:**
🤖 이름: {bot.user.name}
🆔 ID: {bot.user.id}
🏓 지연시간: {round(bot.latency * 1000)}ms
🏰 서버 수: {len(bot.guilds)}개
⚡ 상태: 온라인
    """
    await ctx.send(info_text)

@bot.command(name='안녕', aliases=['hello', '하이', 'hi'])
async def hello(ctx):
    """인사 명령어"""
    await ctx.send(f'안녕하세요 {ctx.author.mention}님! 😊\n`!테스트`로 봇 상태를 확인해보세요!')

@bot.command(name='테스트', aliases=['test', 'status'])
async def test(ctx):
    """봇 상태 테스트"""
    try:
        embed = discord.Embed(
            title="🤖 봇 상태 테스트",
            description="모든 시스템이 정상 작동 중입니다!",
            color=0x00ff00,
            timestamp=datetime.now()
        )
        
        # 기본 정보 (안전한 데이터만)
        embed.add_field(name="🏓 응답 속도", value=f"{round(bot.latency * 1000)}ms", inline=True)
        embed.add_field(name="🏰 서버 수", value=len(bot.guilds), inline=True)
        embed.add_field(name="📱 명령어 접두사", value="`!`", inline=True)
        
        # 서버 정보 (안전하게 처리)
        if ctx.guild:
            try:
                embed.add_field(name="👥 현재 서버 멤버", value=f"{ctx.guild.member_count}명", inline=True)
                embed.add_field(name="📺 채널 수", value=len(ctx.guild.channels), inline=True)
                embed.add_field(name="🎭 역할 수", value=len(ctx.guild.roles), inline=True)
            except Exception as e:
                embed.add_field(name="⚠️ 서버 정보", value="일부 정보 접근 제한", inline=True)
        
        # 사용자 정보 (안전하게 처리)
        try:
            footer_text = f"요청자: {ctx.author}"
            avatar_url = ctx.author.avatar.url if ctx.author.avatar else None
            embed.set_footer(text=footer_text, icon_url=avatar_url)
        except:
            embed.set_footer(text="테스트 완료")
        
        await ctx.send(embed=embed)
        
    except Exception as e:
        # 임베드 생성 실패 시 간단한 메시지로 대체
        try:
            await ctx.send(f"✅ 봇 상태: 정상 작동 중\n🏓 응답 속도: {round(bot.latency * 1000)}ms\n🏰 서버 수: {len(bot.guilds)}개")
        except Exception as e2:
            await ctx.send("✅ 봇이 정상적으로 작동 중입니다!")

@bot.command(name='도움말', aliases=['help', 'commands'])
async def help_command(ctx):
    """사용 가능한 명령어 목록"""
    embed = discord.Embed(
        title="📋 명령어 목록",
        description="사용 가능한 명령어들입니다:",
        color=0x0099ff
    )
    
    commands_list = [
        ("!ping", "봇 응답 테스트"),
        ("!안녕", "인사 명령어"),
        ("!테스트", "봇 상태 확인"),
        ("!서버정보", "서버 정보 표시"),
        ("!도라도라미", "도라도라미 역할 정보"),
        ("!도움말", "이 메시지 표시")
    ]
    
    for cmd, desc in commands_list:
        embed.add_field(name=cmd, value=desc, inline=False)
    
    await ctx.send(embed=embed)

@bot.command(name='서버정보', aliases=['serverinfo', 'server'])
async def server_info(ctx):
    """서버 정보 표시"""
    if not ctx.guild:
        await ctx.send("❌ 이 명령어는 서버에서만 사용할 수 있습니다.")
        return
    
    guild = ctx.guild
    embed = discord.Embed(
        title=f"🏰 {guild.name}",
        color=0x9932cc,
        timestamp=datetime.now()
    )
    
    embed.add_field(name="👥 멤버 수", value=f"{guild.member_count}명", inline=True)
    embed.add_field(name="📅 생성일", value=guild.created_at.strftime("%Y년 %m월 %d일"), inline=True)
    embed.add_field(name="🆔 서버 ID", value=guild.id, inline=True)
    embed.add_field(name="📺 채널 수", value=len(guild.channels), inline=True)
    embed.add_field(name="🎭 역할 수", value=len(guild.roles), inline=True)
    embed.add_field(name="😀 이모지 수", value=len(guild.emojis), inline=True)
    
    if guild.icon:
        embed.set_thumbnail(url=guild.icon.url)
    
    await ctx.send(embed=embed)

@bot.command(name='도라도라미')
async def doradori(ctx):
    """도라도라미 역할 정보"""
    if not ctx.guild:
        await ctx.send("❌ 이 명령어는 서버에서만 사용할 수 있습니다.")
        return
    
    guild = ctx.guild
    role = discord.utils.get(guild.roles, name=DORADORI_ROLE_NAME)
    
    if role:
        members_with_role = [member for member in guild.members if role in member.roles]
        embed = discord.Embed(
            title=f"🎭 {DORADORI_ROLE_NAME} 역할",
            description=f"**멤버 수:** {len(members_with_role)}명",
            color=role.color if role.color.value != 0 else 0x99aab5
        )
        
        if members_with_role:
            member_list = "\n".join([f"• {member.display_name}" for member in members_with_role[:15]])
            if len(members_with_role) > 15:
                member_list += f"\n... 외 {len(members_with_role) - 15}명"
            embed.add_field(name="멤버 목록", value=member_list, inline=False)
        else:
            embed.add_field(name="멤버 목록", value="아직 이 역할을 가진 멤버가 없습니다.", inline=False)
        
        embed.add_field(name="역할 생성일", value=role.created_at.strftime("%Y년 %m월 %d일"), inline=True)
        embed.add_field(name="역할 ID", value=role.id, inline=True)
        embed.add_field(name="멘션 가능", value="예" if role.mentionable else "아니오", inline=True)
        
        await ctx.send(embed=embed)
    else:
        await ctx.send(f"❌ '{DORADORI_ROLE_NAME}' 역할을 찾을 수 없습니다.")

# 오류 처리 - 더 자세한 로깅
@bot.event
async def on_command_error(ctx, error):
    error_msg = str(error)
    error_type = type(error).__name__
    
    # 로그에 자세한 오류 정보 출력
    logger.error(f"명령어 오류 발생:")
    logger.error(f"  - 오류 타입: {error_type}")
    logger.error(f"  - 오류 메시지: {error_msg}")
    logger.error(f"  - 사용자: {ctx.author}")
    logger.error(f"  - 명령어: {ctx.message.content}")
    logger.error(f"  - 채널: {ctx.channel}")
    logger.error(f"  - 서버: {ctx.guild.name if ctx.guild else 'DM'}")
    
    # 스택 트레이스 출력
    import traceback
    logger.error(f"  - 스택 트레이스:\n{traceback.format_exc()}")
    
    if isinstance(error, commands.CommandNotFound):
        await ctx.send("❌ 존재하지 않는 명령어입니다. `!도움말`로 사용 가능한 명령어를 확인해보세요.")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"❌ 필수 인수가 누락되었습니다: `{error.param.name}`")
    elif isinstance(error, commands.BotMissingPermissions):
        await ctx.send("❌ 봇에게 필요한 권한이 없습니다. 서버 관리자에게 문의하세요.")
    elif isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ 이 명령어를 사용할 권한이 없습니다.")
    elif isinstance(error, commands.CommandOnCooldown):
        await ctx.send(f"❌ 명령어 쿨다운 중입니다. {error.retry_after:.1f}초 후 다시 시도하세요.")
    else:
        # 사용자에게는 간단한 메시지, 로그에는 자세한 정보
        await ctx.send(f"❌ 오류 발생: {error_type}\n자세한 내용은 로그를 확인하세요.")

# 새 서버 입장 시
@bot.event
async def on_guild_join(guild):
    logger.info(f"새 서버 입장: {guild.name} (ID: {guild.id})")
    
    # 일반 채널 찾기
    general_channel = None
    for channel in guild.text_channels:
        if channel.permissions_for(guild.me).send_messages:
            general_channel = channel
            break
    
    if general_channel:
        embed = discord.Embed(
            title="🎉 안녕하세요!",
            description=f"**{guild.name}** 서버에 초대해주셔서 감사합니다!\n`!도움말`로 사용 가능한 명령어를 확인해보세요.",
            color=0x00ff00
        )
        try:
            await general_channel.send(embed=embed)
        except:
            pass

# 봇 실행
if __name__ == "__main__":
    if TOKEN:
        try:
            # HTTP 서버 (Koyeb용)
            import threading
            from http.server import HTTPServer, SimpleHTTPRequestHandler
            
            class HealthCheckHandler(SimpleHTTPRequestHandler):
                def do_GET(self):
                    self.send_response(200)
                    self.send_header('Content-type', 'text/plain')
                    self.end_headers()
                    self.wfile.write(b'Bot is running!')
            
            def run_http_server():
                try:
                    server = HTTPServer(('0.0.0.0', int(PORT)), HealthCheckHandler)
                    logger.info(f"HTTP 서버 시작: 포트 {PORT}")
                    server.serve_forever()
                except Exception as e:
                    logger.error(f"HTTP 서버 오류: {e}")
            
            threading.Thread(target=run_http_server, daemon=True).start()
            
            logger.info("Discord 봇 시작 중...")
            bot.run(TOKEN)
            
        except discord.LoginFailure:
            logger.error("❌ Discord 로그인 실패! 토큰을 확인하세요.")
        except discord.PrivilegedIntentsRequired:
            logger.error("❌ 권한 오류! Discord Developer Portal에서 Message Content Intent를 활성화하세요.")
        except Exception as e:
            logger.error(f"❌ 봇 실행 오류: {e}")
    else:
        print("❌ DISCORD_TOKEN 환경 변수를 설정해주세요!")
