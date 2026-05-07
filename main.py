import discord
from discord.ext import commands
from discord.ui import View, Select
import os
import datetime
import random
from dotenv import load_dotenv

load_dotenv()

# ---------------- AYARLAR ----------------
KAYIT_YETKILI = 1499363286615855144
KAYITSIZ_ROL = 1499363348175782028

FUTBOLCU_ROL = 1499363339892162560
BASKAN_ROL = 1499363343683817542
UYE_ROL = 1499363345189310615

JOIN_KANAL = 1499363754402517124

# ---------------- INTENTS ----------------
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(
    command_prefix=".",
    intents=intents
)

kayit_sayilari = {}
invites_cache = {}
kostebek_katilim = []

# ---------------- READY ----------------
@bot.event
async def on_ready():

    for guild in bot.guilds:
        invites_cache[guild.id] = await guild.invites()

    print(f"Bot aktif: {bot.user}")

# ---------------- INVITE TRACK ----------------
async def find_invite(member):

    guild = member.guild

    old_invites = invites_cache.get(guild.id, [])
    new_invites = await guild.invites()

    invites_cache[guild.id] = new_invites

    for new in new_invites:
        for old in old_invites:

            if new.code == old.code and new.uses > old.uses:
                return new

    return None

# ---------------- ERROR ----------------
@bot.event
async def on_command_error(ctx, error):

    if isinstance(error, commands.CommandNotFound):
        return await ctx.send("❌ Komut yok!")

    elif isinstance(error, commands.MissingRequiredArgument):
        return await ctx.send("❌ Eksik bilgi!")

    elif isinstance(error, commands.MemberNotFound):
        return await ctx.send("❌ Kullanıcı bulunamadı!")

    else:
        await ctx.send("❌ Hata oluştu!")
        raise error

# ---------------- KAYITSIZ ----------------
@bot.command()
async def kayitsiz(ctx, member: discord.Member = None):

    if KAYIT_YETKILI not in [r.id for r in ctx.author.roles]:
        return await ctx.send("❌ Yetkin yok!")

    kayitsiz_rol = ctx.guild.get_role(KAYITSIZ_ROL)

    if member is None:
        return await ctx.send("❌ Kullanıcı belirt!")

    await member.edit(roles=[])

    await member.add_roles(kayitsiz_rol)

    await ctx.send(
        f"🔴 {member.mention} kayıtsız yapıldı."
    )

# ---------------- KAYIT MENU ----------------
class KayitMenu(View):

    def __init__(self, member, yetkili):
        super().__init__(timeout=60)

        self.member = member
        self.yetkili = yetkili

    @discord.ui.select(
        placeholder="Birini Seçin",
        options=[
            discord.SelectOption(
                label="Futbolcu",
                value="futbolcu"
            ),
            discord.SelectOption(
                label="Üye",
                value="uye"
            ),
            discord.SelectOption(
                label="Başkan",
                value="baskan"
            ),
        ]
    )
    async def select_callback(
        self,
        interaction: discord.Interaction,
        select: Select
    ):

        if interaction.user != self.yetkili:
            return await interaction.response.send_message(
                "❌ Sana ait değil!",
                ephemeral=True
            )

        secim = select.values[0]

        if secim == "futbolcu":
            rol = interaction.guild.get_role(FUTBOLCU_ROL)

        elif secim == "uye":
            rol = interaction.guild.get_role(UYE_ROL)

        elif secim == "baskan":
            rol = interaction.guild.get_role(BASKAN_ROL)

        kayitsiz = interaction.guild.get_role(KAYITSIZ_ROL)

        await self.member.add_roles(rol)

        if kayitsiz in self.member.roles:
            await self.member.remove_roles(kayitsiz)

        kayit_sayilari[self.yetkili.id] = (
            kayit_sayilari.get(self.yetkili.id, 0) + 1
        )

        await interaction.response.send_message(
            f"✅ {self.member.mention} kayıt edildi: {rol.name}",
            ephemeral=True
        )

