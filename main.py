import discord
from discord.ext import commands
import os
import asyncio
from datetime import datetime, timedelta
import json

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
            "admin_review_permission_error": "❌ 본인만 관리자를 호출할 수 있습니다."
        },
        "settings": {
            "doradori_role_name": "도라도라미",
            "welcome_category": "신입환영",
            "adaptation_check_seconds": 5,
            "timeout_days": 6
        },
        "leave_messages": {
            "channel_deleted": "🚪 {member_name}님이 서버를 나가서 환영 채널이 삭제되었습니다."
        }
    }

# 메시지 설정 로드
MESSAGES = load_messages()

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
DORADORI_ROLE_NAME = MESSAGES["settings"]["doradori_role_name"]

# 처리 중인 멤버 추적 (중복 방지) - 더 강력한 락 메커니즘
processing_members = set()
member_locks = {}  # 멤버별 개별 락
# 최근 처리된 멤버 추적 (5분간 기록)
recent_processed = {}
# 5초 후 확인 대기 중인 멤버들
pending_checks = {}

@bot.event
async def on_ready():
    print(f'{bot.user}가 준비되었습니다!')
    print(f'봇이 {len(bot.guilds)}개의 서버에 연결되어 있습니다.')
    
    # 봇 상태 설정
    await bot.change_presence(
        activity=discord.Game(name="신입 환영하기"),
        status=discord.Status.online
    )
    
    # 처리 중인 멤버 목록 초기화
    processing_members.clear()
    recent_processed.clear()
    member_locks.clear()
    
    # 5초 후 확인 작업 시작
    bot.loop.create_task(check_adaptation_loop())

async def check_adaptation_loop():
    """5초 후 적응 확인을 위한 백그라운드 작업"""
    while True:
        try:
            current_time = datetime.now()
            to_remove = []
            
            for key, check_data in pending_checks.items():
                if current_time >= check_data['check_time']:
                    guild_id, member_id = key.split('-')
                    guild = bot.get_guild(int(guild_id))
                    member = guild.get_member(int(member_id)) if guild else None
                    
                    if guild and member:
                        await send_adaptation_check(guild, member, check_data['channel_id'])
                    
                    to_remove.append(key)
            
            # 처리된 항목들 제거
            for key in to_remove:
                del pending_checks[key]
            
        except Exception as e:
            print(f"적응 확인 루프 오류: {e}")
        
        # 1초마다 확인 (5초 간격이므로 더 자주 확인)
        await asyncio.sleep(1)

async def send_adaptation_check(guild, member, channel_id):
    """5초 후 적응 확인 메시지 전송"""
    try:
        channel = bot.get_channel(channel_id)
        if not channel:
            return
        
        # 메시지 설정에서 템플릿 가져오기
        msg_config = MESSAGES["welcome_messages"]["adaptation_check"]
        
        embed = discord.Embed(
            title=msg_config["title"],
            description=msg_config["description"].format(member_mention=member.mention),
            color=int(msg_config["color"], 16),
            timestamp=datetime.now()
        )
        
        embed.add_field(
            name=msg_config["field_name"],
            value=msg_config["field_value"],
            inline=False
        )
        
        # 버튼 생성
        view = AdaptationView(member, channel)
        await channel.send(embed=embed, view=view)
        
        print(f"{member.display_name}님에게 적응 확인 메시지를 보냈습니다.")
        
    except Exception as e:
        print(f"적응 확인 메시지 전송 오류: {e}")

