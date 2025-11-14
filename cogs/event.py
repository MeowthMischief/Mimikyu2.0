import discord
from discord.ext import commands
from discord import app_commands
import re
import asyncio
import time
from typing import Set, Optional
from config import EMBED_COLOR, IDS_PER_PAGE, RECORDING_TIMEOUT, INACTIVITY_CHECK_INTERVAL

class IDRecorder:
    """Class to handle ID recording for a specific message"""
    def __init__(self, message: discord.Message, user_id: int, control_message: Optional[discord.Message], user_mention: str):
        self.message = message
        self.user_id = user_id
        self.user_mention = user_mention  # Store user mentionn
        self.ids: Set[str] = set()
        self.is_recording = True
        self.control_message = control_message
        self.last_activity = time.time()

    def extract_ids(self, description: str) -> Set[str]:
        """Extract Pokemon IDs from embed description"""
        # Pattern matches numbers in backticks with optional leading/trailing spaces
        # Works for `398121`, **`398121`**, ` 2593`, **` 2593`**, etc.
        pattern = r'`\s*(\d+)\s*`'
        matches = re.findall(pattern, description)
        return set(matches)

    async def update_ids_and_display(self):
        """Update IDs from current message embeds and update control message"""
        if not self.message.embeds:
            return

        old_count = len(self.ids)

        for embed in self.message.embeds:
            if embed.description:
                new_ids = self.extract_ids(embed.description)
                self.ids.update(new_ids)

        new_count = len(self.ids)

        # Update last activity time if new IDs were found
        if new_count > old_count:
            self.last_activity = time.time()

            # Only update if control_message exists
            if self.control_message:
                # Update control message immediately
                time_since_activity = time.time() - self.last_activity
                time_remaining = RECORDING_TIMEOUT - int(time_since_activity)
                minutes_remaining = max(0, time_remaining // 60)

                embed = discord.Embed(
                    title="<:red_dot:1391644116357746728> Recording Pokemon IDs",
                    description=f"Recording IDs from [this message]({self.message.jump_url})\n\n"
                               f"**IDs found:** {new_count}\n"
                               f"**Started by:** {self.user_mention}\n\n"
                               f"The message will be monitored for edits.\n"
                               f"Click the button below when you're done!\n\n"
                               f"⏱️ Auto-stops in ~{minutes_remaining} minutes if no new IDs.",
                    color=EMBED_COLOR
                )
                try:
                    await self.control_message.edit(embed=embed)
                except:
                    pass

class StopRecordingView(discord.ui.View):
    """View with stop recording button"""
    def __init__(self, recorder: IDRecorder, cog):
        super().__init__(timeout=None)
        self.recorder = recorder
        self.cog = cog

    @discord.ui.button(label="Stop Recording", style=discord.ButtonStyle.danger, custom_id="stop_recording")
    async def stop_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Anyone can stop the recording

        # Stop recording
        self.recorder.is_recording = False

        # Disable the button
        button.disabled = True
        await interaction.message.edit(view=self)

        # Show the results
        await interaction.response.defer()
        await self.cog.show_results(interaction.channel, self.recorder, interaction.user)

class IDPaginationView(discord.ui.View):
    """View for paginating large lists of IDs"""
    def __init__(self, pages: list, total_ids: int):
        super().__init__(timeout=180)
        self.pages = pages
        self.current_page = 0
        self.total_ids = total_ids
        self.message: Optional[discord.Message] = None

    def get_message_content(self) -> str:
        """Get message content for current page"""
        footer = f"Total IDs: {self.total_ids} • Page {self.current_page + 1}/{len(self.pages)}"
        return f"{footer}\n```\n{self.pages[self.current_page]}\n```"

    @discord.ui.button(label="◀", style=discord.ButtonStyle.primary, custom_id="prev_page")
    async def prev_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.current_page > 0:
            self.current_page -= 1
            await interaction.response.edit_message(content=self.get_message_content(), view=self)
        else:
            await interaction.response.defer()

    @discord.ui.button(label="▶", style=discord.ButtonStyle.primary, custom_id="next_page")
    async def next_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.current_page < len(self.pages) - 1:
            self.current_page += 1
            await interaction.response.edit_message(content=self.get_message_content(), view=self)
        else:
            await interaction.response.defer()

class EventCog(commands.Cog):
    """Cog for recording Pokemon IDs from messages"""

    def __init__(self, bot):
        self.bot = bot
        self.recorders: dict[int, IDRecorder] = {}  # message_id -> IDRecorder

    @commands.Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message):
        """Listen for message edits to update IDs - IMMEDIATE update"""
        if after.id in self.recorders:
            recorder = self.recorders[after.id]
            if recorder.is_recording:
                recorder.message = after
                await recorder.update_ids_and_display()

    @commands.command(name='id')
    async def record_ids(self, ctx: commands.Context):
        """
        Start recording Pokemon IDs from a replied message.
        Usage: Reply to a message with embeds and use !id
        """
        # Check if this is a reply
        if not ctx.message.reference:
            await ctx.send("❌ Please reply to a message with Pokemon embeds to start recording IDs!")
            return

        # Get the referenced message
        try:
            replied_message = await ctx.channel.fetch_message(ctx.message.reference.message_id)
        except discord.NotFound:
            await ctx.send("❌ Could not find the replied message!")
            return
        except discord.Forbidden:
            await ctx.send("❌ I don't have permission to read that message!")
            return

        # Check if message has embeds
        if not replied_message.embeds:
            await ctx.send("❌ The replied message doesn't have any embeds!")
            return

        # Check if already recording this message
        if replied_message.id in self.recorders:
            await ctx.send("⚠️ Already recording IDs from this message!")
            return

        # Create embed
        embed = discord.Embed(
            title="<:red_dot:1391644116357746728> Recording Pokemon IDs",
            description=f"Recording IDs from [this message]({replied_message.jump_url})\n\n"
                       f"**IDs found:** 0\n"
                       f"**Started by:** {ctx.author.mention}\n\n"
                       f"The message will be monitored for edits.\n"
                       f"Click the button below when you're done!\n\n"
                       f"⏱️ Auto-stops after {RECORDING_TIMEOUT // 60} minutes of inactivity.",
            color=EMBED_COLOR
        )

        # Create a placeholder recorder with user mention stored
        recorder = IDRecorder(replied_message, ctx.author.id, None, ctx.author.mention)

        # Create view with the recorder
        view = StopRecordingView(recorder, self)

        # Send message with embed AND view at the same time
        control_msg = await ctx.send(embed=embed, view=view)

        # Update the recorder with the control message reference
        recorder.control_message = control_msg

        # Now update IDs and add to recorders
        await recorder.update_ids_and_display()
        self.recorders[replied_message.id] = recorder

        # Start timeout monitoring task
        asyncio.create_task(self.monitor_timeout(recorder))

    async def monitor_timeout(self, recorder: IDRecorder):
        """Monitor for timeout only - ID updates happen immediately in on_message_edit"""
        while recorder.is_recording:
            await asyncio.sleep(INACTIVITY_CHECK_INTERVAL)

            if not recorder.is_recording:
                break

            time_since_activity = time.time() - recorder.last_activity

            if time_since_activity >= RECORDING_TIMEOUT:
                # Auto-stop due to inactivity
                recorder.is_recording = False

                # Update control message
                embed = discord.Embed(
                    title="⏹️ Recording Stopped (Timeout)",
                    description=f"Recording automatically stopped due to inactivity.\n\n"
                               f"**IDs found:** {len(recorder.ids)}",
                    color=EMBED_COLOR
                )

                try:
                    # Disable the button
                    view = discord.ui.View()
                    button = discord.ui.Button(label="Stop Recording", style=discord.ButtonStyle.danger, disabled=True)
                    view.add_item(button)
                    await recorder.control_message.edit(embed=embed, view=view)
                except:
                    pass

                # Show results
                await self.show_results(recorder.control_message.channel, recorder, None)
                break

    async def show_results(self, channel: discord.TextChannel, recorder: IDRecorder, stopped_by: Optional[discord.User]):
        """Display the recorded IDs with pagination if needed"""
        # Remove from active recorders
        if recorder.message.id in self.recorders:
            del self.recorders[recorder.message.id]

        if not recorder.ids:
            await channel.send("No Pokemon IDs were found!")
            return

        # Sort IDs (descending - newest first)
        sorted_ids = sorted(recorder.ids, key=lambda x: int(x), reverse=True)

        # Format as space-separated string
        id_string = ' '.join(sorted_ids)

        # Check if pagination is needed
        if len(sorted_ids) <= IDS_PER_PAGE:
            # Single page - send as plain message with backticks
            footer_text = f"Total IDs: {len(sorted_ids)}"
            if stopped_by:
                footer_text += f" • Stopped by {stopped_by.name}"

            await channel.send(f"{footer_text}\n```\n{id_string}\n```")
        else:
            # Multiple pages needed
            pages = []
            for i in range(0, len(sorted_ids), IDS_PER_PAGE):
                page_ids = sorted_ids[i:i + IDS_PER_PAGE]
                pages.append(' '.join(page_ids))

            view = IDPaginationView(pages, len(sorted_ids))
            content = view.get_message_content()
            if stopped_by:
                content = content.replace(f"Total IDs: {len(sorted_ids)}", f"Total IDs: {len(sorted_ids)} • Stopped by {stopped_by.name}")
            message = await channel.send(content=content, view=view)
            view.message = message

async def setup(bot):
    """Setup function to load the cog"""
    await bot.add_cog(EventCog(bot))
