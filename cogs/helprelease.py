import discord
from discord.ext import commands
from discord import app_commands
from typing import Optional
from config import EMBED_COLOR

class ReleaseListPaginationView(discord.ui.View):
    """View for paginating release list"""
    def __init__(self, pages: list, total_ids: int):
        super().__init__(timeout=180)
        self.pages = pages
        self.current_page = 0
        self.total_ids = total_ids
        self.message: Optional[discord.Message] = None

    def get_embed(self) -> discord.Embed:
        """Get embed for current page"""
        embed = discord.Embed(
            title="📋 Your Release List",
            description=f"```\n{self.pages[self.current_page]}\n```",
            color=EMBED_COLOR
        )
        embed.set_footer(text=f"Total: {self.total_ids} ID(s) • Page {self.current_page + 1}/{len(self.pages)}")
        return embed

    @discord.ui.button(label="◀", style=discord.ButtonStyle.primary, custom_id="prev_page_release")
    async def prev_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.current_page > 0:
            self.current_page -= 1
            await interaction.response.edit_message(embed=self.get_embed(), view=self)
        else:
            await interaction.response.defer()

    @discord.ui.button(label="▶", style=discord.ButtonStyle.primary, custom_id="next_page_release")
    async def next_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.current_page < len(self.pages) - 1:
            self.current_page += 1
            await interaction.response.edit_message(embed=self.get_embed(), view=self)
        else:
            await interaction.response.defer()

class AddReleaseIDsModal(discord.ui.Modal, title="Add IDs to Release List"):
    ids_input = discord.ui.TextInput(
        label="Pokemon IDs (space-separated)",
        placeholder="123 456 789",
        style=discord.TextStyle.paragraph,
        required=True,
        max_length=2000
    )

    def __init__(self, cog):
        super().__init__()
        self.cog = cog

    async def on_submit(self, interaction: discord.Interaction):
        ids_to_add = self.ids_input.value.split()

        if not ids_to_add:
            await interaction.response.send_message("❌ Please provide at least one ID!", ephemeral=True)
            return

        current_ids = await self.cog.get_user_ids(interaction.user.id)
        added_count = 0

        for pokemon_id in ids_to_add:
            if pokemon_id not in current_ids:
                current_ids.append(pokemon_id)
                added_count += 1

        await self.cog.save_user_ids(interaction.user.id, current_ids)

        if added_count > 0:
            await interaction.response.send_message(
                f"✅ Added {added_count} ID(s) to your release list! Total IDs: {len(current_ids)}",
                ephemeral=True
            )
        else:
            await interaction.response.send_message(
                f"⚠️ No new IDs added (all were duplicates). Total IDs: {len(current_ids)}",
                ephemeral=True
            )

class RemoveReleaseIDsModal(discord.ui.Modal, title="Remove IDs from Release List"):
    ids_input = discord.ui.TextInput(
        label="Pokemon IDs (space-separated)",
        placeholder="123 456 789",
        style=discord.TextStyle.paragraph,
        required=True,
        max_length=2000
    )

    def __init__(self, cog):
        super().__init__()
        self.cog = cog

    async def on_submit(self, interaction: discord.Interaction):
        ids_to_remove = self.ids_input.value.split()

        if not ids_to_remove:
            await interaction.response.send_message("❌ Please provide at least one ID!", ephemeral=True)
            return

        current_ids = await self.cog.get_user_ids(interaction.user.id)

        if not current_ids:
            await interaction.response.send_message("❌ Your release list is empty!", ephemeral=True)
            return

        removed_count = 0
        for pokemon_id in ids_to_remove:
            if pokemon_id in current_ids:
                current_ids.remove(pokemon_id)
                removed_count += 1

        await self.cog.save_user_ids(interaction.user.id, current_ids)

        if removed_count > 0:
            await interaction.response.send_message(
                f"✅ Removed {removed_count} ID(s) from your release list! Remaining IDs: {len(current_ids)}",
                ephemeral=True
            )
        else:
            await interaction.response.send_message(
                f"⚠️ No IDs were removed (not found in your list). Total IDs: {len(current_ids)}",
                ephemeral=True
            )