class AdaptationView(discord.ui.View):
    def __init__(self, member, channel):
        super().__init__(timeout=MESSAGES["settings"]["timeout_days"] * 24 * 3600)  # 6일
        self.member = member
        self.channel = channel
    
    @discord.ui.button(label=MESSAGES["button_labels"]["delete"], style=discord.ButtonStyle.red, emoji='🗑️')
    async def delete_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id == self.member.id:
            await interaction.response.send_message(MESSAGES["responses"]["delete_confirm"], ephemeral=True)
            await asyncio.sleep(2)
            try:
                await self.channel.delete()
            except:
                pass
        else:
            await interaction.response.send_message(MESSAGES["responses"]["delete_permission_error"], ephemeral=True)
    
    @discord.ui.button(label=MESSAGES["button_labels"]["admin_review"], style=discord.ButtonStyle.green, emoji='✅')
    async def admin_review_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id == self.member.id:
            doradori_role = discord.utils.get(interaction.guild.roles, name=DORADORI_ROLE_NAME)
            if doradori_role:
                response = MESSAGES["responses"]["admin_review_confirm"].format(doradori_mention=doradori_role.mention)
                await interaction.response.send_message(response)
            else:
                await interaction.response.send_message(MESSAGES["responses"]["admin_review_confirm_no_role"])
        else:
            await interaction.response.send_message(MESSAGES["responses"]["admin_review_permission_error"], ephemeral=True)

class InitialView(discord.ui.View):
    def __init__(self, member, channel, doradori_role):
        super().__init__(timeout=300)
        self.member = member
        self.channel = channel
        self.doradori_role = doradori_role
    
    @discord.ui.button(label=MESSAGES["button_labels"]["delete"], style=discord.ButtonStyle.red, emoji='🗑️')
    async def delete_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id == self.member.id:
            await interaction.response.send_message(MESSAGES["responses"]["delete_confirm"], ephemeral=True)
            await asyncio.sleep(2)
            try:
                await self.channel.delete()
            except:
                pass
        else:
            await interaction.response.send_message(MESSAGES["responses"]["delete_permission_error"], ephemeral=True)
    
    @discord.ui.button(label="관리자 호출", style=discord.ButtonStyle.green, emoji='✅')
    async def admin_review_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id == self.member.id:
            if self.doradori_role:
                response = MESSAGES["responses"]["admin_review_confirm"].format(doradori_mention=self.doradori_role.mention)
                await interaction.response.send_message(response)
            else:
                await interaction.response.send_message(MESSAGES["responses"]["admin_review_confirm_no_role"])
        else:
            await interaction.response.send_message(MESSAGES["responses"]["admin_review_permission_error"], ephemeral=True)

