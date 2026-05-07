import discord
from discord.ext import commands
from discord.ui import View
import os
import datetime
import random
import re
from dotenv import load_dotenv

load_dotenv()

# ---------------- AYARLAR ----------------
KAYIT_YETKILI = 1499363286615855144
KAYITSIZ_ROL = 1499363348175782028

FUTBOLCU_ROL = 1499363339892162560
BASKAN_ROL = 1499363343683817542
UYE_ROL = 1499363345189310615

JOIN_KANAL = 1499363754402517124
DEGER_LOG_KANAL = 1499367585266012233

# ---------------- INTENTS ----------------
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix=".", intents=intents)

kayit_sayilari = {}
kostebek_katilim = []

# ---------------- READY ----------------
@bot.event
async def on_ready():
    print(f"Bot aktif: {bot.user}")

# ---------------- ERROR ----------------
@bot.event
async def on_command_error(ctx, error):

    if isinstance(error, commands.CommandNotFound):
        return await ctx.send("❌ Komut yok!")

    elif isinstance(error, commands.MissingRequiredArgument):
        return await ctx.send("❌ Eksik bilgi!")

    elif isinstance(error, commands.MemberNotFound):
        return await ctx.send("❌ Kullanıcı bulunamadı!")

    elif isinstance(error, commands.MissingPermissions):
        return await ctx.send("❌ Yönetici yetkisi gerekli!")

    else:
        await ctx.send("❌ Hata oluştu!")
        raise error

# ---------------- DEĞER SİSTEMİ ----------------
def get_value(nick):
    if not nick:
        return 0
    match = re.search(r"(\d+)M", nick)
    return int(match.group(1)) if match else 0

# ---------------- DEĞER EKLE ----------------
@bot.command()
async def dver(ctx, member: discord.Member, miktar: int):

    if KAYIT_YETKILI not in [r.id for r in ctx.author.roles]:
        return await ctx.send("❌ Yetkin yok!")

    value = get_value(member.display_name)
    value += miktar

    parts = member.display_name.split("|")

    isim = parts[0].strip() if len(parts) > 0 else member.name
    ulke = parts[2].strip() if len(parts) > 2 else "TR"
    mevki = parts[3].strip() if len(parts) > 3 else "Oyuncu"

    new_nick = f"{isim} | {value}M | {ulke} | {mevki}"

    await member.edit(nick=new_nick)

    log = ctx.guild.get_channel(DEGER_LOG_KANAL)
    if log:
        embed = discord.Embed(title="📈 Değer Eklendi", color=discord.Color.green())
        embed.add_field(name="Oyuncu", value=member.mention)
        embed.add_field(name="Miktar", value=f"+{miktar}M")
        embed.add_field(name="Yeni", value=f"{value}M")
        embed.add_field(name="Yetkili", value=ctx.author.mention)
        await log.send(embed=embed)

    await ctx.send(f"✅ +{miktar}M eklendi → {member.mention}")

# ---------------- DEĞER SİL ----------------
@bot.command()
async def dsil(ctx, member: discord.Member, miktar: int):

    if KAYIT_YETKILI not in [r.id for r in ctx.author.roles]:
        return await ctx.send("❌ Yetkin yok!")

    value = get_value(member.display_name)
    value -= miktar
    if value < 0:
        value = 0

    parts = member.display_name.split("|")

    isim = parts[0].strip() if len(parts) > 0 else member.name
    ulke = parts[2].strip() if len(parts) > 2 else "TR"
    mevki = parts[3].strip() if len(parts) > 3 else "Oyuncu"

    new_nick = f"{isim} | {value}M | {ulke} | {mevki}"

    await member.edit(nick=new_nick)

    log = ctx.guild.get_channel(DEGER_LOG_KANAL)
    if log:
        embed = discord.Embed(title="📉 Değer Silindi", color=discord.Color.red())
        embed.add_field(name="Oyuncu", value=member.mention)
        embed.add_field(name="Miktar", value=f"-{miktar}M")
        embed.add_field(name="Yeni", value=f"{value}M")
        await log.send(embed=embed)

    await ctx.send(f"❌ -{miktar}M silindi → {member.mention}")

