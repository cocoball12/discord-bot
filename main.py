import discord
from discord.ext import commands
import os
import asyncio
from datetime import datetime, timedelta
import json

# 환경 변수에서 포트 가져오기 (Koyeb용)
PORT = os.environ.get('PORT', 8080)

# 봇 설정
intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(
    command_prefix='!', 
    intents=intents, 
    help_command=None
)

# 환경 변수 설정
TOKEN = os.getenv('DISCORD_TOKEN')
DORADORI_ROLE_NAME = "도라도라미"

# 봇 이벤트
@bot.event
async def on_ready():
    print(f'{bot.user} 봇이 준비되었습니다!')
    print(f'접속한 서버 수: {len(bot.guilds)}')

# 기본 명령어 예시
@bot.command(name='ping')
async def ping(ctx):
    """봇 응답 테스트"""
    await ctx.send(f'Pong! 지연시간: {round(bot.latency * 1000)}ms')

@bot.command(name='안녕')
async def hello(ctx):
    """인사 명령어"""
    await ctx.send(f'안녕하세요, {ctx.author.mention}님!')

# 도라도라미 역할 관련 명령어 (예시)
@bot.command(name='도라도라미')
async def doradori(ctx):
    """도라도라미 역할 정보"""
    guild = ctx.guild
    role = discord.utils.get(guild.roles, name=DORADORI_ROLE_NAME)
    
    if role:
        members_with_role = [member for member in guild.members if role in member.roles]
        await ctx.send(f'{DORADORI_ROLE_NAME} 역할을 가진 멤버: {len(members_with_role)}명')
    else:
        await ctx.send(f'{DORADORI_ROLE_NAME} 역할을 찾을 수 없습니다.')

# 오류 처리
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        await ctx.send("존재하지 않는 명령어입니다.")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("필수 인수가 누락되었습니다.")
    else:
        print(f"오류 발생: {error}")
        await ctx.send("명령어 처리 중 오류가 발생했습니다.")

# 봇 실행 부분 수정
if __name__ == "__main__":
    if TOKEN:
        try:
            # Koyeb에서 웹 서비스로 실행하기 위한 더미 HTTP 서버
            import threading
            from http.server import HTTPServer, SimpleHTTPRequestHandler
            
            def run_http_server():
                try:
                    server = HTTPServer(('0.0.0.0', int(PORT)), SimpleHTTPRequestHandler)
                    print(f"HTTP 서버가 포트 {PORT}에서 시작됩니다.")
                    server.serve_forever()
                except Exception as e:
                    print(f"HTTP 서버 오류: {e}")
            
            # HTTP 서버를 백그라운드에서 실행
            threading.Thread(target=run_http_server, daemon=True).start()
            
            print("Discord 봇을 시작합니다...")
            # 봇 실행
            bot.run(TOKEN)
        except Exception as e:
            print(f"봇 실행 중 오류 발생: {e}")
            import traceback
            traceback.print_exc()
    else:
        print("DISCORD_TOKEN 환경 변수를 설정해주세요!")
        print("환경 변수 설정 방법:")
        print("1. Discord Developer Portal에서 봇 토큰 생성")
        print("2. Koyeb 환경 변수에 DISCORD_TOKEN 추가")