@bot.event
async def on_member_join(member):
    """새로운 멤버가 서버에 입장했을 때 실행되는 함수"""
    guild = member.guild
    current_time = datetime.now()
    
    # 봇인 경우 무시
    if member.bot:
        return
    
    # 멤버별 고유 식별자
    member_key = f"{guild.id}-{member.id}"
    
    # 개별 락 생성 (이미 있으면 사용)
    if member_key not in member_locks:
        member_locks[member_key] = asyncio.Lock()
    
    # 멤버별 락 획득
    async with member_locks[member_key]:
        # 이미 처리 중인 멤버인지 확인
        if member_key in processing_members:
            print(f"{member.display_name}님은 이미 처리 중입니다.")
            return
        
        # 최근 5분 내에 처리한 멤버인지 확인
        if member_key in recent_processed:
            time_diff = (current_time - recent_processed[member_key]).total_seconds()
            if time_diff < 300:  # 5분 = 300초
                print(f"{member.display_name}님은 최근에 이미 처리되었습니다.")
                return
        
        # 처리 중 목록에 추가
        processing_members.add(member_key)
        recent_processed[member_key] = current_time
        
        try:
            # 도라도라미 역할을 가진 멤버들 찾기
            doradori_role = discord.utils.get(guild.roles, name=DORADORI_ROLE_NAME)
            
            if not doradori_role:
                print(f"'{DORADORI_ROLE_NAME}' 역할을 찾을 수 없습니다.")
                return
            
            # 채널 이름 생성 (고유성 보장)
            timestamp = datetime.now().strftime('%m%d-%H%M')
            channel_name = f"환영-{member.display_name}-{timestamp}"
            
            # 기존 채널 검색 (더 포괄적)
            existing_channels = []
            for ch in guild.channels:
                # 같은 멤버 이름으로 시작하는 모든 환영 채널 찾기
                if (isinstance(ch, discord.TextChannel) and 
                    ch.name.startswith(f"환영-{member.display_name}-")):
                    existing_channels.append(ch)
            
            # 기존 채널이 있으면 재사용
            if existing_channels:
                existing_channel = existing_channels[0]
                print(f"{member.display_name}님을 위한 기존 채널 발견: {existing_channel.name}")
                
                # 추가 중복 채널들 삭제
                for extra_channel in existing_channels[1:]:
                    try:
                        await extra_channel.delete()
                        print(f"중복 채널 삭제: {extra_channel.name}")
                    except Exception as e:
                        print(f"중복 채널 삭제 실패: {e}")
                
                # 기존 채널에 재입장 메시지
                re_join_msg = MESSAGES["welcome_messages"]["re_join"]["message"].format(member_mention=member.mention)
                await existing_channel.send(re_join_msg)
                
                # 재입장 시에도 초기 안내문 전송
                initial_config = MESSAGES["welcome_messages"]["initial_welcome"]
                
                initial_embed = discord.Embed(
                    title=initial_config["title"],
                    description=initial_config["description"],
                    color=int(initial_config["color"], 16),
                    timestamp=datetime.now()
                )
                
                initial_embed.add_field(
                    name=initial_config["field_name"],
                    value=initial_config["field_value"],
                    inline=False
                )
                
                if member.avatar:
                    initial_embed.set_thumbnail(url=member.avatar.url)
                
                initial_view = InitialView(member, existing_channel, doradori_role)
                await existing_channel.send(embed=initial_embed, view=initial_view)
                
                # 도라도라미 멘션 추가
                await existing_channel.send(f"{doradori_role.mention}")
                
                # 5초 후 적응 확인 스케줄 등록 (재입장 시에도)
                check_seconds = MESSAGES["settings"].get("adaptation_check_seconds", 5)
                check_time = current_time + timedelta(seconds=check_seconds)
                pending_checks[member_key] = {
                    'check_time': check_time,
                    'channel_id': existing_channel.id,
                    'member_id': member.id,
                    'guild_id': guild.id
                }
                
                print(f"재입장 - {member.display_name}님에게 환영 메시지 전송 완료")
                print(f"{check_seconds}초 후 적응 확인 예정: {check_time}")
                return
            
            # 도라도라미 역할을 가진 멤버들 중 온라인인 사람 찾기
            online_doradori_members = [
                m for m in doradori_role.members 
                if m.status != discord.Status.offline and not m.bot
            ]
            
            if not online_doradori_members:
                online_doradori_members = [m for m in doradori_role.members if not m.bot]
            
            if not online_doradori_members:
                print("도라도라미 역할을 가진 멤버가 없습니다.")
                return
            
            # 채널 권한 설정
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(read_messages=False),
                member: discord.PermissionOverwrite(read_messages=True, send_messages=True),
                doradori_role: discord.PermissionOverwrite(read_messages=True, send_messages=True),
                guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
            }
            
            # 카테고리 찾기
            category = discord.utils.get(guild.categories, name=MESSAGES["settings"]["welcome_category"])
            
            # 채널 생성 시도
            welcome_channel = None
            max_attempts = 3
            
            for attempt in range(max_attempts):
                try:
                    # 채널 생성 직전 한 번 더 확인
                    final_check = discord.utils.get(guild.channels, name=channel_name)
                    if final_check:
                        print(f"생성 직전 확인: {channel_name} 채널이 이미 존재합니다.")
                        welcome_channel = final_check
                        break
                    
                    # 채널 생성
                    welcome_channel = await guild.create_text_channel(
                        name=channel_name,
                        overwrites=overwrites,
                        category=category,
                        topic=f"{member.mention}님을 위한 환영 채널입니다.",
                        reason=f"{member.display_name}님의 환영 채널 생성"
                    )
                    print(f"채널 생성 성공: {welcome_channel.name}")
                    break
                    
                except discord.HTTPException as e:
                    if "already exists" in str(e).lower() or e.status == 400:
                        print(f"채널 생성 실패 (이미 존재): {e}")
                        # 이미 존재하는 채널 찾기
                        existing = discord.utils.get(guild.channels, name=channel_name)
                        if existing:
                            welcome_channel = existing
                            break
                        else:
                            # 타임스탬프 변경해서 재시도
                            timestamp = datetime.now().strftime('%m%d-%H%M%S')
                            channel_name = f"환영-{member.display_name}-{timestamp}"
                    else:
                        print(f"채널 생성 실패 (시도 {attempt + 1}/{max_attempts}): {e}")
                        if attempt == max_attempts - 1:
                            raise
                        await asyncio.sleep(1)
            
            if not welcome_channel:
                print("채널 생성에 실패했습니다.")
                return
            
            # 생성 후 잠시 대기
            await asyncio.sleep(0.5)
            
            # 중복 채널 정리 (생성 후)
            await cleanup_duplicate_channels_for_member(guild, member.display_name, welcome_channel.id)
            
            # 메시지 설정에서 첫 번째 환영 메시지 가져오기
            initial_config = MESSAGES["welcome_messages"]["initial_welcome"]
            
            initial_embed = discord.Embed(
                title=initial_config["title"],
                description=initial_config["description"],
                color=int(initial_config["color"], 16),
                timestamp=datetime.now()
            )
            
            initial_embed.add_field(
                name=initial_config["field_name"],
                value=initial_config["field_value"],
                inline=False
            )
            
            if member.avatar:
                initial_embed.set_thumbnail(url=member.avatar.url)
            
            initial_view = InitialView(member, welcome_channel, doradori_role)
            await welcome_channel.send(embed=initial_embed, view=initial_view)
            
            # 도라도라미 멘션 추가
            await welcome_channel.send(f"{doradori_role.mention}")
            
            # 5초 후 적응 확인 스케줄 등록
            check_seconds = MESSAGES["settings"].get("adaptation_check_seconds", 5)
            check_time = current_time + timedelta(seconds=check_seconds)
            pending_checks[member_key] = {
                'check_time': check_time,
                'channel_id': welcome_channel.id,
                'member_id': member.id,
                'guild_id': guild.id
            }
            
            print(f"{member.display_name}님을 위한 환영 채널이 생성되었습니다: {welcome_channel.name}")
            print(f"{check_seconds}초 후 적응 확인 예정: {check_time}")
            
        except Exception as e:
            print(f"채널 생성 중 오류가 발생했습니다: {e}")
            import traceback
            traceback.print_exc()
        finally:
            # 처리 완료 후 목록에서 제거
            processing_members.discard(member_key)