class ReleaseIDsModal(discord.ui.Modal, title="Release Pokemon IDs"):
    count_input = discord.ui.TextInput(
        label="Number of IDs to release",
        placeholder="7",
        style=discord.TextStyle.short,
        required=True,
        max_length=10
    )

    def __init__(self, cog):
        super().__init__()
        self.cog = cog

    async def on_submit(self, interaction: discord.Interaction):
        try:
            count = int(self.count_input.value)
            if count <= 0:
                await interaction.response.send_message("❌ Please provide a positive number!", ephemeral=True)
                return
        except ValueError:
            await interaction.response.send_message("❌ Count must be a valid number!", ephemeral=True)
            return

        current_ids = await self.cog.get_user_ids(interaction.user.id)

        if not current_ids:
            await interaction.response.send_message("❌ Your release list is empty! Add IDs first.", ephemeral=True)
            return

        available_count = len(current_ids)
        if count > available_count:
            await interaction.response.send_message(
                f"❌ You only have {available_count} ID(s) available in your release list!",
                ephemeral=True
            )
            return

        ids_to_release = current_ids[:count]
        remaining_ids = current_ids[count:]

        await self.cog.save_user_ids(interaction.user.id, remaining_ids)

        ids_string = ' '.join(ids_to_release)

        embed = discord.Embed(
            description=f"```\n<@716390085896962058> r {ids_string}\n```",
            color=EMBED_COLOR
        )
        embed.set_footer(text=f"{count} ID(s) removed from your release list • {len(remaining_ids)} remaining")

        await interaction.response.send_message(embed=embed)

class ReleasePanelView(discord.ui.View):
    """Main release panel with all action buttons"""
    def __init__(self, cog):
        super().__init__(timeout=300)
        self.cog = cog

    @discord.ui.button(label="➕ Add IDs", style=discord.ButtonStyle.success, row=0)
    async def add_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = AddReleaseIDsModal(self.cog)
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="➖ Remove IDs", style=discord.ButtonStyle.danger, row=0)
    async def remove_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = RemoveReleaseIDsModal(self.cog)
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="📋 View List", style=discord.ButtonStyle.primary, row=0)
    async def list_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        current_ids = await self.cog.get_user_ids(interaction.user.id)

        if not current_ids:
            await interaction.response.send_message(
                "❌ Your release list is empty! Add IDs using the Add button.",
                ephemeral=True
            )
            return

        ids_string = ' '.join(current_ids)
        ids_per_page = 150

        if len(current_ids) <= ids_per_page:
            embed = discord.Embed(
                title="📋 Your Release List",
                description=f"```\n{ids_string}\n```",
                color=EMBED_COLOR
            )
            embed.set_footer(text=f"Total: {len(current_ids)} ID(s)")
            await interaction.response.send_message(embed=embed, ephemeral=True)
        else:
            pages = []
            for i in range(0, len(current_ids), ids_per_page):
                page_ids = current_ids[i:i + ids_per_page]
                pages.append(' '.join(page_ids))

            view = ReleaseListPaginationView(pages, len(current_ids))
            embed = view.get_embed()
            await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    @discord.ui.button(label="🗑️ Clear All", style=discord.ButtonStyle.secondary, row=1)
    async def clear_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        current_ids = await self.cog.get_user_ids(interaction.user.id)

        if not current_ids:
            await interaction.response.send_message("❌ Your release list is already empty!", ephemeral=True)
            return

        await self.cog.save_user_ids(interaction.user.id, [])
        await interaction.response.send_message(
            f"✅ Cleared all {len(current_ids)} ID(s) from your release list!",
            ephemeral=True
        )

    @discord.ui.button(label="🔄 Release IDs", style=discord.ButtonStyle.primary, row=1)
    async def release_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = ReleaseIDsModal(self.cog)
        await interaction.response.send_modal(modal)