# ---------------- KAYITSIZ ----------------
@bot.command()
async def kayitsiz(ctx, member: discord.Member = None):

    if KAYIT_YETKILI not in [r.id for r in ctx.author.roles]:
        return await ctx.send("❌ Yetkin yok!")

    role = ctx.guild.get_role(KAYITSIZ_ROL)

    if not member:
        return await ctx.send("❌ Kullanıcı belirt!")

    await member.edit(roles=[])
    await member.add_roles(role)

    await ctx.send(f"🔴 {member.mention} kayıtsız yapıldı.")

# ---------------- KAYIT ----------------
class KayitMenu(View):
    def __init__(self, member, yetkili):
        super().__init__(timeout=60)
        self.member = member
        self.yetkili = yetkili

    @discord.ui.select(
        placeholder="Birini Seçin",
        options=[
            discord.SelectOption(label="Futbolcu", value="futbolcu"),
            discord.SelectOption(label="Üye", value="uye"),
            discord.SelectOption(label="Başkan", value="baskan"),
        ],
    )
    async def callback(self, interaction, select):

        if interaction.user != self.yetkili:
            return await interaction.response.send_message("❌ Sana ait değil!", ephemeral=True)

        secim = select.values[0]

        if secim == "futbolcu":
            rol = interaction.guild.get_role(FUTBOLCU_ROL)
        elif secim == "uye":
            rol = interaction.guild.get_role(UYE_ROL)
        else:
            rol = interaction.guild.get_role(BASKAN_ROL)

        kayitsiz = interaction.guild.get_role(KAYITSIZ_ROL)

        await self.member.add_roles(rol)
        if kayitsiz in self.member.roles:
            await self.member.remove_roles(kayitsiz)

        kayit_sayilari[self.yetkili.id] = kayit_sayilari.get(self.yetkili.id, 0) + 1

        await interaction.response.send_message("✅ Kayıt yapıldı!", ephemeral=True)

# ---------------- JOIN ----------------
@bot.event
async def on_member_join(member):

    kanal = member.guild.get_channel(JOIN_KANAL)

    if kanal:
        embed = discord.Embed(
            title="🆕 Yeni Üye",
            description=f"{member.mention} katıldı!",
            color=discord.Color.green()
        )

        await kanal.send(
            content=f"<@&{KAYIT_YETKILI}>",
            embed=embed,
            allowed_mentions=discord.AllowedMentions(roles=True)
        )

# ---------------- KÖSTEBEK ----------------
@bot.command()
@commands.has_permissions(administrator=True)
async def kostebekozel(ctx):

    kostebek_katilim.clear()

    embed = discord.Embed(
        title="🕵️ Köstebek Oyunu",
        description="Katılmak için butona bas",
        color=discord.Color.orange()
    )

    view = KostebekView()

    await ctx.send(embed=embed, view=view)

class KostebekView(View):

    def __init__(self):
        super().__init__()

    @discord.ui.button(label="Katıl", style=discord.ButtonStyle.green)
    async def katil(self, interaction, button):

        if interaction.user in kostebek_katilim:
            return await interaction.response.send_message("❌ Zaten katıldın!", ephemeral=True)

        kostebek_katilim.append(interaction.user)

        liste = "\n".join([u.name for u in kostebek_katilim])

        embed = discord.Embed(
            title="🕵️ Köstebek Oyunu",
            description=f"Katılanlar:\n{liste}",
            color=discord.Color.orange()
        )

        await interaction.response.edit_message(embed=embed, view=self)

# ---------------- BASLAT ----------------
@bot.command()
@commands.has_permissions(administrator=True)
async def baslat(ctx):

    if len(kostebek_katilim) < 3:
        return await ctx.send("❌ En az 3 kişi lazım!")

    secilen = random.choice(kostebek_katilim)

    try:
        await ctx.author.send(f"🕵️ Köstebek: {secilen.mention}")
        await ctx.send("🎮 Oyun başladı!")
    except:
        await ctx.send("❌ DM kapalı!")

    kostebek_katilim.clear()

# ---------------- YARDIM ----------------
@bot.command()
async def yardim(ctx):

    embed = discord.Embed(title="📖 Yardım")

    embed.add_field(name="Kayıt", value=".k .kayitsiz .kayıtsay", inline=False)
    embed.add_field(name="Değer", value=".dver .dsil", inline=False)
    embed.add_field(name="Oyun", value=".kostebekozel .baslat", inline=False)

    await ctx.send(embed=embed)

# ---------------- RUN ----------------
bot.run(os.getenv("TOKEN"))