@bot.event
async def on_member_remove(member):
    """멤버가 서버를 나갔을 때 실행되는 함수"""
    guild = member.guild
    
    # 봇인 경우 무시
    if member.bot:
        return
    
    try:
        # 해당 멤버의 환영 채널 찾기
        member_channels = []
        for channel in guild.channels:
            if (isinstance(channel, discord.TextChannel) and 
                channel.name.startswith(f"환영-{member.display_name}-")):
                member_channels.append(channel)
        
        # 환영 채널이 있으면 삭제
        if member_channels:
            # 도라도라미 역할 찾기 (로그 전송용)
            doradori_role = discord.utils.get(guild.roles, name=DORADORI_ROLE_NAME)
            
            # 채널 삭제 전에 로그 메시지 준비
            leave_message = MESSAGES["leave_messages"]["channel_deleted"].format(member_name=member.display_name)
            
            # 각 채널 삭제
            for channel in member_channels:
                try:
                    # 채널 삭제 전에 도라도라미들에게 알림 (가능한 경우)
                    if doradori_role and doradori_role.members:
                        try:
                            await channel.send(f"{doradori_role.mention} {leave_message}")
                            # 잠시 대기 후 삭제
                            await asyncio.sleep(2)
                        except:
                            pass
                    
                    await channel.delete()
                    print(f"환영 채널 삭제 완료: {channel.name} ({member.display_name}님 퇴장)")
                    
                except Exception as e:
                    print(f"환영 채널 삭제 실패: {e}")
            
            # pending_checks에서 해당 멤버 제거
            member_key = f"{guild.id}-{member.id}"
            if member_key in pending_checks:
                del pending_checks[member_key]
            
            # 기타 추적 목록에서도 제거
            processing_members.discard(member_key)
            recent_processed.pop(member_key, None)
            
            print(f"{member.display_name}님이 서버를 나가서 환영 채널 {len(member_channels)}개를 삭제했습니다.")
        
    except Exception as e:
        print(f"멤버 퇴장 처리 중 오류: {e}")
        import traceback
        traceback.print_exc()