# ---------------- KAYIT ----------------
@bot.command()
async def k(ctx, member: discord.Member, *, isim):

    if KAYIT_YETKILI not in [r.id for r in ctx.author.roles]:
        return await ctx.send("❌ Yetkin yok!")

    await member.edit(nick=isim)

    embed = discord.Embed(
        title="Birini Seçin",
        description=f"{member.mention} için kayıt türünü seç.",
        color=discord.Color.blue()
    )

    await ctx.send(
        embed=embed,
        view=KayitMenu(member, ctx.author)
    )

# ---------------- KAYITSAY ----------------
@bot.command(name="kayıtsay", aliases=["kayitsay"])
async def kayitsay(ctx):

    sayi = kayit_sayilari.get(ctx.author.id, 0)

    await ctx.send(
        f"📊 {ctx.author.mention} toplam kayıt: **{sayi}**"
    )

# ---------------- JOIN ----------------
@bot.event
async def on_member_join(member):

    guild = member.guild

    account_age = (
        datetime.datetime.utcnow() - member.created_at
    ).days

    invite = await find_invite(member)

    invite_info = "Bilinmiyor"

    if invite:
        invite_info = f"{invite.code} - {invite.inviter}"

    kanal = guild.get_channel(JOIN_KANAL)

    if kanal:

        embed = discord.Embed(
            title="🆕 Yeni Kullanıcı Katıldı",
            color=discord.Color.green()
        )

        embed.add_field(
            name="Kullanıcı",
            value=member.mention,
            inline=True
        )

        embed.add_field(
            name="ID",
            value=member.id,
            inline=True
        )

        embed.add_field(
            name="Hesap Yaşı",
            value=f"{account_age} gün",
            inline=True
        )

        embed.add_field(
            name="Invite",
            value=invite_info,
            inline=False
        )

        await kanal.send(
            content=f"<@&{KAYIT_YETKILI}>",
            embed=embed,
            allowed_mentions=discord.AllowedMentions(
                roles=True
            )
        )

# ---------------- KÖSTEBEK ----------------
class KostebekView(View):

    def __init__(self):
        super().__init__(timeout=120)

    @discord.ui.button(
        label="Katıl",
        style=discord.ButtonStyle.green
    )
    async def katil(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        if interaction.user in kostebek_katilim:
            return await interaction.response.send_message(
                "❌ Zaten katıldın!",
                ephemeral=True
            )

        kostebek_katilim.append(interaction.user)

        await interaction.response.send_message(
            "✅ Oyuna katıldın!",
            ephemeral=True
        )

# oyun aç
@bot.command()
async def kostebekozel(ctx):

    kostebek_katilim.clear()

    embed = discord.Embed(
        title="🕵️ Gizli Köstebek",
        description="Katılmak için butona bas.\nBaşlatmak için `.baslat` yaz.",
        color=discord.Color.orange()
    )

    await ctx.send(
        embed=embed,
        view=KostebekView()
    )

# başlat
@bot.command()
async def baslat(ctx):

    if len(kostebek_katilim) < 3:
        return await ctx.send(
            "❌ En az 3 kişi gerekli!"
        )

    secilen = random.choice(kostebek_katilim)

    try:

        await ctx.author.send(
            f"🕵️ Gizli Köstebek: {secilen.mention}"
        )

        await ctx.send(
            "🎮 Oyun başladı! Köstebek DM'den gönderildi."
        )

    except:
        await ctx.send("❌ DM kapalı!")

    kostebek_katilim.clear()

# ---------------- YARDIM ----------------
@bot.command(
    name="yardım",
    aliases=["yardim"]
)
async def yardim(ctx):

    embed = discord.Embed(
        title="📖 Yardım Menüsü",
        color=discord.Color.blue()
    )

    embed.add_field(
        name="📝 Kayıt Komutları",
        value=(
            "`.k @üye isim`\n"
            "`.kayitsiz @üye`\n"
            "`.kayıtsay`"
        ),
        inline=False
    )

    embed.add_field(
        name="🎮 Eğlence",
        value=(
            "`.kostebekozel`\n"
            "`.baslat`"
        ),
        inline=False
    )

    await ctx.send(embed=embed)

# ---------------- RUN ----------------
bot.run(os.getenv("TOKEN"))
