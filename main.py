import discord
from discord.ext import commands, tasks
import os
import asyncio
from datetime import datetime, timedelta
import json
import re
import aiohttp
from aiohttp import web
import threading

# 메시지 설정 로드
def load_messages():
    try:
        with open('messages.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print("messages.json 파일을 찾을 수 없습니다. 기본 설정을 사용합니다.")
        return get_default_messages()

def get_default_messages():
    return {
        "welcome_messages": {
            "initial_welcome": {
                "title": "🎉 도라도라미와 속닥속닥",
                "description": "관리자와 개인 대화가 가능합니다!\n5초 내로 적응 상태 확인 메세지를 드릴 예정입니다.",
                "field_name": "📋 서버 규칙을 확인하시고 편안하게 이용해주세요!",
                "field_value": "심심해서 들어온거면 관리진들이 불러줄때 빨리 답장하고 부르면 음챗방 오셈\n답도 안하고 활동 안할거면 **걍 딴 서버 가라**\n그런 새끼 받아주는 서버 아님.",
                "color": "0x00ff00"
            },
            "adaptation_check": {
                "title": "🌟 서버 적응 안내",
                "description": "{member_mention}님, 서버에 잘 적응하고 계신가요?",
                "field_name": "📋 적응 확인",
                "field_value": "서버에 잘 적응하고 계신가요?\n궁금한 것들이 있으시면 언제든 물어보세요!\n\n적응을 완료하셨다면 아래 버튼을 눌러주세요.\n\n🟢 6일 내에 응답이 없으면 자동으로 강퇴됩니다.",
                "color": "0x00ff00"
            },
            "re_join": {
                "message": "🔄 {member_mention}님이 다시 서버에 입장하셨습니다!"
            }
        },
        "button_labels": {
            "delete": "삭제",
            "admin_review": "유지"
        },
        "responses": {
            "delete_confirm": "❌ 채널이 삭제됩니다.",
            "delete_permission_error": "❌ 본인만 삭제할 수 있습니다.",
            "admin_review_confirm": "✅ {doradori_mention} 관리자를 호출했습니다!",
            "admin_review_confirm_no_role": "✅ 관리자를 호출했습니다!",
            "admin_review_permission_error": "❌ 본인만 관리자를 호출할 수 있습니다.",
            "nickname_changed_male": "✅ 닉네임이 '(단팥빵) {name}'으로 변경되었습니다!",
            "nickname_changed_female": "✅ 닉네임이 '(메론빵) {name}'으로 변경되었습니다!",
            "nickname_change_failed": "❌ 닉네임 변경에 실패했습니다. 권한을 확인해주세요.",
            "nickname_already_has_prefix": "✅ 이미 성별 표시가 되어 있습니다!"
        },
        "settings": {
            "doradori_role_name": "도라도라미",
            "welcome_category": "신입환영",
            "adaptation_check_seconds": 5,
            "timeout_days": 6,
            "male_role_name": "남자",
            "female_role_name": "여자",
            "male_prefix": "(단팥빵)",
            "female_prefix": "(메론빵)"
        },
        "leave_messages": {
            "channel_deleted": "🚪 {member_name}님이 서버를 나가서 환영 채널이 삭제되었습니다."
        }
    }

# 웹서버 핸들러
async def health_check(request):
    return web.json_response({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "bot_ready": bot.is_ready(),
        "guilds": len(bot.guilds) if bot.is_ready() else 0
    })

async def root_handler(request):
    return web.json_response({
        "message": "Discord Bot is running!",
        "timestamp": datetime.now().isoformat()
    })

# 웹서버 시작
async def start_web_server():
    app = web.Application()
    app.router.add_get('/', root_handler)
    app.router.add_get('/health', health_check)
    
    port = int(os.getenv('PORT', 8000))
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    print(f"웹서버가 포트 {port}에서 시작되었습니다.")

# 닉네임 처리 함수
def get_clean_name(display_name):
    """닉네임에서 (단팥빵) 또는 (메론빵) 접두사를 제거한 순수한 이름을 반환"""
    clean_name = re.sub(r'^\((?:단팥빵|메론빵)\)\s*', '', display_name)
    return clean_name.strip()

def has_gender_prefix(display_name):
    """닉네임에 이미 성별 접두사가 있는지 확인"""
    return bool(re.match(r'^\((?:단팥빵|메론빵)\)', display_name))

async def change_nickname_with_gender_prefix(member):
    """성별에 따라 닉네임 앞에 접두사를 추가"""
    try:
        if has_gender_prefix(member.display_name):
            return "already_has_prefix"
        
        male_role = discord.utils.get(member.guild.roles, name=MESSAGES["settings"]["male_role_name"])
        female_role = discord.utils.get(member.guild.roles, name=MESSAGES["settings"]["female_role_name"])
        
        current_name = get_clean_name(member.display_name)
        
        new_nickname = None
        gender_type = None
        
        if male_role and male_role in member.roles:
            new_nickname = f"{MESSAGES['settings']['male_prefix']} {current_name}"
            gender_type = "male"
        elif female_role and female_role in member.roles:
            new_nickname = f"{MESSAGES['settings']['female_prefix']} {current_name}"
            gender_type = "female"
        
        if new_nickname:
            await member.edit(nick=new_nickname)
            return gender_type
        else:
            return "no_gender_role"
            
    except discord.Forbidden:
        return "no_permission"
    except Exception as e:
        print(f"닉네임 변경 오류: {e}")
        return "error"

# 메시지 설정 로드
MESSAGES = load_messages()

# 봇 설정
intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(
    command_prefix='!', 
    intents=intents
)

# Keep-Alive 함수들
@tasks.loop(minutes=5)  # 5분마다 실행 (더 자주)
async def keep_alive():
    """봇을 활성 상태로 유지"""
    try:
        # 봇 상태 업데이트
        await bot.change_presence(
            activity=discord.Game(name=f"서버 관리 | {len(bot.guilds)}개 서버"),
            status=discord.Status.online
        )
        print(f"Keep-Alive: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    except Exception as e:
        print(f"Keep-Alive 오류: {e}")

@tasks.loop(minutes=10)  # 10분마다 실행 (더 자주)
async def self_ping():
    """자신에게 HTTP 요청을 보내어 슬립 방지"""
    try:
        # Koyeb 앱 URL 자동 생성
        app_url = os.getenv('KOYEB_APP_URL')
        if not app_url:
            # 환경변수가 없으면 기본값 사용
            app_name = os.getenv('KOYEB_APP_NAME', 'your-app-name')
            app_url = f"https://{app_name}.koyeb.app"
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(f"{app_url}/health", timeout=30) as response:
                    print(f"Self-ping: {response.status} - {await response.text()}")
            except asyncio.TimeoutError:
                print("Self-ping: 타임아웃")
            except Exception as e:
                print(f"Self-ping 요청 오류: {e}")
    except Exception as e:
        print(f"Self-ping 오류: {e}")

# 첫 번째 메시지용 버튼 View 클래스
class InitialWelcomeView(discord.ui.View):
    def __init__(self, member_id):
        super().__init__(timeout=None)
        self.member_id = member_id

    @discord.ui.button(label="삭제", style=discord.ButtonStyle.danger, emoji="❌")
    async def delete_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.member_id:
            await interaction.response.send_message(
                MESSAGES["responses"]["delete_permission_error"], 
                ephemeral=True
            )
            return
        
        await interaction.response.send_message(
            MESSAGES["responses"]["delete_confirm"], 
            ephemeral=True
        )
        await interaction.followup.send("3초 후 채널이 삭제됩니다...")
        await asyncio.sleep(3)
        await interaction.channel.delete()

    @discord.ui.button(label="관리자 호출", style=discord.ButtonStyle.success, emoji="✅")
    async def admin_review_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.member_id:
            await interaction.response.send_message(
                MESSAGES["responses"]["admin_review_permission_error"], 
                ephemeral=True
            )
            return
        
        member = interaction.user
        nickname_result = await change_nickname_with_gender_prefix(member)
        
        doradori_role = discord.utils.get(interaction.guild.roles, name=MESSAGES["settings"]["doradori_role_name"])
        
        response_message = ""
        
        if nickname_result == "male":
            clean_name = get_clean_name(member.display_name)
            response_message += MESSAGES["responses"]["nickname_changed_male"].format(name=clean_name) + "\n"
        elif nickname_result == "female":
            clean_name = get_clean_name(member.display_name)
            response_message += MESSAGES["responses"]["nickname_changed_female"].format(name=clean_name) + "\n"
        elif nickname_result == "already_has_prefix":
            response_message += MESSAGES["responses"]["nickname_already_has_prefix"] + "\n"
        elif nickname_result in ["no_permission", "error"]:
            response_message += MESSAGES["responses"]["nickname_change_failed"] + "\n"
        
        if doradori_role:
            response_message += MESSAGES["responses"]["admin_review_confirm"].format(
                doradori_mention=doradori_role.mention
            )
        else:
            response_message += MESSAGES["responses"]["admin_review_confirm_no_role"]
        
        await interaction.response.send_message(response_message)

# 두 번째 메시지용 버튼 View 클래스
class AdaptationCheckView(discord.ui.View):
    def __init__(self, member_id):
        super().__init__(timeout=None)
        self.member_id = member_id

    @discord.ui.button(label="삭제", style=discord.ButtonStyle.danger, emoji="❌")
    async def delete_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.member_id:
            await interaction.response.send_message(
                MESSAGES["responses"]["delete_permission_error"], 
                ephemeral=True
            )
            return
        
        await interaction.response.send_message(
            MESSAGES["responses"]["delete_confirm"], 
            ephemeral=True
        )
        await interaction.followup.send("3초 후 채널이 삭제됩니다...")
        await asyncio.sleep(3)
        await interaction.channel.delete()

    @discord.ui.button(label="유지", style=discord.ButtonStyle.success, emoji="✅")
    async def admin_review_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.member_id:
            await interaction.response.send_message(
                MESSAGES["responses"]["admin_review_permission_error"], 
                ephemeral=True
            )
            return
        
        member = interaction.user
        nickname_result = await change_nickname_with_gender_prefix(member)
        
        doradori_role = discord.utils.get(interaction.guild.roles, name=MESSAGES["settings"]["doradori_role_name"])
        
        response_message = ""
        
        if nickname_result == "male":
            clean_name = get_clean_name(member.display_name)
            response_message += MESSAGES["responses"]["nickname_changed_male"].format(name=clean_name) + "\n"
        elif nickname_result == "female":
            clean_name = get_clean_name(member.display_name)
            response_message += MESSAGES["responses"]["nickname_changed_female"].format(name=clean_name) + "\n"
        elif nickname_result == "already_has_prefix":
            response_message += MESSAGES["responses"]["nickname_already_has_prefix"] + "\n"
        elif nickname_result in ["no_permission", "error"]:
            response_message += MESSAGES["responses"]["nickname_change_failed"] + "\n"
        
        if doradori_role:
            response_message += MESSAGES["responses"]["admin_review_confirm"].format(
                doradori_mention=doradori_role.mention
            )
        else:
            response_message += MESSAGES["responses"]["admin_review_confirm_no_role"]
        
        await interaction.response.send_message(response_message)

# 봇 이벤트
@bot.event
async def on_ready():
    print(f'{bot.user} 봇이 준비되었습니다!')
    
    # 웹서버 시작
    await start_web_server()
    
    # Keep-Alive 태스크 시작
    if not keep_alive.is_running():
        keep_alive.start()
    
    if not self_ping.is_running():
        self_ping.start()
    
    # 초기 상태 설정
    await bot.change_presence(
        activity=discord.Game(name=f"서버 관리 | {len(bot.guilds)}개 서버"),
        status=discord.Status.online
    )

@bot.event
async def on_member_join(member):
    welcome_category = discord.utils.get(member.guild.categories, name=MESSAGES["settings"]["welcome_category"])
    if welcome_category:
        existing_channel = discord.utils.get(welcome_category.channels, name=f"환영-{member.name}")
        if existing_channel:
            await existing_channel.send(MESSAGES["welcome_messages"]["re_join"]["message"].format(member_mention=member.mention))
            return
    
    if not welcome_category:
        welcome_category = await member.guild.create_category(MESSAGES["settings"]["welcome_category"])
    
    overwrites = {
        member.guild.default_role: discord.PermissionOverwrite(read_messages=False),
        member: discord.PermissionOverwrite(read_messages=True, send_messages=True),
        member.guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
    }
    
    doradori_role = discord.utils.get(member.guild.roles, name=MESSAGES["settings"]["doradori_role_name"])
    if doradori_role:
        overwrites[doradori_role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)
    
    channel = await welcome_category.create_text_channel(
        f"환영-{member.name}",
        overwrites=overwrites
    )
    
    initial_welcome = MESSAGES["welcome_messages"]["initial_welcome"]
    embed = discord.Embed(
        title=initial_welcome["title"],
        description=initial_welcome["description"],
        color=int(initial_welcome["color"], 16)
    )
    embed.add_field(
        name=initial_welcome["field_name"],
        value=initial_welcome["field_value"],
        inline=False
    )
    
    doradori_role = discord.utils.get(member.guild.roles, name=MESSAGES["settings"]["doradori_role_name"])
    if doradori_role:
        embed.add_field(
            name="",
            value=f"{doradori_role.mention}",
            inline=False
        )
    
    view = InitialWelcomeView(member.id)
    await channel.send(embed=embed, view=view)
    
    await asyncio.sleep(MESSAGES["settings"]["adaptation_check_seconds"])
    
    adaptation_check = MESSAGES["welcome_messages"]["adaptation_check"]
    embed = discord.Embed(
        title=adaptation_check["title"],
        description=adaptation_check["description"].format(member_mention=member.mention),
        color=int(adaptation_check["color"], 16)
    )
    embed.add_field(
        name=adaptation_check["field_name"],
        value=adaptation_check["field_value"],
        inline=False
    )
    
    view = AdaptationCheckView(member.id)
    await channel.send(embed=embed, view=view)

@bot.event
async def on_member_remove(member):
    welcome_category = discord.utils.get(member.guild.categories, name=MESSAGES["settings"]["welcome_category"])
    if welcome_category:
        channel = discord.utils.get(welcome_category.channels, name=f"환영-{member.name}")
        if channel:
            await channel.send(MESSAGES["leave_messages"]["channel_deleted"].format(member_name=member.name))
            await asyncio.sleep(5)
            await channel.delete()

# 상태 확인 명령어
@bot.command(name='상태')
async def status(ctx):
    """봇 상태 확인"""
    embed = discord.Embed(
        title="🤖 봇 상태",
        color=0x00ff00
    )
    embed.add_field(name="서버 수", value=f"{len(bot.guilds)}개", inline=True)
    embed.add_field(name="지연시간", value=f"{round(bot.latency * 1000)}ms", inline=True)
    embed.add_field(name="실행시간", value=f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", inline=True)
    
    await ctx.send(embed=embed)

# 봇 실행
if __name__ == "__main__":
    token = os.getenv('DISCORD_TOKEN')
    if not token:
        print("오류: DISCORD_TOKEN 환경변수가 설정되지 않았습니다.")
        print("Koyeb에서 환경변수를 설정하세요.")
        exit(1)
    
    bot.run(token)
