import discord
from discord.ext import commands
import os
import asyncio
from datetime import datetime, timedelta
import json
import logging

# 로깅 설정 (디버깅을 위해)
logging.basicConfig(level=logging.DEBUG)

# 환경 변수에서 포트 가져오기 (Koyeb용)
PORT = os.environ.get('PORT', 8080)

# 봇 설정 - 모든 필요한 intents 활성화
intents = discord.Intents.all()  # 모든 인텐트 활성화 (디버깅용)

bot = commands.Bot(
    command_prefix='!', 
    intents=intents, 
    help_command=None,
    case_insensitive=True  # 대소문자 구분 안함
)

# 환경 변수 설정
TOKEN = os.getenv('DISCORD_TOKEN')
DORADORI_ROLE_NAME = "도라도라미"

print(f"=== 봇 시작 정보 ===")
print(f"TOKEN 존재: {'예' if TOKEN else '아니오'}")
print(f"TOKEN 앞 4자리: {TOKEN[:4] if TOKEN else 'None'}...")
print(f"포트: {PORT}")
print("==================")

# 봇 이벤트 - 상세한 로깅
@bot.event
async def on_ready():
    print(f"\n🤖 {bot.user}이(가) 준비되었습니다!")
    print(f"📊 접속한 서버 수: {len(bot.guilds)}")
    print(f"🆔 봇 ID: {bot.user.id}")
    print(f"⚡ 지연시간: {round(bot.latency * 1000)}ms")
    
    # 접속한 서버 목록 출력
    for guild in bot.guilds:
        print(f"   - {guild.name} (ID: {guild.id})")
    
    # 봇 상태 설정
    await bot.change_presence(
        activity=discord.Game(name="!ping 으로 테스트"),
        status=discord.Status.online
    )
    print("✅ 봇이 완전히 준비되었습니다!\n")

# 메시지 수신 이벤트 (디버깅용)
@bot.event
async def on_message(message):
    # 봇 자신의 메시지는 무시
    if message.author == bot.user:
        return
    
    print(f"💬 메시지 수신: [{message.guild.name if message.guild else 'DM'}] {message.author}: {message.content}")
    
    # 명령어 처리
    await bot.process_commands(message)

# 명령어 실행 전 이벤트 (디버깅용)
@bot.event
async def on_command(ctx):
    print(f"🔧 명령어 실행: {ctx.command} by {ctx.author}")

# 기본 명령어들 - 더 상세한 응답
@bot.command(name='ping', aliases=['핑'])
async def ping(ctx):
    """봇 응답 테스트"""
    print(f"🏓 ping 명령어 실행 - 사용자: {ctx.author}")
    
    embed = discord.Embed(
        title="🏓 Pong!",
        description=f"**지연시간:** {round(bot.latency * 1000)}ms",
        color=0x00ff00
    )
    embed.add_field(name="서버", value=ctx.guild.name, inline=True)
    embed.add_field(name="채널", value=ctx.channel.name, inline=True)
    embed.add_field(name="사용자", value=ctx.author.mention, inline=True)
    
    await ctx.send(embed=embed)

@bot.command(name='안녕', aliases=['hello', '하이'])
async def hello(ctx):
    """인사 명령어"""
    print(f"👋 안녕 명령어 실행 - 사용자: {ctx.author}")
    await ctx.send(f'안녕하세요, {ctx.author.mention}님! 🎉')

@bot.command(name='테스트', aliases=['test'])
async def test(ctx):
    """봇 상태 테스트"""
    print(f"🔍 테스트 명령어 실행 - 사용자: {ctx.author}")
    
    embed = discord.Embed(
        title="🤖 봇 상태 테스트",
        color=0x0099ff
    )
    embed.add_field(name="봇 이름", value=bot.user.name, inline=True)
    embed.add_field(name="서버 수", value=len(bot.guilds), inline=True)
    embed.add_field(name="지연시간", value=f"{round(bot.latency * 1000)}ms", inline=True)
    embed.add_field(name="명령어 접두사", value="!", inline=True)
    embed.add_field(name="현재 시간", value=datetime.now().strftime("%Y-%m-%d %H:%M:%S"), inline=True)
    
    await ctx.send(embed=embed)