async def cleanup_duplicate_channels_for_member(guild, member_name, keep_channel_id):
    """특정 멤버의 중복 채널들을 정리하는 함수"""
    try:
        # 해당 멤버의 모든 환영 채널 찾기
        member_channels = [
            ch for ch in guild.channels 
            if (isinstance(ch, discord.TextChannel) and 
                ch.name.startswith(f"환영-{member_name}-") and 
                ch.id != keep_channel_id)
        ]
        
        # 중복 채널들 삭제
        for channel in member_channels:
            try:
                await channel.delete()
                print(f"중복 채널 삭제 완료: {channel.name}")
            except Exception as e:
                print(f"중복 채널 삭제 실패: {e}")
        
        if member_channels:
            print(f"{member_name}님의 중복 채널 {len(member_channels)}개를 정리했습니다.")
            
    except Exception as e:
        print(f"중복 채널 정리 중 오류: {e}")

@bot.command(name='중복채널정리')
@commands.has_permissions(manage_channels=True)
async def cleanup_duplicate_channels(ctx):
    """중복된 환영 채널을 정리하는 명령어"""
    guild = ctx.guild
    
    # 환영 채널들 찾기
    welcome_channels = [
        ch for ch in guild.channels 
        if isinstance(ch, discord.TextChannel) and ch.name.startswith("환영-")
    ]
    
    if not welcome_channels:
        await ctx.send("중복된 환영 채널이 없습니다.")
        return
    
    # 멤버별로 그룹화
    member_channels = {}
    for channel in welcome_channels:
        # 채널명에서 멤버명 추출 (환영-멤버명-타임스탬프 형식)
        parts = channel.name.split('-')
        if len(parts) >= 2:
            member_name = parts[1]
            if member_name not in member_channels:
                member_channels[member_name] = []
            member_channels[member_name].append(channel)
    
    # 각 멤버별로 가장 최근 채널 하나만 남기고 나머지 삭제
    deleted_count = 0
    for member_name, channels in member_channels.items():
        if len(channels) > 1:
            # 채널 생성 시간 기준으로 정렬 (최신순)
            channels.sort(key=lambda x: x.created_at, reverse=True)
            
            # 가장 최근 채널 하나만 남기고 나머지 삭제
            for channel in channels[1:]:
                try:
                    await channel.delete()
                    deleted_count += 1
                    print(f"중복 채널 삭제: {channel.name}")
                except Exception as e:
                    print(f"채널 삭제 실패: {e}")
    
    await ctx.send(f"중복 채널 정리 완료! {deleted_count}개의 중복 채널을 삭제했습니다.")

# 봇 실행
if __name__ == '__main__':
    if TOKEN:
        bot.run(TOKEN)
    else:
        print("DISCORD_TOKEN 환경 변수가 설정되지 않았습니다.")
