import discord
from discord.ext import commands
from discord.ui import View, Select
import os
from dotenv import load_dotenv

load_dotenv()

# ---------------- AYARLAR ----------------
KAYIT_YETKILI = 1499363286615855144
KAYITSIZ_ROL = 1499363348175782028

FUTBOLCU_ROL = 1499363339892162560
BASKAN_ROL = 1499363343683817542
UYE_ROL = 1499363345189310615

LOG_KANAL = 123456789012345678

# ---------------- INTENTS ----------------
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix=".", intents=intents)

kayit_sayilari = {}

# ---------------- LOG ----------------
async def log_gonder(guild, mesaj):
    kanal = guild.get_channel(LOG_KANAL)
    if kanal:
        await kanal.send(mesaj)

# ---------------- ERROR SYSTEM ----------------
@bot.event
async def on_command_error(ctx, error):

    if isinstance(error, commands.CommandNotFound):
        return await ctx.send("❌ Komut bulunamadı!")

    elif isinstance(error, commands.MissingRequiredArgument):
        return await ctx.send("❌ Eksik argüman!")

    elif isinstance(error, commands.MemberNotFound):
        return await ctx.send("❌ Kullanıcı bulunamadı!")

    elif isinstance(error, commands.MissingRole):
        return await ctx.send("❌ Yetkin yok!")

    else:
        await ctx.send("❌ Beklenmeyen hata!")
        raise error

# ---------------- KAYITSIZ ----------------
@bot.command()
async def kayitsiz(ctx, member: discord.Member = None):

    if KAYIT_YETKILI not in [r.id for r in ctx.author.roles]:
        return await ctx.send("❌ Yetkin yok!")

    # ALL KOMUTU
    if member is None or str(member).lower() == "all":

        await ctx.send("⚠️ Tüm kullanıcılar kayıtsıza çekiliyor...")

        kayitsiz_rol = ctx.guild.get_role(KAYITSIZ_ROL)

        for m in ctx.guild.members:
            if m.bot:
                continue
            try:
                await m.edit(roles=[])
                await m.add_roles(kayitsiz_rol)
            except:
                pass

        await ctx.send("✅ Tüm kullanıcılar kayıtsıza alındı.")
        await log_gonder(ctx.guild, f"🔴 TOPLU KAYITSIZ | Yetkili: {ctx.author}")
        return

    # TEK KULLANICI
    await member.edit(roles=[])

    rol = ctx.guild.get_role(KAYITSIZ_ROL)
    await member.add_roles(rol)

    await ctx.send(f"🔴 {member.mention} kayıtsız yapıldı.")
    await log_gonder(ctx.guild, f"🔴 Kayıtsız: {member} | Yetkili: {ctx.author}")

# ---------------- KAYIT MENU ----------------
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
    async def select_callback(self, interaction: discord.Interaction, select: Select):

        if interaction.user != self.yetkili:
            return await interaction.response.send_message("❌ Bu menü sana ait değil!", ephemeral=True)

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

        kayit_sayilari[self.yetkili.id] = kayit_sayilari.get(self.yetkili.id, 0) + 1

        await interaction.response.send_message(
            f"✅ {self.member.mention} kayıt edildi: {rol.name}",
            ephemeral=True
        )

        await log_gonder(
            interaction.guild,
            f"🟢 Kayıt: {self.member} → {rol.name} | Yetkili: {self.yetkili}"
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

    await ctx.send(embed=embed, view=KayitMenu(member, ctx.author))

# ---------------- KAYIT SAY ----------------
@bot.command()
async def kayitsay(ctx):
    sayi = kayit_sayilari.get(ctx.author.id, 0)
    await ctx.send(f"📊 {ctx.author.mention} toplam kayıt: {sayi}")

# ---------------- READY ----------------
@bot.event
async def on_ready():
    print(f"Bot aktif: {bot.user}")

# ---------------- RUN ----------------
bot.run(os.getenv("TOKEN"))