# 서버 정보 명령어
@bot.command(name='서버정보', aliases=['serverinfo'])
async def server_info(ctx):
    """서버 정보 표시"""
    if not ctx.guild:
        await ctx.send("이 명령어는 서버에서만 사용할 수 있습니다.")
        return
    
    guild = ctx.guild
    embed = discord.Embed(
        title=f"🏰 {guild.name}",
        color=0x9932cc
    )
    embed.add_field(name="멤버 수", value=guild.member_count, inline=True)
    embed.add_field(name="생성일", value=guild.created_at.strftime("%Y-%m-%d"), inline=True)
    embed.add_field(name="서버 ID", value=guild.id, inline=True)
    embed.add_field(name="채널 수", value=len(guild.channels), inline=True)
    embed.add_field(name="역할 수", value=len(guild.roles), inline=True)
    
    await ctx.send(embed=embed)

# 도라도라미 역할 관련 명령어
@bot.command(name='도라도라미')
async def doradori(ctx):
    """도라도라미 역할 정보"""
    if not ctx.guild:
        await ctx.send("이 명령어는 서버에서만 사용할 수 있습니다.")
        return
    
    guild = ctx.guild
    role = discord.utils.get(guild.roles, name=DORADORI_ROLE_NAME)
    
    if role:
        members_with_role = [member for member in guild.members if role in member.roles]
        embed = discord.Embed(
            title=f"🎭 {DORADORI_ROLE_NAME} 역할",
            description=f"**멤버 수:** {len(members_with_role)}명",
            color=role.color
        )
        if members_with_role:
            member_list = "\n".join([f"• {member.display_name}" for member in members_with_role[:10]])
            embed.add_field(name="멤버 목록", value=member_list, inline=False)
        
        await ctx.send(embed=embed)
    else:
        await ctx.send(f"❌ '{DORADORI_ROLE_NAME}' 역할을 찾을 수 없습니다.")

# 오류 처리 - 더 상세한 로깅
@bot.event
async def on_command_error(ctx, error):
    print(f"❌ 명령어 오류: {error}")
    print(f"   - 명령어: {ctx.message.content}")
    print(f"   - 사용자: {ctx.author}")
    print(f"   - 채널: {ctx.channel}")
    
    if isinstance(error, commands.CommandNotFound):
        await ctx.send("❌ 존재하지 않는 명령어입니다. `!테스트`로 봇 상태를 확인해보세요.")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("❌ 필수 인수가 누락되었습니다.")
    elif isinstance(error, commands.BotMissingPermissions):
        await ctx.send("❌ 봇에게 필요한 권한이 없습니다.")
    elif isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ 사용자에게 필요한 권한이 없습니다.")
    else:
        await ctx.send(f"❌ 명령어 처리 중 오류가 발생했습니다: {str(error)}")

# 길드 입장 시 알림
@bot.event
async def on_guild_join(guild):
    print(f"✅ 새 서버 입장: {guild.name} (ID: {guild.id})")

# 길드 퇴장 시 알림
@bot.event
async def on_guild_remove(guild):
    print(f"❌ 서버 퇴장: {guild.name} (ID: {guild.id})")

# 봇 실행 부분
if __name__ == "__main__":
    if TOKEN:
        try:
            # Koyeb에서 웹 서비스로 실행하기 위한 더미 HTTP 서버
            import threading
            from http.server import HTTPServer, SimpleHTTPRequestHandler
            
            def run_http_server():
                try:
                    server = HTTPServer(('0.0.0.0', int(PORT)), SimpleHTTPRequestHandler)
                    print(f"🌐 HTTP 서버가 포트 {PORT}에서 시작됩니다.")
                    server.serve_forever()
                except Exception as e:
                    print(f"❌ HTTP 서버 오류: {e}")
            
            # HTTP 서버를 백그라운드에서 실행
            threading.Thread(target=run_http_server, daemon=True).start()
            
            print("🚀 Discord 봇을 시작합니다...")
            # 봇 실행
            bot.run(TOKEN)
            
        except discord.LoginFailure:
            print("❌ 로그인 실패! 토큰을 확인해주세요.")
        except discord.PrivilegedIntentsRequired:
            print("❌ 권한이 필요합니다! Discord Developer Portal에서 Privileged Gateway Intents를 활성화해주세요.")
        except Exception as e:
            print(f"❌ 봇 실행 중 오류 발생: {e}")
            import traceback
            traceback.print_exc()
    else:
        print("❌ DISCORD_TOKEN 환경 변수를 설정해주세요!")
        print("\n📋 체크리스트:")
        print("1. Discord Developer Portal에서 봇 토큰 복사")
        print("2. Koyeb 환경 변수에 DISCORD_TOKEN 추가")
        print("3. 봇을 서버에 올바른 권한으로 초대")
        print("4. Discord Developer Portal에서 Privileged Gateway Intents 활성화")