class HelpRelease(commands.Cog):
    """Commands for managing Pokemon release IDs"""

    def __init__(self, bot):
        self.bot = bot
        self.db = None

    async def cog_load(self):
        """Initialize database connection"""
        self.db = self.bot.db if hasattr(self.bot, 'db') else None
        if not self.db:
            print("Warning: Database not available in HelpRelease cog")

    async def get_user_ids(self, user_id: int) -> list:
        """Get user's release IDs from database"""
        if not self.db:
            return []

        collection = self.db.db.release_ids
        user_data = await collection.find_one({"user_id": user_id})

        if user_data and 'ids' in user_data:
            return user_data['ids']
        return []

    async def save_user_ids(self, user_id: int, ids: list):
        """Save user's release IDs to database"""
        if not self.db:
            return

        collection = self.db.db.release_ids
        await collection.update_one(
            {"user_id": user_id},
            {"$set": {"ids": ids}},
            upsert=True
        )

    @commands.command(name='releasepanel', aliases=['rp'])
    async def release_panel(self, ctx: commands.Context):
        """
        Open the release management panel.
        Usage: !releasepanel
        Aliases: !rp
        """
        embed = discord.Embed(
            title="🔧 Release Management Panel",
            description=(
                "**Welcome to the Release ID Manager!**\n\n"
                "Use the buttons below to manage your Pokemon release list:\n\n"
                "➕ **Add IDs** - Add new Pokemon IDs to your list\n"
                "➖ **Remove IDs** - Remove IDs from your list\n"
                "📋 **View List** - See all your saved IDs\n"
                "🗑️ **Clear All** - Remove all IDs from your list\n"
                "🔄 **Release IDs** - Use IDs to release Pokemon\n\n"
                "*Panel expires after 5 minutes of inactivity*"
            ),
            color=EMBED_COLOR
        )
        embed.set_footer(text=f"Requested by {ctx.author.display_name}", icon_url=ctx.author.display_avatar.url)

        view = ReleasePanelView(self)
        await ctx.reply(embed=embed, view=view, mention_author=False)

    @commands.command(name='releaseadd', aliases=['ra'])
    async def release_add(self, ctx: commands.Context, *ids: str):
        """
        Add Pokemon IDs to your release list.
        Usage: !releaseadd 123 456 789 or !ra 123 456 789
        """
        if not ids:
            await ctx.reply("❌ Please provide at least one ID!", mention_author=False)
            return

        current_ids = await self.get_user_ids(ctx.author.id)

        added_count = 0
        for pokemon_id in ids:
            if pokemon_id not in current_ids:
                current_ids.append(pokemon_id)
                added_count += 1

        await self.save_user_ids(ctx.author.id, current_ids)

        if added_count > 0:
            await ctx.reply(f"✅ Added {added_count} ID(s) to your release list! Total IDs: {len(current_ids)}", mention_author=False)
        else:
            await ctx.reply(f"⚠️ No new IDs added (all were duplicates). Total IDs: {len(current_ids)}", mention_author=False)

    @commands.command(name='releaseremove', aliases=['rr'])
    async def release_remove(self, ctx: commands.Context, *ids: str):
        """
        Remove Pokemon IDs from your release list.
        Usage: !releaseremove 123 456 789 or !rr 123 456 789
        """
        if not ids:
            await ctx.reply("❌ Please provide at least one ID!", mention_author=False)
            return

        current_ids = await self.get_user_ids(ctx.author.id)

        if not current_ids:
            await ctx.reply("❌ Your release list is empty!", mention_author=False)
            return

        removed_count = 0
        for pokemon_id in ids:
            if pokemon_id in current_ids:
                current_ids.remove(pokemon_id)
                removed_count += 1

        await self.save_user_ids(ctx.author.id, current_ids)

        if removed_count > 0:
            await ctx.reply(f"✅ Removed {removed_count} ID(s) from your release list! Remaining IDs: {len(current_ids)}", mention_author=False)
        else:
            await ctx.reply(f"⚠️ No IDs were removed (not found in your list). Total IDs: {len(current_ids)}", mention_author=False)

    @commands.command(name='releaseclear', aliases=['rc'])
    async def release_clear(self, ctx: commands.Context):
        """
        Clear all Pokemon IDs from your release list.
        Usage: !releaseclear or !rc
        """
        current_ids = await self.get_user_ids(ctx.author.id)

        if not current_ids:
            await ctx.reply("❌ Your release list is already empty!", mention_author=False)
            return

        await self.save_user_ids(ctx.author.id, [])

        await ctx.reply(f"✅ Cleared all {len(current_ids)} ID(s) from your release list!", mention_author=False)

    @commands.command(name='releaselist', aliases=['rl'])
    async def release_list(self, ctx: commands.Context):
        """
        View all Pokemon IDs in your release list.
        Usage: !releaselist or !rl
        """
        current_ids = await self.get_user_ids(ctx.author.id)

        if not current_ids:
            await ctx.reply("❌ Your release list is empty! Add IDs using `!releaseadd` first.", mention_author=False)
            return

        ids_string = ' '.join(current_ids)
        ids_per_page = 150

        if len(current_ids) <= ids_per_page:
            embed = discord.Embed(
                title="📋 Your Release List",
                description=f"```\n{ids_string}\n```",
                color=EMBED_COLOR
            )
            embed.set_footer(text=f"Total: {len(current_ids)} ID(s)")

            await ctx.reply(embed=embed, mention_author=False)
        else:
            pages = []
            for i in range(0, len(current_ids), ids_per_page):
                page_ids = current_ids[i:i + ids_per_page]
                pages.append(' '.join(page_ids))

            view = ReleaseListPaginationView(pages, len(current_ids))
            embed = view.get_embed()
            message = await ctx.reply(embed=embed, view=view, mention_author=False)
            view.message = message

    @commands.command(name='release', aliases=['r'])
    async def release_command(self, ctx: commands.Context, count: int):
        """
        Release Pokemon IDs from your list.
        Usage: !release 7 or !r 7
        """
        if count <= 0:
            await ctx.reply("❌ Please provide a positive number!", mention_author=False)
            return

        current_ids = await self.get_user_ids(ctx.author.id)

        if not current_ids:
            await ctx.reply("❌ Your release list is empty! Add IDs using `!releaseadd` first.", mention_author=False)
            return

        available_count = len(current_ids)
        if count > available_count:
            await ctx.reply(f"❌ You only have {available_count} ID(s) available in your release list!", mention_author=False)
            return

        ids_to_release = current_ids[:count]
        remaining_ids = current_ids[count:]

        await self.save_user_ids(ctx.author.id, remaining_ids)

        ids_string = ' '.join(ids_to_release)

        embed = discord.Embed(
            description=f"```\n<@716390085896962058> r {ids_string}\n```",
            color=EMBED_COLOR
        )
        embed.set_footer(text=f"{count} ID(s) removed from your release list • {len(remaining_ids)} remaining")

        await ctx.reply(embed=embed, mention_author=False)

    @app_commands.command(name='release', description='Release Pokemon IDs from your list')
    @app_commands.describe(count='Number of IDs to release')
    async def release_slash(self, interaction: discord.Interaction, count: int):
        """
        Slash command version of release.
        Usage: /release 7
        """
        if count <= 0:
            await interaction.response.send_message("❌ Please provide a positive number!", ephemeral=True)
            return

        current_ids = await self.get_user_ids(interaction.user.id)

        if not current_ids:
            await interaction.response.send_message(
                "❌ Your release list is empty! Add IDs using `!releaseadd` first.",
                ephemeral=True
            )
            return

        available_count = len(current_ids)
        if count > available_count:
            await interaction.response.send_message(
                f"❌ You only have {available_count} ID(s) available in your release list!",
                ephemeral=True
            )
            return

        ids_to_release = current_ids[:count]
        remaining_ids = current_ids[count:]

        await self.save_user_ids(interaction.user.id, remaining_ids)

        ids_string = ' '.join(ids_to_release)

        embed = discord.Embed(
            description=f"```\n<@716390085896962058> r {ids_string}\n```",
            color=EMBED_COLOR
        )
        embed.set_footer(text=f"{count} ID(s) removed from your release list • {len(remaining_ids)} remaining")

        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(HelpRelease(bot))
