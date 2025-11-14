import discord
from discord.ext import commands
from discord import app_commands
from typing import Optional, List, Dict
from config import EMBED_COLOR

class EvolveListView(discord.ui.View):
    """View for evolve list with tabs for 1x and 2x uses"""
    def __init__(self, once_ids: List[str], twice_ids: List[str], ids_per_page: int = 50):
        super().__init__(timeout=180)
        self.once_ids = once_ids
        self.twice_ids = twice_ids
        self.ids_per_page = ids_per_page
        self.current_tab = "once"  # Start with once (priority)
        self.current_page = 0
        self.message: Optional[discord.Message] = None

        # Create pages for each tab
        self.once_pages = self._create_pages(once_ids)
        self.twice_pages = self._create_pages(twice_ids)

    def _create_pages(self, ids: List[str]) -> List[str]:
        """Create pages from ID list"""
        if not ids:
            return []

        pages = []
        for i in range(0, len(ids), self.ids_per_page):
            page_ids = ids[i:i + self.ids_per_page]
            pages.append(' '.join(page_ids))
        return pages

    def get_embed(self) -> discord.Embed:
        """Get embed for current tab and page"""
        if self.current_tab == "once":
            pages = self.once_pages
            tab_name = "1x Use (Priority)"
            total = len(self.once_ids)
        else:
            pages = self.twice_pages
            tab_name = "2x Uses"
            total = len(self.twice_ids)

        if not pages:
            description = "```\nNo IDs in this category\n```"
            footer_text = f"{tab_name} • 0 ID(s)"
            title = f"📋 Your Evolve List - {tab_name}"
        else:
            description = f"```\n{pages[self.current_page]}\n```"
            footer_text = f"{total} ID(s) • Page {self.current_page + 1}/{len(pages)}"
            title = f"📋 Your Evolve List - {tab_name}"

        embed = discord.Embed(
            title=title,
            description=description,
            color=EMBED_COLOR
        )
        embed.set_footer(text=footer_text)
        return embed

    @discord.ui.button(label="Once (1x) ⭐", style=discord.ButtonStyle.primary, custom_id="tab_once")
    async def once_tab(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_tab = "once"
        self.current_page = 0
        await interaction.response.edit_message(embed=self.get_embed(), view=self)

    @discord.ui.button(label="Twice (2x)", style=discord.ButtonStyle.secondary, custom_id="tab_twice")
    async def twice_tab(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_tab = "twice"
        self.current_page = 0
        await interaction.response.edit_message(embed=self.get_embed(), view=self)

    @discord.ui.button(label="◀", style=discord.ButtonStyle.primary, custom_id="prev_page_evolve")
    async def prev_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        pages = self.once_pages if self.current_tab == "once" else self.twice_pages
        if pages and self.current_page > 0:
            self.current_page -= 1
            await interaction.response.edit_message(embed=self.get_embed(), view=self)
        else:
            await interaction.response.defer()

    @discord.ui.button(label="▶", style=discord.ButtonStyle.primary, custom_id="next_page_evolve")
    async def next_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        pages = self.once_pages if self.current_tab == "once" else self.twice_pages
        if pages and self.current_page < len(pages) - 1:
            self.current_page += 1
            await interaction.response.edit_message(embed=self.get_embed(), view=self)
        else:
            await interaction.response.defer()

class AddIDsModal(discord.ui.Modal, title="Add IDs to Evolve List"):
    ids_input = discord.ui.TextInput(
        label="Pokemon IDs (space-separated)",
        placeholder="123 456 789",
        style=discord.TextStyle.paragraph,
        required=True,
        max_length=2000
    )

    uses = discord.ui.TextInput(
        label="Uses per ID (1 or 2)",
        placeholder="2",
        style=discord.TextStyle.short,
        required=True,
        default="2",
        max_length=1
    )

    def __init__(self, cog):
        super().__init__()
        self.cog = cog

    async def on_submit(self, interaction: discord.Interaction):
        try:
            uses = int(self.uses.value)
            if uses not in [1, 2]:
                await interaction.response.send_message("❌ Uses must be either 1 or 2!", ephemeral=True)
                return
        except ValueError:
            await interaction.response.send_message("❌ Uses must be a number (1 or 2)!", ephemeral=True)
            return

        ids_to_add = self.ids_input.value.split()

        if not ids_to_add:
            await interaction.response.send_message("❌ Please provide at least one ID!", ephemeral=True)
            return

        current_ids = await self.cog.get_user_ids(interaction.user.id)
        added_count = 0

        for pokemon_id in ids_to_add:
            exists = any(item['id'] == pokemon_id for item in current_ids)
            if not exists:
                current_ids.append({'id': pokemon_id, 'uses': uses})
                added_count += 1

        await self.cog.save_user_ids(interaction.user.id, current_ids)

        use_text = "1 use" if uses == 1 else "2 uses"
        if added_count > 0:
            await interaction.response.send_message(
                f"✅ Added {added_count} ID(s) with {use_text} to your evolve list! Total IDs: {len(current_ids)}",
                ephemeral=True
            )
        else:
            await interaction.response.send_message(
                f"⚠️ No new IDs added (all were duplicates). Total IDs: {len(current_ids)}",
                ephemeral=True
            )

class RemoveIDsModal(discord.ui.Modal, title="Remove IDs from Evolve List"):
    ids_input = discord.ui.TextInput(
        label="Pokemon IDs (space-separated)",
        placeholder="123 456 789",
        style=discord.TextStyle.paragraph,
        required=True,
        max_length=2000
    )

    remove_type = discord.ui.TextInput(
        label="Remove type (all/once)",
        placeholder="all",
        style=discord.TextStyle.short,
        required=True,
        default="all",
        max_length=10
    )

    def __init__(self, cog):
        super().__init__()
        self.cog = cog

    async def on_submit(self, interaction: discord.Interaction):
        remove_type = self.remove_type.value.lower()
        if remove_type not in ["all", "once"]:
            await interaction.response.send_message("❌ Remove type must be 'all' or 'once'!", ephemeral=True)
            return

        remove_once = remove_type == "once"
        ids_to_remove = self.ids_input.value.split()

        if not ids_to_remove:
            await interaction.response.send_message("❌ Please provide at least one ID!", ephemeral=True)
            return

        current_ids = await self.cog.get_user_ids(interaction.user.id)

        if not current_ids:
            await interaction.response.send_message("❌ Your evolve list is empty!", ephemeral=True)
            return

        removed_count = 0
        new_ids = []

        for item in current_ids:
            if item['id'] in ids_to_remove:
                if remove_once and item['uses'] > 1:
                    new_ids.append({'id': item['id'], 'uses': item['uses'] - 1})
                    removed_count += 1
                elif remove_once and item['uses'] == 1:
                    removed_count += 1
                elif not remove_once:
                    removed_count += 1
                else:
                    new_ids.append(item)
            else:
                new_ids.append(item)

        await self.cog.save_user_ids(interaction.user.id, new_ids)

        if removed_count > 0:
            action = "use(s) removed from" if remove_once else "ID(s) removed from"
            await interaction.response.send_message(
                f"✅ {removed_count} {action} your evolve list! Remaining IDs: {len(new_ids)}",
                ephemeral=True
            )
        else:
            await interaction.response.send_message(
                f"⚠️ No IDs were removed (not found in your list). Total IDs: {len(new_ids)}",
                ephemeral=True
            )

class EvolveIDsModal(discord.ui.Modal, title="Evolve Pokemon IDs"):
    count_input = discord.ui.TextInput(
        label="Number of IDs to evolve",
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
            await interaction.response.send_message("❌ Your evolve list is empty! Add IDs first.", ephemeral=True)
            return

        available_count = len(current_ids)
        if count > available_count:
            await interaction.response.send_message(
                f"❌ You only have {available_count} ID(s) available in your evolve list!",
                ephemeral=True
            )
            return

        # Priority: Pick from 1x (once) first, then 2x (twice)
        ids_to_evolve, remaining_ids = self.cog.select_ids_with_priority(current_ids, count)

        await self.cog.save_user_ids(interaction.user.id, remaining_ids)

        ids_string = ' '.join([item['id'] for item in ids_to_evolve])

        # Count how many came from each category
        once_used = sum(1 for item in ids_to_evolve if item['uses'] == 1)
        twice_used = sum(1 for item in ids_to_evolve if item['uses'] == 2)
        
        footer_parts = []
        if once_used > 0:
            footer_parts.append(f"{once_used} from 1x")
        if twice_used > 0:
            footer_parts.append(f"{twice_used} from 2x")
        footer_text = f"{count} ID(s) used ({', '.join(footer_parts)}) • {len(remaining_ids)} remaining"

        embed = discord.Embed(
            description=f"```\n<@716390085896962058> evolve {ids_string}\n```",
            color=EMBED_COLOR
        )
        embed.set_footer(text=footer_text)

        await interaction.response.send_message(embed=embed)

class EvolvePanelView(discord.ui.View):
    """Main evolve panel with all action buttons"""
    def __init__(self, cog):
        super().__init__(timeout=300)
        self.cog = cog

    @discord.ui.button(label="➕ Add IDs", style=discord.ButtonStyle.success, row=0)
    async def add_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = AddIDsModal(self.cog)
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="➖ Remove IDs", style=discord.ButtonStyle.danger, row=0)
    async def remove_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = RemoveIDsModal(self.cog)
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="📋 View List", style=discord.ButtonStyle.primary, row=0)
    async def list_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        current_ids = await self.cog.get_user_ids(interaction.user.id)

        if not current_ids:
            await interaction.response.send_message(
                "❌ Your evolve list is empty! Add IDs using the Add button.",
                ephemeral=True
            )
            return

        once_ids = [item['id'] for item in current_ids if item['uses'] == 1]
        twice_ids = [item['id'] for item in current_ids if item['uses'] == 2]

        view = EvolveListView(once_ids, twice_ids)
        embed = view.get_embed()
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    @discord.ui.button(label="🗑️ Clear All", style=discord.ButtonStyle.secondary, row=1)
    async def clear_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        current_ids = await self.cog.get_user_ids(interaction.user.id)

        if not current_ids:
            await interaction.response.send_message("❌ Your evolve list is already empty!", ephemeral=True)
            return

        await self.cog.save_user_ids(interaction.user.id, [])
        await interaction.response.send_message(
            f"✅ Cleared all {len(current_ids)} ID(s) from your evolve list!",
            ephemeral=True
        )

    @discord.ui.button(label="🔄 Evolve IDs", style=discord.ButtonStyle.primary, row=1)
    async def evolve_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = EvolveIDsModal(self.cog)
        await interaction.response.send_modal(modal)

class HelpEvolve(commands.Cog):
    """Commands for managing Pokemon evolve IDs"""

    def __init__(self, bot):
        self.bot = bot
        self.db = None

    async def cog_load(self):
        """Initialize database connection"""
        self.db = self.bot.db if hasattr(self.bot, 'db') else None
        if not self.db:
            print("Warning: Database not available in HelpEvolve cog")

    async def get_user_ids(self, user_id: int) -> List[Dict]:
        """Get user's evolve IDs from database"""
        if not self.db:
            return []

        collection = self.db.db.evolve_ids
        user_data = await collection.find_one({"user_id": user_id})

        if user_data and 'ids' in user_data:
            return user_data['ids']
        return []

    async def save_user_ids(self, user_id: int, ids: List[Dict]):
        """Save user's evolve IDs to database"""
        if not self.db:
            return

        collection = self.db.db.evolve_ids
        await collection.update_one(
            {"user_id": user_id},
            {"$set": {"ids": ids}},
            upsert=True
        )

    def select_ids_with_priority(self, current_ids: List[Dict], count: int) -> tuple[List[Dict], List[Dict]]:
        """
        Select IDs with priority: 1x (once) first, then 2x (twice)
        Returns: (ids_to_evolve, remaining_ids)
        """
        # Separate into once and twice lists
        once_ids = [item for item in current_ids if item['uses'] == 1]
        twice_ids = [item for item in current_ids if item['uses'] == 2]

        ids_to_evolve = []
        
        # First, take from once (1x) list
        if len(once_ids) >= count:
            # We have enough in once list
            ids_to_evolve = once_ids[:count]
            remaining_once = once_ids[count:]
            remaining_twice = twice_ids
        else:
            # Take all from once, then fill from twice
            ids_to_evolve = once_ids.copy()
            needed = count - len(once_ids)
            ids_to_evolve.extend(twice_ids[:needed])
            remaining_once = []
            remaining_twice = twice_ids[needed:]

        # Build remaining IDs list
        remaining_ids = []
        
        # Add remaining once IDs (these stay as is)
        remaining_ids.extend(remaining_once)
        
        # Add remaining twice IDs (these stay as is)
        remaining_ids.extend(remaining_twice)
        
        # For twice IDs that were used, add them back with uses-1
        for item in ids_to_evolve:
            if item['uses'] == 2:
                remaining_ids.append({'id': item['id'], 'uses': 1})

        return ids_to_evolve, remaining_ids

    @commands.command(name='evolvepanel', aliases=['ep'])
    async def evolve_panel(self, ctx: commands.Context):
        """
        Open the evolve management panel.
        Usage: !evolvepanel
        Aliases: !ep
        """
        embed = discord.Embed(
            title="🔧 Evolve Management Panel",
            description=(
                "**Welcome to the Evolve ID Manager!**\n\n"
                "Use the buttons below to manage your Pokemon evolve list:\n\n"
                "➕ **Add IDs** - Add new Pokemon IDs to your list\n"
                "➖ **Remove IDs** - Remove IDs from your list\n"
                "📋 **View List** - See all your saved IDs\n"
                "🗑️ **Clear All** - Remove all IDs from your list\n"
                "🔄 **Evolve IDs** - Use IDs to evolve Pokemon\n\n"
                "⭐ **Priority System:** IDs with 1x use are picked first, then 2x use\n"
                "*Panel expires after 5 minutes of inactivity*"
            ),
            color=EMBED_COLOR
        )
        embed.set_footer(text=f"Requested by {ctx.author.display_name}", icon_url=ctx.author.display_avatar.url)

        view = EvolvePanelView(self)
        await ctx.reply(embed=embed, view=view, mention_author=False)

    @commands.command(name='evolveadd', aliases=['ea'])
    async def evolve_add(self, ctx: commands.Context, *args):
        """
        Add Pokemon IDs to your evolve list.
        Usage: !evolveadd 123 456 789 (defaults to 2 uses)
               !evolveadd 123 456 --once (adds with 1 use)
        Aliases: !ea
        """
        if not args:
            await ctx.reply("❌ Please provide at least one ID!", mention_author=False)
            return

        args_list = list(args)
        uses = 1 if '--once' in args_list else 2

        ids_to_add = [arg for arg in args_list if arg != '--once']

        if not ids_to_add:
            await ctx.reply("❌ Please provide at least one ID!", mention_author=False)
            return

        current_ids = await self.get_user_ids(ctx.author.id)

        added_count = 0
        for pokemon_id in ids_to_add:
            exists = any(item['id'] == pokemon_id for item in current_ids)
            if not exists:
                current_ids.append({'id': pokemon_id, 'uses': uses})
                added_count += 1

        await self.save_user_ids(ctx.author.id, current_ids)

        use_text = "1 use" if uses == 1 else "2 uses"
        if added_count > 0:
            total_count = len(current_ids)
            await ctx.reply(f"✅ Added {added_count} ID(s) with {use_text} to your evolve list! Total IDs: {total_count}", mention_author=False)
        else:
            await ctx.reply(f"⚠️ No new IDs added (all were duplicates). Total IDs: {len(current_ids)}", mention_author=False)

    @commands.command(name='evolveremove', aliases=['er'])
    async def evolve_remove(self, ctx: commands.Context, *args):
        """
        Remove Pokemon IDs from your evolve list.
        Usage: !evolveremove 123 456 (removes completely)
               !evolveremove 123 456 --once (removes one use only)
        Aliases: !er
        """
        if not args:
            await ctx.reply("❌ Please provide at least one ID!", mention_author=False)
            return

        args_list = list(args)
        remove_once = '--once' in args_list

        ids_to_remove = [arg for arg in args_list if arg != '--once']

        if not ids_to_remove:
            await ctx.reply("❌ Please provide at least one ID!", mention_author=False)
            return

        current_ids = await self.get_user_ids(ctx.author.id)

        if not current_ids:
            await ctx.reply("❌ Your evolve list is empty!", mention_author=False)
            return

        removed_count = 0
        new_ids = []

        for item in current_ids:
            if item['id'] in ids_to_remove:
                if remove_once and item['uses'] > 1:
                    new_ids.append({'id': item['id'], 'uses': item['uses'] - 1})
                    removed_count += 1
                elif remove_once and item['uses'] == 1:
                    removed_count += 1
                elif not remove_once:
                    removed_count += 1
                else:
                    new_ids.append(item)
            else:
                new_ids.append(item)

        await self.save_user_ids(ctx.author.id, new_ids)

        if removed_count > 0:
            action = "use(s) removed from" if remove_once else "ID(s) removed from"
            await ctx.reply(f"✅ {removed_count} {action} your evolve list! Remaining IDs: {len(new_ids)}", mention_author=False)
        else:
            await ctx.reply(f"⚠️ No IDs were removed (not found in your list). Total IDs: {len(new_ids)}", mention_author=False)

    @commands.command(name='evolveclear', aliases=['ec'])
    async def evolve_clear(self, ctx: commands.Context):
        """
        Clear all Pokemon IDs from your evolve list.
        Usage: !evolveclear
        Aliases: !ec
        """
        current_ids = await self.get_user_ids(ctx.author.id)

        if not current_ids:
            await ctx.reply("❌ Your evolve list is already empty!", mention_author=False)
            return

        await self.save_user_ids(ctx.author.id, [])

        await ctx.reply(f"✅ Cleared all {len(current_ids)} ID(s) from your evolve list!", mention_author=False)

    @commands.command(name='evolvelist', aliases=['el'])
    async def evolve_list(self, ctx: commands.Context):
        """
        View all Pokemon IDs in your evolve list.
        Usage: !evolvelist
        Aliases: !el
        """
        current_ids = await self.get_user_ids(ctx.author.id)

        if not current_ids:
            await ctx.reply("❌ Your evolve list is empty! Add IDs using `!evolveadd` first.", mention_author=False)
            return

        once_ids = [item['id'] for item in current_ids if item['uses'] == 1]
        twice_ids = [item['id'] for item in current_ids if item['uses'] == 2]

        view = EvolveListView(once_ids, twice_ids)
        embed = view.get_embed()
        message = await ctx.reply(embed=embed, view=view, mention_author=False)
        view.message = message

    @commands.command(name='evolve', aliases=['e'])
    async def evolve_command(self, ctx: commands.Context, count: int):
        """
        Evolve Pokemon IDs from your list.
        Usage: !evolve 7
        Aliases: !e
        """
        if count <= 0:
            await ctx.send("❌ Please provide a positive number!")
            return

        current_ids = await self.get_user_ids(ctx.author.id)

        if not current_ids:
            await ctx.send("❌ Your evolve list is empty! Add IDs using `!evolveadd` first.")
            return

        available_count = len(current_ids)
        if count > available_count:
            await ctx.send(f"❌ You only have {available_count} ID(s) available in your evolve list!")
            return

        # Priority: Pick from 1x (once) first, then 2x (twice)
        ids_to_evolve, remaining_ids = self.select_ids_with_priority(current_ids, count)

        await self.save_user_ids(ctx.author.id, remaining_ids)

        ids_string = ' '.join([item['id'] for item in ids_to_evolve])

        # Count how many came from each category
        once_used = sum(1 for item in ids_to_evolve if item['uses'] == 1)
        twice_used = sum(1 for item in ids_to_evolve if item['uses'] == 2)
        
        footer_parts = []
        if once_used > 0:
            footer_parts.append(f"{once_used} from 1x")
        if twice_used > 0:
            footer_parts.append(f"{twice_used} from 2x")
        footer_text = f"{count} ID(s) used ({', '.join(footer_parts)}) • {len(remaining_ids)} remaining"

        embed = discord.Embed(
            description=f"```\n<@716390085896962058> evolve {ids_string}\n```",
            color=EMBED_COLOR
        )
        embed.set_footer(text=footer_text)

        await ctx.send(embed=embed)

    @app_commands.command(name='evolve', description='Evolve Pokemon IDs from your list')
    @app_commands.describe(count='Number of IDs to evolve')
    async def evolve_slash(self, interaction: discord.Interaction, count: int):
        """
        Slash command version of evolve.
        Usage: /evolve 7
        """
        if count <= 0:
            await interaction.response.send_message("❌ Please provide a positive number!", ephemeral=True)
            return

        current_ids = await self.get_user_ids(interaction.user.id)

        if not current_ids:
            await interaction.response.send_message(
                "❌ Your evolve list is empty! Add IDs using `!evolveadd` first.",
                ephemeral=True
            )
            return

        available_count = len(current_ids)
        if count > available_count:
            await interaction.response.send_message(
                f"❌ You only have {available_count} ID(s) available in your evolve list!",
                ephemeral=True
            )
            return

        # Priority: Pick from 1x (once) first, then 2x (twice)
        ids_to_evolve, remaining_ids = self.select_ids_with_priority(current_ids, count)

        await self.save_user_ids(interaction.user.id, remaining_ids)

        ids_string = ' '.join([item['id'] for item in ids_to_evolve])

        # Count how many came from each category
        once_used = sum(1 for item in ids_to_evolve if item['uses'] == 1)
        twice_used = sum(1 for item in ids_to_evolve if item['uses'] == 2)
        
        footer_parts = []
        if once_used > 0:
            footer_parts.append(f"{once_used} from 1x")
        if twice_used > 0:
            footer_parts.append(f"{twice_used} from 2x")
        footer_text = f"{count} ID(s) used ({', '.join(footer_parts)}) • {len(remaining_ids)} remaining"

        embed = discord.Embed(
            description=f"```\n<@716390085896962058> evolve {ids_string}\n```",
            color=EMBED_COLOR
        )
        embed.set_footer(text=footer_text)

        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(HelpEvolve(bot))
